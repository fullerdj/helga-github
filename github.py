import treq
import re
from helga.plugins import match, ResponseNotReady
from helga import log, settings

from twisted.internet import defer
from twisted.internet import _sslverify

_sslverify.platformTrust = lambda: None    # disable SSL certificate validation

logger = log.getLogger(__name__)

def construct_urls(proj, repo, number):
    """
    Helper to build a list of URLs to search for a matching PR.
    """
    stem = "https://api.github.com/repos/"
    urls = []
    if proj:
       if repo:
          return [stem + proj + '/' + repo + '/pulls/' + number]
       else:
          raise NotImplemented
 
    for proj_repo in settings.GITHUB_PROJECTS:
       urls.append(stem + proj_repo + '/pulls/' + number)
 
    logger.debug("constructed " + str(urls))
    return urls

@defer.inlineCallbacks
def get_pr_info(pr):
    """
    Search the list of GITHUB_PROJECTS for an open PR with the given number
    and return the first one found. If no open PRs are found, return the first
    closed one found.

    TODO: improve error handling. Right now, it's hard to tell what went wrong
    since it's expected that some PRs will not be round.

    Find the "html_url" string (corresponding to the browser landing page) and
    the "title" string in the JSON data of the matching PR
    :param (proj, repo, number), a tuple with the target project, repo, and PR
           number. If project or repo are None, search all projects/repos in
           settings.GITHUB_PROJECTS.
    :returns: twisted.internet.defer.Deferred. When this Deferred fires, it
              will return a tuple containing the landing page and title for
              the PR of interest
    """
    logger.debug("searching for " + str(pr))
    proj, repo, number = pr
    pr_urls = construct_urls(proj, repo, number)
    pr_jsons = []

    for pr_url in pr_urls:
        try:
            response = yield treq.get(pr_url,
                                      headers={'User-Agent':'helga-github/0.1'},
                                      timeout=5)
            logger.debug(pr_url + " HTTP response code " + str(response.code))
            if response.code != 200:
                continue
            else:
                content = yield treq.json_content(response)
                pr_jsons.append(content)
        except Exception, e:
            # For example, if treq.get() timed out, or if treq.json_content()
            # could not parse the JSON, etc.
            err = 'could not read PR, %s' % e.message
            defer.returnValue((pr_url, err))

    first_closed = html_url = title = ""
    for pr_json in pr_jsons:
        is_open = False
        try:
            html_url = pr_json['html_url']
            title = pr_json['title']
            is_open = pr_json['state'] == 'open'
        except KeyError:
            continue
        if is_open:
            defer.returnValue((html_url, title))
        elif not first_closed:
            first_closed = (html_url, title)
    else:
        if first_closed:
            defer.returnValue(first_closed)
        else:
            defer.returnValue(("", "couldn't find PR " + number))

def construct_message(urls_and_titles, nick):
    """
    Return a string about a nick and a list of tickets' URLs and titles.
    """
    msgs = []
    for url_and_title in urls_and_titles:
        pr_url, title = url_and_title
        msgs.append('%s [%s]' % (pr_url, title))
    if len(msgs) == 1:
        msg = msgs[0]
    else:
        msg = "{} and {}".format(", ".join(msgs[:-1]), msgs[-1])
    return "%s might be talking about %s" % (nick, msg)

def send_message(urls_and_titles, client, channel, nick):
    """
    Send a message to an IRC/XMPP channel about a list of PR URLs and titles.
    """
    msg = construct_message(urls_and_titles, nick)
    client.msg(channel, msg)

def match_prs(message):
    prs = []
    pattern = re.compile(r"""
       (?:                        # Prefix to trigger the plugin:
            prs?                  #   "pr" or "prs"
          | githubs?              #   "github" or "githubs"
       )
       (?:
            /?\s?
            (?P<proj>[^/]+)/      #  project name
            (?P<repo>[^/ ]+)/?    #  ...followed by repo name
       )?
       \s*
       (?P<numbers>
       [#]?
       [0-9]+            # Number, optionally preceded by "#"
       (?:               # The following pattern will match zero or more times:
          ,?             #   Optional comma
          \s+            #
          (?:and\s+)?    #   Optional "and "
          [#]?[0-9]+     #   Number, optionally preceded by "#"
       )*
       )
       """, re.VERBOSE | re.IGNORECASE
    )
    
    for m in re.finditer(pattern, message):
        for pr in re.findall(r'[0-9]+', m.group('numbers')):
            prs.append((m.group('proj'), m.group('repo'), pr))
 
    logger.debug(prs)
    return prs


@match(match_prs, priority=0)
def github(client, channel, nick, message, matches):
    """
    Match possible GitHub pull requests, return links and subject info
    """
    deferreds = []
    for pr in matches:
        deferreds.append(get_pr_info(pr))

    d = defer.gatherResults(deferreds, consumeErrors=True)
    d.addCallback(send_message, client, channel, nick)
    raise ResponseNotReady

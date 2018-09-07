import treq
import re
from helga.plugins import match, ResponseNotReady
from helga import log, settings

from twisted.internet import defer
from twisted.internet import _sslverify

_sslverify.platformTrust = lambda: None    # disable SSL certificate validation

logger = log.getLogger(__name__)

@defer.inlineCallbacks
def get_pr_info(pr_url):
    """
    Find the "html_url" string (corresponding to the browser landing page) and
    the "title" string in the JSON data of a pull request
    :param ticket_url: GitHub API URL for a pull request
    :returns: twisted.internet.defer.Deferred. When this Deferred fires, it
              will return a tuple containing the landing page and title for
              the PR of interest
    """
    logger.info(pr_url)
    try:
        response = yield treq.get(pr_url,
                                  headers={'User-Agent': 'helga-github/0.1'},
                                  timeout=5)
        if response.code != 200:
            err = 'could not read PR, HTTP code %i' % response.code
            defer.returnValue((pr_url, err))
        else:
            content = yield treq.json_content(response)
            defer.returnValue((content['html_url'], content['title']))
    except Exception, e:
        # For example, if treq.get() timed out, or if treq.json_content() could
        # not parse the JSON, etc.
        err = 'could not read PR, %s' % e.message
        defer.returnValue((pr_url, err))

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
    tickets = []
    pattern = re.compile(r"""
       (?:                        # Prefix to trigger the plugin:
            prs?                  #   "pr" or "prs"
          | githubs?              #   "github" or "githubs"
          | .*github.com/.*/pull/ #   literal github URL TODO: restrict to
       )                          #       GITHUB_PROJECT, support multiple
       \s*                        #       github URLs
       [#]?[0-9]+                 # Number, optionally preceded by "#"
       (?:               # The following pattern will match zero or more times:
          ,?             #   Optional comma
          \s+            #
          (?:and\s+)?    #   Optional "and "
          [#]?[0-9]+     #   Number, optionally preceded by "#"
       )*
       """, re.VERBOSE | re.IGNORECASE
    )
    for match in re.findall(pattern, message):
        logger.info(match)
        for ticket in re.findall(r'[0-9]+', match):
            tickets.append(ticket)
    return tickets


@match(match_prs, priority=0)
def github(client, channel, nick, message, matches):
    """
    Match possible GitHub pull requests, return links and subject info
    """
    deferreds = []
    for pr_number in matches:
        try:
            pr_url = ("https://api.github.com/repos/"
                      + settings.GITHUB_PROJECT
                      + "/pulls/"
                      + pr_number)
        except AttributeError:
            return 'Please configure GITHUB_PROJECT to point to your project by owner and project name (example: \'fred/foobar\')'
        logger.info(pr_url)

        deferreds.append(get_pr_info(pr_url))

    d = defer.gatherResults(deferreds, consumeErrors=True)
    d.addCallback(send_message, client, channel, nick)
    raise ResponseNotReady

from github import match_prs, get_pr_info, construct_message, send_message
import pytest
import re
import json
from treq.testing import StubTreq
from twisted.web.resource import Resource


def line_matrix():
    pre_garbage = [' ', '', 'some question about ',]
    prefixes = ['PR', 'gItHUb', 'https://github.com/fred/crap/'
    numbers = ['#123467890', '1234567890']
    garbage = ['?', ' ', '.', '!', '..', '...']
    lines = []

    for pre in pre_garbage:
        for prefix in prefixes:
            for number in numbers:
                for g in garbage:
                    lines.append('%s%s %s%s' % (
                        pre, prefix, number, g
                        )
                    )
    return lines

def fail_line_matrix():
    pre_garbage = [' ', '', 'some question about ',]
    pre_prefixes = ['', ' ', 'f']
    prefixes = ['prs', 'githubs', 'https://github.com/fred/crap/']
    numbers = ['#G123467890', 'F1234567890']
    garbage = ['?', ' ', '.', '!', '..', '...']
    lines = []

    for pre in pre_garbage:
        for pre_prefix in pre_prefixes:
            for prefix in prefixes:
                for number in numbers:
                    for g in garbage:
                        lines.append('%s%s%s %s%s' % (
                            pre, pre_prefix, prefix, number, g
                            )
                        )
    return lines


multiple_pr_lines = [
    'prs #1 #2 #3',
    'prs 1, 2, 3',
    'prs 1, 2 and 3',
    'prs 1, 2, and 3',
    'prs 1 and 2 and 3',
    'prs 1, and 2, and 3',
]


class TestIsPr(object):

    @pytest.mark.parametrize('line', line_matrix())
    def test_matches(self, line):
        assert len(match_prs(line)) > 0

    @pytest.mark.parametrize('line', fail_line_matrix())
    def test_does_not_match(self, line):
        assert match_prs(line) == []

    @pytest.mark.parametrize('line', multiple_ticket_lines)
    def test_matches_multiple_prs(self, line):
        assert match_prs(line) == ['1', '2', '3']


class FakeClient(object):
    """
    Fake Helga client (eg IRC or XMPP) that simply saves the last
    message sent.
    """
    def msg(self, channel, msg):
        self.last_message = (channel, msg)


class TestSendMessage(object):
    def test_send_message(self):
        title = 'some PR title'
        html_url = 'https://github.com/fred/crap/pull/1'
        prs_and_titles = [(html_url, title)]
        client = FakeClient()
        channel = '#bots'
        nick = 'fred'
        # Send the message using our fake client
        send_message(prs_and_titles, client, channel, nick)
        expected = ('fred might be talking about '
                    'https://github.com/fred/crap/pull/1 [some issue subject]')
        assert client.last_message == (channel, expected)


class TestConstructMessage(object):
    def test_construct_message(self):
        title = 'some PR title'
        html_url = 'https://github.com/fred/crap/pull/1'
        nick = 'fred'
        result = construct_message([(html_url, title)], nick)
        expected = ('fred might be talking about '
                    'https://github.com/fred/crap/pull/1 [some issue subject]')
        assert result == expected

    def test_two_tickets(self):
        prs_and_titles = []
        prs_and_titles.append(('https://github.com/fred/crap/1', 'subj 1'))
        title.append(('https://github.com/fred/crap/2', 'subj 2'))
        nick = 'fred'
        result = construct_message(prs_and_titles, nick)
        expected = (' might be talking about '
                    'https://github.com/fred/crap/1 [subj 1] and '
                    'https://github.com/fred/crap/2 [subj 2]')
        assert result == expected

    def test_four_tickets(self):
        """ Verify that commas "," and "and" get put in the right places. """
        prs_and_titles = []
        prs_and_titles.append(('https://github.com/fred/crap/1', 'subj 1'))
        prs_and_titles.append(('https://github.com/fred/crap/2', 'subj 2'))
        prs_and_titles.append(('https://github.com/fred/crap/3', 'subj 3'))
        prs_and_titles.append(('https://github.com/fred/crap/4', 'subj 4'))
        nick = 'fred'
        result = construct_message(prs_and_titles, nick)
        expected = ('fred might be talking about '
                    'https://github.com/fred/crap/1 [subj 1], '
                    'https://github.com/fred/crap/2 [subj 2], '
                    'https://github.com/fred/crap/3 [subj 3] and '
                    'https://github.com/fred/crap/4 [subj 4]')
        assert result == expected


class FakeSettings(object):
    pass


class _PrTestResource(Resource):
    """
    A twisted.web.resource.Resource that represents a GitHub pull request.
    Return JSON data of interest for a fake PR.
    """
    isLeaf = True

    def render(self, request):
        request.setResponseCode(200)
        payload = {'html_url': 'https://github.com/fred/crap/pull/123',
                   'title': 'some PR title'}
        return json.dumps(payload).encode('utf-8')

class TestGetPrTitle(object):

    @pytest.inlineCallbacks
    def test_get_title(self, monkeypatch):
        monkeypatch.setattr('github.treq', StubTreq(_PrTestResource()))
        pr_url = 'https://api.github.com/repos/fred/crap/123'
        result = yield get_pr_info(pr_url)
        assert result == ('https://github.com/fred/crap/pull/123',
                          'some PR title')

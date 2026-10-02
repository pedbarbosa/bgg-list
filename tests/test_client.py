import unittest

import requests

from bgglist.client import API_BASE, TIMEOUT, BGGClient, create_session
from bgglist.errors import BGGAuthError, BGGError
from tests.fakes import fixture

class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text

class FakeSession:
    """Answers each request with the next response, or raises it if it's an exception."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

class BGGClientTest(unittest.TestCase):
    def client(self, *responses, **options):
        self.session = FakeSession(*responses)
        self.sleeps = []
        self.logs = []
        options.setdefault("clock", lambda: 0.0)
        return BGGClient(self.session, sleep=self.sleeps.append, log=self.logs.append, **options)

    def test_requests_the_collection_with_stats(self):
        games = self.client(FakeResponse(200, fixture("collection.xml"))).get_collection("pedbarbosa")
        self.assertEqual(self.session.calls, [
            (f"{API_BASE}/collection", {"username": "pedbarbosa", "own": 1, "stats": 1}, TIMEOUT),
        ])
        self.assertEqual(games["13"]["rank"], 500)

    def test_can_leave_expansions_out(self):
        self.client(FakeResponse(200, "<items/>")).get_collection("pedbarbosa", exclude_expansions=True)
        self.assertEqual(self.session.calls[0][1]["excludesubtype"], "boardgameexpansion")

    def test_waits_while_bgg_prepares_the_collection(self):
        client = self.client(FakeResponse(202), FakeResponse(202), FakeResponse(200, "<items/>"))
        self.assertEqual(client.get_collection("pedbarbosa"), {})
        self.assertEqual(self.sleeps.count(5), 2)
        self.assertEqual(self.logs[0], "BoardGameGeek is still preparing pedbarbosa's collection. Retrying in 5 seconds...")

    def test_gives_up_when_the_collection_never_gets_ready(self):
        client = self.client(*[FakeResponse(202)] * 3, queue_attempts=3)
        with self.assertRaisesRegex(BGGError, "after 3 attempts"):
            client.get_collection("pedbarbosa")

    def test_rejected_key(self):
        for status in (401, 403):
            with self.subTest(status=status), self.assertRaises(BGGAuthError):
                self.client(FakeResponse(status)).get_collection("pedbarbosa")

    def test_server_error(self):
        with self.assertRaisesRegex(BGGError, "returned 500"):
            self.client(FakeResponse(500)).get_collection("pedbarbosa")

    def test_network_error(self):
        with self.assertRaisesRegex(BGGError, "Couldn't reach BoardGameGeek"):
            self.client(requests.ConnectionError("refused")).get_collection("pedbarbosa")

    def test_requests_things_without_stats(self):
        details = self.client(FakeResponse(200, fixture("thing.xml"))).get_things(["13", "174430", "325"])
        self.assertEqual(self.session.calls[0][:2], (f"{API_BASE}/thing", {"id": "13,174430,325"}))
        self.assertEqual(details["174430"]["name"], "Gloomhaven")

    def test_refuses_more_than_twenty_things(self):
        with self.assertRaises(ValueError):
            self.client().get_things([str(i) for i in range(21)])

    def test_spaces_requests_out(self):
        # The first request starts at 0; the second is ready at 0.25 and must wait out the rest of the second
        times = iter([0.0, 0.25, 0.25])
        client = self.client(FakeResponse(200, "<items/>"), FakeResponse(200, "<items/>"), clock=lambda: next(times))
        client.get_things(["1"])
        client.get_things(["2"])
        self.assertEqual(self.sleeps, [0.75])

class CreateSessionTest(unittest.TestCase):
    def test_sends_the_key_and_retries_rate_limits_and_server_errors(self):
        session = create_session("secret")
        self.assertEqual(session.headers["Authorization"], "Bearer secret")
        retry = session.get_adapter(API_BASE).max_retries
        self.assertEqual(retry.total, 5)
        self.assertTrue({429, 500, 502, 503, 504} <= set(retry.status_forcelist))
        self.assertTrue(retry.respect_retry_after_header)

if __name__ == "__main__":
    unittest.main()

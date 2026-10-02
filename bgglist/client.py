import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .errors import BGGAuthError, BGGError
from .parsing import parse_collection, parse_things

# BGG asks for the bare domain: the www. subdomain can interfere with authorization
API_BASE = "https://boardgamegeek.com/xmlapi2"
THING_BATCH_SIZE = 20  # the most ids BGG accepts in one thing request
TIMEOUT = 30  # seconds

def create_session(api_key, retries=5, backoff=2):
    """A session that sends the API key and retries rate limits and server errors.

    Retries back off exponentially, or wait as long as BGG's Retry-After header asks.
    """
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {api_key}"
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session

class BGGClient:
    """The XML API2 calls this tool makes.

    Requests are spaced at least min_interval seconds apart. BGG answers 202
    while it prepares a collection; those are retried every queue_wait seconds,
    up to queue_attempts times.
    """

    def __init__(self, session, min_interval=1.0, queue_wait=5, queue_attempts=24,
                 log=print, sleep=time.sleep, clock=time.monotonic):
        self.session = session
        self.min_interval = min_interval
        self.queue_wait = queue_wait
        self.queue_attempts = queue_attempts
        self.log = log
        self.sleep = sleep
        self.clock = clock
        self._last_request = None

    def _throttle(self):
        if self._last_request is not None:
            wait = self.min_interval - (self.clock() - self._last_request)
            if wait > 0:
                self.sleep(wait)
        self._last_request = self.clock()

    def _get(self, endpoint, params, label):
        for _ in range(self.queue_attempts):
            self._throttle()
            try:
                response = self.session.get(f"{API_BASE}/{endpoint}", params=params, timeout=TIMEOUT)
            except requests.RequestException as e:
                raise BGGError(f"Couldn't reach BoardGameGeek for {label} ({e})") from e

            if response.status_code == 202:
                self.log(f"{label[0].upper()}{label[1:]} not ready. Retrying in {self.queue_wait} seconds...")
                self.sleep(self.queue_wait)
                continue
            if response.status_code in (401, 403):
                raise BGGAuthError(f"BoardGameGeek rejected the API key ({response.status_code}). Check BGG_API_KEY in your .env file.")
            if response.status_code != 200:
                raise BGGError(f"BoardGameGeek returned {response.status_code} for {label}")
            return response.text

        raise BGGError(f"BoardGameGeek still hadn't prepared {label} after {self.queue_attempts} attempts")

    def get_collection(self, username, exclude_expansions=False):
        """The games a user owns, with their rank, player count and play time."""
        params = {"username": username, "own": 1, "stats": 1}
        if exclude_expansions:
            # BGG returns expansions under the boardgame subtype unless told otherwise
            params["excludesubtype"] = "boardgameexpansion"
        xml_text = self._get("collection", params, f"{username}'s collection")
        return parse_collection(xml_text)

    def get_things(self, game_ids):
        """Names, years, ages and categories for up to THING_BATCH_SIZE ids, in one request."""
        if len(game_ids) > THING_BATCH_SIZE:
            raise ValueError(f"BGG accepts at most {THING_BATCH_SIZE} ids per thing request")
        xml_text = self._get("thing", {"id": ",".join(game_ids)}, f"details for {len(game_ids)} games")
        return parse_things(xml_text)

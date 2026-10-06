import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from bgg_list.serve import create_server

class ServeTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        Path(temp.name, "app.js").write_text("console.log('hi');")
        # Port 0 picks a free port
        self.server = create_server(temp.name, port=0)
        self.server.RequestHandlerClass.log_message = lambda *args: None
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f"http://localhost:{self.server.server_address[1]}"

    def test_files_are_served_with_no_cache(self):
        with urllib.request.urlopen(f"{self.base}/app.js") as response:
            self.assertEqual(response.read(), b"console.log('hi');")
            self.assertEqual(response.headers["Cache-Control"], "no-cache")

    def test_unchanged_files_get_a_not_modified_reply(self):
        with urllib.request.urlopen(f"{self.base}/app.js") as response:
            last_modified = response.headers["Last-Modified"]
        request = urllib.request.Request(f"{self.base}/app.js", headers={"If-Modified-Since": last_modified})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 304)

if __name__ == "__main__":
    unittest.main()

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from bgglist import cli
from tests.fakes import FakeClient, details, entry

class LoadApiKeyTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "repo"
        self.current = Path(temp.name) / "current"
        self.root.mkdir()
        self.current.mkdir()
        # Use temporary repository and current folders, with no key in the environment
        for patcher in (mock.patch.object(cli, "ROOT", self.root), mock.patch.dict(os.environ)):
            patcher.start()
            self.addCleanup(patcher.stop)
        os.environ.pop("BGG_API_KEY", None)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.current)

    def test_reads_the_env_file_in_the_repository_folder(self):
        (self.root / ".env").write_text("BGG_API_KEY=from-repo\n")
        self.assertEqual(cli.load_api_key(), "from-repo")

    def test_reads_the_env_file_in_the_current_folder(self):
        (self.current / ".env").write_text("BGG_API_KEY=from-current\n")
        self.assertEqual(cli.load_api_key(), "from-current")

    def test_current_folder_takes_precedence_over_the_repository(self):
        (self.root / ".env").write_text("BGG_API_KEY=from-repo\n")
        (self.current / ".env").write_text("BGG_API_KEY=from-current\n")
        self.assertEqual(cli.load_api_key(), "from-current")

    def test_environment_takes_precedence(self):
        (self.current / ".env").write_text("BGG_API_KEY=from-current\n")
        os.environ["BGG_API_KEY"] = "from-environment"
        self.assertEqual(cli.load_api_key(), "from-environment")

    def test_missing_key(self):
        with self.assertRaisesRegex(SystemExit, "BGG_API_KEY is not set"):
            cli.load_api_key()

class PromptTest(unittest.TestCase):
    def test_no_prompts_without_a_terminal(self):
        with mock.patch("sys.stdin", io.StringIO("rank\n")), mock.patch("builtins.input") as prompt:
            self.assertEqual(cli.ask("Sort field? "), "")
            self.assertEqual(cli.choose_sort_field(), cli.DEFAULT_SORT)
        prompt.assert_not_called()

    def test_reprompts_for_an_invalid_sort_field(self):
        with mock.patch.object(cli, "ask", side_effect=["size", "rank"]):
            self.assertEqual(cli.choose_sort_field(), "rank")

class MainTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        client = FakeClient({"alice": {"13": entry("13", "Catan", rank=500)}}, {"13": details("CATAN")})
        patchers = (
            mock.patch.object(cli, "load_api_key", return_value="key"),
            mock.patch.object(cli, "create_session"),
            mock.patch.object(cli, "BGGClient", return_value=client),
            mock.patch("sys.stdin", io.StringIO()),
        )
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, *argv):
        output = io.StringIO()
        with redirect_stdout(output):
            cli.main([*argv, "--cache-dir", str(self.folder / "cache")])
        return output.getvalue()

    def test_unattended_run_writes_the_requested_files(self):
        csv_path, json_path = self.folder / "out" / "games.csv", self.folder / "out" / "games.json"
        output = self.run_main("-u", "alice", "-o", str(csv_path), "--json", str(json_path))
        self.assertTrue(csv_path.exists())
        self.assertEqual(json.loads(json_path.read_text())["games"][0]["name"], "CATAN")
        self.assertIn("CATAN", output)

    def test_no_csv(self):
        csv_path = self.folder / "games.csv"
        self.run_main("-u", "alice", "-o", str(csv_path), "--no-csv")
        self.assertFalse(csv_path.exists())

    def test_unattended_run_needs_usernames(self):
        with self.assertRaisesRegex(SystemExit, "No usernames given"):
            self.run_main()

    def test_no_games_found(self):
        output = self.run_main("-u", "nobody", "--no-csv")
        self.assertIn("❌ No games found.", output)

if __name__ == "__main__":
    unittest.main()

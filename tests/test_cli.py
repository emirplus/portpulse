import unittest
from unittest.mock import patch
from click.testing import CliRunner

from portpulse.cli import main
from portpulse.scanner import PortEntry

class CliTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_version_flag(self):
        result = self.runner.invoke(main, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("portpulse v0.1.0", result.output)

    def test_list_command_text(self):
        mock_entry = PortEntry(port=8080, protocol="TCP", pid=123, name="python", status="LISTEN", memory_mb=12.5, command="python -m http.server")
        with patch("portpulse.cli.scan_ports", return_value=[mock_entry]):
            result = self.runner.invoke(main, ["list"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("8080", result.output)
            self.assertIn("python", result.output)

    def test_list_command_json(self):
        mock_entry = PortEntry(port=8080, protocol="TCP", pid=123, name="python", status="LISTEN", memory_mb=12.5, command="python -m http.server")
        with patch("portpulse.cli.scan_ports", return_value=[mock_entry]):
            result = self.runner.invoke(main, ["list", "--json"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('"port": 8080', result.output)

    def test_find_command_found(self):
        mock_entry = PortEntry(port=3000, protocol="TCP", pid=456, name="nextjs", status="LISTEN", memory_mb=80.0, command="next dev")
        with patch("portpulse.cli.scan_ports", return_value=[mock_entry]):
            result = self.runner.invoke(main, ["find", "3000"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("nextjs", result.output)
            self.assertIn("456", result.output)

    def test_find_command_not_found(self):
        with patch("portpulse.cli.scan_ports", return_value=[]):
            result = self.runner.invoke(main, ["find", "9999"])
            self.assertEqual(result.exit_code, 1)
            self.assertIn("No process listening on port 9999", result.output)

    def test_kill_command(self):
        with patch("portpulse.cli.kill_port", return_value=(True, "Freed port 3000")):
            result = self.runner.invoke(main, ["kill", "3000"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Freed port 3000", result.output)

if __name__ == "__main__":
    unittest.main()

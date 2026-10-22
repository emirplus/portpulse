import unittest
from unittest.mock import patch, MagicMock
import os
import psutil

from portpulse.killer import kill_process, kill_port
from portpulse.scanner import PortEntry

class KillerTests(unittest.TestCase):
    def test_kill_process_pid_zero(self):
        success, msg = kill_process(0)
        self.assertFalse(success)
        self.assertIn("Cannot kill system process", msg)

    def test_kill_process_self(self):
        success, msg = kill_process(os.getpid())
        self.assertFalse(success)
        self.assertIn("Cannot kill portpulse itself", msg)

    def test_kill_process_not_found(self):
        with patch("psutil.Process", side_effect=psutil.NoSuchProcess(99999)):
            success, msg = kill_process(99999)
            self.assertFalse(success)
            self.assertIn("does not exist", msg)

    def test_kill_process_success(self):
        mock_proc = MagicMock()
        mock_proc.children.return_value = []
        with patch("psutil.Process", return_value=mock_proc), patch("psutil.wait_procs", return_value=([mock_proc], [])):
            success, msg = kill_process(4567, force=False, tree=False)
            self.assertTrue(success)
            self.assertIn("Killed 1 process(es)", msg)
            mock_proc.terminate.assert_called_once()

    def test_kill_process_force(self):
        mock_proc = MagicMock()
        mock_proc.children.return_value = []
        with patch("psutil.Process", return_value=mock_proc), patch("psutil.wait_procs", return_value=([mock_proc], [])):
            success, msg = kill_process(4567, force=True, tree=False)
            self.assertTrue(success)
            mock_proc.kill.assert_called_once()

    def test_kill_port_not_found(self):
        with patch("portpulse.scanner.scan_ports", return_value=[]):
            success, msg = kill_port(9999)
            self.assertFalse(success)
            self.assertIn("No active process found", msg)

    def test_kill_port_success(self):
        mock_entry = PortEntry(port=3000, protocol="TCP", pid=8888, name="node", status="LISTEN", memory_mb=25.0, command="node")
        with patch("portpulse.scanner.scan_ports", return_value=[mock_entry]), patch("portpulse.killer.kill_process", return_value=(True, "killed")):
            success, msg = kill_port(3000)
            self.assertTrue(success)
            self.assertIn("Freed port 3000", msg)

if __name__ == "__main__":
    unittest.main()

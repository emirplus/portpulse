import unittest
from unittest.mock import patch, MagicMock
from collections import namedtuple
import socket
import psutil

from portpulse.scanner import scan_ports, get_process_details, PortEntry

MockAddr = namedtuple("Addr", ["ip", "port"])
MockConn = namedtuple("Conn", ["status", "type", "laddr", "pid"])

class ScannerTests(unittest.TestCase):
    def test_get_process_details_system(self):
        name, mem, cmdline = get_process_details(0)
        self.assertEqual(name, "system")
        self.assertEqual(mem, 0.0)

    def test_get_process_details_missing_process(self):
        with patch("psutil.Process", side_effect=psutil.NoSuchProcess(999999)):
            name, mem, cmdline = get_process_details(999999)
            self.assertEqual(name, "unknown")
            self.assertEqual(mem, 0.0)

    def test_get_process_details_active(self):
        mock_proc = MagicMock()
        mock_proc.name.return_value = "node"
        mock_proc.memory_info.return_value.rss = 104857600
        mock_proc.cmdline.return_value = ["node", "server.js"]
        with patch("psutil.Process", return_value=mock_proc):
            name, mem, cmdline = get_process_details(1234)
            self.assertEqual(name, "node")
            self.assertEqual(mem, 100.0)
            self.assertEqual(cmdline, "node server.js")

    def test_scan_ports_filter_by_port(self):
        conns = [
            MockConn(status=psutil.CONN_LISTEN, type=socket.SOCK_STREAM, laddr=MockAddr("127.0.0.1", 3000), pid=101),
            MockConn(status=psutil.CONN_LISTEN, type=socket.SOCK_STREAM, laddr=MockAddr("127.0.0.1", 8080), pid=102),
        ]
        with patch("psutil.net_connections", return_value=conns), patch("portpulse.scanner.get_process_details", return_value=("node", 50.0, "node server.js")):
            results = scan_ports(target_port=3000)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].port, 3000)
            self.assertEqual(results[0].protocol, "TCP")
            self.assertEqual(results[0].pid, 101)

    def test_scan_ports_filter_text(self):
        conns = [
            MockConn(status=psutil.CONN_LISTEN, type=socket.SOCK_STREAM, laddr=MockAddr("127.0.0.1", 3000), pid=101),
            MockConn(status=psutil.CONN_LISTEN, type=socket.SOCK_STREAM, laddr=MockAddr("127.0.0.1", 5432), pid=102),
        ]
        def mock_details(pid):
            if pid == 101:
                return ("node", 40.0, "node app.js")
            return ("postgres", 120.0, "postgres -D data")

        with patch("psutil.net_connections", return_value=conns), patch("portpulse.scanner.get_process_details", side_effect=mock_details):
            results = scan_ports(filter_text="post")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].name, "postgres")
            self.assertEqual(results[0].port, 5432)

if __name__ == "__main__":
    unittest.main()

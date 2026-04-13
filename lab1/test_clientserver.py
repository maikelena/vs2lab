"""
Simple client server unit test
"""

import logging
import threading
import unittest

import time

import clientserver
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


class TestPhoneDirectoryService(unittest.TestCase):
    """Socket-based tests for the phone directory service."""

    _server = None
    _server_thread = None

    @classmethod
    def setUpClass(cls):
        cls._server = clientserver.Server()
        cls._server_thread = threading.Thread(target=cls._server.serve)
        cls._server_thread.start()
        time.sleep(0.2)

    def setUp(self):
        self.client = clientserver.Client()

    def test_get_existing_entry(self):
        """GET should return the matching entry for an existing name."""
        result = self.client.get("Alice")
        self.assertEqual(result, "OK|Alice|12345")

    def test_get_unknown_entry(self):
        """GET should return NOTFOUND for an unknown name."""
        result = self.client.get("Unknown")
        self.assertEqual(result, "ERROR|NOTFOUND")

    def test_getall(self):
        """GETALL should return all phonebook entries."""
        result = self.client.getall()

        self.assertTrue(result.startswith("OKALL|"))
        self.assertIn("Alice:12345", result)
        self.assertIn("Bob:67890", result)
        self.assertIn("Charlie:55555", result)
        self.assertIn("David:54321", result)
        self.assertIn("Eve:98765", result)
        self.assertIn("Frank:11111", result)

    def test_bad_request(self):
        """Invalid requests should return BAD_REQUEST."""
        result = self.client._send_request("INVALID")
        self.assertEqual(result, "ERROR|BAD_REQUEST")

    def test_bad_get_request_without_name(self):
        """GET without a name should return BAD_REQUEST."""
        result = self.client._send_request("GET")
        self.assertEqual(result, "ERROR|BAD_REQUEST")

    def tearDown(self):
        self.client.close()

    @classmethod
    def tearDownClass(cls):
        cls._server.stop()
        cls._server_thread.join(timeout=5)


class TestPhoneDirectoryBackend(unittest.TestCase):
    """Direct backend/protocol tests without socket communication."""

    def setUp(self):
        self.server = clientserver.Server()

    def tearDown(self):
        self.server.sock.close()

    def test_backend_get_existing_entry(self):
        """Direct backend GET should return number for existing name."""
        result = self.server.get("Alice")
        self.assertEqual(result, "12345")

    def test_backend_get_unknown_entry(self):
        """Direct backend GET should return None for unknown name."""
        result = self.server.get("Unknown")
        self.assertIsNone(result)

    def test_backend_getall(self):
        """Direct backend GETALL should return full dictionary."""
        result = self.server.getall()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["Alice"], "12345")
        self.assertEqual(result["Bob"], "67890")
        self.assertEqual(result["Charlie"], "55555")
        self.assertEqual(result["David"], "54321")
        self.assertEqual(result["Eve"], "98765")
        self.assertEqual(result["Frank"], "11111")

    def test_handle_request_get(self):
        """Protocol handler should process GET correctly."""
        result = self.server.handle_request("GET|Alice")
        self.assertEqual(result, "OK|Alice|12345")

    def test_handle_request_get_unknown(self):
        """Protocol handler should return NOTFOUND for missing names."""
        result = self.server.handle_request("GET|Unknown")
        self.assertEqual(result, "ERROR|NOTFOUND")

    def test_handle_request_getall(self):
        """Protocol handler should process GETALL correctly."""
        result = self.server.handle_request("GETALL")

        self.assertTrue(result.startswith("OKALL|"))
        self.assertIn("Alice:12345", result)
        self.assertIn("Bob:67890", result)
        self.assertIn("Charlie:55555", result)
        self.assertIn("David:54321", result)
        self.assertIn("Eve:98765", result)
        self.assertIn("Frank:11111", result)

    def test_handle_request_bad_request(self):
        """Protocol handler should reject invalid commands."""
        result = self.server.handle_request("FOO|BAR")
        self.assertEqual(result, "ERROR|BAD_REQUEST")

    def test_handle_request_empty_request(self):
        """Protocol handler should reject empty requests."""
        result = self.server.handle_request("")
        self.assertEqual(result, "ERROR|BAD_REQUEST")

    def test_handle_request_get_without_name(self):
        """Protocol handler should reject GET without a name."""
        result = self.server.handle_request("GET")
        self.assertEqual(result, "ERROR|BAD_REQUEST")


if __name__ == "__main__":
    unittest.main()
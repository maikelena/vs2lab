"""
Simple client server unit test
"""

import logging
import threading
import time
import unittest

import telefonauskunft
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


class TestServer(unittest.TestCase):
    """Testing Server Logic"""

    def setUp(self):
        self.server = telefonauskunft.Server()

    def tearDown(self):
        self.server.sock.close()

    def test_get_existing_entry(self):
        result = self.server.get("Maike")
        self.assertEqual(result, "222")

    def test_get_unknown_entry(self):
        result = self.server.get("Unknown")
        self.assertIsNone(result)

    def test_getall(self):
        result = self.server.getAll()
        self.assertEqual(len(result), 3)
        self.assertEqual(result["Chloe"], "111")
        self.assertEqual(result["Maike"], "222")
        self.assertEqual(result["Romy"], "333")


class TestClient(unittest.TestCase):
    """Testing Client Logic"""

    @classmethod
    def setUpClass(cls):
        cls.server = telefonauskunft.Server()
        cls.server_thread = threading.Thread(target=cls.server.serve)
        cls.server_thread.start()

        time.sleep(0.2)

    def setUp(self):
        self.client = telefonauskunft.Client()

    def tearDown(self):
        self.client.close()

    def test_get_existing_entry(self):
        result = self.client.get("Maike")
        self.assertEqual(result, "OK|Maike|222")

    def test_get_unknown_entry(self):
        result = self.client.get("Unknown")
        self.assertEqual(result, "ERROR|NOTFOUND")

    def test_getall(self):
        result = self.client.getall()
        self.assertTrue(result.startswith("OKALL|"))
        self.assertIn("Chloe=111", result)
        self.assertIn("Maike=222", result)
        self.assertIn("Romy=333", result)

    def test_bad_request(self):
        result = self.client.call("INVALID")
        self.assertEqual(result, "ERROR|BAD_REQUEST")

    @classmethod
    def tearDownClass(cls):
        cls.server._serving = False  # stop loop
        cls.server_thread.join(timeout=5)

if __name__ == '__main__':
    unittest.main()

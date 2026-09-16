import unittest
from task2 import Endpoint


class TestEndpoint(unittest.TestCase):
    def test_valid_endpoint(self):
        e = Endpoint("localhost",8000)
        self.assertEqual(e.host,"localhost")
        self.assertEqual(e.port, 8000)
        self.assertEqual(e.url,"http://localhost:8000")


    def test_boundary_ports_are_valid(self):
        self.assertEqual(Endpoint("h", 1).port, 1)
        self.assertEqual(Endpoint("h", 65535).port, 65535)

    def test_port_too_low(self):
        with self.assertRaises(ValueError):
            Endpoint("h", 0)

    def test_port_too_high(self):
        with self.assertRaises(ValueError):
            Endpoint("h", 65536)

    def test_negative_port(self):
        with self.assertRaises(ValueError):
            Endpoint("h", -1)

    def test_non_integer_port(self):
        with self.assertRaises(ValueError):
            Endpoint("h", "8000")

    def test_url_is_read_only(self):
        e = Endpoint("h", 80)
        with self.assertRaises(AttributeError):
            e.url = "http://evil"


if __name__ == "__main__":
    unittest.main()




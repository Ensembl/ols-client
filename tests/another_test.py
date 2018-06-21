import socket
import unittest
import warnings

warnings.simplefilter("ignore", ResourceWarning)

def abusesocket():
    s = socket.socket()
    s.connect(("www.google.com", 80))


def ignore_warnings(test_func):
    def do_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            test_func(self, *args, **kwargs)

    return do_test

class Test(unittest.TestCase):


    @ignore_warnings
    def test3(self):
            abusesocket()

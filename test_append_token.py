from unittest import TestCase
from trumpbot import append_token, START, END

class TestAppend_token(TestCase):
    def test_append_token(self):
        self.assertEqual("A?", append_token("A", "?"))
        self.assertEqual("A $500", append_token("A $", "500"))
        self.assertEqual("A dog", append_token("A", "dog"))
        self.assertEqual("A", append_token("", "A"))

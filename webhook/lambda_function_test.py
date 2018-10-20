import unittest

import lambda_function


class FindTaco(unittest.TestCase):
    def test_find_none(self):
        self.assertEqual(lambda_function.find_taco("test test :taco test"), 0)

    def test_find_one(self):
        self.assertEqual(lambda_function.find_taco("test test :taco: test"), 1)

    def test_find_two(self):
        self.assertEqual(lambda_function.find_taco(":taco: test :taco: test :heart:"), 2)

    def test_find_four(self):
        self.assertEqual(lambda_function.find_taco(":taco: test :taco::taco: test :heart::taco:"), 4)

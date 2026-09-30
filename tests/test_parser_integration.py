"""Optional smoke test: set R6_TEST_REPLAY_PATH to a complete replay folder."""
import os
import unittest

from r6stats.parser.siege_dissect import parse_match


@unittest.skipUnless(os.getenv("R6_TEST_REPLAY_PATH"), "No real replay supplied")
class ParserIntegrationTests(unittest.TestCase):
    def test_complete_match(self):
        match = parse_match(os.environ["R6_TEST_REPLAY_PATH"])
        self.assertGreater(len(match.rounds), 1)
        self.assertTrue(match.map_name)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch
from base.data import Data
from games.tasks.minesweeper.scripts.minesweeper_verifier import MinesweeperVerifier

class TestMinesweeperVerifier(unittest.TestCase):
    def setUp(self):
        self.verifier = MinesweeperVerifier()
        # Create a mock Data object
        self.mock_data = MagicMock(spec=Data)
        self.mock_data.metadata = {
            "current_mines": [(0, 1), (2, 3), (4, 5)]
        }

    def test_verify_correct_answer(self):
        # Test with correct answers in different formats
        correct_answers = [
            "I found the mines at coordinates [(0, 1), (2, 3), (4, 5)].",
            "The mines are at positions: (0,1), (2,3), (4,5)",
            "After analyzing the grid, I determined the mines are at: [[0, 1], [2, 3], [4, 5]]"
        ]
        
        for answer in correct_answers:
            self.assertTrue(self.verifier.verify(self.mock_data, answer), 
                           f"Should verify as correct: {answer}")

    def test_verify_wrong_answer(self):
        # Test with incorrect answers
        wrong_answers = [
            # Missing mines
            "I found mines at coordinates [(0, 1), (2, 3)].",
            # Extra mines
            "The mines are at positions: (0,1), (2,3), (4,5), (6,7)",
            # Completely different mines
            "The mines are at: [[1, 1], [3, 3], [5, 5]]"
        ]
        
        for answer in wrong_answers:
            self.assertFalse(self.verifier.verify(self.mock_data, answer),
                            f"Should verify as incorrect: {answer}")

    def test_extract_answer_tuple_list_format(self):
        # Test extraction from tuple list format
        response = "I found the mines at these coordinates: [(0, 1), (2, 3), (4, 5)]"
        expected = [(0, 1), (2, 3), (4, 5)]
        self.assertEqual(self.verifier.extract_answer(response), expected)

    def test_extract_answer_list_of_lists_format(self):
        # Test extraction from list of lists format
        response = "The mines are located at [[0, 1], [2, 3], [4, 5]]"
        expected = [(0, 1), (2, 3), (4, 5)]
        self.assertEqual(self.verifier.extract_answer(response), expected)

    def test_extract_answer_comma_separated_tuples(self):
        # Test extraction from comma-separated tuples
        response = "After analysis, I determined the mines are at (0,1), (2,3), (4,5)"
        expected = [(0, 1), (2, 3), (4, 5)]
        self.assertEqual(self.verifier.extract_answer(response), expected)

    def test_extract_answer_mixed_formats(self):
        # Test extraction from text with multiple formats
        response = """
        I first found mines at (0,1) and (2,3).
        Later, I also discovered a mine at [4, 5].
        So the complete set of mines is [(0,1), (2,3), (4,5)].
        """
        expected = [(0, 1), (2, 3), (4, 5)]
        result = self.verifier.extract_answer(response)
        # Sort both lists to ensure order doesn't matter
        self.assertEqual(sorted(result), sorted(expected))

    def test_extract_answer_fallback_method(self):
        # Test the fallback method when no standard format is found
        response = "The coordinates of the mines are 0,1 and 2,3 and 4,5"
        expected = [(0, 1), (2, 3), (4, 5)]
        result = self.verifier.extract_answer(response)
        # Sort both lists to ensure order doesn't matter
        self.assertEqual(sorted(result), sorted(expected))

    def test_extract_answer_empty_response(self):
        # Test with empty response
        response = ""
        expected = []
        self.assertEqual(self.verifier.extract_answer(response), expected)

    def test_extract_answer_no_coordinates(self):
        # Test with response that has no coordinates
        response = "I couldn't find any mines in this puzzle."
        expected = []
        self.assertEqual(self.verifier.extract_answer(response), expected)

    def test_verify_handles_exceptions(self):
        # Test that verify handles exceptions gracefully
        with patch.object(self.verifier, 'extract_answer', side_effect=Exception("Test exception")):
            self.assertFalse(self.verifier.verify(self.mock_data, "Any response"))

if __name__ == '__main__':
    unittest.main()
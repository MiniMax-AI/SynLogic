"""
Wordscapes data module for the reasonreason framework.
"""

import json
from base.data import Data

class WordscapesData(Data):
    """
    Data class for Wordscapes game
    """
    def __init__(self, idx, grid, across_words, down_words, solution):
        """
        Initialize a WordscapesData instance
        
        Args:
            idx: Unique identifier for the puzzle
            grid: 2D grid with 'X' and '0' indicating letter positions
            across_words: List of words to be placed horizontally
            down_words: List of words to be placed vertically
            solution: 2D grid with the filled letters
        """
        self.idx = idx
        self.grid = grid  # 2D array with 'X' and '0'
        self.across_words = across_words
        self.down_words = down_words
        self.solution = solution
        
        # Format for answer validation
        self.answer = self._format_answer(solution)
        
        # Generate question string
        self.question = self._format_question()

    def _format_question(self):
        """Format the puzzle as a question string"""
        grid_str = "\n".join([" ".join(row) for row in self.grid])
        across_str = "Across: " + ", ".join(self.across_words)
        down_str = "Down: " + ", ".join(self.down_words)
        
        return f"Grid:\n{grid_str}\n\n{across_str}\n{down_str}"
    
    def _format_answer(self, solution):
        """Format the solution as an answer string for verification"""
        # Convert 2D solution grid to a string representation
        return json.dumps(solution)
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "idx": self.idx,
            "grid": self.grid,
            "across_words": self.across_words,
            "down_words": self.down_words,
            "solution": self.solution,
            "question": self.question,
            "answer": self.answer
        }
    
    @classmethod
    def from_dict(cls, data_dict):
        """Create a WordscapesData instance from a dictionary"""
        instance = cls(
            data_dict["idx"],
            data_dict["grid"],
            data_dict["across_words"],
            data_dict["down_words"],
            data_dict["solution"]
        )
        instance.question = data_dict.get("question", instance.question)
        instance.answer = data_dict.get("answer", instance.answer)
        return instance 
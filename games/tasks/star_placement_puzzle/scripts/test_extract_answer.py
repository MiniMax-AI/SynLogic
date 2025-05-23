import unittest
import re
from games.tasks.star_placement_puzzle.scripts.star_placement_puzzle import StarPlacementPuzzle

class TestExtractAnswer(unittest.TestCase):
    """
    测试从模型回答中提取星星坐标的功能
    """
    
    def setUp(self):
        self.game = StarPlacementPuzzle(n=4, k=1)
    
    def test_extract_answer_simple(self):
        """
        测试简单情况下的答案提取
        """
        # 简单直接的回答，使用Python代码块格式
        answer_simple = """
        ```python
        {
            'A': [(1, 1), (2, 3)],
            'B': [(2, 4), (4, 2)]
        }
        ```
        """
        
        # 提取坐标
        coords = self.game.extract_answer(answer_simple)
        self.assertIsNotNone(coords)
        self.assertEqual(len(coords), 2)  # 两个区域
        
        # 检查A区域
        self.assertIn("A", coords)
        self.assertEqual(len(coords["A"]), 2)  # 两颗星星
        self.assertIn((0, 0), coords["A"])  # (1,1) -> (0,0)
        self.assertIn((1, 2), coords["A"])  # (2,3) -> (1,2)
        
        # 检查B区域
        self.assertIn("B", coords)
        self.assertEqual(len(coords["B"]), 2)
        self.assertIn((1, 3), coords["B"])  # (2,4) -> (1,3)
        self.assertIn((3, 1), coords["B"])  # (4,2) -> (3,1)
    
    def test_extract_answer_with_reasoning(self):
        """
        测试含有推理过程的答案提取
        """
        # 包含推理过程的回答，使用Python代码块格式
        answer_with_reasoning = """
        首先，我需要分析这个问题...
        
        让我开始放置星星...
        
        星星不能相邻，所以...
        
        最终解答是：
        
        ```python
        {
            'A': [(1, 1), (2, 3)],
            'B': [(2, 4), (4, 2)]
        }
        ```
        
        希望这个解答是正确的。
        """
        
        # 提取坐标
        coords = self.game.extract_answer(answer_with_reasoning)
        self.assertIsNotNone(coords)
        self.assertEqual(len(coords), 2)
        
        # 检查A区域
        self.assertIn("A", coords)
        self.assertEqual(len(coords["A"]), 2)
        
        # 检查B区域
        self.assertIn("B", coords)
        self.assertEqual(len(coords["B"]), 2)
    
    def test_extract_answer_multiple_formats(self):
        """
        测试不同格式的回答
        """
        # 格式1：Python代码块中的字典格式略有不同
        answer1 = """
        ```python
        {
            'A': [(1, 1), (2, 3)],
            'B': [(2, 4), (4, 2)]
        }
        ```
        """
        coords1 = self.game.extract_answer(answer1)
        self.assertIsNotNone(coords1)
        self.assertEqual(len(coords1), 2)
        
        # 格式2：Python代码块中的字典格式使用双引号
        answer2 = """
        ```python
        {
            "A": [(1, 1), (2, 3)],
            "B": [(2, 4), (4, 2)]
        }
        ```
        """
        coords2 = self.game.extract_answer(answer2)
        self.assertIsNotNone(coords2)
        self.assertEqual(len(coords2), 2)
        
        # 格式3：Python代码块中的字典作为变量
        answer3 = """
        ```python
        solution = {
            'A': [(1, 1), (2, 3)],
            'B': [(2, 4), (4, 2)]
        }
        ```
        """
        coords3 = self.game.extract_answer(answer3)
        self.assertIsNotNone(coords3)
        self.assertEqual(len(coords3), 2)
    
    def test_extract_answer_invalid(self):
        """
        测试无效的回答格式
        """
        # 没有Python代码块
        answer_invalid1 = "A(1,1)(2,3)\n\nB(2,4)(4,2)"
        coords1 = self.game.extract_answer(answer_invalid1)
        self.assertIsNone(coords1)
        
        # Python代码块格式错误
        answer_invalid2 = """
        ```python
        {
            'A': [1, 1], (2, 3)], // 语法错误
            'B': [(2, 4), (4, 2)]
        }
        ```
        """
        coords2 = self.game.extract_answer(answer_invalid2)
        self.assertIsNone(coords2)
        
        # 完全无关的回答
        answer_invalid3 = "我不知道如何解决这个问题。"
        coords3 = self.game.extract_answer(answer_invalid3)
        self.assertIsNone(coords3)
    
    def test_extract_answer_complex(self):
        """
        测试复杂的回答（多个区域、多颗星星）
        """
        # 复杂回答，多个区域，使用Python代码块格式
        answer_complex = """
        ```python
        {
            'A': [(1, 1), (2, 3), (3, 5)],
            'B': [(2, 4), (4, 2)],
            'C': [(1, 5), (3, 1), (5, 3), (5, 5)],
            'D': [(4, 4)]
        }
        ```
        """
        
        coords = self.game.extract_answer(answer_complex)
        
        self.assertIsNotNone(coords)
        self.assertEqual(len(coords), 4)  # 四个区域
        
        # 检查每个区域的星星数量
        self.assertEqual(len(coords["A"]), 3)
        self.assertEqual(len(coords["B"]), 2)
        self.assertEqual(len(coords["C"]), 4)
        self.assertEqual(len(coords["D"]), 1)
        
        # 验证某些具体坐标
        self.assertIn((0, 0), coords["A"])  # (1,1) -> (0,0)
        self.assertIn((2, 4), coords["A"])  # (3,5) -> (2,4)
        self.assertIn((4, 2), coords["C"])  # (5,3) -> (4,2)
        self.assertIn((3, 3), coords["D"])  # (4,4) -> (3,3)
    
    def test_extract_answer_python_code_block(self):
        """
        测试从Python代码块中提取答案
        """
        # Python代码块格式
        answer_with_python = """
        思考过程...
        
        ```python
        # 解答
        {
            'A': [(1, 1), (2, 3)],
            'B': [(2, 4), (4, 2)]
        }
        ```
        
        希望这个解答是正确的。
        """
        
        coords = self.game.extract_answer(answer_with_python)
        self.assertIsNotNone(coords)
        self.assertEqual(len(coords), 2)
        
        # 检查A区域
        self.assertIn("A", coords)
        self.assertEqual(len(coords["A"]), 2)
        self.assertIn((0, 0), coords["A"])  # (1,1) -> (0,0)
        self.assertIn((1, 2), coords["A"])  # (2,3) -> (1,2)
        
        # 检查B区域
        self.assertIn("B", coords)
        self.assertEqual(len(coords["B"]), 2)
        self.assertIn((1, 3), coords["B"])  # (2,4) -> (1,3)
        self.assertIn((3, 1), coords["B"])  # (4,2) -> (3,1)

if __name__ == "__main__":
    unittest.main() 
import unittest
from games.tasks.number_wall.scripts.number_wall_verifier import NumberWallVerifier
from base.data import Data

class TestNumberWallVerifier(unittest.TestCase):
    def setUp(self):
        self.verifier = NumberWallVerifier()
        
    def test_valid_solution(self):
        """测试有效的解决方案"""
        grid = [["X", "X", "X", "X", "X"],
                ["X", "X", 2, "X", 1],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", "X", "X"],
                ["X", 2, "X", 2, "X"]]
                
        solution = [["A", "A", "A", "A", "A"],
                    ["A", "X", 2, "A", 1],
                    ["A", "A", "A", "A", "A"],
                    ["A", "X", "A", "X", "A"],
                    ["A", 2, "A", 2, "A"]]
                    
        data = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid,
                "n": 5
            }
        )
        
        solution_str = """
        Here is my solution:
        ```python
        [["A", "A", "A", "A", "A"],
         ["A", "X", 2, "A", 1],
         ["A", "A", "A", "A", "A"],
         ["A", "X", "A", "X", "A"],
         ["A", 2, "A", 2, "A"]]
        ```
        """
        
        self.assertTrue(self.verifier.verify(data, solution_str))
        
    def test_invalid_number_changed(self):
        """测试原始数字被改变的情况"""
        grid = [["X", "X", "X", "X", "X"],
                ["X", "X", 2, "X", 1],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", "X", "X"],
                ["X", 2, "X", 2, "X"]]
                
        solution = [["A", "A", "A", "A", "A"],
                    ["A", "X", 3, "A", 1],  # 数字2被改为3
                    ["A", "A", "A", "A", "A"],
                    ["A", "X", "A", "X", "A"],
                    ["A", 2, "A", 2, "A"]]
                    
        data = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid,
                "n": 5
            }
        )
        
        solution_str = """
        Here is my solution:
        ```python
        [["A", "A", "A", "A", "A"],
         ["A", "X", 3, "A", 1],
         ["A", "A", "A", "A", "A"],
         ["A", "X", "A", "X", "A"],
         ["A", 2, "A", 2, "A"]]
        ```
        """
        
        self.assertFalse(self.verifier.verify(data, solution_str))
        
    def test_invalid_wall_block(self):
        """测试存在2x2墙壁块的情况"""
        grid = [["X", "X", "X", "X", "X"],
                ["X", "X", 2, "X", 1],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", "X", "X"],
                ["X", 2, "X", 2, "X"]]
                
        solution = [["A", "A", "A", "A", "A"],
                    ["A", "A", "A", "A", 1],  # 形成2x2墙壁块
                    ["A", "A", 2, "X", "X"],
                    ["A", "X", "A", "X", "A"],
                    ["A", 2, "A", 2, "A"]]
                    
        data = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid,
                "n": 5
            }
        )
        
        solution_str = """
        Here is my solution:
        ```python
        [["A", "A", "A", "A", "A"],
         ["A", "A", "A", "A", 1],
         ["A", "A", 2, "X", "X"],
         ["A", "X", "A", "X", "A"],
         ["A", 2, "A", 2, "A"]]
        ```
        """
        
        self.assertFalse(self.verifier.verify(data, solution_str))
        
    def test_invalid_island_size(self):
        """测试岛屿大小与数字不匹配的情况"""
        grid = [["X", "X", "X", "X", "X"],
                ["X", "X", 2, "X", 1],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", "X", "X"],
                ["X", 2, "X", 2, "X"]]
                
        solution = [["A", "A", "A", "A", "A"],
                    ["A", "X", 2, "A", 1],
                    ["A", "A", "X", "A", "A"],  # 岛屿大小为3，但数字是2
                    ["A", "X", "A", "X", "A"],
                    ["A", 2, "A", 2, "A"]]
                    
        data = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid,
                "n": 5
            }
        )
        
        solution_str = """
        Here is my solution:
        ```python
        [["A", "A", "A", "A", "A"],
         ["A", "X", 2, "A", 1],
         ["A", "A", "X", "A", "A"],
         ["A", "X", "A", "X", "A"],
         ["A", 2, "A", 2, "A"]]
        ```
        """
        
        self.assertFalse(self.verifier.verify(data, solution_str))
        
    def test_invalid_multiple_numbers(self):
        """测试一个岛屿包含多个数字的情况"""
        grid = [[1, "X", "X", "X", 3],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", "X", 4],
                ["X", "X", "X", "X", "X"],
                [5, "X", "X", "X", "X"]]
                
        solution = [[1, "A", "X", "X", 3],
                    ["A", "A", "A", "A", "X"],  # 3和4在同一个岛屿
                    ["X", "A", "X", "X", 4],
                    ["X", "A", "A", "A", "X"],
                    [5, "X", "X", "A", "A"]]
                    
        data = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid,
                "n": 5
            }
        )
        
        solution_str = """
        Here is my solution:
        ```python
        [[1, "A", "X", "X", 3],
         ["A", "A", "A", "A", "X"],
         ["X", "A", "X", "X", 4],
         ["X", "A", "A", "A", "X"],
         [5, "X", "X", "A", "A"]]
        ```
        """
        
        self.assertFalse(self.verifier.verify(data, solution_str))
        
    def test_invalid_no_number(self):
        """测试岛屿没有数字的情况"""
        grid = [[1, "X", "X", "X", 3],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", "X", 4],
                ["X", "X", "X", "X", "X"],
                [5, "X", "X", "X", "X"]]
                
        solution = [[1, "A", "X", "X", 3],
                    ["A", "A", "A", "A", "A"],
                    ["X", "A", "X", "X", 4],
                    ["X", "X", "X", "A", "X"],  # 孤立的岛屿没有数字
                    [5, "X", "X", "A", "A"]]
                    
        data = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid,
                "n": 5
            }
        )
        
        solution_str = """
        Here is my solution:
        ```python
        [[1, "A", "X", "X", 3],
         ["A", "A", "A", "A", "A"],
         ["X", "A", "X", "X", 4],
         ["X", "X", "X", "A", "X"],
         [5, "X", "X", "A", "A"]]
        ```
        """
        
        self.assertFalse(self.verifier.verify(data, solution_str))
        
    def test_invalid_diagonal_borders(self):
        """测试存在斜线边的情况"""
        grid = [[1, "X", "X", "X", 3],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", "X", 4],
                ["X", "X", "X", "X", "X"],
                [5, "X", "X", "X", "X"]]
                
        # 在(0,2)和(1,3)之间存在斜线边
        solution = [[1, "A", "X", "A", 3],
                    ["A", "A", "A", "X", "X"],
                    ["A", "A", "A", "A", 4],
                    ["A", "A", "A", "A", "X"],
                    [5, "X", "X", "X", "A"]]
                    
        data = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid,
                "n": 5
            }
        )
        
        solution_str = """
        Here is my solution:
        ```python
        [[1, "A", "X", "A", 3],
         ["A", "A", "A", "X", "X"],
         ["A", "A", "A", "A", 4],
         ["A", "A", "A", "A", "X"],
         [5, "X", "X", "X", "A"]]
        ```
        """
        
        self.assertFalse(self.verifier.verify(data, solution_str))
        
    def test_another_diagonal_borders(self):
        """测试另一种斜线边情况"""
        grid = [[1, "X", "X", "X", 3],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", "X", 4],
                ["X", "X", "X", "X", "X"],
                [5, "X", "X", "X", "X"]]
                
        # 在(1,1)和(2,2)之间存在斜线边
        solution = [[1, "A", "A", "A", 3],
                    ["A", "X", "A", "X", "X"],
                    ["A", "A", "X", "X", 4],
                    ["X", "X", "X", "A", "X"],
                    [5, "X", "X", "A", "A"]]
                    
        data = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid,
                "n": 5
            }
        )
        
        solution_str = """
        Here is my solution:
        ```python
        [[1, "A", "A", "A", 3],
         ["A", "X", "A", "X", "X"],
         ["A", "A", "X", "X", 4],
         ["X", "X", "X", "A", "X"],
         [5, "X", "X", "A", "A"]]
        ```
        """
        
        self.assertFalse(self.verifier.verify(data, solution_str))
        
    def test_extract_answer(self):
        """测试从响应中提取答案"""
        response = """
        I've solved the Number Wall puzzle. Here's my solution:
        
        ```python
        [["A", "A", "A", "A", "A"],
         ["A", "X", 2, "A", 1],
         ["A", "A", "A", "A", "A"],
         ["A", "X", "A", "X", "A"],
         ["A", 2, "A", 2, "A"]]
        ```
        
        This solution satisfies all the rules.
        """
        
        expected = [["A", "A", "A", "A", "A"],
                    ["A", "X", 2, "A", 1],
                    ["A", "A", "A", "A", "A"],
                    ["A", "X", "A", "X", "A"],
                    ["A", 2, "A", 2, "A"]]
                    
        result = self.verifier.extract_answer(response)
        self.assertEqual(result, expected)
        
    def test_extract_answer_with_string_numbers(self):
        """测试从响应中提取包含字符串数字的答案"""
        response = """
        I've solved the Number Wall puzzle. Here's my solution:
        
        ```python
        [["A", "A", "A", "A", "A"],
         ["A", "X", "2", "A", "1"],
         ["A", "A", "A", "A", "A"],
         ["A", "X", "A", "X", "A"],
         ["A", "2", "A", "2", "A"]]
        ```
        
        This solution satisfies all the rules.
        """
        
        expected = [["A", "A", "A", "A", "A"],
                    ["A", "X", 2, "A", 1],
                    ["A", "A", "A", "A", "A"],
                    ["A", "X", "A", "X", "A"],
                    ["A", 2, "A", 2, "A"]]
                    
        result = self.verifier.extract_answer(response)
        self.assertEqual(result, expected)
        
    def test_real_examples(self):
        """测试真实示例"""
        # 示例1
        grid1 = [[1, "X", "X", "X", 3],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", "X", 4],
                ["X", "X", "X", "X", "X"],
                [5, "X", "X", "X", "X"]]
                
        solution1 = [[1, "A", "X", "X", 3],
                    ["A", "A", "A", "A", "A"],
                    ["X", "A", "X", "X", 4],
                    ["X", "A", "A", "A", "X"],
                    [5, "X", "X", "A", "A"]]
                    
        data1 = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid1,
                "n": 5
            }
        )
        
        solution_str1 = """
        Here is my solution:
        ```python
        [[1, "A", "X", "X", 3],
         ["A", "A", "A", "A", "A"],
         ["X", "A", "X", "X", 4],
         ["X", "A", "A", "A", "X"],
         [5, "X", "X", "A", "A"]]
        ```
        """
        
        # 这个解答应该是有效的
        self.assertTrue(self.verifier.verify(data1, solution_str1))
        
        # 示例2
        grid2 = [["X", "X", "X", "X", "X"],
                ["X", "X", 2, "X", 1],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", "X", "X"],
                ["X", 2, "X", 2, "X"]]
                
        solution2 = [["A", "A", "A", "A", "A"],
                    ["A", "X", 2, "A", 1],
                    ["A", "A", "A", "A", "A"],
                    ["A", "X", "A", "X", "A"],
                    ["A", 2, "A", 2, "A"]]
                    
        data2 = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid2,
                "n": 5
            }
        )
        
        solution_str2 = """
        Here is my solution:
        ```python
        [["A", "A", "A", "A", "A"],
         ["A", "X", 2, "A", 1],
         ["A", "A", "A", "A", "A"],
         ["A", "X", "A", "X", "A"],
         ["A", 2, "A", 2, "A"]]
        ```
        """
        
        # 这个解答应该是有效的
        self.assertTrue(self.verifier.verify(data2, solution_str2))
        
        # 示例3
        grid3 = [[1, "X", "X", 2, "X"],
                ["X", "X", "X", "X", "X"],
                ["X", 5, "X", "X", "X"],
                ["X", "X", "X", "X", "X"],
                ["X", "X", "X", 1, "X"]]
                
        solution3 = [[1, "A", "X", 2, "A"],
                    ["A", "A", "A", "A", "A"],
                    ["X", 5, "X", "X", "A"],
                    ["A", "X", "A", "A", "A"],
                    ["A", "A", "A", 1, "A"]]
                    
        data3 = Data(
            question="测试问题",
            answer="",
            metadata={
                "grid": grid3,
                "n": 5
            }
        )
        
        solution_str3 = """
        Here is my solution:
        ```python
        [[1, "A", "X", 2, "A"],
         ["A", "A", "A", "A", "A"],
         ["X", 5, "X", "X", "A"],
         ["A", "X", "A", "A", "A"],
         ["A", "A", "A", 1, "A"]]
        ```
        """
        
        # 这个解答应该是有效的
        self.assertTrue(self.verifier.verify(data3, solution_str3))


if __name__ == "__main__":
    unittest.main()
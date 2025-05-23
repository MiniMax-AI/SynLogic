import unittest
from games.tasks.skyscraper_puzzle.scripts.skyscraper_puzzle import SkyscraperPuzzle

class TestExtractAnswer(unittest.TestCase):
    """
    测试从模型回答中提取答案的功能
    """
    def setUp(self):
        """初始化测试环境"""
        self.game = SkyscraperPuzzle(n=4)
    
    def test_extract_simple_answer(self):
        """测试提取简单格式的答案"""
        test_solution = """
        分析了摩天楼游戏的规则，我已经找出了解决方案。

        根据游戏规则和提供的线索，答案是：

        ```python
        [
          [3, 1, 2, 4],
          [4, 2, 1, 3],
          [1, 4, 3, 2],
          [2, 3, 4, 1]
        ]
        ```
        """
        
        # 提取答案
        extracted = self.game.extract_answer(test_solution)
        
        # 验证提取结果
        expected = [[3, 1, 2, 4], [4, 2, 1, 3], [1, 4, 3, 2], [2, 3, 4, 1]]
        self.assertEqual(extracted, expected)
    
    def test_extract_complex_answer(self):
        """测试提取复杂格式的答案"""
        test_solution = """
        我来解决这个摩天楼游戏。

        首先，我需要分析边缘数字提供的线索...
        [经过很长的分析过程]
        
        最终，我得到了以下解决方案：
        
        ```python
        [
          [2, 4, 1, 3],
          [3, 1, 4, 2],
          [4, 2, 3, 1],
          [1, 3, 2, 4]
        ]
        ```
        """
        
        # 提取答案
        extracted = self.game.extract_answer(test_solution)
        
        # 验证提取结果
        expected = [[2, 4, 1, 3], [3, 1, 4, 2], [4, 2, 3, 1], [1, 3, 2, 4]]
        self.assertEqual(extracted, expected)
    
    def test_extract_simple_list_format(self):
        """测试提取单行列表格式的答案"""
        test_solution = """
        我的解答是：
        
        ```python
        [
            [3, 1, 2, 4],
            [4, 2, 1, 3],
            [1, 4, 3, 2],
            [2, 3, 4, 1]
        ]
        ```
        """
        
        # 提取答案
        extracted = self.game.extract_answer(test_solution)
        
        # 验证提取结果
        expected = [[3, 1, 2, 4], [4, 2, 1, 3], [1, 4, 3, 2], [2, 3, 4, 1]]
        self.assertEqual(extracted, expected)
        
    def test_extract_comma_separated_format(self):
        """测试提取逗号分隔格式的答案"""
        test_solution = """
        解答如下：
        
        ```python
        [
          [3, 1, 2, 4],
          [4, 2, 1, 3],
          [1, 4, 3, 2],
          [2, 3, 4, 1]
        ]
        ```
        """
        
        # 提取答案
        extracted = self.game.extract_answer(test_solution)
        
        # 验证提取结果
        expected = [[3, 1, 2, 4], [4, 2, 1, 3], [1, 4, 3, 2], [2, 3, 4, 1]]
        self.assertEqual(extracted, expected)
        
    def test_extract_invalid_format(self):
        """测试提取无效格式的答案"""
        test_solution = """
        我觉得这个问题很难，无法找到解决方案。
        """
        
        # 提取答案
        extracted = self.game.extract_answer(test_solution)
        
        # 验证提取结果，应该返回原始字符串
        self.assertEqual(extracted, test_solution)

    def test_extract_code_block_format(self):
        """测试从```python代码块中提取答案"""
        test_solution = """
        我分析了这个摩天楼谜题，得出以下解答：

        ```python
        [
          [3, 1, 2, 4],
          [4, 2, 1, 3],
          [1, 4, 3, 2],
          [2, 3, 4, 1]
        ]
        ```

        上面的解答满足了所有约束条件：
        1. 每行每列数字不重复
        2. 外围数字与可见摩天楼数量相符
        """
        
        # 提取答案
        extracted = self.game.extract_answer(test_solution)
        
        # 验证提取结果
        expected = [[3, 1, 2, 4], [4, 2, 1, 3], [1, 4, 3, 2], [2, 3, 4, 1]]
        self.assertEqual(extracted, expected)
        
    def test_extract_code_block_with_comments(self):
        """测试从带有注释的```python代码块中提取答案"""
        test_solution = """
        以下是我的解答：

        ```python
        # 这是最终答案
        [
          [2, 4, 1, 3],  # 第一行
          [3, 1, 4, 2],  # 第二行
          [4, 2, 3, 1],  # 第三行
          [1, 3, 2, 4]   # 第四行
        ]
        # 这个解答满足所有条件
        ```
        """
        
        # 提取答案
        extracted = self.game.extract_answer(test_solution)
        
        # 验证提取结果
        expected = [[2, 4, 1, 3], [3, 1, 4, 2], [4, 2, 3, 1], [1, 3, 2, 4]]
        self.assertEqual(extracted, expected)

if __name__ == "__main__":
    unittest.main() 
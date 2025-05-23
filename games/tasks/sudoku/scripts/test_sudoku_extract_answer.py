import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from games.tasks.sudoku.scripts.sudoku import Sudoku

class TestSudokuExtractAnswer(unittest.TestCase):
    """
    测试数独游戏答案提取方法
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        self.game = Sudoku()
        
        # 构造一个标准的9x9数独答案（元组形式）
        self.sudoku_answer = (
            (1, 2, 3, 4, 5, 6, 7, 8, 9),
            (4, 5, 6, 7, 8, 9, 1, 2, 3),
            (7, 8, 9, 1, 2, 3, 4, 5, 6),
            (2, 3, 4, 5, 6, 7, 8, 9, 1),
            (5, 6, 7, 8, 9, 1, 2, 3, 4),
            (8, 9, 1, 2, 3, 4, 5, 6, 7),
            (3, 4, 5, 6, 7, 8, 9, 1, 2),
            (6, 7, 8, 9, 1, 2, 3, 4, 5),
            (9, 1, 2, 3, 4, 5, 6, 7, 8)
        )
        
        self.sudoku_answer_str = str(self.sudoku_answer)
        
    def test_extract_from_markdown_code_block(self):
        """
        测试从Markdown代码块中提取答案
        """
        # 构造一个包含Markdown代码块的回答
        markdown_solution = """
我解答了这个数独题目。

根据数独规则，每行、每列和每个3x3方格中的数字1-9不能重复。

解答如下：

```python
((1, 2, 3, 4, 5, 6, 7, 8, 9),
 (4, 5, 6, 7, 8, 9, 1, 2, 3),
 (7, 8, 9, 1, 2, 3, 4, 5, 6),
 (2, 3, 4, 5, 6, 7, 8, 9, 1),
 (5, 6, 7, 8, 9, 1, 2, 3, 4),
 (8, 9, 1, 2, 3, 4, 5, 6, 7),
 (3, 4, 5, 6, 7, 8, 9, 1, 2),
 (6, 7, 8, 9, 1, 2, 3, 4, 5),
 (9, 1, 2, 3, 4, 5, 6, 7, 8))
```

这就是数独的解答。
"""
        
        # 提取答案
        extracted_answer = self.game.extract_answer(markdown_solution)
        
        # 清理提取的答案和预期答案，移除空格和换行符以便比较
        clean_extracted = ''.join(extracted_answer.split())
        clean_expected = ''.join(self.sudoku_answer_str.split())
        
        # 检查提取的答案是否正确
        self.assertEqual(clean_extracted, clean_expected)
        
    def test_extract_from_markdown_code_block_no_newlines(self):
        """
        测试从没有换行符的Markdown代码块中提取答案
        """
        # 构造一个没有换行符的Markdown代码块
        markdown_solution = """
数独题目已解决。

```python
((1,2,3,4,5,6,7,8,9),(4,5,6,7,8,9,1,2,3),(7,8,9,1,2,3,4,5,6),(2,3,4,5,6,7,8,9,1),(5,6,7,8,9,1,2,3,4),(8,9,1,2,3,4,5,6,7),(3,4,5,6,7,8,9,1,2),(6,7,8,9,1,2,3,4,5),(9,1,2,3,4,5,6,7,8))
```
"""
        
        # 提取答案
        extracted_answer = self.game.extract_answer(markdown_solution)
        
        # 清理提取的答案和预期答案，移除空格和换行符以便比较
        clean_extracted = ''.join(extracted_answer.split())
        clean_expected = ''.join(self.sudoku_answer_str.split())
        
        # 检查提取的答案是否正确
        self.assertEqual(clean_extracted, clean_expected)
        
    def test_extract_from_multiple_code_blocks(self):
        """
        测试从多个代码块中提取答案（应该返回最后一个）
        """
        # 构造一个包含多个代码块的回答
        markdown_solution = """
我先分析一下数独：

```python
# 分析代码
def analyze_sudoku(grid):
    # ...分析代码
    pass
```

最终解答是：

```python
((1, 2, 3, 4, 5, 6, 7, 8, 9),
 (4, 5, 6, 7, 8, 9, 1, 2, 3),
 (7, 8, 9, 1, 2, 3, 4, 5, 6),
 (2, 3, 4, 5, 6, 7, 8, 9, 1),
 (5, 6, 7, 8, 9, 1, 2, 3, 4),
 (8, 9, 1, 2, 3, 4, 5, 6, 7),
 (3, 4, 5, 6, 7, 8, 9, 1, 2),
 (6, 7, 8, 9, 1, 2, 3, 4, 5),
 (9, 1, 2, 3, 4, 5, 6, 7, 8))
```
"""
        
        # 提取答案
        extracted_answer = self.game.extract_answer(markdown_solution)
        
        # 清理提取的答案和预期答案，移除空格和换行符以便比较
        clean_extracted = ''.join(extracted_answer.split())
        clean_expected = ''.join(self.sudoku_answer_str.split())
        
        # 检查提取的答案是否正确
        self.assertEqual(clean_extracted, clean_expected)
        
    def test_extract_from_raw_tuple(self):
        """
        测试从原始元组字符串中提取答案（没有代码块）
        """
        # 构造一个只包含元组的回答
        tuple_solution = """
解数独的结果是：

((1, 2, 3, 4, 5, 6, 7, 8, 9),
(4, 5, 6, 7, 8, 9, 1, 2, 3),
(7, 8, 9, 1, 2, 3, 4, 5, 6),
(2, 3, 4, 5, 6, 7, 8, 9, 1),
(5, 6, 7, 8, 9, 1, 2, 3, 4),
(8, 9, 1, 2, 3, 4, 5, 6, 7),
(3, 4, 5, 6, 7, 8, 9, 1, 2),
(6, 7, 8, 9, 1, 2, 3, 4, 5),
(9, 1, 2, 3, 4, 5, 6, 7, 8))
"""
        
        # 提取答案
        extracted_answer = self.game.extract_answer(tuple_solution)
        
        # 清理提取的答案和预期答案，移除空格和换行符以便比较
        clean_extracted = ''.join(extracted_answer.split())
        clean_expected = ''.join(self.sudoku_answer_str.split())
        
        # 检查提取的答案是否正确
        self.assertEqual(clean_extracted, clean_expected)
        
    def test_extract_from_empty_response(self):
        """
        测试从空回答中提取答案
        """
        # 提取答案
        extracted_answer = self.game.extract_answer("")
        
        # 应该返回空字符串
        self.assertEqual(extracted_answer, "")
        
    def test_extract_from_response_without_answer(self):
        """
        测试从不包含答案的回答中提取答案
        """
        # 构造一个不包含答案的回答
        no_answer_solution = """
我无法解决这个数独题目，因为它太难了。
请给我一个更简单的题目。
"""
        
        # 提取答案
        extracted_answer = self.game.extract_answer(no_answer_solution)
        
        # 应该返回空字符串
        self.assertEqual(extracted_answer, "")

if __name__ == '__main__':
    unittest.main()
import unittest
import sys
import os
import copy

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from base.data import Data
from games.tasks.sudoku.scripts.sudoku import Sudoku
from games.tasks.sudoku.scripts.sudoku_verifier import SudokuVerifier

class TestSudokuVerify(unittest.TestCase):
    """
    测试数独游戏验证方法
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        self.game = Sudoku()
        self.verifier = SudokuVerifier()
        
        # 创建一个简单的数独示例
        self.complete_sudoku = [
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            [4, 5, 6, 7, 8, 9, 1, 2, 3],
            [7, 8, 9, 1, 2, 3, 4, 5, 6],
            [2, 3, 4, 5, 6, 7, 8, 9, 1],
            [5, 6, 7, 8, 9, 1, 2, 3, 4],
            [8, 9, 1, 2, 3, 4, 5, 6, 7],
            [3, 4, 5, 6, 7, 8, 9, 1, 2],
            [6, 7, 8, 9, 1, 2, 3, 4, 5],
            [9, 1, 2, 3, 4, 5, 6, 7, 8]
        ]
        
        # 创建一个带空格的数独题目
        self.masked_sudoku = copy.deepcopy(self.complete_sudoku)
        # 将一些格子设为'X'
        self.masked_sudoku[0][1] = 'X'
        self.masked_sudoku[1][2] = 'X'
        self.masked_sudoku[2][3] = 'X'
        self.masked_sudoku[3][4] = 'X'
        self.masked_sudoku[4][5] = 'X'
        self.masked_sudoku[5][6] = 'X'
        self.masked_sudoku[6][7] = 'X'
        self.masked_sudoku[7][8] = 'X'
        self.masked_sudoku[8][0] = 'X'
        
        # 创建数据对象
        self.data = Data(
            question="测试数独题目",
            answer=str(tuple(tuple(row) for row in self.complete_sudoku)),
            metadata={
                "original_sudoku": self.masked_sudoku,
                "complete_sudoku": self.complete_sudoku,
                "difficulty": 1
            }
        )
        
    def test_verify_correct_solution(self):
        """
        测试验证正确解答
        """
        # 将完整数独转换为元组形式的字符串
        solution = str(tuple(tuple(row) for row in self.complete_sudoku))
        
        # 验证解答
        result = self.verifier.verify(self.data, solution)
        
        # 应该返回True
        self.assertTrue(result)
        
    def test_verify_incorrect_solution_wrong_number(self):
        """
        测试验证错误解答 - 数字错误
        """
        # 复制完整数独并修改一个数字
        incorrect_sudoku = copy.deepcopy(self.complete_sudoku)
        incorrect_sudoku[0][0] = 2  # 修改第一个数字
        
        # 将错误数独转换为元组形式的字符串
        solution = str(tuple(tuple(row) for row in incorrect_sudoku))
        
        # 验证解答
        result = self.verifier.verify(self.data, solution)
        
        # 应该返回False
        self.assertFalse(result)
        
    def test_verify_incorrect_solution_invalid_sudoku(self):
        """
        测试验证错误解答 - 无效数独（不符合数独规则）
        """
        # 复制完整数独并修改一些数字使其不符合数独规则
        incorrect_sudoku = copy.deepcopy(self.complete_sudoku)
        incorrect_sudoku[0][0] = incorrect_sudoku[0][1]  # 在同一行中放置相同的数字
        
        # 将错误数独转换为元组形式的字符串
        solution = str(tuple(tuple(row) for row in incorrect_sudoku))
        
        # 验证解答
        result = self.verifier.verify(self.data, solution)
        
        # 应该返回False
        self.assertFalse(result)
        
    def test_verify_empty_solution(self):
        """
        测试验证空解答
        """
        # 验证空解答
        result = self.verifier.verify(self.data, "")
        
        # 应该返回False
        self.assertFalse(result)
        
    def test_verify_malformed_solution(self):
        """
        测试验证格式错误的解答
        """
        # 格式错误的解答
        malformed_solution = "这不是一个有效的数独解答"
        
        # 验证解答
        result = self.verifier.verify(self.data, malformed_solution)
        
        # 应该返回False
        self.assertFalse(result)
        
    def test_verify_incomplete_solution(self):
        """
        测试验证不完整的解答
        """
        # 不完整的解答（只有部分行）
        incomplete_sudoku = self.complete_sudoku[:5]  # 只取前5行
        
        # 将不完整数独转换为元组形式的字符串
        solution = str(tuple(tuple(row) for row in incomplete_sudoku))
        
        # 验证解答
        result = self.verifier.verify(self.data, solution)
        
        # 应该返回False
        self.assertFalse(result)
        
    def test_verify_solution_with_missing_metadata(self):
        """
        测试当元数据缺失时的验证
        """
        # 创建一个没有original_sudoku元数据的数据对象
        data_without_metadata = Data(
            question="测试数独题目",
            answer=str(tuple(tuple(row) for row in self.complete_sudoku)),
            metadata={}
        )
        
        # 将完整数独转换为元组形式的字符串
        solution = str(tuple(tuple(row) for row in self.complete_sudoku))
        
        # 验证解答
        result = self.verifier.verify(data_without_metadata, solution)
        
        # 由于缺少元数据，应该返回False
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main() 
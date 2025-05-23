import unittest
import sys
import os
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from games.tasks.sudoku.scripts.sudoku import Sudoku

class TestSudokuGenerate(unittest.TestCase):
    """
    测试数独游戏生成方法
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        self.game = Sudoku()
        self.num_of_questions = 5  # 为了快速测试，只生成少量题目
        
    def test_generate_with_default_parameters(self):
        """
        测试使用默认参数生成数独
        """
        game_data_list = self.game.generate(num_of_questions=self.num_of_questions)
        
        # 检查是否生成了正确数量的题目
        self.assertEqual(len(game_data_list), self.num_of_questions)
        
        # 检查每个题目的元数据
        for data in game_data_list:
            # 检查元数据是否存在
            self.assertIsNotNone(data.metadata)
            
            # 检查元数据中是否包含必要字段
            self.assertIn("original_sudoku", data.metadata)
            self.assertIn("complete_sudoku", data.metadata)
            self.assertIn("difficulty", data.metadata)
            self.assertIn("trace_id", data.metadata)
            
            # 检查难度值是否在正确范围内
            self.assertGreaterEqual(data.metadata["difficulty"], 1)
            self.assertLessEqual(data.metadata["difficulty"], 5)
            
            # 检查原始数独和完整数独的尺寸
            original_sudoku = data.metadata["original_sudoku"]
            complete_sudoku = data.metadata["complete_sudoku"]
            
            self.assertEqual(len(original_sudoku), 9)
            self.assertEqual(len(complete_sudoku), 9)
            
            for i in range(9):
                self.assertEqual(len(original_sudoku[i]), 9)
                self.assertEqual(len(complete_sudoku[i]), 9)
    
    def test_generate_with_different_difficulties(self):
        """
        测试使用不同难度级别生成数独
        """
        for difficulty in range(1, 5):  # 测试难度1-4
            game_data_list = self.game.generate(
                num_of_questions=1,
                difficulty=difficulty
            )
            
            # 检查是否生成了题目
            self.assertEqual(len(game_data_list), 1)
            
            # 检查难度级别是否正确
            self.assertEqual(game_data_list[0].metadata["difficulty"], difficulty)
            
            # 检查空格数量是否与难度相符
            original_sudoku = game_data_list[0].metadata["original_sudoku"]
            empty_cells = sum(1 for row in original_sudoku for cell in row if cell == 'X')
            
            # 根据难度级别，空格数量应该在特定范围内
            # 难度1：简单，保留35-45个提示单元格，即有36-46个空格
            # 难度2：中等，保留30-35个提示单元格，即有46-51个空格
            # 难度3：困难，保留25-30个提示单元格，即有51-56个空格
            # 难度4：专家，保留20-25个提示单元格，即有56-61个空格
            cells_to_keep_range = {
                1: (35, 45),  # 简单
                2: (30, 35),  # 中等
                3: (25, 30),  # 困难
                4: (20, 25),  # 专家
            }
            
            min_cells, max_cells = cells_to_keep_range.get(difficulty, (20, 25))
            min_empty = 81 - max_cells
            max_empty = 81 - min_cells
            
            # 检查空格数量是否在预期范围内（允许有±5的误差）
            self.assertGreaterEqual(empty_cells, min_empty - 5)
            self.assertLessEqual(empty_cells, max_empty + 5)
    
    def test_complete_sudoku_validity(self):
        """
        测试生成的完整数独是否有效
        """
        game_data_list = self.game.generate(num_of_questions=1)
        complete_sudoku = game_data_list[0].metadata["complete_sudoku"]
        
        # 检查每行是否包含1-9的数字
        for row in complete_sudoku:
            self.assertEqual(set(row), set(range(1, 10)))
        
        # 检查每列是否包含1-9的数字
        for col in range(9):
            column = [complete_sudoku[row][col] for row in range(9)]
            self.assertEqual(set(column), set(range(1, 10)))
        
        # 检查每个3x3子网格是否包含1-9的数字
        for box_row in range(0, 9, 3):
            for box_col in range(0, 9, 3):
                box = []
                for r in range(box_row, box_row + 3):
                    for c in range(box_col, box_col + 3):
                        box.append(complete_sudoku[r][c])
                self.assertEqual(set(box), set(range(1, 10)))
    
    def test_generate_with_invalid_difficulty(self):
        """
        测试使用无效的难度级别
        """
        # 测试小于1的难度
        with self.assertRaises(ValueError):
            self.game.generate(num_of_questions=1, difficulty=0)
        
        # 测试大于4的难度
        with self.assertRaises(ValueError):
            self.game.generate(num_of_questions=1, difficulty=5)

if __name__ == '__main__':
    unittest.main() 
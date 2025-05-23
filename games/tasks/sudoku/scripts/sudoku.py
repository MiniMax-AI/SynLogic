import random
import uuid
import argparse
import json
import pathlib
import os
import copy
import re
import sys
from typing import List, Tuple, Optional
from collections import Counter
import time

from games.base.game import Game
from base.data import Data
from games.tasks.sudoku.scripts.sudoku_verifier import SudokuVerifier
from games.tasks.sudoku.scripts.sudoku_prompt import prompt_sudoku

class Sudoku(Game):
    """
    数独游戏类
    """
    def __init__(self):
        """
        初始化数独游戏
        """
        super().__init__("Sudoku", SudokuVerifier)
        
    def generate(self, num_of_questions: int = 100, max_attempts: int = 100,
                 difficulty: int = 3, unique_solution: bool = True):
        """
        生成数独游戏的题目
        
        @param num_of_questions: 要生成的题目数量
        @param max_attempts: 每个题目的最大尝试次数
        @param difficulty: 难度级别（1-4）
        @param unique_solution: 是否要求数独有唯一解
        @return: 生成的题目列表
        """
        # 参数校验
        if difficulty < 1 or difficulty > 4:
            raise ValueError("难度级别必须在1-4之间")
            
        game_data_list = []
        attempts = 0
        
        while len(game_data_list) < num_of_questions and attempts < max_attempts:
            try:
                attempts += 1
                
                # 生成完整的数独解答
                complete_sudoku = self._generate_complete_sudoku()
                
                # 根据难度级别遮挡部分数字
                masked_sudoku = self._mask_sudoku_by_difficulty(complete_sudoku, difficulty, unique_solution)
                
                # 生成问题描述（随机选择中文或英文）
                is_chinese = random.choice([True, False])
                question = prompt_sudoku(masked_sudoku, is_chinese)
                
                # 将完整解答转换为字符串形式
                answer_str = str(tuple(tuple(row) for row in complete_sudoku))
                
                # 创建游戏数据
                game_data = Data(
                    question=question,
                    answer=answer_str,
                    difficulty=difficulty,
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "original_sudoku": masked_sudoku,
                        "complete_sudoku": complete_sudoku,
                        "difficulty": difficulty,
                        "unique_solution": unique_solution,
                    }
                )
                
                game_data_list.append(game_data)
                
            except Exception as e:
                print(f"生成题目时出错: {e}")
                continue
                
        if len(game_data_list) < num_of_questions:
            print(f"警告: 只能生成 {len(game_data_list)}/{num_of_questions} 条游戏数据")
        
        return game_data_list
    
    def _generate_complete_sudoku(self):
        """
        生成一个完整有效的数独解答
        
        @return: 9x9的数独解答
        """
        # 初始化9x9的空数独网格
        grid = [[0 for _ in range(9)] for _ in range(9)]
        
        # 使用回溯算法填充数独
        if self._solve_sudoku(grid):
            return grid
        else:
            raise RuntimeError("无法生成有效的数独解答")
    
    def _is_valid_placement(self, grid, row, col, num):
        """
        检查在指定位置放置数字是否有效
        
        @param grid: 数独网格
        @param row: 行索引
        @param col: 列索引
        @param num: 要放置的数字
        @return: 是否是有效放置
        """
        # 检查行
        for x in range(9):
            if grid[row][x] == num:
                return False
        
        # 检查列
        for x in range(9):
            if grid[x][col] == num:
                return False
        
        # 检查3x3子网格
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if grid[i + start_row][j + start_col] == num:
                    return False
        
        return True
    
    def _solve_sudoku(self, grid):
        """
        使用回溯法解决数独
        
        @param grid: 数独网格
        @return: 是否成功解决
        """
        empty_cell = self._find_empty_cell(grid)
        if not empty_cell:
            return True  # 所有单元格都已填充，数独已解决
        
        row, col = empty_cell
        
        # 创建1-9的随机排列
        nums = list(range(1, 10))
        random.shuffle(nums)
        
        for num in nums:
            if self._is_valid_placement(grid, row, col, num):
                grid[row][col] = num
                
                if self._solve_sudoku(grid):
                    return True
                
                grid[row][col] = 0  # 回溯
        
        return False
    
    def _find_empty_cell(self, grid):
        """
        在数独网格中找到一个空单元格
        
        @param grid: 数独网格
        @return: 空单元格的(行,列)坐标，如果没有空单元格则返回None
        """
        for i in range(9):
            for j in range(9):
                if grid[i][j] == 0:
                    return (i, j)
        return None
    
    def _mask_sudoku_by_difficulty(self, complete_sudoku, difficulty, unique_solution=False):
        """
        根据难度级别遮挡数独中的一些数字
        
        @param complete_sudoku: 完整的数独解答
        @param difficulty: 难度级别（1-4）
        @param unique_solution: 是否要求数独有唯一解
        @return: 遮挡后的数独网格
        """
        # 复制完整数独以避免修改原始数据
        masked_sudoku = copy.deepcopy(complete_sudoku)
        
        # 根据难度确定要保留的单元格数量
        cells_to_keep_range = {
            1: (70, 80),
            2: (55, 70),
            3: (40, 55),
            4: (25, 40),
            # 老版难度
            # 1: (35, 45),  # 简单
            # 2: (30, 35),  # 中等
            # 3: (25, 30),  # 困难
            # 4: (20, 25),  # 专家
        }
        
        # 获取当前难度的单元格保留范围
        min_cells, max_cells = cells_to_keep_range.get(difficulty, (20, 25))
        
        # 在范围内随机选择要保留的单元格数量
        cells_to_keep = random.randint(min_cells, max_cells)
        
        # 创建所有单元格的列表
        all_cells = [(i, j) for i in range(9) for j in range(9)]
        
        # 随机打乱单元格顺序
        random.shuffle(all_cells)
        
        if not unique_solution:
            # 如果不要求唯一解，直接随机选择要保留的单元格
            cells_to_keep_coords = all_cells[:cells_to_keep]
            
            # 遮挡其他单元格
            for i in range(9):
                for j in range(9):
                    if (i, j) not in cells_to_keep_coords:
                        masked_sudoku[i][j] = 'X'
            
            return masked_sudoku
        
        # 如果要求唯一解，使用逐步移除的方法
        # 首先保留所有单元格（即完整的解答）
        current_sudoku = copy.deepcopy(complete_sudoku)
        cells_to_remove = len(all_cells) - cells_to_keep
        removed_cells = 0
        
        # 按照随机顺序尝试移除单元格
        for i, j in all_cells:
            # 暂时保存当前值
            temp_value = current_sudoku[i][j]
            current_sudoku[i][j] = 'X'
            
            # 检查移除后是否仍然有唯一解
            if self._has_unique_solution(current_sudoku, complete_sudoku):
                removed_cells += 1
                if removed_cells >= cells_to_remove:
                    break
            else:
                # 如果没有唯一解，恢复该单元格
                current_sudoku[i][j] = temp_value
        
        return current_sudoku
    
    def _has_unique_solution(self, masked_sudoku, expected_solution):
        """
        检查给定的数独是否有唯一解
        
        @param masked_sudoku: 遮挡后的数独网格
        @param expected_solution: 预期的解答
        @return: 是否有唯一解
        """
        # 创建一个数独副本用于求解
        sudoku_copy = [[0 if masked_sudoku[i][j] == 'X' else masked_sudoku[i][j] 
                        for j in range(9)] for i in range(9)]
        
        # 记录找到的解的数量和第一个解
        solutions = []
        
        def solve_all(grid, i=0, j=0):
            # 如果已经找到了多个解，可以提前返回
            if len(solutions) > 1:
                return
            
            # 如果到达了最后一行之后，说明找到了一个解
            if i == 9:
                # 检查这个解是否与预期的解相同
                if all(grid[i][j] == expected_solution[i][j] for i in range(9) for j in range(9)):
                    solutions.append(True)
                else:
                    solutions.append(False)
                return
            
            # 计算下一个单元格的坐标
            next_i, next_j = (i, j + 1) if j < 8 else (i + 1, 0)
            
            # 如果当前单元格已经有数字，直接处理下一个单元格
            if grid[i][j] != 0:
                solve_all(grid, next_i, next_j)
                return
            
            # 尝试在当前单元格填入1-9
            for num in range(1, 10):
                if self._is_valid_placement(grid, i, j, num):
                    grid[i][j] = num
                    solve_all(grid, next_i, next_j)
                    # 如果已经找到了多个解，可以提前返回
                    if len(solutions) > 1:
                        return
                    grid[i][j] = 0
        
        solve_all(sudoku_copy)
        
        # 如果只找到一个解，并且这个解与预期的解相同，则说明数独有唯一解
        return len(solutions) == 1 and solutions[0] == True
    
    def extract_answer(self, test_solution: str):
        """
        从模型的回答中提取数独解答
        
        @param test_solution: 模型的完整回答
        @return: 提取的答案（元组形式的字符串）
        """
        if not test_solution:
            return ""
        
        # 提取Python代码块中的内容
        code_block_pattern = r"```python\s*([\s\S]*?)\s*```"
        matches = re.findall(code_block_pattern, test_solution)
        
        if matches:
            # 取最后一个Python代码块
            python_code = matches[-1].strip()
            return python_code
        
        # 如果没有找到Python代码块，尝试找到任何类似于元组的结构
        tuple_pattern = r"\(\s*\(\s*\d+\s*,.*?\)\s*\)"
        matches = re.findall(tuple_pattern, test_solution, re.DOTALL)
        
        if matches:
            return matches[-1].strip()
        
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="数独游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个题目的最大尝试次数")
    parser.add_argument("--difficulty", type=int, default=3, help="难度级别（1-4）")
    parser.add_argument("--unique_solution", action="store_true", help="是否要求数独有唯一解（默认：否）")
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置输出文件名
    output_dir = data_dir / f"unique_solution_{args.unique_solution}/difficulty_{args.difficulty}/num_of_data_{args.num_of_data}"
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "data.jsonl"
    
    # 创建游戏实例
    game = Sudoku()
    
    # 记录开始时间
    start_time = time.time()
    
    # 生成游戏数据
    print("正在生成数独游戏数据...")
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts,
        difficulty=args.difficulty,
        unique_solution=args.unique_solution
    )
    
    # 记录结束时间
    end_time = time.time()
    generation_time = end_time - start_time
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据，耗时 {generation_time:.2f} 秒")
    print(f"唯一解设置: {'是' if args.unique_solution else '否'}")
    
    # 将数据保存到文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"游戏数据已保存到 {output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}") 
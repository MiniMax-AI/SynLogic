import random
import numpy as np
import re
from typing import List, Dict, Tuple
import json
import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from calcudoko_prompt import prompt_calcudoko
from tqdm import tqdm
import json
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)
    
class CalcudokoGenerator:
    def __init__(self, grid_size: int):
        """
        Initialize the Calcudoko generator
        @param grid_size: size of the grid (N)
        """
        self.grid_size = grid_size
        self.operators = ['+', '-', '*', '÷']
        self.grid = None
        self.regions = []
        
    @staticmethod
    def extract_answer(response: str) -> List[List[int]]:
        """
        Extract answer from model response
        @param response: model response string
        @return: list of lists containing the answer grid
        """
        # Find the answer pattern [[...]]
        pattern = r'\[\[(.*?)\]\]'
        match = re.search(pattern, response)
        if not match:
            raise ValueError("No answer found in the response")
        
        # Extract the answer content
        answer_str = match.group(1)
        
        # Split into rows
        rows = answer_str.split(',')
        
        # Convert each row into a list of integers
        grid = []
        for row in rows:
            # Split row into numbers and convert to integers
            numbers = [int(n) for n in row.strip().split()]
            grid.append(numbers)
        
        return grid
    
    def generate_sudoku_grid(self) -> np.ndarray:
        """
        Generate a valid Sudoku grid
        @return: numpy array of the grid
        """
        def is_valid(grid: np.ndarray, row: int, col: int, num: int) -> bool:
            # Check row
            if num in grid[row]:
                return False
            # Check column
            if num in grid[:, col]:
                return False
            return True
        
        def solve(grid: np.ndarray) -> bool:
            for row in range(self.grid_size):
                for col in range(self.grid_size):
                    if grid[row][col] == 0:
                        for num in range(1, self.grid_size + 1):
                            if is_valid(grid, row, col, num):
                                grid[row][col] = num
                                if solve(grid):
                                    return True
                                grid[row][col] = 0
                        return False
            return True
        
        # Initialize empty grid
        grid = np.zeros((self.grid_size, self.grid_size), dtype=int)
        # Fill first row randomly
        grid[0] = np.random.permutation(range(1, self.grid_size + 1))
        # Solve the rest
        solve(grid)
        return grid
    
    def create_regions(self) -> List[Dict]:
        """
        Create regions by grouping coordinates and assigning operators
        @return: list of regions with cells, target numbers and operators
        """
        # Get all coordinates
        coords = [(i, j) for i in range(self.grid_size) for j in range(self.grid_size)]
        random.shuffle(coords)
        
        # Create regions
        regions = []
        used_coords = set()
        max_attempts = 1000  # 防止无限循环
        
        while len(used_coords) < len(coords):
            attempts = 0
            while attempts < max_attempts:
                # 获取未使用的坐标
                available_coords = [c for c in coords if c not in used_coords]
                if not available_coords:
                    break
                
                # 从未使用的坐标中随机选择一个作为起点
                start_coord = random.choice(available_coords)
                
                # 确定区域大小（至少2个格子）
                max_size = min(4, len(available_coords))  # 限制最大区域大小为4
                if max_size < 2:
                    # 如果剩余格子不足2个，直接将其添加到最后一个区域
                    if regions:
                        last_region = regions[-1]
                        for coord in available_coords:
                            last_region['cells'].append(f"({coord[0]+1},{coord[1]+1})")
                            used_coords.add(coord)
                    break
                
                # 随机选择区域大小
                region_size = random.randint(2, max_size)
                
                # 尝试构建一个连续的区域
                region_coords = [start_coord]
                current_coord = start_coord
                for _ in range(region_size - 1):
                    # 获取相邻的未使用坐标
                    neighbors = []
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        nx, ny = current_coord[0] + dx, current_coord[1] + dy
                        if (0 <= nx < self.grid_size and 
                            0 <= ny < self.grid_size and 
                            (nx, ny) in available_coords and 
                            (nx, ny) not in region_coords):
                            neighbors.append((nx, ny))
                    
                    if not neighbors:
                        break
                    
                    # 随机选择一个相邻坐标
                    next_coord = random.choice(neighbors)
                    region_coords.append(next_coord)
                    current_coord = next_coord
                
                # 如果区域大小不足2，重试
                if len(region_coords) < 2:
                    attempts += 1
                    continue
                
                # 获取区域内的数字
                numbers = [self.grid[r][c] for r, c in region_coords]
                
                # 检查数字是否唯一
                if len(set(numbers)) != len(numbers):
                    attempts += 1
                    continue
                
                # 根据区域大小选择运算符
                if len(region_coords) == 2:
                    operator = random.choice(['-', '÷'])
                else:
                    operator = random.choice(['+', '*'])
                
                # 计算目标数字
                if operator == '+':
                    target = sum(numbers)
                elif operator == '-':
                    target = abs(numbers[0] - numbers[1])
                elif operator == '*':
                    target = np.prod(numbers)
                else:  # division
                    target = max(numbers[0] // numbers[1], numbers[1] // numbers[0])
                
                # 添加区域
                regions.append({
                    "cells": [f"({r+1},{c+1})" for r, c in region_coords],
                    "target": target,
                    "operator": operator
                })
                
                # 更新已使用的坐标
                for coord in region_coords:
                    used_coords.add(coord)
                break
            
            if attempts >= max_attempts:
                # 如果多次尝试失败，将剩余的格子作为单独的区域
                remaining_coords = [c for c in coords if c not in used_coords]
                if remaining_coords and len(remaining_coords) >= 2:
                    # 将剩余格子两两配对
                    while len(remaining_coords) >= 2:
                        pair = remaining_coords[:2]
                        numbers = [self.grid[r][c] for r, c in pair]
                        operator = random.choice(['-', '÷'])
                        if operator == '-':
                            target = abs(numbers[0] - numbers[1])
                        else:  # division
                            target = max(numbers[0] // numbers[1], numbers[1] // numbers[0])
                        
                        regions.append({
                            "cells": [f"({r+1},{c+1})" for r, c in pair],
                            "target": target,
                            "operator": operator
                        })
                        for coord in pair:
                            used_coords.add(coord)
                        remaining_coords = remaining_coords[2:]
                elif remaining_coords and regions:
                    # 如果只剩一个格子，将其添加到最后一个区域
                    last_region = regions[-1]
                    for coord in remaining_coords:
                        last_region['cells'].append(f"({coord[0]+1},{coord[1]+1})")
                        used_coords.add(coord)
        
        # 检查是否所有格子都被分配到区域中，如果没有，返回None以触发重新生成
        if len(used_coords) == len(coords) and regions:
            return regions
        return None  # 如果生成失败，返回None
    
    def generate(self) -> Tuple[str, np.ndarray]:
        """
        Generate a complete Calcudoku puzzle
        @return: tuple of (question, solution grid)
        """
        # Generate Sudoku grid
        self.grid = self.generate_sudoku_grid()
        
        # Create regions and ensure they are generated
        while True:
            self.regions = self.create_regions()
            if self.regions:  # Only proceed if regions were successfully created
                break
        
        # Generate question
        question = prompt_calcudoko(self.grid_size, self.regions)
        
        # Convert grid to answer string format
        answer = "[[" + ",".join([" ".join(map(str, row)) for row in self.grid]) + "]]"
        
        return question, answer, self.regions

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate Calcudoko puzzles')
    parser.add_argument('--num_of_data', type=int, default=100, help='Number of puzzles to generate')
    parser.add_argument('--grid_size', type=int, default=4, help='Size of the grid (N)')
    args = parser.parse_args()
    
    # 获取calcudoko目录的路径
    calcudoko_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 在calcudoko目录下创建data文件夹
    data_dir = os.path.join(calcudoko_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # 在data目录下创建grid_size子目录
    output_dir = os.path.join(data_dir, f"grid_size_{args.grid_size}")
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成包含参数信息的文件名
    output_filename = f"puzzles_grid{args.grid_size}_n{args.num_of_data}.jsonl"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"开始生成 {args.num_of_data} 个 {args.grid_size}x{args.grid_size} 的数独谜题...")
    
    # Generate puzzles with progress bar
    generator = CalcudokoGenerator(args.grid_size)
    
    # 使用一个文件保存所有数据
    with open(output_path, 'w') as f:
        for i in tqdm(range(args.num_of_data), desc="生成进度"):
            question, answer, regions = generator.generate()
            # 写入一行数据，包含题目序号，确保换行符被替换为 \n
            # question = question.replace(chr(10), "\\n")
            # metadata = {"grid_size":args.grid_size, "regions":regions}
            # metadata = {
            #         "grid_size": args.grid_size, 
            #         "regions": regions
            #     }
            # metadata_str=json.dumps(metadata)
            data = {
                "id": i+1, 
                "question": question.replace(chr(10), "\\n"), 
                "answer": answer, 
                "metadata": {
                    "grid_size": args.grid_size, 
                    "regions": regions
                }
                
            }
            # 使用json.dumps正确序列化为JSON字符串
            json_str = json.dumps(data, ensure_ascii=False, cls=NumpyEncoder)
            f.write(json_str + "\n")
            
    
    print(f"\n数据已保存到: {output_path}")

if __name__ == "__main__":
    main() 
from games.base.game import Game
from base.data import Data
from games.tasks.kukurasu.scripts.kukurasu_verifier import KukurasuVerifier
from games.tasks.kukurasu.scripts.kukurasu_prompt import prompt_kukurasu
import random
import re
import argparse
import json
import pathlib
import uuid
import numpy as np


class Kukurasu(Game):
    """
    Kukurasu puzzle game
    数独拼图游戏
    """
    def __init__(self, n: int = 4, m: int = 4, ones_probability: float = 0.3):
        super().__init__("Kukurasu", KukurasuVerifier)
        print(f"Initializing Kukurasu with grid size {n}×{m}, ones probability: {ones_probability}")
        self.n = n  # 行数
        self.m = m  # 列数
        self.ones_probability = ones_probability  # "1"的概率
        
    def generate(self, num_of_questions: int = 100, max_attempts: int = 1000):
        """Generate Kukurasu puzzles that have at least one solution
        生成至少有一个解的Kukurasu拼图"""
        game_data_list = []  # 游戏数据列表
        puzzle_hashes = set()  # 拼图哈希集合，用于避免重复
        
        for _ in range(num_of_questions):
            for attempt_idx in range(max_attempts):
                # Generate a random solution grid with 1s and Xs
                # 生成一个包含1和X的随机解决方案网格
                solution_grid = self._generate_random_solution()
                
                # Calculate row and column sums based on the solution
                # 根据解决方案计算行和列的总和
                row_sums, col_sums = self._calculate_sums(solution_grid)
                
                # Create an empty grid filled with "X"
                # 创建一个填充了"X"的空网格
                empty_grid = [["X" for _ in range(self.m)] for _ in range(self.n)]
                
                # Create a hash of the puzzle to avoid duplicates
                # 创建拼图的哈希值以避免重复
                puzzle_hash = hash(tuple(map(tuple, solution_grid)))
                if puzzle_hash in puzzle_hashes:
                    continue
                
                puzzle_hashes.add(puzzle_hash)
                
                # Verify the puzzle is solvable and has a unique solution
                # 验证拼图是可解的并且有唯一解
                if self._is_valid_puzzle(row_sums, col_sums):
                    game_data = Data(
                        question=prompt_kukurasu(empty_grid, row_sums, col_sums),
                        answer="",
                        metadata={
                            "trace_id": str(uuid.uuid4()),
                            "grid": empty_grid,
                            "row_sums": row_sums,  # 行总和
                            "col_sums": col_sums,  # 列总和
                            "solution": solution_grid,  # 解决方案
                            "n": self.n,
                            "m": self.m,
                            "ones_probability": self.ones_probability  # 添加"1"的概率到元数据
                        }
                    )
                    game_data_list.append(game_data)
                    break
                    
            if attempt_idx == max_attempts - 1:
                print(f"Failed to generate a valid puzzle after {max_attempts} attempts")
                print(f"在{max_attempts}次尝试后未能生成有效的拼图")
        
        return game_data_list
    
    def _generate_random_solution(self):
        """Generate a random valid solution grid
        生成一个随机有效的解决方案网格"""
        # Create a grid with random 1s and Xs
        # 创建一个包含随机1和X的网格
        grid = []
        for i in range(self.n):
            row = []
            for j in range(self.m):
                # Randomly decide if this cell should be 1 or X based on ones_probability
                # 根据ones_probability随机决定这个单元格应该是1还是X
                if random.random() < self.ones_probability:  # 使用ones_probability参数
                    row.append("1")
                else:
                    row.append("X")
            grid.append(row)
        
        return grid
    
    def _calculate_sums(self, grid):
        """Calculate row and column sums based on the solution grid
        根据解决方案网格计算行和列的总和"""
        row_sums = []  # 行总和
        col_sums = []  # 列总和
        
        # Calculate row sums
        # 计算行总和
        for i, row in enumerate(grid):
            row_sum = 0
            for j, cell in enumerate(row):
                if cell == "1":
                    # Weight is column position (1-indexed)
                    # 权重是列位置（从1开始索引）
                    row_sum += (j + 1)
            row_sums.append(row_sum)
        
        # Calculate column sums
        # 计算列总和
        for j in range(self.m):
            col_sum = 0
            for i in range(self.n):
                if grid[i][j] == "1":
                    # Weight is row position (1-indexed)
                    # 权重是行位置（从1开始索引）
                    col_sum += (i + 1)
            col_sums.append(col_sum)
        
        return row_sums, col_sums
    
    def _is_valid_puzzle(self, row_sums, col_sums):
        """Check if the puzzle has a valid solution
        检查拼图是否有有效的解决方案"""
        if 0 in row_sums or 0 in col_sums:
            return False
        
        if sum(row_sums) != sum(col_sums):
            return False
        
        return True
    
    def extract_answer(self, response: str):
        """Extract the answer grid from the model's response
        从模型的响应中提取答案网格"""
        # Look for a grid representation in the response
        # 在响应中寻找网格表示
        grid_pattern = r'\[\s*\[(?:\s*"[X1]"\s*,\s*)*\s*"[X1]"\s*\]\s*(?:,\s*\[(?:\s*"[X1]"\s*,\s*)*\s*"[X1]"\s*\]\s*)*\]'
        match = re.search(grid_pattern, response)
        
        if match:
            try:
                # Try to parse the grid as JSON
                # 尝试将网格解析为JSON
                grid_str = match.group(0)
                return json.loads(grid_str)
            except json.JSONDecodeError:
                pass
        
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_of_data", type=int, default=100)  # 数据数量
    parser.add_argument("--max_attempts", type=int, default=1000)  # 最大尝试次数
    parser.add_argument("--n", type=int, default=4)  # 行数
    parser.add_argument("--m", type=int, default=4)  # 列数
    parser.add_argument("--ones_probability", type=float, default=0.3)  # "1"的概率
    args = parser.parse_args()
    
    data_dir = pathlib.Path(__file__).parent.parent / "data" / f"n_{args.n}" / f"m_{args.m}" / f"p_{args.ones_probability}"  # 数据目录
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = data_dir / f"kukurasu_{args.n}x{args.m}_p{args.ones_probability}_{args.num_of_data}.jsonl"  # 输出文件名包含概率
    
    game = Kukurasu(n=args.n, m=args.m, ones_probability=args.ones_probability)
    game_data_list = game.generate(args.num_of_data, args.max_attempts)  # 生成游戏数据列表
    
    if len(game_data_list) == 0:
        print(f"Failed to generate any Kukurasu puzzles after {args.max_attempts} attempts")
        print(f"在{args.max_attempts}次尝试后未能生成任何Kukurasu拼图")
        exit(1)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        for game_data in game_data_list:
            f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
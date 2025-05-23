from games.base.game import Game
from base.data import Data
from games.tasks.numbrix.scripts.numbrix_prompt import prompt_numbrix
from games.tasks.numbrix.scripts.numbrix_verifier import NumbrixVerifier
import random       
import re
import argparse
import json
import pathlib
import uuid
import numpy as np
import math
from collections import deque

class Numbrix(Game):
    """
    Numbrix 游戏
    一个基于网格的数字逻辑谜题，玩家需要将数字从 1 到 n² 填入网格中，形成一条连续的路径
    """
    def __init__(self, n: int = 4, fill_rate: float = 0.3):
        super().__init__("Numbrix", NumbrixVerifier)
        print(f"初始化 Numbrix 游戏，网格大小: {n}x{n}，填充率: {fill_rate}")
        self.n = n  # 网格大小
        self.fill_rate = fill_rate  # 预填充的比例

    def _generate_solution(self):
        """生成一个有效的 Numbrix 解决方案（蛇形路径）"""
        n = self.n
        max_attempts = 100  # 限制尝试次数
        
        for _ in range(max_attempts):
            grid = [[0 for _ in range(n)] for _ in range(n)]
            
            # 定义可能的移动方向（上、右、下、左）
            directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            
            # 随机选择起点
            row, col = random.randrange(n), random.randrange(n)
            grid[row][col] = 1
            
            # 使用贪心算法生成路径
            current_num = 2
            steps_without_progress = 0
            max_steps_without_progress = n * n * 2
            
            while current_num <= n * n and steps_without_progress < max_steps_without_progress:
                # 收集所有可能的下一步位置
                possible_moves = []
                for dr, dc in directions:
                    new_row, new_col = row + dr, col + dc
                    if (0 <= new_row < n and 0 <= new_col < n and grid[new_row][new_col] == 0):
                        possible_moves.append((new_row, new_col))
                
                if not possible_moves:
                    # 没有可用的移动，重新开始当前尝试
                    steps_without_progress += 1
                    continue
                
                # 随机选择下一步
                next_row, next_col = random.choice(possible_moves)
                grid[next_row][next_col] = current_num
                row, col = next_row, next_col
                current_num += 1
                steps_without_progress = 0
            
            # 检查是否成功生成完整解决方案
            if current_num > n * n:
                return grid
        
        # 如果多次尝试后仍未成功，使用简单的蛇形模式
        return self._generate_snake_pattern()

    def _generate_snake_pattern(self):
        """生成一个简单的蛇形模式作为备选解决方案"""
        n = self.n
        grid = [[0 for _ in range(n)] for _ in range(n)]
        
        num = 1
        for i in range(n):
            if i % 2 == 0:  # 从左到右
                for j in range(n):
                    grid[i][j] = num
                    num += 1
            else:  # 从右到左
                for j in range(n-1, -1, -1):
                    grid[i][j] = num
                    num += 1
        
        return grid

    def generate(self, num_of_questions: int = 100, max_attempts: int = 1000):
        """生成一系列有解的 Numbrix 谜题"""
        game_data_list = []
        grid_combinations = set()  # 用于避免重复谜题
        
        for _ in range(num_of_questions):
            success = False
            # 尝试生成随机谜题直到找到一个有解的
            for attempt_idx in range(max_attempts):
                # 生成一个完整的解决方案（蛇形路径）
                solution_grid = self._generate_solution()
                
                # 验证解决方案是否有效
                flattened = [num for row in solution_grid for num in row]
                if sorted(flattened) != list(range(1, self.n * self.n + 1)):
                    continue  # 解决方案无效，重试
                
                # 基于解决方案创建谜题（部分填充）
                puzzle_grid = self._create_puzzle_from_solution(solution_grid)
                
                # 将谜题转换为可哈希格式以检查重复
                puzzle_tuple = tuple(map(tuple, puzzle_grid))
                if puzzle_tuple in grid_combinations:
                    continue
                
                grid_combinations.add(puzzle_tuple)
                
                # 创建游戏数据
                game_data = Data(
                    question=prompt_numbrix(puzzle_grid),
                    answer="",
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "grid": puzzle_grid,
                        "solution": solution_grid,
                        "n": self.n,
                        "fill_rate": self.fill_rate
                    }
                )
                game_data_list.append(game_data)
                success = True
                break
                
            if not success:
                print(f"警告：在 {max_attempts} 次尝试后未能生成足够的谜题")
                break
                    
        return game_data_list
        
    def _create_puzzle_from_solution(self, solution_grid):
        """从完整解决方案创建部分填充的谜题"""
        puzzle = [row[:] for row in solution_grid]  # 深拷贝
        total_cells = self.n * self.n
        cells_to_remove = int(total_cells * (1 - self.fill_rate))
        
        # 创建所有单元格的列表（排除1和n²，确保它们始终可见）
        all_cells = [(r, c) for r in range(self.n) for c in range(self.n) 
                    if solution_grid[r][c] != 1 and solution_grid[r][c] != self.n * self.n]
        
        # 随机选择要移除的单元格
        cells_to_remove = min(cells_to_remove, len(all_cells))
        remove_cells = random.sample(all_cells, cells_to_remove)
        
        # 移除选定的单元格
        for r, c in remove_cells:
            puzzle[r][c] = "X"
            
        return puzzle
   
    def _solve_numbrix(self, puzzle_grid):
        """解决 Numbrix 谜题（完整解题器）"""
        # 这里应该实现一个完整的解题器
        # 由于解题器比较复杂，这里只提供一个框架
        grid = [row[:] for row in puzzle_grid]
        
        # 找到所有已知数字的位置
        known_positions = {}
        for r in range(self.n):
            for c in range(self.n):
                if grid[r][c] != "X":
                    known_positions[grid[r][c]] = (r, c)
        
        # 使用回溯法解题
        def backtrack():
            # 检查是否所有单元格都已填充
            if all(grid[r][c] != "X" for r in range(self.n) for c in range(self.n)):
                return True
                
            # 找到下一个要填充的单元格
            # 这里可以实现更智能的选择策略
            for r in range(self.n):
                for c in range(self.n):
                    if grid[r][c] == "X":
                        # 尝试可能的数字
                        for num in range(1, self.n * self.n + 1):
                            if self._is_valid_placement(grid, r, c, num):
                                grid[r][c] = num
                                if backtrack():
                                    return True
                                grid[r][c] = "X"  # 回溯
                        return False
            
            return True
        
        backtrack()
        return grid
        
    def _is_valid_placement(self, grid, row, col, num):
        """检查在指定位置放置数字是否有效"""
        # 检查数字是否已经存在
        for r in range(self.n):
            for c in range(self.n):
                if grid[r][c] == num:
                    return False
        
        # 检查相邻性规则
        # 数字 num 应该与 num-1 和 num+1 相邻（如果它们已经放置）
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        
        # 检查 num-1 是否相邻
        if num > 1:
            found_prev = False
            for r in range(self.n):
                for c in range(self.n):
                    if grid[r][c] == num - 1:
                        # 检查是否与当前位置相邻
                        if abs(r - row) + abs(c - col) == 1:
                            found_prev = True
                        else:
                            return False  # num-1 存在但不相邻
            
            # 如果 num-1 已经放置但不相邻，则无效
            if not found_prev and any(grid[r][c] == num - 1 for r in range(self.n) for c in range(self.n)):
                return False
        
        # 检查 num+1 是否相邻（类似逻辑）
        if num < self.n * self.n:
            found_next = False
            for r in range(self.n):
                for c in range(self.n):
                    if grid[r][c] == num + 1:
                        if abs(r - row) + abs(c - col) == 1:
                            found_next = True
                        else:
                            return False
            
            if not found_next and any(grid[r][c] == num + 1 for r in range(self.n) for c in range(self.n)):
                return False
        
        return True
     
    def extract_answer(self, test_solution: str, strict=False):
        """从模型回答中提取网格"""
        try:
            import ast
            import re
            # 尝试找到 Python 列表格式的答案
            # 寻找形如 [[1, 2, 3], [4, 5, 6], [7, 8, 9]] 的模式
            pattern = r'\[\s*\[\s*\d+.*?\]\s*\]'
            matches = re.finditer(pattern, test_solution, re.DOTALL)
            match = None
            
            # 获取最后一个匹配项
            for m in matches:
                match = m
            if not match:
                return None
            
            # 提取匹配的文本并尝试解析为 Python 对象
            grid_text = match.group(0)
            
            # 清理文本，确保它是有效的 Python 列表
            # 移除可能导致解析错误的字符
            grid_text = grid_text.replace("'", "").replace('"', "")
            
            # 解析为 Python 对象
            grid = ast.literal_eval(grid_text)
            
            # 确保是二维列表且所有元素都是整数
            if not isinstance(grid, list) or not all(isinstance(row, list) for row in grid):
                return None
            
            if not all(isinstance(cell, int) for row in grid for cell in row):
                return None
            
            return grid
        except Exception as e:
            print(f"提取答案时出错: {e}")
            return None
    
def generate_puzzles_in_range(n_min, n_max, fill_rate_min, fill_rate_max, total_puzzles, max_attempts):
    """生成指定范围内的网格大小和填充率的谜题，总数为 total_puzzles"""
    all_game_data = []
    
    # 计算每种配置的谜题数量
    n_values = list(range(n_min, n_max + 1))
    
    # 如果填充率是范围，则创建一个列表
    if fill_rate_min == fill_rate_max:
        fill_rates = [fill_rate_min]
    else:
        # 将范围分成10个点，然后四舍五入到小数点后1位
        fill_rates = [round(fill_rate_min + i * (fill_rate_max - fill_rate_min) / 9, 1) for i in range(10)]
    
    # 计算配置总数
    total_configs = len(n_values) * len(fill_rates)
    
    # 计算每种配置应生成的谜题数量
    puzzles_per_config = math.ceil(total_puzzles / total_configs)
    
    print(f"将生成以下配置的谜题 (总数约 {total_puzzles} 个):")
    for n in n_values:
        for fill_rate in fill_rates:
            print(f"  - {n}x{n} 网格, 填充率 = {fill_rate}")
    
    # 为每种配置生成谜题
    puzzles_generated = 0
    for n in n_values:
        for fill_rate in fill_rates:
            # 计算当前配置需要生成的谜题数量
            remaining_puzzles = total_puzzles - puzzles_generated
            if remaining_puzzles <= 0:
                break
                
            # 确保不会生成超过总数的谜题
            current_batch_size = min(puzzles_per_config, remaining_puzzles)
            
            print(f"\n开始生成 {n}x{n} 网格, 填充率 = {fill_rate} 的谜题 ({current_batch_size} 个)...")
            game = Numbrix(n=n, fill_rate=fill_rate)
            game_data_list = game.generate(current_batch_size, max_attempts)
            
            print(f"已生成 {len(game_data_list)} 个 {n}x{n} 网格, 填充率 = {fill_rate} 的谜题")
            all_game_data.extend(game_data_list)
            puzzles_generated += len(game_data_list)
            
            # 检查是否已达到目标总数
            if puzzles_generated >= total_puzzles:
                break
        
        if puzzles_generated >= total_puzzles:
            break
    
    return all_game_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_of_data", type=int, default=40, help="要生成的谜题总数")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个谜题的最大尝试次数")
    parser.add_argument("--n_min", type=int, default=6, help="最小网格大小")
    parser.add_argument("--n_max", type=int, default=9, help="最大网格大小")
    parser.add_argument("--fill_rate_min", type=float, default=0.3, help="最小填充率 (0-1)")
    parser.add_argument("--fill_rate_max", type=float, default=0.3, help="最大填充率 (0-1)")
    parser.add_argument("--output_file", type=str, default=None, help="输出文件路径")
    args = parser.parse_args()
    
    # 验证参数
    if args.n_min > args.n_max:
        print("错误: n_min 必须小于或等于 n_max")
        exit(1)
    
    if args.fill_rate_min > args.fill_rate_max:
        print("错误: fill_rate_min 必须小于或等于 fill_rate_max")
        exit(1)
    
    if args.fill_rate_min < 0 or args.fill_rate_max > 1:
        print("错误: 填充率必须在 0 到 1 之间")
        exit(1)
    
    # 生成谜题
    all_game_data = generate_puzzles_in_range(
        args.n_min, args.n_max, 
        args.fill_rate_min, args.fill_rate_max,
        args.num_of_data, args.max_attempts
    )
    
    # 确定输出文件路径
    if args.output_file:
        output_file = pathlib.Path(args.output_file)
    else:
        # 创建默认输出文件路径
        data_dir = pathlib.Path(__file__).parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建文件名
        if args.n_min == args.n_max:
            n_part = f"n{args.n_min}"
        else:
            n_part = f"n{args.n_min}-{args.n_max}"
            
        if args.fill_rate_min == args.fill_rate_max:
            fill_part = f"fill{args.fill_rate_min}"
        else:
            fill_part = f"fill{args.fill_rate_min}-{args.fill_rate_max}"
            
        output_file = data_dir / f"numbrix_{n_part}_{fill_part}_{len(all_game_data)}.jsonl"
    
    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 将所有谜题写入单个文件
    with open(output_file, "w") as f:
        for game_data in all_game_data:
            f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
    
    print(f"\n总共生成了 {len(all_game_data)} 个 Numbrix 谜题")
    print(f"所有谜题已保存到: {output_file}")
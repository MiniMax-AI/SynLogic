from games.base.game import Game
from base.data import Data
from games.tasks.minesweeper.scripts.minesweeper_verifier import MinesweeperVerifier
from games.tasks.minesweeper.scripts.minesweeper_prompt import prompt_minesweeper
import random
import re
import argparse
import json
import pathlib
import uuid
import numpy as np
from typing import List, Tuple, Set, Dict, Optional
from collections import defaultdict
import math


class Minesweeper(Game):
    """
    Minesweeper puzzle game
    扫雷游戏
    """
    def __init__(self, n: int = 8, mine_den: float = 0.2, reveal_frac: float = 0.4):
        super().__init__("Minesweeper", MinesweeperVerifier)
        print(f"Initializing Minesweeper with grid size {n}×{n}, mine density: {mine_den}, reveal fraction: {reveal_frac}")
        self.n = n  # 网格大小
        self.mine_den = mine_den  # 地雷密度
        self.reveal_frac = reveal_frac  # 初始揭示比例
        
    def generate(self, num_of_questions: int = 100, max_attempts: int = 5000):
        """Generate Minesweeper puzzles that have deterministic mine positions
        生成具有确定性地雷位置的扫雷谜题"""
        game_data_list = []  # 游戏数据列表
        puzzle_hashes = set()  # 拼图哈希集合，用于避免重复
        full_grid_hashes = set()  # 完整网格哈希集合，避免完整网格重复
        
        for _ in range(num_of_questions):
            valid_puzzle_found = False
            for attempt_idx in range(max_attempts):
                # 生成一个包含地雷和数字的随机完整网格
                full_grid = self._generate_full_grid()
                # 检查完整网格是否重复
                full_grid_hash = hash(tuple(map(tuple, full_grid)))
                if full_grid_hash in full_grid_hashes:
                    continue
                full_grid_hashes.add(full_grid_hash)
                
                # 创建一个部分揭示的网格
                revealed_grid, revealed_positions = self._create_revealed_grid(full_grid)
                
                # 创建拼图的哈希值以避免重复
                puzzle_hash = hash(tuple(map(tuple, revealed_grid)))
                if puzzle_hash in puzzle_hashes:
                    continue

                # 找出所有可以从已揭示网格确定的地雷
                current_mines, reasoning_steps = self._find_deterministic_mines(full_grid, revealed_grid, revealed_positions)
                
                # 只接受至少有一个确定性地雷的谜题
                if len(current_mines) > 0:
                    # 验证解决方案是唯一的
                    if self._verify_unique_solution(revealed_grid, current_mines):
                        puzzle_hashes.add(puzzle_hash)
                        
                        game_data = Data(
                            question=prompt_minesweeper(revealed_grid),
                            answer="",
                            metadata={
                                "trace_id": str(uuid.uuid4()),
                                "full_grid": full_grid,
                                "revealed_grid": revealed_grid,
                                "current_mines": list(current_mines),  # 转换为列表以便JSON序列化
                                "reasoning_steps": reasoning_steps,  # 添加推理步骤
                                "n": self.n,
                                "mine_den": self.mine_den,
                                "reveal_frac": self.reveal_frac
                            }
                        )
                        game_data_list.append(game_data)
                        valid_puzzle_found = True
                        break
            
            if not valid_puzzle_found:
                print(f"Failed to generate a valid puzzle after {max_attempts} attempts for puzzle {len(game_data_list) + 1}")
                print(f"在{max_attempts}次尝试后未能为谜题 {len(game_data_list) + 1} 生成有效的拼图")
        
        return game_data_list
    
    def _generate_full_grid(self):
        """Generate a full grid with mines and numbers
        生成一个包含地雷和数字的完整网格"""
        # 根据密度计算地雷数量
        total_cells = self.n * self.n
        num_mines = int(total_cells * self.mine_den)
        
        # 随机放置地雷
        mine_positions = random.sample([(i, j) for i in range(self.n) for j in range(self.n)], num_mines)
        
        # 创建完整网格
        full_grid = [["0" for _ in range(self.n)] for _ in range(self.n)]
        
        # 放置地雷
        for i, j in mine_positions:
            full_grid[i][j] = "M"
        
        # 计算非地雷单元格的数字
        for i in range(self.n):
            for j in range(self.n):
                if full_grid[i][j] != "M":
                    # Count adjacent mines
                    # 计算相邻地雷数量
                    mine_count = 0
                    for di in [-1, 0, 1]:
                        for dj in [-1, 0, 1]:
                            if di == 0 and dj == 0:
                                continue
                            ni, nj = i + di, j + dj
                            if 0 <= ni < self.n and 0 <= nj < self.n and full_grid[ni][nj] == "M":
                                mine_count += 1
                    full_grid[i][j] = str(mine_count)
        
        return full_grid
    
    def _create_revealed_grid(self, full_grid):
        """Create a partially revealed grid
        创建一个部分揭示的网格"""
        # 统计非地雷单元格
        non_mine_cells = []
        for i in range(self.n):
            for j in range(self.n):
                if full_grid[i][j] != "M":
                    non_mine_cells.append((i, j))
        
        # 计算要揭示的单元格数量
        num_to_reveal = int(len(non_mine_cells) * self.reveal_frac)
        num_to_reveal = max(num_to_reveal, 1)  # 至少揭示一个单元格
        
        # 随机选择要揭示的单元格
        revealed_positions = random.sample(non_mine_cells, num_to_reveal)
        
        # 创建揭示的网格
        revealed_grid = [["X" for _ in range(self.n)] for _ in range(self.n)]
        for i, j in revealed_positions:
            revealed_grid[i][j] = full_grid[i][j]
        
        return revealed_grid, revealed_positions
    
    def _get_adjacent_cells(self, i, j):
        """Get all adjacent cells (including diagonals)
        获取所有相邻单元格（包括对角线）"""
        adjacent_cells = []
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < self.n and 0 <= nj < self.n:
                    adjacent_cells.append((ni, nj))
        return adjacent_cells
    
    def _find_deterministic_mines(self, full_grid, revealed_grid, revealed_positions):
        """Find all mines that can be determined from the revealed grid using one-step logic
        使用一步逻辑从已揭示网格中确定所有地雷"""
        deterministic_mines = set()
        reasoning_steps = []  # 记录推理步骤
        
        # 创建每个单元格到约束它的已揭示数字的映射
        cell_to_constraints = defaultdict(list)
        for i, j in revealed_positions:
            if revealed_grid[i][j] not in ["0", "X", "M"]:  # 跳过0、未揭示和地雷
                for ni, nj in self._get_adjacent_cells(i, j):
                    if revealed_grid[ni][nj] == "X":
                        cell_to_constraints[(ni, nj)].append((i, j))
        
        # 继续查找地雷，直到没有新的地雷被发现
        new_mines_found = True
        iteration = 0
        
        while new_mines_found:
            iteration += 1
            new_mines_found = False
            
            # 策略1：对于每个已揭示的数字，如果数字等于未揭示单元格的数量，所有未揭示单元格必须是地雷
            for i, j in revealed_positions:
                if revealed_grid[i][j] not in ["0", "X", "M"]:  # 跳过0、未揭示和地雷
                    adjacent_cells = self._get_adjacent_cells(i, j)
                    
                    # 获取未揭示的相邻单元格
                    adjacent_unrevealed = [(ni, nj) for ni, nj in adjacent_cells 
                                          if revealed_grid[ni][nj] == "X" and (ni, nj) not in deterministic_mines]
                    
                    # 获取这个单元格周围已知的地雷
                    known_mines = [(ni, nj) for ni, nj in adjacent_cells 
                                  if (ni, nj) in deterministic_mines]
                    
                    # 如果未揭示单元格数量加上已知地雷数量等于单元格中的数字，所有未揭示单元格必须是地雷
                    if len(adjacent_unrevealed) + len(known_mines) == int(revealed_grid[i][j]) and adjacent_unrevealed:
                        step_mines = []
                        for mine_pos in adjacent_unrevealed:
                            if mine_pos not in deterministic_mines:
                                deterministic_mines.add(mine_pos)
                                step_mines.append(mine_pos)
                                new_mines_found = True
                        
                        if step_mines:
                            reasoning_steps.append({
                                "iteration": iteration,
                                "source_cell": (i, j),
                                "source_value": revealed_grid[i][j],
                                "found_mines": step_mines,
                                "logic": "All unrevealed cells must be mines because their count plus known mines equals the cell value"
                            })
            
            # 策略2：如果一个数字周围已经确定了恰好等于该数字的地雷数量，
            # 则该数字周围的任何其他未揭示单元格必须是安全的（不用于地雷确定，
            # 但可以在更复杂的实现中用于进一步揭示）
            
            # 如果在此迭代中没有发现新的地雷，我们就完成了
            if not new_mines_found:
                break
        
        # 验证所有确定性地雷在完整网格中实际上是地雷
        for i, j in deterministic_mines:
            assert full_grid[i][j] == "M", f"Cell ({i},{j}) was determined to be a mine but is not in the full grid"
        
        return deterministic_mines, reasoning_steps
    
    def _verify_unique_solution(self, revealed_grid, current_mines):
        """Verify that the solution is unique
        验证解决方案是唯一的"""
        test_grid = [row[:] for row in revealed_grid]
        
        # 在测试网格中将所有确定的地雷标记为"M"
        for i, j in current_mines:
            test_grid[i][j] = "M"
        
        # 获取所有剩余的未揭示单元格
        remaining_unrevealed = []
        for i in range(self.n):
            for j in range(self.n):
                if test_grid[i][j] == "X":
                    remaining_unrevealed.append((i, j))
        
        # 如果没有剩余的未揭示单元格，解决方案就是唯一的
        if not remaining_unrevealed:
            return True
        
        return len(current_mines) > 0
       
    def extract_answer(self, response: str) -> List[Tuple[int, int]]:
        """从模型的响应中提取地雷坐标
        Extract mine coordinates from the model's response"""
        patterns = [
            r'\[\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)(?:\s*,\s*\(\s*\d+\s*,\s*\d+\s*\))*\s*\]',  # [(0,1),(2,3)]
            r'\[\s*\[\s*(\d+)\s*,\s*(\d+)\s*\](?:\s*,\s*\[\s*\d+\s*,\s*\d+\s*\])*\s*\]',  # [[0,1],[2,3]]
            r'\(\s*(\d+)\s*,\s*(\d+)\s*\)(?:\s*,\s*\(\s*\d+\s*,\s*\d+\s*\))*',  # (0,1),(2,3)
        ]
        
        for pattern in patterns:
            coords = []
            for match in re.finditer(pattern, response):
                try:
                    # 提取所有坐标对
                    coord_pattern = r'(?:\(|\[)\s*(\d+)\s*,\s*(\d+)\s*(?:\)|\])'
                    for coord_match in re.finditer(coord_pattern, match.group(0)):
                        i, j = int(coord_match.group(1)), int(coord_match.group(2))
                        coords.append((i, j))
                except Exception:
                    continue
            
            if coords:
                return coords
        
        # 如果没有找到坐标，尝试查找可能是坐标的任何数字
        number_pairs = re.findall(r'(\d+)[^\d]+(\d+)', response)
        if number_pairs:
            return [(int(i), int(j)) for i, j in number_pairs]
        
        return []


def generate_puzzles_in_range(n_min, n_max, mine_den_min, mine_den_max, reveal_frac_min, reveal_frac_max, 
                             total_puzzles, max_attempts):
    """Generate puzzles with grid sizes and parameters within specified ranges
    在指定范围内生成具有不同网格大小和参数的谜题"""
    all_game_data = []
    
    # 计算每种配置的谜题数量
    n_values = list(range(n_min, n_max + 1))
    
    # 如果地雷密度是范围，则创建一个列表
    if mine_den_min == mine_den_max:
        mine_densities = [mine_den_min]
    else:
        # 将范围分成10个点，然后四舍五入到小数点后2位
        mine_densities = [round(mine_den_min + i * (mine_den_max - mine_den_min) / 9, 2) for i in range(10)]
    
    # 如果揭示比例是范围，则创建一个列表
    if reveal_frac_min == reveal_frac_max:
        reveal_fractions = [reveal_frac_min]
    else:
        # 将范围分成10个点，然后四舍五入到小数点后2位
        reveal_fractions = [round(reveal_frac_min + i * (reveal_frac_max - reveal_frac_min) / 9, 2) for i in range(10)]
    
    # 计算配置总数
    total_configs = len(n_values) * len(mine_densities) * len(reveal_fractions)
    
    # 计算每种配置应生成的谜题数量
    puzzles_per_config = math.ceil(total_puzzles / total_configs)
    
    print(f"将生成以下配置的谜题 (总数约 {total_puzzles} 个):")
    for n in n_values:
        for mine_den in mine_densities:
            for reveal_frac in reveal_fractions:
                print(f"  - {n}x{n} 网格, 地雷密度 = {mine_den}, 揭示比例 = {reveal_frac}")
    
    # 为每种配置生成谜题
    puzzles_generated = 0
    for n in n_values:
        for mine_den in mine_densities:
            for reveal_frac in reveal_fractions:
                # 计算当前配置需要生成的谜题数量
                remaining_puzzles = total_puzzles - puzzles_generated
                if remaining_puzzles <= 0:
                    break
                    
                # 确保不会生成超过总数的谜题
                current_batch_size = min(puzzles_per_config, remaining_puzzles)
                
                print(f"\n开始生成 {n}x{n} 网格, 地雷密度 = {mine_den}, 揭示比例 = {reveal_frac} 的谜题 ({current_batch_size} 个)...")
                game = Minesweeper(n=n, mine_den=mine_den, reveal_frac=reveal_frac)
                game_data_list = game.generate(current_batch_size, max_attempts)
                
                print(f"已生成 {len(game_data_list)} 个 {n}x{n} 网格, 地雷密度 = {mine_den}, 揭示比例 = {reveal_frac} 的谜题")
                all_game_data.extend(game_data_list)
                puzzles_generated += len(game_data_list)
                
                # 检查是否已达到目标总数
                if puzzles_generated >= total_puzzles:
                    break
            
            if puzzles_generated >= total_puzzles:
                break
        
        if puzzles_generated >= total_puzzles:
            break
    
    return all_game_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_of_data", type=int, default=10, help="要生成的谜题总数")
    parser.add_argument("--max_attempts", type=int, default=5000, help="每个谜题的最大尝试次数")
    parser.add_argument("--n_min", type=int, default=8, help="最小网格大小")
    parser.add_argument("--n_max", type=int, default=8, help="最大网格大小")
    parser.add_argument("--mine_den_min", type=float, default=0.2, help="最小地雷密度 (0-1)")
    parser.add_argument("--mine_den_max", type=float, default=0.2, help="最大地雷密度 (0-1)")
    parser.add_argument("--reveal_frac_min", type=float, default=0.4, help="最小揭示比例 (0-1)")
    parser.add_argument("--reveal_frac_max", type=float, default=0.4, help="最大揭示比例 (0-1)")
    parser.add_argument("--output_file", type=str, default=None, help="输出文件路径")
    args = parser.parse_args()
    
    # 验证参数
    if args.n_min > args.n_max:
        print("错误: n_min 必须小于或等于 n_max")
        exit(1)
    
    if args.mine_den_min > args.mine_den_max:
        print("错误: mine_den_min 必须小于或等于 mine_den_max")
        exit(1)
    
    if args.reveal_frac_min > args.reveal_frac_max:
        print("错误: reveal_frac_min 必须小于或等于 reveal_frac_max")
        exit(1)
    
    if args.mine_den_min < 0 or args.mine_den_max > 1:
        print("错误: 地雷密度必须在 0 到 1 之间")
        exit(1)
    
    if args.reveal_frac_min < 0 or args.reveal_frac_max > 1:
        print("错误: 揭示比例必须在 0 到 1 之间")
        exit(1)
    
    # 生成谜题
    all_game_data = generate_puzzles_in_range(
        args.n_min, args.n_max, 
        args.mine_den_min, args.mine_den_max,
        args.reveal_frac_min, args.reveal_frac_max,
        args.num_of_data, args.max_attempts
    )
    
    # 确定输出文件路径
    if args.output_file:
        output_file = pathlib.Path(args.output_file)
    else:
        # 创建默认输出文件路径
        data_dir = pathlib.Path(__file__).parent.parent / "data"
        
        # 创建文件名
        if args.n_min == args.n_max:
            n_part = f"n_{args.n_min}"
        else:
            n_part = f"n_{args.n_min}-{args.n_max}"
            
        if args.mine_den_min == args.mine_den_max:
            mine_part = f"mine_den_{args.mine_den_min}"
        else:
            mine_part = f"mine_den_{args.mine_den_min}-{args.mine_den_max}"
            
        if args.reveal_frac_min == args.reveal_frac_max:
            reveal_part = f"reveal_{args.reveal_frac_min}"
        else:
            reveal_part = f"reveal_{args.reveal_frac_min}-{args.reveal_frac_max}"
            
        data_dir = data_dir / n_part / mine_part / reveal_part
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = data_dir / f"minesweeper_{n_part}_{mine_part}_{reveal_part}_{len(all_game_data)}.jsonl"
    
    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 将所有谜题写入单个文件
    with open(output_file, "w") as f:
        for game_data in all_game_data:
            f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
    
    print(f"\n总共生成了 {len(all_game_data)} 个 Minesweeper 谜题")
    print(f"所有谜题已保存到: {output_file}")
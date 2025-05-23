from games.tasks.norinori.scripts.norinori_prompt import prompt_norinori
from games.base.game import Game
from base.data import Data
from games.tasks.norinori.scripts.norinori_verifier import NorinoriVerifier
import random
import string
import uuid
import json
import pathlib
import argparse
import numpy as np
import re
from collections import defaultdict, deque
from tqdm import tqdm

class Norinori(Game):
    """
    Norinori 游戏
    一个基于网格的逻辑谜题，玩家需要在网格中放置多米诺（1×2或2×1的矩形块）
    """
    def __init__(self, n: int = 6, region_nums_range: tuple = (6, 10), shadow_ratio: float = 0.05):
        super().__init__("Norinori", NorinoriVerifier)
        print(f"初始化 Norinori，参数：n={n}, region_nums_range={region_nums_range}, shadow_ratio={shadow_ratio}")
        self.n = n  # 网格大小
        self.region_nums_range = region_nums_range  # 区域数量范围
        self.shadow_ratio = shadow_ratio  # 阴影格子比率
       

    def generate(self, n_samples: int = 100, max_attempts: int = 1000):
        """生成指定数量的 Norinori 谜题"""
        game_data_list = []
        generated_grids = set()  # 用于避免重复生成相同的谜题
        
        # 使用tqdm创建进度条
        pbar = tqdm(total=n_samples, desc="生成 Norinori 谜题")
        
        for _ in range(n_samples):
            for attempt_idx in range(max_attempts):
                # 为当前谜题随机选择区域数量
                region_nums = random.randint(self.region_nums_range[0], self.region_nums_range[1])
                
                # 生成区域网格
                region_grid, region_map = self._generate_regions(region_nums)
                
                # 添加阴影格子
                region_grid = self._add_shadows(region_grid)
                
                # 将网格转换为字符串用于检查重复
                grid_str = ''.join([''.join(row) for row in region_grid])
                if grid_str in generated_grids:
                    continue
                
                # 尝试求解谜题
                solution = self._solve(region_grid, region_map)
                if not solution:
                    continue  # 如果无解，重新生成
                
                # 记录生成的网格
                generated_grids.add(grid_str)
                    
                # 创建游戏数据
                game_data = Data(
                        question=prompt_norinori(region_grid),
                        answer="",  # 答案由验证器检查
                        metadata={
                            "trace_id": str(uuid.uuid4()),
                            "region_grid": region_grid,
                            "solution": solution,
                            "n": self.n,
                            "region_nums": region_nums,
                            "shadow_ratio": self.shadow_ratio
                        }
                    )
                game_data_list.append(game_data)
                
                # 更新进度条
                pbar.update(1)
                break
                
            if attempt_idx == max_attempts - 1:
                print(f"警告：在 {max_attempts} 次尝试后未能生成有效谜题")
        
        # 关闭进度条
        pbar.close()
        
        return game_data_list

    def _generate_regions(self, region_nums):
        """生成区域网格，确保每个区域至少有2个格子"""
        # 初始化网格，所有格子都未分配
        grid = [[None for _ in range(self.n)] for _ in range(self.n)]
        region_map = {}  # 记录每个区域包含的格子
        
        # 可用的区域标识符
        region_labels = list(string.ascii_uppercase[:region_nums])
        
        # 为每个区域分配格子
        for label in region_labels:
            # 确保每个区域至少有2个格子
            region_size = random.randint(2, 4)  # 区域大小在2-4之间
            region_map[label] = []
            
            # 随机选择一个起始点
            while True:
                if all(all(cell is not None for cell in row) for row in grid):
                    # 如果网格已满但区域未分配完，重新开始
                    return self._generate_regions(region_nums)
                
                start_i = random.randint(0, self.n - 1)
                start_j = random.randint(0, self.n - 1)
                if grid[start_i][start_j] is None:
                    break
            
            # 从起始点开始生长区域
            grid[start_i][start_j] = label
            region_map[label].append((start_i, start_j))
            
            # 使用BFS扩展区域
            queue = deque([(start_i, start_j)])
            while queue and len(region_map[label]) < region_size:
                i, j = queue.popleft()
                
                # 尝试向四个方向扩展
                directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                random.shuffle(directions)
                
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if (0 <= ni < self.n and 0 <= nj < self.n and 
                        grid[ni][nj] is None):
                        grid[ni][nj] = label
                        region_map[label].append((ni, nj))
                        queue.append((ni, nj))
                        if len(region_map[label]) >= region_size:
                            break
        
        # 填充剩余的空格
        for i in range(self.n):
            for j in range(self.n):
                if grid[i][j] is None:
                    # 找到相邻的区域
                    neighbors = []
                    for di, dj in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        ni, nj = i + di, j + dj
                        if (0 <= ni < self.n and 0 <= nj < self.n and 
                            grid[ni][nj] is not None):
                            neighbors.append(grid[ni][nj])
                    
                    if neighbors:
                        # 随机选择一个相邻区域
                        label = random.choice(neighbors)
                        grid[i][j] = label
                        region_map[label].append((i, j))
                    else:
                        # 如果没有相邻区域，随机选择一个区域
                        label = random.choice(region_labels)
                        grid[i][j] = label
                        region_map[label].append((i, j))
        
        return grid, region_map
    
    def _add_shadows(self, grid):
        """在网格中添加阴影格子（X），确保每个区域至少保留2个格子"""
        # 计算阴影格子数量
        shadow_count = int(self.n * self.n * self.shadow_ratio)
        
        # 统计每个区域的格子数量
        region_counts = defaultdict(int)
        for i in range(self.n):
            for j in range(self.n):
                if grid[i][j] != "X":
                    region_counts[grid[i][j]] += 1
        
        # 随机选择格子添加阴影
        for _ in range(shadow_count):
            attempts = 0
            while attempts < 100:  # 限制尝试次数，避免无限循环
                i = random.randint(0, self.n - 1)
                j = random.randint(0, self.n - 1)
                region = grid[i][j]
                
                # 确保不重复添加阴影，且不会使任何区域的格子数少于2
                if region != "X" and region_counts[region] > 2:
                    grid[i][j] = "X"
                    region_counts[region] -= 1
                    break
                
                attempts += 1
            
            # 如果尝试多次仍无法添加阴影，则停止添加
            if attempts >= 100:
                break
        
        return grid
        
    def _solve(self, grid, region_map):
        """
        尝试解决 Norinori 谜题
        使用回溯算法放置多米诺，确保每个区域恰好有2个格子被覆盖
        """
        # 创建一个副本用于求解
        board = [row[:] for row in grid]
        n = len(board)
        
        # 记录已放置的多米诺
        dominoes = []
        
        # 记录每个格子是否已被覆盖
        covered = [[False for _ in range(n)] for _ in range(n)]
        
        # 获取所有阴影格子的位置
        shadow_cells = []
        for i in range(n):
            for j in range(n):
                if board[i][j] == "X":
                    shadow_cells.append((i, j))
        
        # 计算每个区域需要覆盖的格子数
        region_to_cover = {}
        for region in region_map:
            if region != "X":  # 跳过阴影区域
                region_to_cover[region] = 2  # 每个区域需要覆盖2个格子

        def is_valid_placement(i1, j1, i2, j2):
            """检查在 (i1,j1) 和 (i2,j2) 放置多米诺是否有效"""
            # 检查坐标是否在网格内
            if not (0 <= i1 < n and 0 <= j1 < n and 0 <= i2 < n and 0 <= j2 < n):
                return False
            
            # 检查格子是否已被覆盖
            if covered[i1][j1] or covered[i2][j2]:
                return False
            
            # 检查是否与已放置的多米诺相邻（共享边）
            for i, j in [(i1, j1), (i2, j2)]:
                for di, dj in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    ni, nj = i + di, j + dj
                    if (0 <= ni < n and 0 <= nj < n and 
                        covered[ni][nj] and (ni, nj) != (i1, j1) and (ni, nj) != (i2, j2)):
                        return False
            
            # 检查区域覆盖限制
            for i, j in [(i1, j1), (i2, j2)]:
                if 0 <= i < n and 0 <= j < n and board[i][j] != "X":
                    region = board[i][j]
                    if region_to_cover.get(region, 0) <= 0:
                        return False  # 该区域已经覆盖了2个格子
            
            return True
        
        def update_coverage(i1, j1, i2, j2, add=True):
            """更新覆盖状态"""
            for i, j in [(i1, j1), (i2, j2)]:
                if 0 <= i < n and 0 <= j < n:
                    covered[i][j] = add
                    if board[i][j] != "X" and add:
                        region_to_cover[board[i][j]] -= 1
                    elif board[i][j] != "X" and not add:
                        region_to_cover[board[i][j]] += 1
        
        def all_conditions_met():
            """检查是否满足所有条件"""
            # 检查所有阴影格子是否被覆盖
            if not all(covered[i][j] for i, j in shadow_cells):
                return False
            
            # 检查每个区域是否恰好有2个格子被覆盖
            for region, remaining in region_to_cover.items():
                if remaining != 0:
                    return False
                    
            return True
        
        def backtrack():
            """回溯算法放置多米诺"""
            # 如果满足所有条件，找到解
            if all_conditions_met():
                # 转换为1-indexed坐标
                return [[(i+1, j+1), (i2+1, j2+1)] for (i, j), (i2, j2) in dominoes]
            
            # 优先处理阴影格子
            for i, j in shadow_cells:
                if not covered[i][j]:
                    # 尝试水平放置
                    if j + 1 < n and not covered[i][j+1] and is_valid_placement(i, j, i, j+1):
                        update_coverage(i, j, i, j+1, True)
                        dominoes.append(((i, j), (i, j+1)))
                        result = backtrack()
                        if result:
                            return result
                        dominoes.pop()
                        update_coverage(i, j, i, j+1, False)
                    
                    # 尝试垂直放置
                    if i + 1 < n and not covered[i+1][j] and is_valid_placement(i, j, i+1, j):
                        update_coverage(i, j, i+1, j, True)
                        dominoes.append(((i, j), (i+1, j)))
                        result = backtrack()
                        if result:
                            return result
                        dominoes.pop()
                        update_coverage(i, j, i+1, j, False)
                    
                    # 尝试水平放置（反向）
                    if j - 1 >= 0 and not covered[i][j-1] and is_valid_placement(i, j-1, i, j):
                        update_coverage(i, j-1, i, j, True)
                        dominoes.append(((i, j-1), (i, j)))
                        result = backtrack()
                        if result:
                            return result
                        dominoes.pop()
                        update_coverage(i, j-1, i, j, False)
                    
                    # 尝试垂直放置（反向）
                    if i - 1 >= 0 and not covered[i-1][j] and is_valid_placement(i-1, j, i, j):
                        update_coverage(i-1, j, i, j, True)
                        dominoes.append(((i-1, j), (i, j)))
                        result = backtrack()
                        if result:
                            return result
                        dominoes.pop()
                        update_coverage(i-1, j, i, j, False)
                    
                    # 如果无法覆盖阴影格子，返回None
                    return None
            
            # 处理需要覆盖的区域
            for region, remaining in list(region_to_cover.items()):
                if remaining > 0:
                    # 找出该区域的所有未覆盖格子
                    cells = [(i, j) for i, j in region_map[region] if not covered[i][j]]
                    
                    # 尝试覆盖这些格子
                    for idx, (i, j) in enumerate(cells):
                        # 尝试水平放置
                        if j + 1 < n and (i, j+1) in cells and is_valid_placement(i, j, i, j+1):
                            update_coverage(i, j, i, j+1, True)
                            dominoes.append(((i, j), (i, j+1)))
                            result = backtrack()
                            if result:
                                return result
                            dominoes.pop()
                            update_coverage(i, j, i, j+1, False)
                        
                        # 尝试垂直放置
                        if i + 1 < n and (i+1, j) in cells and is_valid_placement(i, j, i+1, j):
                            update_coverage(i, j, i+1, j, True)
                            dominoes.append(((i, j), (i+1, j)))
                            result = backtrack()
                            if result:
                                return result
                            dominoes.pop()
                            update_coverage(i, j, i+1, j, False)
                    
                    # 如果该区域无法满足覆盖要求，返回None
                    if remaining == 2:  # 如果区域需要覆盖2个格子但无法放置
                        return None
            
            # 如果所有条件都满足，返回结果
            if all_conditions_met():
                return [[(i+1, j+1), (i2+1, j2+1)] for (i, j), (i2, j2) in dominoes]
            
            # 尝试放置额外的多米诺来满足条件
            for i in range(n):
                for j in range(n):
                    if not covered[i][j]:
                        # 尝试水平放置
                        if j + 1 < n and not covered[i][j+1] and is_valid_placement(i, j, i, j+1):
                            update_coverage(i, j, i, j+1, True)
                            dominoes.append(((i, j), (i, j+1)))
                            result = backtrack()
                            if result:
                                return result
                            dominoes.pop()
                            update_coverage(i, j, i, j+1, False)
                        
                        # 尝试垂直放置
                        if i + 1 < n and not covered[i+1][j] and is_valid_placement(i, j, i+1, j):
                            update_coverage(i, j, i+1, j, True)
                            dominoes.append(((i, j), (i+1, j)))
                            result = backtrack()
                            if result:
                                return result
                            dominoes.pop()
                            update_coverage(i, j, i+1, j, False)
            
            return None
        
        # 开始回溯
        return backtrack()

    def extract_answer(self, test_solution: str, strict=False):
        """
        从回答中提取答案
        
        参数:
        test_solution -- 用户的回答
        strict -- 是否严格模式
        
        返回:
        str -- 提取的答案
        """
        # 尝试找到答案部分
        answer_patterns = [
            r'\[\s*\[\s*\(\s*\d+\s*,\s*\d+\s*\)\s*,\s*\(\s*\d+\s*,\s*\d+\s*\)\s*\]',  # 寻找格式如 [[(1,2), (1,3)], ...] 的答案
            r'答案是\s*(.*?)\s*$',  # 中文格式
            r'answer is\s*(.*?)\s*$',  # 英文格式
            r'solution is\s*(.*?)\s*$'  # 另一种英文格式
        ]
        
        for pattern in answer_patterns:
            matches = re.findall(pattern, test_solution, re.IGNORECASE | re.DOTALL)
            if matches:
                # 返回最后一个匹配项，通常是最终答案
                return matches[-1]
        
        # 如果没有找到明确的答案格式，返回整个解答
        return test_solution


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_samples", type=int, default=100, help="生成的谜题数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个谜题的最大尝试次数")
    parser.add_argument("--n", type=int, default=5, help="网格大小")
    parser.add_argument("--min_regions", type=int, default=3, help="最小区域数量")
    parser.add_argument("--max_regions", type=int, default=5, help="最大区域数量")
    parser.add_argument("--shadow_ratio", type=float, default=0.1, help="阴影格子比率")
    args = parser.parse_args()
    
    region_range = (args.min_regions, args.max_regions)
    data_dir = pathlib.Path(__file__).parent.parent / "data" / f"n_{args.n}" / f"regions_{region_range[0]}-{region_range[1]}" / f"shadow_{args.shadow_ratio}"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = data_dir / f"norinori_n{args.n}_regions{region_range[0]}-{region_range[1]}_shadow{args.shadow_ratio}_{args.n_samples}.jsonl"
    
    game = Norinori(n=args.n, region_nums_range=region_range, shadow_ratio=args.shadow_ratio)
    game_data_list = game.generate(args.n_samples, args.max_attempts)
    
    if len(game_data_list) == 0:
        print(f"在 {args.max_attempts} 次尝试后未能生成任何有效谜题")
        exit(1)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        for game_data in game_data_list:
            f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
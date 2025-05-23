from games.base.game import Game
from base.data import Data
from games.tasks.number_wall.scripts.number_wall_verifier import NumberWallVerifier
from games.tasks.number_wall.scripts.number_wall_prompt import prompt_number_wall
import random
import re
import argparse
import json
import pathlib
import uuid
import numpy as np
from collections import deque


class NumberWall(Game):
    """
    Number Wall puzzle game
    数字墙拼图游戏
    """
    def __init__(self, n: int = 5, number_rate: float = 0.2):
        super().__init__("NumberWall", NumberWallVerifier)
        print(f"Initializing Number Wall with grid size {n}×{n}, number rate: {number_rate}, number range: {1}-{n}")
        self.n = n  # 网格大小
        self.number_rate = number_rate  # 数字填充率
        self.min_number = 1  # 最小数字
        self.max_number = n  # 最大数字
        self.failed_attempts_cache = set()  # 缓存失败的尝试
        
    def generate(self, num_of_questions: int = 100, max_attempts: int = 1000):
        """Generate Number Wall puzzles that have at least one solution
        生成至少有一个解的Number Wall拼图"""
        game_data_list = []  # 游戏数据列表
        puzzle_hashes = set()  # 拼图哈希集合，用于避免重复
        
        for _ in range(num_of_questions):
            for attempt_idx in range(max_attempts):
                # 生成一个随机拼图
                grid, solution = self._generate_simple_puzzle()
                
                if grid is None or solution is None:
                    continue
                
                # 创建拼图的哈希值以避免重复
                puzzle_hash = hash(str(grid))
                if puzzle_hash in puzzle_hashes or puzzle_hash in self.failed_attempts_cache:
                    continue
                
                # 验证拼图是可解的
                if self._is_valid_puzzle(grid, solution):
                    puzzle_hashes.add(puzzle_hash)
                    game_data = Data(
                        question=prompt_number_wall(grid),
                        answer="",
                        metadata={
                            "trace_id": str(uuid.uuid4()),
                            "grid": grid,
                            "solution": solution,
                            "n": self.n,
                            "number_rate": self.number_rate
                        }
                    )
                    game_data_list.append(game_data)
                    break
                else:
                    # 记录失败的尝试
                    self.failed_attempts_cache.add(puzzle_hash)
                    
            if len(game_data_list) % 10 == 0 and len(game_data_list) > 0:
                print(f"Generated {len(game_data_list)} puzzles so far (Failed attempts cache size: {len(self.failed_attempts_cache)})")
        
        return game_data_list
    
    def _generate_simple_puzzle(self):
        """Generate a simple Number Wall puzzle using a more reliable approach
        使用更可靠的方法生成简单的Number Wall拼图"""
        # 创建一个空网格
        grid = [["X" for _ in range(self.n)] for _ in range(self.n)]
        
        # 确定要放置的数字数量 (较少的数字，更容易生成)
        num_numbers = max(1, int(self.n * self.n * self.number_rate * 0.8))
        
        # 创建一个解决方案网格，初始全部为墙壁
        solution = [["A" for _ in range(self.n)] for _ in range(self.n)]
        
        # 随机选择位置放置数字和岛屿
        placed_numbers = []
        
        # 创建一个网格中所有位置的列表
        all_positions = [(i, j) for i in range(self.n) for j in range(self.n)]
        random.shuffle(all_positions)
        
        # 尝试放置数字
        for row, col in all_positions:
            if len(placed_numbers) >= num_numbers:
                break
                
            # 检查与已放置数字的距离
            too_close = False
            for p_row, p_col, _ in placed_numbers:
                if abs(row - p_row) + abs(col - p_col) < 2:  # 确保数字之间至少有1格距离
                    too_close = True
                    break
            
            if too_close:
                continue
            
            number = random.randint(self.min_number, self.max_number)
            
            # 创建一个简单的岛屿
            island_cells = self._create_simple_island(solution, row, col, number)
            if island_cells:
                # 成功创建岛屿
                grid[row][col] = number
                solution[row][col] = number
                placed_numbers.append((row, col, number))
                
                # 将岛屿的其他格子标记为"X"
                for r, c in island_cells:
                    if (r, c) != (row, col):  # 跳过数字格子
                        solution[r][c] = "X"
        
        if not placed_numbers:
            return None, None
        
        # 确保墙壁不形成2x2方块
        self._fix_wall_blocks(solution)
        
        # 确保没有斜线边
        self._fix_diagonal_borders(solution)
        
        return grid, solution
    
    def _create_simple_island(self, solution, row, col, number):
        """Create a simple island around the number
        在数字周围创建一个简单的岛屿"""
        # 岛屿格子集合
        island_cells = set([(row, col)])
        
        # 如果数字是1，只需要数字格子本身
        if number == 1:
            return island_cells
        
        # 创建一个简单的十字形或L形岛屿
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        
        cells_needed = number - 1  # 已经有了数字格子
        
        # 尝试沿着随机方向扩展岛屿
        for dr, dc in directions:
            if cells_needed <= 0:
                break
                
            # 尝试在这个方向上添加格子
            r, c = row, col
            for _ in range(min(cells_needed, 2)):  # 最多在一个方向上添加2个格子
                r += dr
                c += dc
                
                # 检查是否在网格内
                if 0 <= r < self.n and 0 <= c < self.n:
                    island_cells.add((r, c))
                    cells_needed -= 1
                else:
                    break
        
        # 如果还需要更多格子，尝试其他方向
        if cells_needed > 0:
            # 再次尝试所有方向
            for dr, dc in directions:
                if cells_needed <= 0:
                    break
                    
                # 从数字格子开始
                r, c = row, col
                r += dr
                c += dc
                
                # 检查是否在网格内且不在岛屿中
                if 0 <= r < self.n and 0 <= c < self.n and (r, c) not in island_cells:
                    island_cells.add((r, c))
                    cells_needed -= 1
        
        # 如果无法创建足够大的岛屿，返回None
        if cells_needed > 0:
            return None
        
        return island_cells
    
    def _fix_wall_blocks(self, solution):
        """Fix 2x2 wall blocks by converting one wall to an empty cell
        通过将一个墙壁转换为空格来修复2x2墙壁块"""
        for i in range(self.n - 1):
            for j in range(self.n - 1):
                if (solution[i][j] == "A" and solution[i][j+1] == "A" and
                    solution[i+1][j] == "A" and solution[i+1][j+1] == "A"):
                    # 找到了一个2x2墙壁块，随机选择一个转换为空格
                    r, c = random.choice([(i, j), (i, j+1), (i+1, j), (i+1, j+1)])
                    solution[r][c] = "X"
    
    def _fix_diagonal_borders(self, solution):
        """Fix diagonal borders between islands by adding walls
        通过添加墙壁修复岛屿之间的斜线边"""
        # 标记所有岛屿
        island_map = {}  # 映射格子坐标到岛屿ID
        island_id = 0
        
        for i in range(self.n):
            for j in range(self.n):
                if solution[i][j] != "A" and (i, j) not in island_map:
                    # 发现一个新岛屿
                    queue = deque([(i, j)])
                    while queue:
                        r, c = queue.popleft()
                        island_map[(r, c)] = island_id
                        
                        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < self.n and 0 <= nc < self.n and 
                                solution[nr][nc] != "A" and (nr, nc) not in island_map):
                                queue.append((nr, nc))
                    
                    island_id += 1
        
        # 检查斜线边
        for i in range(self.n - 1):
            for j in range(self.n - 1):
                # 检查2x2方格中的对角格子
                if (solution[i][j] != "A" and solution[i+1][j+1] != "A" and
                    solution[i][j+1] == "A" and solution[i+1][j] == "A"):
                    # 对角格子属于不同岛屿，需要添加墙壁
                    if island_map.get((i, j)) != island_map.get((i+1, j+1)):
                        # 随机选择一个对角格子转换为墙壁
                        if random.choice([True, False]):
                            solution[i][j] = "A"
                        else:
                            solution[i+1][j+1] = "A"
                
                # 检查另一对对角格子
                if (solution[i][j+1] != "A" and solution[i+1][j] != "A" and
                    solution[i][j] == "A" and solution[i+1][j+1] == "A"):
                    # 对角格子属于不同岛屿，需要添加墙壁
                    if island_map.get((i, j+1)) != island_map.get((i+1, j)):
                        # 随机选择一个对角格子转换为墙壁
                        if random.choice([True, False]):
                            solution[i][j+1] = "A"
                        else:
                            solution[i+1][j] = "A"
    
    def _is_valid_puzzle(self, grid, solution):
        """Check if the puzzle is valid
        检查拼图是否有效"""
        if solution is None:
            return False
            
        # 检查原始数字是否保留
        for i in range(self.n):
            for j in range(self.n):
                if isinstance(grid[i][j], int) and grid[i][j] != solution[i][j]:
                    return False
        
        # 检查墙壁布局是否有效
        for i in range(self.n - 1):
            for j in range(self.n - 1):
                if (solution[i][j] == "A" and solution[i][j+1] == "A" and
                    solution[i+1][j] == "A" and solution[i+1][j+1] == "A"):
                    return False
        
        # 检查岛屿是否有效
        visited = set()
        
        for i in range(self.n):
            for j in range(self.n):
                if (i, j) not in visited and solution[i][j] != "A":
                    # 发现一个新岛屿
                    island_cells = []
                    island_number = None
                    queue = deque([(i, j)])
                    visited.add((i, j))
                    
                    while queue:
                        r, c = queue.popleft()
                        island_cells.append((r, c))
                        
                        if isinstance(solution[r][c], int):
                            if island_number is not None:
                                # 岛屿有多个数字
                                return False
                            island_number = solution[r][c]
                        
                        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < self.n and 0 <= nc < self.n and 
                                (nr, nc) not in visited and 
                                solution[nr][nc] != "A"):
                                queue.append((nr, nc))
                                visited.add((nr, nc))
                    
                    if island_number is None:
                        # 岛屿没有数字
                        return False
                    
                    if len(island_cells) != island_number:
                        # 岛屿大小与数字不匹配
                        return False
        
        # 检查是否有斜线边
        if self._has_diagonal_borders(solution):
            return False
        
        return True
    
    def _has_diagonal_borders(self, solution):
        """Check if there are diagonal borders between islands
        检查岛屿之间是否有斜线边"""
        # 标记所有岛屿
        island_map = {}  # 映射格子坐标到岛屿ID
        island_id = 0
        
        for i in range(self.n):
            for j in range(self.n):
                if solution[i][j] != "A" and (i, j) not in island_map:
                    # 发现一个新岛屿
                    queue = deque([(i, j)])
                    while queue:
                        r, c = queue.popleft()
                        island_map[(r, c)] = island_id
                        
                        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < self.n and 0 <= nc < self.n and 
                                solution[nr][nc] != "A" and (nr, nc) not in island_map):
                                queue.append((nr, nc))
                    
                    island_id += 1
        
        # 检查斜线边
        for i in range(self.n - 1):
            for j in range(self.n - 1):
                # 检查2x2方格中的对角格子
                if (solution[i][j] != "A" and solution[i+1][j+1] != "A" and
                    solution[i][j+1] == "A" and solution[i+1][j] == "A"):
                    # 对角格子属于不同岛屿，存在斜线边
                    if island_map.get((i, j)) != island_map.get((i+1, j+1)):
                        return True
                
                # 检查另一对对角格子
                if (solution[i][j+1] != "A" and solution[i+1][j] != "A" and
                    solution[i][j] == "A" and solution[i+1][j+1] == "A"):
                    # 对角格子属于不同岛屿，存在斜线边
                    if island_map.get((i, j+1)) != island_map.get((i+1, j)):
                        return True
        
        return False
        
 
 
    def extract_answer(self, response: str):
        """从模型的响应中提取答案网格"""    
        # 在响应中寻找网格表示
        # 修改正则表达式以匹配字符串形式的数字
        grid_pattern = r'\[\s*\[(?:\s*(?:"[XA]"|\'[XA]\'|[0-9]+|"[0-9]+"|\'[0-9]+\')\s*,\s*)*\s*(?:"[XA]"|\'[XA]\'|[0-9]+|"[0-9]+"|\'[0-9]+\')\s*\]\s*(?:,\s*\[(?:\s*(?:"[XA]"|\'[XA]\'|[0-9]+|"[0-9]+"|\'[0-9]+\')\s*,\s*)*\s*(?:"[XA]"|\'[XA]\'|[0-9]+|"[0-9]+"|\'[0-9]+\')\s*\]\s*)*\]'
        matches = re.findall(grid_pattern, response)
        
        if matches:
            # 尝试解析最后一个匹配项
            grid_str = matches[-1]
            
            try:
                # 尝试清理字符串，替换可能导致问题的字符
                cleaned_grid_str = grid_str.replace('\n', '').replace('\r', '').strip()
                grid = json.loads(cleaned_grid_str)
                
                # 将字符串数字转换为整数
                for i in range(len(grid)):
                    for j in range(len(grid[i])):
                        if isinstance(grid[i][j], str) and grid[i][j].isdigit():
                            grid[i][j] = int(grid[i][j])
                
                return grid
            except json.JSONDecodeError as e:
                # 尝试使用 ast.literal_eval 作为备选方案
                try:
                    import ast
                    grid = ast.literal_eval(cleaned_grid_str)
                    
                    # 将字符串数字转换为整数
                    for i in range(len(grid)):
                        for j in range(len(grid[i])):
                            if isinstance(grid[i][j], str) and grid[i][j].isdigit():
                                grid[i][j] = int(grid[i][j])
                    
                    return grid
                except Exception as e2:
                    print(f"ast.literal_eval also failed: {e2}")
        else:
            print("No grid pattern found in the response")
        
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_of_data", type=int, default=100)  # 数据数量
    parser.add_argument("--max_attempts", type=int, default=1000)  # 最大尝试次数
    parser.add_argument("--n_min", type=int, default=3)  # 最小网格大小
    parser.add_argument("--n_max", type=int, default=6)  # 最大网格大小
    parser.add_argument("--number_rate_min", type=float, default=0.15)  # 最小数字填充率
    parser.add_argument("--number_rate_max", type=float, default=0.3)  # 最大数字填充率
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data" / f"n_{args.n_min}_to_{args.n_max}" / f"rate_{args.number_rate_min}_to_{args.number_rate_max}"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = data_dir / f"number_wall_varied_{args.num_of_data}.jsonl"  # 输出文件
    
    game_data_list = []
    puzzles_generated = 0
    
    while puzzles_generated < args.num_of_data:
        # 随机选择网格大小和填充率
        n = random.randint(args.n_min, args.n_max)
        number_rate = round(random.uniform(args.number_rate_min, args.number_rate_max), 2)
        
        print(f"Attempting to generate puzzle with n={n}, number_rate={number_rate}")
        
        # 创建游戏实例
        game = NumberWall(n=n, number_rate=number_rate)
        
        # 尝试生成一个拼图
        puzzle_data = game.generate(1, args.max_attempts)
        
        if puzzle_data:
            # 添加到数据列表
            game_data_list.extend(puzzle_data)
            puzzles_generated += len(puzzle_data)
            print(f"Generated {puzzles_generated}/{args.num_of_data} puzzles")
    
    if len(game_data_list) == 0:
        print(f"Failed to generate any Number Wall puzzles")
        exit(1)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        for game_data in game_data_list:
            f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
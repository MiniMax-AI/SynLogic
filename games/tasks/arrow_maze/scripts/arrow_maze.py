import random
import json
import uuid
import argparse
import pathlib
import copy
from typing import List, Tuple, Dict, Any, Optional

from games.base.game import Game
from base.data import Data
from games.tasks.arrow_maze.scripts.arrow_maze_verifier import ArrowMazeVerifier
from games.tasks.arrow_maze.scripts.arrow_maze_prompt import prompt_arrow_maze

class ArrowMaze(Game):
    """
    箭头迷宫游戏类
    
    迷宫由n×m的网格组成，其中X代表空白格子，数字代表射线箭头串的起点。
    玩家需要在空白格子中填入箭头，箭头可以向上（↑）、下（↓）、左（←）、右（→）
    或对角线方向（↖、↗、↘、↙）延伸。
    数字代表射线箭头串的起点，且从该数字出发的所有射线箭头串中箭头总数等于该数字。
    """
    
    # 定义箭头符号和其对应的方向
    ARROWS = {
        "↑": (-1, 0),   # 上
        "↓": (1, 0),    # 下
        "←": (0, -1),   # 左
        "→": (0, 1),    # 右
        "↖": (-1, -1),  # 左上
        "↗": (-1, 1),   # 右上
        "↘": (1, 1),    # 右下
        "↙": (1, -1)    # 左下
    }
    
    def __init__(self):
        """
        初始化箭头迷宫游戏
        """
        super().__init__("Arrow Maze", ArrowMazeVerifier)
    
    def generate(self, num_of_questions: int = 100, max_attempts: int = 10000,
                width: int = 8, height: int = 8, 
                arrow_fill_rate_min: float = 0.0, arrow_fill_rate_max: float = 0.0):
        """
        生成箭头迷宫游戏问题
        
        @param num_of_questions: 要生成的问题数量
        @param max_attempts: 每个问题的最大尝试次数
        @param width: 迷宫宽度
        @param height: 迷宫高度
        @param arrow_fill_rate_min: 预填箭头比例最小值（0.0-1.0之间）
        @param arrow_fill_rate_max: 预填箭头比例最大值（0.0-1.0之间）
        @return: 生成的问题列表
        """
        game_data_list = []
        attempts = 0
        
        while len(game_data_list) < num_of_questions and attempts < max_attempts:
            attempts += 1
            
            try:
                # 使用指定的宽度和高度
                n = height
                m = width
                
                # 在指定范围内随机选择填充率
                arrow_fill_rate = random.uniform(arrow_fill_rate_min, arrow_fill_rate_max)
                # 将填充率四舍五入到一位小数，使其更整齐
                arrow_fill_rate = round(arrow_fill_rate, 1)
                # 决定数字数量，控制范围避免过密，使用m+n作为最大值
                max_numbers = m + n
                num_numbers = random.randint(4, min(max_numbers, n * m // 5))
                
                # 生成迷宫，最小数字量为4
                maze, solution = self._generate_maze(n, m, num_numbers, min_numbers=4)
                
                # 按照指定比例预填充箭头，以控制难度
                if arrow_fill_rate > 0:
                    # 找出所有可填充的位置（在maze中是X，在solution中是箭头的格子）
                    fillable_positions = []
                    for i in range(n):
                        for j in range(m):
                            if maze[i][j] == "X" and solution[i][j] in self.ARROWS:
                                fillable_positions.append((i, j))
                    
                    # 随机选择指定比例的位置进行填充
                    fill_count = int(len(fillable_positions) * arrow_fill_rate)
                    if fill_count > 0:
                        random.shuffle(fillable_positions)
                        for i, j in fillable_positions[:fill_count]:
                            maze[i][j] = solution[i][j]  # 用solution中的箭头填充maze
                
                # 检查生成的迷宫是否有效
                if not self._is_valid_maze(maze, solution):
                    continue
                
                # 生成游戏描述
                question = prompt_arrow_maze(maze, n, m, random.choice([True, False]))
                
                # 将solution转换为字符串格式作为答案
                answer = json.dumps(solution)
                
                # 创建游戏数据
                maze_data = Data(
                    question=question,
                    answer=answer,
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "maze": maze,
                        "solution": solution,
                        "height": n,
                        "width": m,
                        "arrow_fill_rate": arrow_fill_rate
                    }
                )
                
                game_data_list.append(maze_data)
                print(f"成功生成第 {len(game_data_list)}/{num_of_questions} 条游戏数据")
                
            except Exception as e:
                print(f"生成迷宫时出错: {e}")
                continue
        
        if len(game_data_list) < num_of_questions:
            print(f"警告: 只能生成 {len(game_data_list)}/{num_of_questions} 条游戏数据")
        
        return game_data_list
    
    def _generate_maze(self, n: int, m: int, num_numbers: int, min_numbers: int = 4) -> Tuple[List[List[str]], List[List[str]]]:
        """
        生成迷宫和对应的解决方案
        使用均衡分布数字和递进式构造策略，适度减少数字数量和值为1的数字
        
        @param n: 迷宫行数
        @param m: 迷宫列数
        @param num_numbers: 数字数量上限
        @param min_numbers: 最小数字数量
        @return: (迷宫, 解决方案)
        """
        # 初始化空迷宫
        maze = [["X" for _ in range(m)] for _ in range(n)]
        solution = [["X" for _ in range(m)] for _ in range(n)]
        
        # 适度减少实际使用的数字数量，避免数字太少导致无法生成有效迷宫
        actual_num_numbers = max(min_numbers, int(num_numbers * random.uniform(0.7, 0.9)))
        
        # 将迷宫划分为9个区域，确保中心区域也有数字
        num_regions = 9
        
        # 创建更细致的区域划分，包括中心区域
        region_rows_1 = n // 3
        region_rows_2 = 2 * n // 3
        region_cols_1 = m // 3
        region_cols_2 = 2 * m // 3
        
        # 定义9个区域
        regions = [
            (0, 0, region_rows_1, region_cols_1),             # 左上
            (0, region_cols_1, region_rows_1, region_cols_2), # 上中
            (0, region_cols_2, region_rows_1, m),             # 右上
            (region_rows_1, 0, region_rows_2, region_cols_1), # 左中
            (region_rows_1, region_cols_1, region_rows_2, region_cols_2), # 中心
            (region_rows_1, region_cols_2, region_rows_2, m), # 右中
            (region_rows_2, 0, n, region_cols_1),             # 左下
            (region_rows_2, region_cols_1, n, region_cols_2), # 下中
            (region_rows_2, region_cols_2, n, m)              # 右下
        ]
        
        # 为每个区域分配数字数量，给中心区域分配更多数字
        base_numbers = actual_num_numbers // num_regions
        extra_numbers = actual_num_numbers % num_regions
        
        numbers_per_region = [base_numbers] * num_regions
        
        # 给中心区域额外的数字
        center_region_idx = 4  # 中心区域的索引
        numbers_per_region[center_region_idx] += min(2, extra_numbers)
        
        # 分配剩余的额外数字
        remaining_extra = max(0, extra_numbers - 2)
        for i in range(num_regions):
            if i != center_region_idx and remaining_extra > 0:
                numbers_per_region[i] += 1
                remaining_extra -= 1
            
        number_positions = []
        
        # 在每个区域内放置指定数量的数字，适当调整数字间距
        for region_idx, (start_i, start_j, end_i, end_j) in enumerate(regions):
            # 计算区域面积
            region_area = (end_i - start_i) * (end_j - start_j)
            if region_area == 0:
                continue  # 跳过面积为0的区域
                
            region_positions = [(i, j) for i in range(start_i, end_i) for j in range(start_j, end_j)]
            random.shuffle(region_positions)
            
            # 调整区域内最小距离，使中心区域可以放置更多数字
            if region_idx == center_region_idx:
                min_distance = max(1, min(n, m) // 6)  # 中心区域使用更小的距离限制
            else:
                min_distance = max(2, min(n, m) // 5)  # 其他区域使用正常距离限制
            
            # 放置该区域的数字
            placed_in_region = 0
            for pos in region_positions:
                if placed_in_region >= numbers_per_region[region_idx]:
                    break
                    
                i, j = pos
                
                # 检查是否与已有数字距离太近
                too_close = False
                for ni, nj in number_positions:
                    if abs(ni - i) + abs(nj - j) < min_distance:
                        too_close = True
                        break
                
                if not too_close:
                    maze[i][j] = "1"  # 先用1作为占位数字
                    solution[i][j] = "1"
                    number_positions.append((i, j))
                    placed_in_region += 1
            
            # 如果区域内放置的数字不足，降低距离限制再次尝试
            if placed_in_region < numbers_per_region[region_idx] // 2:
                min_distance = max(1, min_distance // 2)
                for pos in region_positions:
                    if placed_in_region >= numbers_per_region[region_idx]:
                        break
                        
                    i, j = pos
                    if (i, j) in number_positions:
                        continue
                        
                    # 检查是否与已有数字距离太近（使用更小的距离限制）
                    too_close = False
                    for ni, nj in number_positions:
                        if abs(ni - i) + abs(nj - j) < min_distance:
                            too_close = True
                            break
                    
                    if not too_close:
                        maze[i][j] = "1"
                        solution[i][j] = "1"
                        number_positions.append((i, j))
                        placed_in_region += 1
        
        # 确保至少有最小数量的数字
        if len(number_positions) < min(min_numbers, min(n, m) // 2):
            # 如果数字太少，就随机添加一些，优先添加到中心区域
            center_positions = []
            for i in range(n//3, 2*n//3):
                for j in range(m//3, 2*m//3):
                    if (i, j) not in number_positions and solution[i][j] == "X":
                        center_positions.append((i, j))
            
            random.shuffle(center_positions)
            
            # 先尝试在中心区域添加
            for i, j in center_positions:
                if len(number_positions) >= min(min_numbers, min(n, m) // 2):
                    break
                maze[i][j] = "1"
                solution[i][j] = "1"
                number_positions.append((i, j))
            
            # 如果中心区域添加后仍不够，再尝试其他位置
            if len(number_positions) < min(min_numbers, min(n, m) // 2):
                available_positions = [(i, j) for i in range(n) for j in range(m) 
                                      if (i, j) not in number_positions and solution[i][j] == "X"]
                random.shuffle(available_positions)
                
                while len(number_positions) < min(min_numbers, min(n, m) // 2) and available_positions:
                    i, j = available_positions.pop(0)
                    maze[i][j] = "1"
                    solution[i][j] = "1"
                    number_positions.append((i, j))
        
        # 记录已被覆盖的位置
        covered = set()
        for i, j in number_positions:
            covered.add((i, j))
        
        # 修改处理数字的顺序，使用平衡策略而非边缘优先
        # 计算距离中心的距离和距离边缘的距离的平均值，使得数字分布更加均衡
        center_i, center_j = n/2, m/2
        
        balanced_priority = lambda pos: (
            -0.5 * min(pos[0], pos[1], n-1-pos[0], m-1-pos[1]) -  # 边缘因素（较小权重）
            0.5 * (abs(pos[0] - center_i) + abs(pos[1] - center_j))  # 中心因素（较小权重）
        )
        
        random.shuffle(number_positions)  # 先随机打乱
        number_positions.sort(key=balanced_priority)  # 然后按平衡优先级排序
        
        for priority_idx, (i, j) in enumerate(number_positions):
            # 随机选择方向创建射线，数量根据优先级递增
            directions = list(self.ARROWS.items())
            random.shuffle(directions)
            
            # 对于中心区域的数字，可能需要限制某些方向的长度
            in_center = (n//3 <= i < 2*n//3) and (m//3 <= j < 2*m//3)
            
            # 平衡每个数字覆盖的射线数量
            min_rays = min(1, len(directions))  # 至少要有1个方向
            max_rays = min(len(directions), 2 + (priority_idx * 2) // max(1, len(number_positions)))
            selected_directions = directions[:random.randint(min_rays, max_rays)]
            
            total_arrows = 0
            ray_positions = []  # 存储该数字覆盖的所有箭头位置
            
            for arrow_symbol, (di, dj) in selected_directions:
                ni, nj = i + di, j + dj
                ray_length = 0
                
                # 为中心区域的数字控制射线长度
                min_length = 1  # 每个射线至少延伸1格
                
                # 沿该方向延伸射线
                while 0 <= ni < n and 0 <= nj < m:
                    # 如果遇到已有数字或已被覆盖的位置，停止延伸
                    if (ni, nj) in covered or solution[ni][nj].isdigit():
                        break
                        
                    solution[ni][nj] = arrow_symbol
                    covered.add((ni, nj))
                    ray_positions.append((ni, nj))
                    ray_length += 1
                    total_arrows += 1
                    
                    # 控制射线长度
                    max_length = 2 + (priority_idx * 2) // max(1, len(number_positions))
                    if in_center:
                        # 中心区域的数字射线稍短，避免压制边缘数字
                        max_length = min(max_length, 3)
                    
                    # 确保至少延伸到最小长度
                    if ray_length >= min_length and (ray_length >= max_length or random.random() < 0.4):
                        break
                        
                    ni += di
                    nj += dj
            
            # 更新数字为实际覆盖的箭头数量
            if total_arrows > 0:
                maze[i][j] = str(total_arrows)
                solution[i][j] = str(total_arrows)
            else:
                # 如果没有箭头被覆盖，尝试至少添加一个箭头
                for arrow_symbol, (di, dj) in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < n and 0 <= nj < m and solution[ni][nj] == "X":
                        solution[ni][nj] = arrow_symbol
                        covered.add((ni, nj))
                        maze[i][j] = "1"
                        solution[i][j] = "1"
                        break
                
                # 如果仍然无法添加箭头，移除该数字
                if maze[i][j] == "1" and self._count_arrow_rays(solution, i, j) == 0:
                    maze[i][j] = "X"
                    solution[i][j] = "X"
                    number_positions[priority_idx] = None  # 标记为已移除
        
        # 移除无效的数字位置
        number_positions = [pos for pos in number_positions if pos is not None]
        
        # 处理剩余的空格，确保所有格子都有内容
        remaining_positions = []
        for i in range(n):
            for j in range(m):
                if solution[i][j] == "X":
                    remaining_positions.append((i, j))
        
        # 递进式填充剩余空格，优先添加箭头而非数字
        while remaining_positions:
            if not remaining_positions:
                break
                
            # 优先处理被数字周围的空格，增加迷宫的连贯性
            remaining_positions.sort(key=lambda pos: min(
                abs(pos[0]-num_pos[0]) + abs(pos[1]-num_pos[1]) 
                for num_pos in number_positions
            ) if number_positions else 0)
            
            curr_pos = remaining_positions.pop(0)
            i, j = curr_pos
            
            # 减少添加新数字的概率，更倾向于添加箭头
            # 调整概率，增加迷宫生成的稳定性
            add_number_prob = 0.15  # 只有15%的概率添加新数字
            if len(number_positions) < min(n, m) // 3:
                add_number_prob = 0.25  # 如果数字太少，增加添加概率
            
            # 尝试添加数字，但概率降低
            added_number = False
            if random.random() < add_number_prob:
                directions = list(self.ARROWS.items())
                random.shuffle(directions)
                
                for arrow_symbol, (di, dj) in directions:
                    ni, nj = i + di, j + dj
                    
                    # 检查是否可以添加一个数字和一个箭头，且与已有数字保持一定距离
                    if 0 <= ni < n and 0 <= nj < m and solution[ni][nj] == "X":
                        # 检查与已有数字的距离，减小最小距离要求，提高成功率
                        too_close = False
                        for num_i, num_j in number_positions:
                            if abs(num_i - i) + abs(num_j - j) < 2:  # 降低距离要求
                                too_close = True
                                break
                                
                        if too_close:
                            continue
                            
                        # 尝试创建射线，但不要求太长，提高成功率
                        possible_arrows = 0
                        test_ni, test_nj = ni, nj
                        while 0 <= test_ni < n and 0 <= test_nj < m and solution[test_ni][test_nj] == "X":
                            possible_arrows += 1
                            test_ni += di
                            test_nj += dj
                            if possible_arrows >= 2:  # 限制预检测长度，防止循环过长
                                break
                            
                        # 允许添加较短的射线，提高成功率
                        if possible_arrows < 1:
                            continue
                            
                        # 添加数字和箭头
                        solution[i][j] = "1"  # 先用1占位
                        
                        # 添加射线
                        arrow_count = 0
                        for k in range(possible_arrows):
                            if 0 <= ni < n and 0 <= nj < m and solution[ni][nj] == "X":
                                solution[ni][nj] = arrow_symbol
                                if (ni, nj) in remaining_positions:
                                    remaining_positions.remove((ni, nj))
                                ni += di
                                nj += dj
                                arrow_count += 1
                        
                        # 更新数字值
                        solution[i][j] = str(arrow_count)
                        maze[i][j] = str(arrow_count)
                        
                        # 添加到数字位置列表
                        number_positions.append((i, j))
                        added_number = True
                        break
            
            # 如果不添加数字，则添加箭头
            if not added_number:
                # 找到最近的数字以确定箭头方向，提高连贯性
                nearest_number = None
                nearest_dist = float('inf')
                
                for ni, nj in number_positions:
                    # 计算曼哈顿距离
                    dist = abs(ni - i) + abs(nj - j)
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest_number = (ni, nj)
                
                if nearest_number and nearest_dist < n + m:  # 确保距离不会太远
                    ni, nj = nearest_number
                    
                    # 计算方向
                    di = 0 if i == ni else (1 if i < ni else -1)
                    dj = 0 if j == nj else (1 if j < nj else -1)
                    
                    # 找到对应的箭头符号
                    arrow_symbol = None
                    for arrow, (d_i, d_j) in self.ARROWS.items():
                        if (d_i, d_j) == (di, dj):
                            arrow_symbol = arrow
                            break
                    
                    if arrow_symbol:
                        solution[i][j] = arrow_symbol
                    else:
                        # 如果找不到合适的方向，随机选择一个箭头
                        solution[i][j] = random.choice(list(self.ARROWS.keys()))
                else:
                    # 如果找不到最近的数字，随机选择一个箭头
                    solution[i][j] = random.choice(list(self.ARROWS.keys()))
        
        # 最后调整每个数字的值，确保其值等于覆盖的箭头数量
        for i in range(n):
            for j in range(m):
                if solution[i][j].isdigit():
                    # 计算该数字覆盖的箭头数量
                    arrows_count = self._count_arrow_rays(solution, i, j)
                    
                    # 更新数字值
                    if arrows_count > 0:
                        maze[i][j] = str(arrows_count)
                        solution[i][j] = str(arrows_count)
                    else:
                        # 如果没有箭头被覆盖，尝试添加一个箭头
                        added = False
                        for arrow_symbol, (di, dj) in self.ARROWS.items():
                            ni, nj = i + di, j + dj
                            if 0 <= ni < n and 0 <= nj < m and solution[ni][nj] == "X":
                                solution[ni][nj] = arrow_symbol
                                maze[i][j] = "1"
                                solution[i][j] = "1"
                                added = True
                                break
                        
                        # 如果仍然无法添加箭头，将其替换为随机箭头
                        if not added:
                            maze[i][j] = "X"
                            solution[i][j] = random.choice(list(self.ARROWS.keys()))
        
        # 创建覆盖标记数组，用于最终验证
        covered = [[False for _ in range(m)] for _ in range(n)]
        for i in range(n):
            for j in range(m):
                if solution[i][j].isdigit():
                    covered[i][j] = True
                    self._mark_covered_arrows(solution, covered, i, j)
        
        # 如果还有未覆盖的箭头，添加新数字覆盖它们
        uncovered_arrows = []
        for i in range(n):
            for j in range(m):
                if solution[i][j] in self.ARROWS and not covered[i][j]:
                    uncovered_arrows.append((i, j))
        
        # 迭代处理未覆盖的箭头，确保每个箭头都被覆盖
        while uncovered_arrows:
            # 每次处理一个未覆盖的箭头
            i, j = uncovered_arrows.pop(0)
            if covered[i][j]:  # 如果已经被覆盖，跳过
                continue
                
            # 查找周围可以放置数字的位置
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue
                        
                    ni, nj = i + di, j + dj
                    if not (0 <= ni < n and 0 <= nj < m):
                        continue
                        
                    # 如果是箭头或空格，可以替换为数字
                    if solution[ni][nj] in self.ARROWS or solution[ni][nj] == "X":
                        # 如果是箭头且已被覆盖，跳过
                        if solution[ni][nj] in self.ARROWS and covered[ni][nj]:
                            continue
                            
                        # 找到从该数字到箭头的方向
                        direction = None
                        for arrow, (d_i, d_j) in self.ARROWS.items():
                            if (d_i, d_j) == (-di, -dj):  # 使用相反方向
                                direction = arrow
                                break
                                
                        if direction:
                            original_value = solution[ni][nj]
                            
                            # 替换为数字1并尝试更新覆盖
                            maze[ni][nj] = "1"
                            solution[ni][nj] = "1"
                            
                            # 如果原来是箭头，可能需要更改其方向
                            if solution[i][j] != direction:
                                solution[i][j] = direction
                            
                            # 重新计算覆盖情况
                            new_covered = [[False for _ in range(m)] for _ in range(n)]
                            for r in range(n):
                                for c in range(m):
                                    if solution[r][c].isdigit():
                                        new_covered[r][c] = True
                                        self._mark_covered_arrows(solution, new_covered, r, c)
                            
                            # 检查是否覆盖了原未覆盖的箭头
                            if new_covered[i][j]:
                                covered = new_covered
                                break
                            else:
                                # 如果没有覆盖，恢复原始值
                                solution[ni][nj] = original_value
                                maze[ni][nj] = "X" if original_value in self.ARROWS else original_value
                        
                if covered[i][j]:  # 如果已经被覆盖，跳过后续处理
                    break       
        # 尝试减少值为1的数字，提高迷宫的复杂性
        # 统计值为1的数字
        value_one_numbers = []
        for i in range(n):
            for j in range(m):
                if solution[i][j] == "1":
                    value_one_numbers.append((i, j))
        
        # 如果值为1的数字太多，尝试合并一些
        if len(value_one_numbers) > max(2, len(number_positions) // 3):
            # 随机打乱，避免总是处理相同的数字
            random.shuffle(value_one_numbers)
            
            # 尝试处理一部分值为1的数字
            for i, j in value_one_numbers[:len(value_one_numbers) // 2]:
                # 获取该数字覆盖的箭头
                arrow_positions = []
                for arrow_symbol, (di, dj) in self.ARROWS.items():
                    ni, nj = i + di, j + dj
                    if 0 <= ni < n and 0 <= nj < m and solution[ni][nj] == arrow_symbol:
                        arrow_positions.append((ni, nj, arrow_symbol))
                
                if arrow_positions:
                    ni, nj, arrow_symbol = arrow_positions[0]  # 获取该数字覆盖的箭头
                    
                    # 寻找附近的其他数字，优先选择数值较大的数字
                    nearby_numbers = []
                    # 先搜索较小范围内的数字
                    for search_dist in [2, 3, 4]:  # 逐步扩大搜索范围
                        for di in range(-search_dist, search_dist + 1):
                            for dj in range(-search_dist, search_dist + 1):
                                if di == 0 and dj == 0:
                                    continue
                                new_i, new_j = i + di, j + dj
                                if 0 <= new_i < n and 0 <= new_j < m and solution[new_i][new_j].isdigit() and (new_i, new_j) != (i, j):
                                    # 存储距离和位置，优先处理更大的数字
                                    value = int(solution[new_i][new_j])
                                    distance = abs(di) + abs(dj)
                                    nearby_numbers.append((value, distance, new_i, new_j))
                        
                        # 如果找到了数字就停止扩大搜索范围
                        if nearby_numbers:
                            break
                    
                    # 排序：优先选择数值大的，其次是距离近的
                    nearby_numbers.sort(key=lambda x: (-x[0], x[1]))
                    
                    if nearby_numbers:
                        # 选择最好的候选数字（数值最大或距离最近）
                        _, _, new_i, new_j = nearby_numbers[0]
                        
                        # 计算从新数字到箭头的方向
                        dir_i = 1 if ni > new_i else (-1 if ni < new_i else 0)
                        dir_j = 1 if nj > new_j else (-1 if nj < new_j else 0)
                        
                        # 找到对应的箭头符号
                        new_arrow_symbol = None
                        for arrow, (d_i, d_j) in self.ARROWS.items():
                            if (d_i, d_j) == (dir_i, dir_j):
                                new_arrow_symbol = arrow
                                break
                        
                        if new_arrow_symbol:
                            # 尝试创建新的射线路径，检查是否可行
                            can_make_path = True
                            test_ni, test_nj = new_i, new_j
                            
                            # 确保新路径上没有障碍物
                            while test_ni != i or test_nj != j:
                                test_ni += dir_i
                                test_nj += dir_j
                                # 如果遇到其他数字或边界，则路径不可行
                                if test_ni < 0 or test_ni >= n or test_nj < 0 or test_nj >= m or solution[test_ni][test_nj].isdigit():
                                    if (test_ni, test_nj) != (i, j):  # 除了当前要转换的数字1
                                        can_make_path = False
                                        break
                            
                            if can_make_path:
                                # 临时保存原始状态，以便在失败时回滚
                                temp_maze = copy.deepcopy(maze)
                                temp_solution = copy.deepcopy(solution)
                                
                                # 尝试合并
                                try:
                                    # 将原数字改为箭头
                                    solution[i][j] = new_arrow_symbol
                                    maze[i][j] = "X"
                                    
                                    # 沿新路径更新所有箭头
                                    test_ni, test_nj = new_i + dir_i, new_j + dir_j
                                    while test_ni != i or test_nj != j:
                                        if 0 <= test_ni < n and 0 <= test_nj < m:
                                            solution[test_ni][test_nj] = new_arrow_symbol
                                        test_ni += dir_i
                                        test_nj += dir_j
                                    
                                    # 更新原有箭头的方向
                                    solution[ni][nj] = new_arrow_symbol
                                    
                                    # 更新数字的值
                                    new_count = self._count_arrow_rays(solution, new_i, new_j)
                                    solution[new_i][new_j] = str(new_count)
                                    maze[new_i][new_j] = str(new_count)
                                    
                                    # 验证修改后的迷宫是否仍然有效
                                    check_covered = [[False for _ in range(m)] for _ in range(n)]
                                    for r in range(n):
                                        for c in range(m):
                                            if solution[r][c].isdigit():
                                                check_covered[r][c] = True
                                                self._mark_covered_arrows(solution, check_covered, r, c)
                                    
                                    # 检查所有箭头是否被覆盖
                                    all_covered = True
                                    for r in range(n):
                                        for c in range(m):
                                            if solution[r][c] in self.ARROWS and not check_covered[r][c]:
                                                all_covered = False
                                                break
                                        if not all_covered:
                                            break
                                    
                                    # 如果修改后不再有效，回滚更改
                                    if not all_covered:
                                        maze = temp_maze
                                        solution = temp_solution
                                except Exception:
                                    # 如果发生任何错误，回滚到原始状态
                                    maze = temp_maze
                                    solution = temp_solution
        
        # 再次尝试合并剩余值为1的数字，这次尝试2和1的合并
        value_one_numbers = []
        value_two_numbers = []
        for i in range(n):
            for j in range(m):
                if solution[i][j] == "1":
                    value_one_numbers.append((i, j))
                elif solution[i][j] == "2":
                    value_two_numbers.append((i, j))
        
        # 尝试将一部分值为1的数字与值为2的数字合并
        if len(value_one_numbers) > 1 and value_two_numbers:
            random.shuffle(value_one_numbers)
            # 尝试处理一半的值为1的数字
            removal_count = min(len(value_one_numbers) // 2, len(value_one_numbers) - 1)
            
            for i, j in value_one_numbers[:removal_count]:
                # 找出附近的值为2的数字
                nearby_twos = []
                for ti, tj in value_two_numbers:
                    dist = abs(ti - i) + abs(tj - j)
                    if dist <= 4:  # 限制在合理距离内
                        nearby_twos.append((dist, ti, tj))
                
                # 按距离排序
                nearby_twos.sort()
                
                # 尝试与最近的值为2的数字合并
                if nearby_twos:
                    _, ti, tj = nearby_twos[0]
                    
                    # 得到值为1的数字覆盖的箭头
                    one_arrow_pos = None
                    for arrow_symbol, (di, dj) in self.ARROWS.items():
                        ni, nj = i + di, j + dj
                        if 0 <= ni < n and 0 <= nj < m and solution[ni][nj] == arrow_symbol:
                            one_arrow_pos = (ni, nj, arrow_symbol)
                            break
                    
                    if one_arrow_pos:
                        ni, nj, one_arrow_symbol = one_arrow_pos
                        
                        # 计算从值为2的数字到该箭头的方向
                        dir_i = 1 if ni > ti else (-1 if ni < ti else 0)
                        dir_j = 1 if nj > tj else (-1 if nj < tj else 0)
                        
                        # 找到对应的箭头符号
                        new_arrow_symbol = None
                        for arrow, (d_i, d_j) in self.ARROWS.items():
                            if (d_i, d_j) == (dir_i, dir_j):
                                new_arrow_symbol = arrow
                                break
                        
                        if new_arrow_symbol:
                            # 临时保存原始状态
                            temp_maze = copy.deepcopy(maze)
                            temp_solution = copy.deepcopy(solution)
                            
                            try:
                                # 将值为1的数字改为箭头
                                solution[i][j] = new_arrow_symbol
                                maze[i][j] = "X"
                                
                                # 更新箭头方向
                                solution[ni][nj] = new_arrow_symbol
                                
                                # 更新值为2的数字
                                new_count = self._count_arrow_rays(solution, ti, tj)
                                solution[ti][tj] = str(new_count)
                                maze[ti][tj] = str(new_count)
                                
                                # 验证
                                check_covered = [[False for _ in range(m)] for _ in range(n)]
                                for r in range(n):
                                    for c in range(m):
                                        if solution[r][c].isdigit():
                                            check_covered[r][c] = True
                                            self._mark_covered_arrows(solution, check_covered, r, c)
                                
                                # 检查所有箭头是否被覆盖
                                all_covered = True
                                for r in range(n):
                                    for c in range(m):
                                        if solution[r][c] in self.ARROWS and not check_covered[r][c]:
                                            all_covered = False
                                            break
                                    if not all_covered:
                                        break
                                
                                # 如果修改后不再有效，回滚更改
                                if not all_covered:
                                    maze = temp_maze
                                    solution = temp_solution
                            except:
                                maze = temp_maze
                                solution = temp_solution
        
        # 最后再次检查并更新所有数字的值，确保迷宫有效
        for i in range(n):
            for j in range(m):
                if solution[i][j].isdigit():
                    arrows_count = self._count_arrow_rays(solution, i, j)
                    maze[i][j] = str(arrows_count)
                    solution[i][j] = str(arrows_count)
        
        # 最后验证迷宫有效性
        if not self._is_valid_maze(maze, solution):
            # 如果验证失败，简化策略，重新生成一个基本迷宫
            return self._generate_basic_maze(n, m, num_numbers, min_numbers)
            
        return maze, solution
        
    def _generate_basic_maze(self, n: int, m: int, num_numbers: int, min_numbers: int = 4) -> Tuple[List[List[str]], List[List[str]]]:
        """
        生成一个基本的迷宫，作为备选策略
        使用简化的算法确保能生成有效解决方案
        
        @param n: 迷宫行数
        @param m: 迷宫列数
        @param num_numbers: 数字数量
        @param min_numbers: 最小数字数量
        @return: (迷宫, 解决方案)
        """
        # 初始化空迷宫
        maze = [["X" for _ in range(m)] for _ in range(n)]
        solution = [["X" for _ in range(m)] for _ in range(n)]
        
        # 简化数字数量
        actual_num_numbers = min(num_numbers, n*m//4)
        # 确保至少有最小数量的数字
        actual_num_numbers = max(min_numbers, actual_num_numbers)
        
        # 随机选择位置放置数字
        positions = [(i, j) for i in range(n) for j in range(m)]
        random.shuffle(positions)
        
        number_positions = []
        for idx in range(min(actual_num_numbers, len(positions))):
            i, j = positions[idx]
            maze[i][j] = "1"  # 先用1作占位
            solution[i][j] = "1"
            number_positions.append((i, j))
        
        # 每个数字创建一些箭头
        for i, j in number_positions:
            # 随机选择1-2个方向
            directions = list(self.ARROWS.items())
            random.shuffle(directions)
            selected_directions = directions[:random.randint(1, min(2, len(directions)))]
            
            total_arrows = 0
            for arrow_symbol, (di, dj) in selected_directions:
                ni, nj = i + di, j + dj
                arrows_added = 0
                
                # 延伸射线
                while 0 <= ni < n and 0 <= nj < m and arrows_added < 2:  # 限制最多2个箭头
                    if solution[ni][nj].isdigit():
                        break
                    if solution[ni][nj] != "X":  # 已经有箭头
                        break
                        
                    solution[ni][nj] = arrow_symbol
                    arrows_added += 1
                    total_arrows += 1
                    
                    ni += di
                    nj += dj
            
            # 更新数字
            if total_arrows > 0:
                maze[i][j] = str(total_arrows)
                solution[i][j] = str(total_arrows)
        
        # 填充剩余空格
        for i in range(n):
            for j in range(m):
                if solution[i][j] == "X":
                    # 默认使用向下箭头
                    solution[i][j] = "↓"
        
        # 确保每个箭头都被数字覆盖
        covered = [[False for _ in range(m)] for _ in range(n)]
        for i in range(n):
            for j in range(m):
                if solution[i][j].isdigit():
                    covered[i][j] = True
                    self._mark_covered_arrows(solution, covered, i, j)
        
        # 处理未覆盖的箭头
        for i in range(n):
            for j in range(m):
                if solution[i][j] in self.ARROWS and not covered[i][j]:
                    # 为该箭头添加一个数字
                    for di in [-1, 0, 1]:
                        for dj in [-1, 0, 1]:
                            if di == 0 and dj == 0:
                                continue
                            ni, nj = i + di, j + dj
                            if 0 <= ni < n and 0 <= nj < m and solution[ni][nj] in self.ARROWS and not covered[ni][nj]:
                                # 找到箭头方向
                                direction = None
                                for arrow, (d_i, d_j) in self.ARROWS.items():
                                    if (d_i, d_j) == (-di, -dj):
                                        direction = arrow
                                        break
                                
                                if direction and solution[i][j] == direction:
                                    maze[ni][nj] = "1"
                                    solution[ni][nj] = "1"
                                    
                                    # 更新覆盖信息
                                    covered[ni][nj] = True
                                    self._mark_covered_arrows(solution, covered, ni, nj)
                                    break
                        if covered[i][j]:
                            break
                    
                    # 如果仍未覆盖，创建一个新数字
                    if not covered[i][j]:
                        # 找一个合适的位置
                        for di in [-1, 0, 1]:
                            for dj in [-1, 0, 1]:
                                if di == 0 and dj == 0:
                                    continue
                                ni, nj = i + di, j + dj
                                if not (0 <= ni < n and 0 <= nj < m):
                                    continue
                                if solution[ni][nj] not in self.ARROWS:
                                    continue
                                
                                # 确保方向匹配
                                direction = None
                                for arrow, (d_i, d_j) in self.ARROWS.items():
                                    if (d_i, d_j) == (-di, -dj):
                                        direction = arrow
                                        break
                                
                                if direction:
                                    solution[i][j] = direction
                                    maze[ni][nj] = "1"
                                    solution[ni][nj] = "1"
                                    
                                    # 更新覆盖
                                    covered[ni][nj] = True
                                    self._mark_covered_arrows(solution, covered, ni, nj)
                                    break
                            if covered[i][j]:
                                break
        
        # 最后更新所有数字的值
        for i in range(n):
            for j in range(m):
                if solution[i][j].isdigit():
                    arrows_count = self._count_arrow_rays(solution, i, j)
                    maze[i][j] = str(arrows_count)
                    solution[i][j] = str(arrows_count)
        
        return maze, solution
    
    def _mark_covered_arrows(self, solution: List[List[str]], covered: List[List[bool]], i: int, j: int):
        """
        标记被数字覆盖的所有箭头
        
        @param solution: 解决方案网格
        @param covered: 覆盖标记数组
        @param i: 数字行索引
        @param j: 数字列索引
        """
        n = len(solution)
        m = len(solution[0])
        
        # 检查所有方向
        for arrow_symbol, (di, dj) in self.ARROWS.items():
            ni, nj = i + di, j + dj
            
            # 沿该方向标记连续的相同箭头
            while 0 <= ni < n and 0 <= nj < m and solution[ni][nj] == arrow_symbol:
                covered[ni][nj] = True
                ni += di
                nj += dj
    
    def _is_valid_maze(self, maze: List[List[str]], solution: List[List[str]]) -> bool:
        """
        检查迷宫是否有效
        
        @param maze: 迷宫网格
        @param solution: 解决方案网格
        @return: 迷宫是否有效
        """
        n = len(maze)
        m = len(maze[0])
        
        # 检查所有空格是否被填满
        for i in range(n):
            for j in range(m):
                if maze[i][j] == "X" and solution[i][j] == "X":
                    return False
        
        # 检查数字位置是否一致
        for i in range(n):
            for j in range(m):
                if maze[i][j].isdigit() and maze[i][j] != solution[i][j]:
                    return False
        
        # 检查所有箭头是否合法
        for i in range(n):
            for j in range(m):
                if solution[i][j] not in ["X"] + [str(k) for k in range(1, 10)] and solution[i][j] not in self.ARROWS:
                    return False
        
        # 创建覆盖标记数组
        covered = [[False for _ in range(m)] for _ in range(n)]
        
        # 标记所有数字位置为已覆盖
        for i in range(n):
            for j in range(m):
                if solution[i][j].isdigit():
                    covered[i][j] = True
        
        # 检查每个数字的箭头串和覆盖情况
        for i in range(n):
            for j in range(m):
                if maze[i][j].isdigit():
                    number = int(maze[i][j])
                    arrows_count = self._count_arrow_rays(solution, i, j)
                    if arrows_count != number:
                        return False
                    
                    # 标记该数字覆盖的所有箭头
                    self._mark_covered_arrows(solution, covered, i, j)
        
        # 检查所有箭头是否都被覆盖
        for i in range(n):
            for j in range(m):
                if solution[i][j] in self.ARROWS and not covered[i][j]:
                    return False
        
        return True
    
    def _count_arrow_rays(self, solution: List[List[str]], i: int, j: int) -> int:
        """
        计算从数字出发的所有射线箭头串中箭头总数
        
        @param solution: 解决方案网格
        @param i: 数字行索引
        @param j: 数字列索引
        @return: 箭头总数
        """
        n = len(solution)
        m = len(solution[0])
        count = 0
        
        # 检查所有方向
        for arrow_symbol, (di, dj) in self.ARROWS.items():
            ni, nj = i + di, j + dj
            ray_length = 0
            
            # 沿该方向计数连续的相同箭头
            while 0 <= ni < n and 0 <= nj < m and solution[ni][nj] == arrow_symbol:
                ray_length += 1
                ni += di
                nj += dj
            
            count += ray_length
        
        return count
    
    def extract_answer(self, test_solution: str) -> str:
        """
        从模型的回答中提取答案
        
        @param test_solution: 模型的完整回答
        @return: 提取的答案 (JSON格式的二维数组)
        """
        if not test_solution:
            return ""
        
        # 尝试匹配Python代码块
        import re
        code_block_patterns = [
            r'```python\s*\n(.*?\[.*?\].*?)\n```',  # 标准Python代码块
            r'```\s*\n(.*?\[.*?\].*?)\n```',       # 无语言标记的代码块
            r'```(.*?\[.*?\].*?)```'               # 无换行的代码块
        ]
        
        for pattern in code_block_patterns:
            matches = re.findall(pattern, test_solution, re.DOTALL)
            if matches:
                # 获取最后一个匹配项
                code_block = matches[-1].strip()
                try:
                    # 尝试解析为Python列表
                    grid = eval(code_block)
                    # 验证格式是否为二维数组
                    if isinstance(grid, list) and all(isinstance(row, list) for row in grid):
                        return json.dumps(grid)
                except Exception as e:
                    print(f"解析代码块失败: {e}")
                    continue
        
        # 如果没有找到有效的代码块，尝试直接寻找列表
        list_pattern = r'\[\s*\[.*?\]\s*\]'
        matches = re.findall(list_pattern, test_solution, re.DOTALL)
        if matches:
            try:
                # 尝试解析为Python列表
                grid = eval(matches[-1])
                # 验证格式是否为二维数组
                if isinstance(grid, list) and all(isinstance(row, list) for row in grid):
                    return json.dumps(grid)
            except Exception as e:
                print(f"解析列表失败: {e}")
        
        # 如果上述方法都失败，返回空字符串
        return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="箭头迷宫游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=10000, help="每个题目的最大尝试次数")
    parser.add_argument("--width", type=int, default=8, help="迷宫宽度")
    parser.add_argument("--height", type=int, default=8, help="迷宫高度")
    parser.add_argument("--arrow_fill_rate_min", type=float, default=0.0, help="预填箭头比例最小值（0.0-1.0之间）")
    parser.add_argument("--arrow_fill_rate_max", type=float, default=0.0, help="预填箭头比例最大值（0.0-1.0之间）")
    args = parser.parse_args()
    
    # 确保arrow_fill_rate在有效范围内
    args.arrow_fill_rate_min = max(0.0, min(1.0, args.arrow_fill_rate_min))
    args.arrow_fill_rate_max = max(args.arrow_fill_rate_min, min(1.0, args.arrow_fill_rate_max))
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    
    # 创建游戏实例
    game = ArrowMaze()
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts,
        width=args.width,
        height=args.height,
        arrow_fill_rate_min=args.arrow_fill_rate_min,
        arrow_fill_rate_max=args.arrow_fill_rate_max
    )
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据")
    
    # 创建嵌套目录结构
    base_data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not base_data_dir.exists():
        base_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建嵌套目录结构
    nested_dir = base_data_dir / f"num_of_data_{args.num_of_data}" / f"width_{args.width}_height_{args.height}" / f"fill_rate_{args.arrow_fill_rate_min:.1f}_{args.arrow_fill_rate_max:.1f}"
    if not nested_dir.exists():
        nested_dir.mkdir(parents=True, exist_ok=True)
    
    nested_output_file = nested_dir / f"arrow_maze_{args.num_of_data}.jsonl"
    
    # 将数据保存到文件
    try:
        # 同时保存到嵌套目录
       with open(nested_output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
            print(f"游戏数据也已保存到 {nested_output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}")
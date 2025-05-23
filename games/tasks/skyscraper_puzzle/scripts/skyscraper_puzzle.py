from games.tasks.skyscraper_puzzle.scripts.skyscraper_puzzle_prompt import prompt_skyscraper_puzzle, generate_prompts
from games.tasks.skyscraper_puzzle.scripts.skyscraper_puzzle_verifier import SkyscraperPuzzleVerifier
from games.base.game import Game
from base.data import Data
import random
import re
import itertools
import argparse
import json
import pathlib
import os
import uuid
import time
import copy
import ast

class SkyscraperPuzzle(Game):
    """
    摩天楼游戏类实现
    """
    def __init__(self, n=4):
        """
        初始化摩天楼游戏
        
        @param n: 网格大小
        """
        super().__init__("Skyscraper Puzzle", SkyscraperPuzzleVerifier)
        self.n = n
        print(f"初始化摩天楼游戏: n={n}")
    
    def generate(self, num_of_questions: int = 100, max_attempts: int = 1000):
        """
        生成摩天楼游戏题目
        
        @param num_of_questions: 要生成的题目数量
        @param max_attempts: 每个题目的最大尝试次数
        @return: 生成的题目列表
        """
        game_data_list = []
        
        while len(game_data_list) < num_of_questions and max_attempts > 0:
            # 使用固定的网格大小
            n = self.n
            
            # 生成有效的摩天楼布局
            solved_grid, top, bottom, left, right = self._generate_valid_skyscraper(n)
            
            if solved_grid:
                # 创建一个初始全为'X'的网格
                initial_grid = [['X' for _ in range(n)] for _ in range(n)]
                
                # 生成提示语
                question = prompt_skyscraper_puzzle(n, initial_grid, top, bottom, left, right)
                
                # 生成20条不同描述的提示语
                all_prompts = generate_prompts(n, initial_grid, top, bottom, left, right)
                
                # 创建游戏数据对象
                game_data = Data(
                    question=question,
                    answer="",  # 不提供标准答案，由验证器验证
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "n": n,
                        "solved_grid": solved_grid,
                        "top": top,
                        "bottom": bottom,
                        "left": left,
                        "right": right,
                        "all_prompts": all_prompts
                    }
                )
                
                game_data_list.append(game_data)
            else:
                max_attempts -= 1
        
        return game_data_list
    
    def extract_answer(self, test_solution: str):
        """
        从模型的回答中提取网格数据
        
        @param test_solution: 模型的完整回答
        @return: 提取的解答网格数据
        """
        try:
            n = self.n
            
            # 从 ```python 代码块中提取
            code_block_pattern = r"```python\s*\n([\s\S]*?)\n\s*```"
            code_blocks = re.findall(code_block_pattern, test_solution)
            
            if code_blocks:
                # 取第一个代码块（通常只有一个）
                code_block = code_blocks[0].strip()
                try:
                    # 直接解析代码块
                    grid = ast.literal_eval(code_block)
                    # 验证是否为有效的n×n网格
                    if (isinstance(grid, list) and 
                        len(grid) == n and 
                        all(isinstance(row, list) and len(row) == n for row in grid)):
                        return grid
                except Exception:
                    # 如果直接解析失败，尝试移除注释后再解析
                    code_without_comments = re.sub(r'#.*$', '', code_block, flags=re.MULTILINE)
                    try:
                        grid = ast.literal_eval(code_without_comments.strip())
                        if (isinstance(grid, list) and 
                            len(grid) == n and 
                            all(isinstance(row, list) and len(row) == n for row in grid)):
                            return grid
                    except Exception:
                        pass
            
            # 如果提取失败，返回原始答案
            return test_solution
        except Exception as e:
            print(f"提取网格时出错: {e}")
            return test_solution
    
    def _generate_valid_skyscraper(self, n):
        """
        生成一个有效的摩天楼谜题
        
        @param n: 网格大小
        @return: 完整解答网格、上下左右的观察提示
        """
        # 尝试生成一个有效的网格填充
        # 这里，我们随机生成一个拉丁方阵（每行每列数字不重复）
        for _ in range(100):  # 尝试最多100次
            try:
                # 生成行的排列
                rows = []
                numbers = list(range(1, n+1))
                
                # 首行可以是任意排列
                first_row = copy.deepcopy(numbers)
                random.shuffle(first_row)
                rows.append(first_row)
                
                # 后续行需要满足列不重复
                for i in range(1, n):
                    # 尝试找到有效的行
                    available_perms = list(itertools.permutations(numbers))
                    random.shuffle(available_perms)
                    
                    # 检查是否有有效排列
                    valid_perm_found = False
                    for perm in available_perms:
                        # 检查这个排列是否与现有列不冲突
                        valid = True
                        for col in range(n):
                            col_values = [rows[r][col] for r in range(i)]
                            if perm[col] in col_values:
                                valid = False
                                break
                        
                        if valid:
                            rows.append(list(perm))
                            valid_perm_found = True
                            break
                    
                    if not valid_perm_found:
                        # 没有找到有效排列，放弃这个尝试
                        raise ValueError("无法找到有效行排列")
                
                # 计算四个方向的可见摩天楼数量
                grid = rows
                top = []
                bottom = []
                left = []
                right = []
                
                # 计算上方可见楼数
                for j in range(n):
                    top.append(self._count_visible_skyscrapers([grid[i][j] for i in range(n)]))
                
                # 计算下方可见楼数
                for j in range(n):
                    bottom.append(self._count_visible_skyscrapers([grid[i][j] for i in range(n-1, -1, -1)]))
                
                # 计算左侧可见楼数
                for i in range(n):
                    left.append(self._count_visible_skyscrapers(grid[i]))
                
                # 计算右侧可见楼数
                for i in range(n):
                    right.append(self._count_visible_skyscrapers(grid[i][::-1]))
                
                return grid, top, bottom, left, right
                
            except Exception as e:
                print(f"生成有效网格时出错: {e}")
                continue
        
        # 如果无法生成有效的网格，返回None
        return None, None, None, None, None
    
    def _count_visible_skyscrapers(self, heights):
        """
        计算从一个方向看过去能看到的摩天楼数量
        
        @param heights: 从观察方向依次排列的摩天楼高度列表
        @return: 可见的摩天楼数量
        """
        visible_count = 0
        max_height = 0
        
        for height in heights:
            if height > max_height:
                visible_count += 1
                max_height = height
        
        return visible_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="摩天楼游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个题目的最大尝试次数")
    parser.add_argument("--n", type=int, default=4, help="网格大小")
    parser.add_argument("--output_dir", type=str, default=None, help="输出目录")
    args = parser.parse_args()
    
    # 设置输出目录
    if args.output_dir:
        output_dir = pathlib.Path(args.output_dir)
    else:
        output_dir = pathlib.Path(__file__).parent.parent / "data"

    # 创建更具体的输出路径，包含所有参数
    nested_dir = output_dir / "hyperparameter_search" / f"n_{args.n}" / f"num_of_data_{args.num_of_data}"
    
    # 确保嵌套目录存在
    if not nested_dir.exists():
        nested_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置嵌套目录中的输出文件名
    nested_output_file = nested_dir / f"num_of_data_{args.num_of_data}.jsonl"
    
    # 设置与run.sh兼容的输出文件名
    direct_output_file = output_dir / f"skyscraper_puzzle_{args.num_of_data}.jsonl"
    
    # 创建游戏实例
    game = SkyscraperPuzzle(n=args.n)
    
    # 生成游戏数据
    print(f"开始生成 {args.num_of_data} 条摩天楼游戏数据...")
    game_data_list = game.generate(args.num_of_data, args.max_attempts)
    
    print(f"成功生成 {len(game_data_list)} 条摩天楼游戏数据")
    
    # 将数据保存到文件
    try:
        # 保存到嵌套目录
        with open(nested_output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"游戏数据已保存到嵌套目录: {nested_output_file}")
        
        # 同时保存到直接目录以兼容run.sh
        with open(direct_output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"游戏数据已保存到直接目录: {direct_output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}") 
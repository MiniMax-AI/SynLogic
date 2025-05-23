import random
import numpy as np
import re
import uuid
import json
import argparse
import pathlib
import os
from typing import List, Tuple

from games.base.game import Game
from base.data import Data
from games.tasks.survo.scripts.survo_verifier import SurvoVerifier
from games.tasks.survo.scripts.survo_prompt import prompt_survo

class Survo(Game):
    """
    Survo矩阵填充游戏类
    """
    def __init__(self):
        """
        初始化Survo矩阵填充游戏
        """
        super().__init__("Survo", SurvoVerifier)
        
    def generate(self, num_of_questions: int = 100, max_attempts: int = 100,
                 n: int = 4, x: int = 3, min_num: int = 1, max_num: int = 9):
        """
        生成Survo矩阵填充游戏的题目
        
        @param num_of_questions: 要生成的题目数量
        @param max_attempts: 每个题目的最大尝试次数
        @param n: 矩阵的维度，n>3
        @param x: 待填充数字的数量，0<x<=(n-1)*(n-1)
        @param min_num: 矩阵中数字的最小值
        @param max_num: 矩阵中数字的最大值
        @return: 生成的题目列表
        """
        # 参数校验
        if n <= 3:
            raise ValueError("矩阵维度n必须大于3")
        if x <= 0 or x > (n-1)*(n-1):
            raise ValueError(f"待填充数字数量x必须在1到{(n-1)*(n-1)}之间")
        if min_num >= max_num:
            raise ValueError("最小值必须小于最大值")
            
        game_data_list = []
        generated_matrices = set()
        attempts = 0
        
        while len(game_data_list) < num_of_questions and attempts < max_attempts:
            try:
                attempts += 1
                
                # 生成有解的矩阵和待填充数字
                matrix, original_matrix, candidate_numbers = self._generate_valid_matrix(n, x, min_num, max_num)
                
                # 将矩阵转换为字符串以检查重复
                matrix_str = str(original_matrix.tolist())
                if matrix_str in generated_matrices:
                    continue
                
                generated_matrices.add(matrix_str)
                
                # 随机选择中文或英文提示
                is_chinese = random.choice([True, False])
                
                # 生成问题描述
                question = prompt_survo(original_matrix, candidate_numbers, n, is_chinese)
                
                # 创建游戏数据
                game_data = Data(
                    question=question,
                    answer=str(matrix.tolist()),  # 保存正确答案
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "original_matrix": original_matrix.tolist(),
                        "filled_matrix": matrix.tolist(),
                        "candidate_numbers": candidate_numbers,
                        "n": n,
                        "x": x,
                        "min_num": min_num,
                        "max_num": max_num
                    }
                )
                
                game_data_list.append(game_data)
                
            except Exception as e:
                print(f"生成题目时出错: {e}")
                # 添加调试信息
                import traceback
                print(f"错误详情: {traceback.format_exc()}")
                continue
                
        if len(game_data_list) < num_of_questions:
            print(f"警告: 只能生成 {len(game_data_list)}/{num_of_questions} 条游戏数据")
        
        return game_data_list
    
    def _generate_valid_matrix(self, n: int, x: int, min_num: int, max_num: int) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """
        生成有效的Survo矩阵
        
        @param n: 矩阵的维度
        @param x: 待填充数字的数量
        @param min_num: 矩阵中数字的最小值
        @param max_num: 矩阵中数字的最大值
        @return: (完整矩阵, 包含0的矩阵, 待填充的数字列表)
        """
        # 创建n*n的矩阵，初始值为0
        matrix = np.zeros((n, n), dtype=int)  # 使用int类型
        
        # 随机填充(n-1)*(n-1)的子矩阵
        for i in range(n-1):
            for j in range(n-1):
                matrix[i, j] = random.randint(min_num, max_num)
        
        # 计算每行和每列的和
        for i in range(n-1):
            # 计算第i行的和，并填充到最后一列
            row_sum = sum(matrix[i, 0:n-1])
            matrix[i, n-1] = row_sum
            
            # 计算第i列的和，并填充到最后一行
            col_sum = sum(matrix[0:n-1, i])
            matrix[n-1, i] = col_sum
        
        # 计算最后一个元素(n-1, n-1)
        # 这个元素可以是任意值，但为了保持一致性，我们设置为前n-1行的最后一列的和
        # 或者等价地，前n-1列的最后一行的和
        matrix[n-1, n-1] = sum(matrix[0:n-1, n-1])
        
        # 保存完整矩阵的副本
        filled_matrix = matrix.copy()
        
        # 随机选择x个位置，将它们替换为0
        # 这些位置必须在(n-1)*(n-1)的子矩阵中
        positions = [(i, j) for i in range(n-1) for j in range(n-1)]
        selected_positions = random.sample(positions, x)
        
        # 记录被替换位置的原始值，这些将成为候选数字
        candidate_numbers = []
        for i, j in selected_positions:
            # 添加类型检查
            if not isinstance(matrix[i, j], (int, np.integer)):
                raise TypeError(f"矩阵位置 ({i}, {j}) 的值 {matrix[i, j]} 不是整数类型")
            candidate_numbers.append(int(matrix[i, j]))
            matrix[i, j] = 0
        
        return filled_matrix, matrix, candidate_numbers
        
    def extract_answer(self, test_solution: str):
        """
        从模型的回答中提取答案（矩阵）
        
        @param test_solution: 模型的完整回答
        @return: 提取的矩阵答案字符串
        """
        if not test_solution:
            return ""
        
        # 尝试提取Python代码块中的矩阵
        code_block_pattern = r'```python\s*([\s\S]*?)\s*```'
        code_matches = re.findall(code_block_pattern, test_solution)
        
        if code_matches:
            # 使用最后一个Python代码块
            matrix_str = code_matches[-1].strip()
            return matrix_str
        
        # 如果没有找到Python代码块，尝试提取任何代码块
        general_code_block = r'```([\s\S]*?)```'
        general_matches = re.findall(general_code_block, test_solution)
        
        if general_matches:
            # 使用最后一个代码块
            matrix_str = general_matches[-1].strip()
            return matrix_str
        
        # 如果没有找到代码块，尝试提取可能的矩阵表示
        matrix_pattern = r'\[\s*\[.*?\]\s*\]'
        matrix_matches = re.findall(matrix_pattern, test_solution, re.DOTALL)
        
        if matrix_matches:
            # 使用最后一个匹配的矩阵
            return matrix_matches[-1].strip()
        
        # 如果所有方法都失败，返回空字符串
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Survo矩阵填充游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个题目的最大尝试次数")
    parser.add_argument("--n", type=int, default=4, help="矩阵的维度")
    parser.add_argument("--x", type=int, default=3, help="待填充数字的数量")
    parser.add_argument("--min_num", type=int, default=1, help="矩阵中数字的最小值")
    parser.add_argument("--max_num", type=int, default=9, help="矩阵中数字的最大值")
    args = parser.parse_args()
    
    # 创建数据目录
    base_data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not base_data_dir.exists():
        base_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建游戏实例
    game = Survo()
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts,
        n=args.n,
        x=args.x,
        min_num=args.min_num,
        max_num=args.max_num
    )
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据")

    # 创建嵌套目录结构
    nested_dir = base_data_dir / f"num_of_data_{args.num_of_data}" / f"n_{args.n}" / f"x_{args.x}" / f"min_num_{args.min_num}_max_num_{args.max_num}"
    if not nested_dir.exists():
        nested_dir.mkdir(parents=True, exist_ok=True)

    # 设置输出文件名
    output_file = nested_dir / f"survo_{args.num_of_data}.jsonl"
    
    # 将数据保存到文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"游戏数据已保存到 {output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}") 
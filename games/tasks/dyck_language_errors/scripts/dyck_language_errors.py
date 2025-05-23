import random
import string
import json
import uuid
import pathlib
from typing import List, Tuple
import argparse
import os

from games.base.game import Game
from base.data import Data
from games.tasks.dyck_language_errors.scripts.dyck_language_errors_verifier import DyckLanguageErrorsVerifier
from games.tasks.dyck_language_errors.scripts.dyck_language_errors_prompt import prompt_dyck_language_errors

class DyckLanguageErrors(Game):
    """
    括号闭合的错误识别游戏类
    """
    # 所有可用的括号对
    BRACKET_PAIRS = [
        ('(', ')'),
        ('[', ']'),
        ('{', '}'),
        ('<', '>')
    ]
    
    def __init__(self):
        """
        初始化括号闭合的错误识别游戏
        """
        super().__init__("Dyck Language Errors", DyckLanguageErrorsVerifier)
    
    def generate(self, num_of_questions: int = 100, max_attempts: int = 100,
                n_types: int = 3, total_length: int = 20):
        """
        生成括号闭合的错误识别游戏题目
        
        @param num_of_questions: 要生成的题目数量
        @param max_attempts: 每个题目的最大尝试次数
        @param n_types: 括号对的种类数量，范围为1到4
        @param total_length: 括号序列的总长度
        @return: 生成的题目列表
        """
        # 参数校验
        if n_types < 1 or n_types > 4:
            raise ValueError("括号对的种类数量必须在1到4之间")
        if total_length < 2:
            raise ValueError("括号序列的总长度必须至少为2")
            
        game_data_list = []
        generated_strings = set()
        attempts = 0
        
        while len(game_data_list) < num_of_questions and attempts < max_attempts:
            try:
                attempts += 1
                
                # 随机选择括号对
                bracket_pairs = random.sample(self.BRACKET_PAIRS, n_types)
                
                # 随机决定生成有效或无效的括号序列
                is_valid = random.random() < 0.2
                
                if is_valid:
                    # 生成有效的括号序列
                    bracket_string, first_error_pos = self._generate_valid_brackets(bracket_pairs, total_length)
                    # 如果生成的序列实际上是无效的（由于随机添加括号导致），更新is_valid标志
                    if first_error_pos is not None:
                        is_valid = False
                        answer = str(first_error_pos)
                    else:
                        answer = "-1"  # 改为-1表示合法
                else:
                    # 生成无效的括号序列（带有错误）
                    bracket_string, first_error_pos = self._generate_invalid_brackets(bracket_pairs, total_length)
                    answer = str(first_error_pos)
                
                # 检查生成的字符串是否重复
                if bracket_string in generated_strings:
                    continue
                
                generated_strings.add(bracket_string)
                
                # 使用提示模板生成问题描述
                is_chinese = random.random() < 0.5
                question = prompt_dyck_language_errors(bracket_string, n_types, total_length, is_chinese)
                
                # 创建游戏数据
                game_data = Data(
                    question=question,
                    answer=answer,
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "bracket_string": bracket_string,
                        "first_error_pos": first_error_pos,
                        "is_valid": is_valid,
                        "n_types": n_types,
                        "total_length": total_length,
                        "bracket_pairs": [{"open": open_b, "close": close_b} for open_b, close_b in bracket_pairs]
                    }
                )
                
                game_data_list.append(game_data)
                
            except Exception as e:
                print(f"生成题目时出错: {e}")
                continue
                
        if len(game_data_list) < num_of_questions:
            print(f"警告: 只能生成 {len(game_data_list)}/{num_of_questions} 条游戏数据")
        
        return game_data_list
    
    def _generate_valid_brackets(self, bracket_pairs: List[Tuple[str, str]], total_length: int) -> Tuple[str, None]:
        """
        生成有效的括号序列
        
        @param bracket_pairs: 要使用的括号对列表
        @param total_length: 序列的总长度
        @return: (括号序列, None)，因为有效序列没有错误位置
        """
        # 计算能够生成的最大偶数长度
        max_even_length = (total_length // 2) * 2
        
        # 使用递归方法生成有效的括号序列
        bracket_string = self._generate_balanced_brackets(bracket_pairs, max_even_length // 2)
        
        # 如果需要的长度是奇数，添加一个随机括号使序列无效
        if total_length % 2 != 0 and max_even_length < total_length:
            random_brackets = [b for pair in bracket_pairs for b in pair]
            bracket_string += random.choice(random_brackets)
        
        # 确保最终长度等于total_length
        bracket_list = list(bracket_string)
        while len(bracket_list) > total_length:
            bracket_list.pop()
        
        # 如果长度不足，添加随机括号字符
        while len(bracket_list) < total_length:
            random_brackets = [b for pair in bracket_pairs for b in pair]
            bracket_list.append(random.choice(random_brackets))
        
        bracket_string = ''.join(bracket_list)
        
        # 检查序列是否合法，如果不合法，返回错误位置
        error_pos = self._find_first_error_position(list(bracket_string), bracket_pairs)
        return bracket_string, error_pos
    
    def _generate_balanced_brackets(self, bracket_pairs: List[Tuple[str, str]], pairs_count: int) -> str:
        """
        递归生成平衡的括号序列
        
        @param bracket_pairs: 括号对列表
        @param pairs_count: 需要生成的括号对数量
        @return: 平衡的括号序列
        """
        if pairs_count == 0:
            return ""
        
        result = []
        stack = []
        
        # 确保至少有一个完整的括号对
        open_bracket, close_bracket = random.choice(bracket_pairs)
        result.append(open_bracket)
        stack.append((open_bracket, close_bracket))
        
        # 生成剩余的括号
        for _ in range(pairs_count * 2 - 1):
            if stack and random.random() < 0.5:  # 50%概率闭合现有括号
                open_b, close_b = stack.pop()
                result.append(close_b)
            else:  # 50%概率添加新的开括号
                if len(stack) < pairs_count:  # 确保不超过总对数
                    open_b, close_b = random.choice(bracket_pairs)
                    result.append(open_b)
                    stack.append((open_b, close_b))
                else:  # 如果达到最大深度，必须闭合
                    if stack:
                        open_b, close_b = stack.pop()
                        result.append(close_b)
        
        # 确保所有开括号都被闭合
        while stack:
            open_b, close_b = stack.pop()
            result.append(close_b)
        
        return ''.join(result)
    
    def _generate_invalid_brackets(self, bracket_pairs: List[Tuple[str, str]], total_length: int) -> Tuple[str, int]:
        """
        生成无效的括号序列（包含错误）
        
        @param bracket_pairs: 要使用的括号对列表
        @param total_length: 序列的总长度
        @return: (括号序列, 第一个错误的位置(1-索引))
        """
        # 首先生成有效的括号序列
        valid_sequence, _ = self._generate_valid_brackets(bracket_pairs, total_length)
        
        # 将有效序列转换为列表以便修改
        sequence_list = list(valid_sequence)
        
        # 随机选择错误类型
        error_type = random.choice(['mismatch', 'unclosed', 'extra_closing'])
        
        if error_type == 'mismatch':
            # 找出一个闭括号并将其替换为错误的闭括号
            closing_indices = [i for i, char in enumerate(sequence_list) 
                             if any(char == close_b for _, close_b in bracket_pairs)]
            
            if closing_indices:
                error_index = random.choice(closing_indices)
                current_close = sequence_list[error_index]
                
                # 找出与当前不同的闭括号
                other_close_brackets = [close_b for _, close_b in bracket_pairs 
                                      if close_b != current_close]
                
                if other_close_brackets:
                    sequence_list[error_index] = random.choice(other_close_brackets)
                    first_error_pos = error_index + 1  # 1-indexed
                else:
                    # 如果没有其他闭括号可用，改为使用开括号
                    open_brackets = [open_b for open_b, _ in bracket_pairs]
                    sequence_list[error_index] = random.choice(open_brackets)
                    first_error_pos = error_index + 1  # 1-indexed
            else:
                # 回退到其他错误类型
                error_type = 'extra_closing'
        
        if error_type == 'unclosed':
            # 移除一个闭括号
            closing_indices = [i for i, char in enumerate(sequence_list) 
                             if any(char == close_b for _, close_b in bracket_pairs)]
            
            if closing_indices:
                error_index = random.choice(closing_indices)
                # 移除闭括号
                del sequence_list[error_index]
                
                # 在序列末尾添加一个随机字符以维持长度
                random_brackets = [b for pair in bracket_pairs for b in pair]
                sequence_list.append(random.choice(random_brackets))
                
                # 找出导致不平衡的第一个位置
                first_error_pos = self._find_first_error_position(sequence_list, bracket_pairs)
            else:
                # 回退到其他错误类型
                error_type = 'extra_closing'
        
        if error_type == 'extra_closing':
            # 在随机位置添加一个额外的闭括号
            close_brackets = [close_b for _, close_b in bracket_pairs]
            extra_close = random.choice(close_brackets)
            
            # 随机选择插入位置
            insert_pos = random.randint(0, len(sequence_list) - 1)
            sequence_list.insert(insert_pos, extra_close)
            
            # 确保最终长度等于total_length
            while len(sequence_list) > total_length:
                sequence_list.pop()
            
            # 如果长度不足，添加随机括号字符
            while len(sequence_list) < total_length:
                random_brackets = [b for pair in bracket_pairs for b in pair]
                sequence_list.append(random.choice(random_brackets))
            
            # 找出导致不平衡的第一个位置
            first_error_pos = self._find_first_error_position(sequence_list, bracket_pairs)
        
        # 转回字符串
        invalid_sequence = ''.join(sequence_list)
        
        return invalid_sequence, first_error_pos
    
    def _find_first_error_position(self, sequence_list: List[str], bracket_pairs: List[Tuple[str, str]]) -> int:
        """
        找出序列中第一个错误的位置
        
        @param sequence_list: 括号序列列表
        @param bracket_pairs: 括号对列表
        @return: 第一个错误的位置(1-索引)
        """
        stack = []
        opening_brackets = [open_b for open_b, _ in bracket_pairs]
        closing_brackets = [close_b for _, close_b in bracket_pairs]
        bracket_map = {close_b: open_b for open_b, close_b in bracket_pairs}
        
        for i, char in enumerate(sequence_list):
            if char in opening_brackets:
                stack.append(char)
            elif char in closing_brackets:
                if not stack:  # 栈为空时遇到闭括号
                    return i + 1  # 1-indexed
                
                last_open = stack.pop()
                if last_open != bracket_map[char]:  # 括号不匹配
                    return i + 1  # 1-indexed
        
        # 如果序列结束但栈非空（有未闭合的括号）
        # 返回序列长度+1表示最后位置之后的错误
        # 但由于我们要标记的是最早的错误，所以应该是第一个未匹配的开括号之后的位置
        if stack:
            return len(sequence_list) + 1
        
        return None  # 没有错误
    
    def extract_answer(self, test_solution: str):
        """
        从模型的回答中提取答案
        
        @param test_solution: 模型的完整回答
        @return: 提取的答案
        """
        import re
        
        # 清理回答文本
        solution = test_solution.strip() if test_solution else ""
        
        # 提取所有数字（包括负数）
        numbers = re.findall(r'-?\d+', solution)
        if numbers:
            # 优先返回"-1"（如果存在）
            if "-1" in numbers:
                return "-1"
            # 否则返回找到的第一个非负整数
            for num in numbers:
                if num.isdigit() and int(num) >= 0:
                    return num
            # 如果只有负数，返回第一个
            return numbers[0]
        
        # 检查是否表示合法
        if any(keyword in solution.lower() for keyword in ["合法", "valid", "correct"]):
            return "-1"
        
        # 默认返回空字符串
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="括号闭合的错误识别游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个题目的最大尝试次数")
    parser.add_argument("--n_types", type=int, default=3, help="括号对的种类数量(1-4)")
    parser.add_argument("--total_length", type=int, default=20, help="括号序列的总长度")
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建游戏实例
    game = DyckLanguageErrors()
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts,
        n_types=args.n_types,
        total_length=args.total_length
    )
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据")
    
    # 创建嵌套目录结构
    nested_dir = data_dir / f"num_of_data_{args.num_of_data}" / f"n_types_{args.n_types}" / f"total_length_{args.total_length}"
    if not nested_dir.exists():
        nested_dir.mkdir(parents=True, exist_ok=True)
    
    nested_output_file = nested_dir / f"dyck_language_errors_{args.num_of_data}.jsonl"
    
    # 将数据保存到文件
    try:
        # 保存到嵌套目录
        with open(nested_output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"游戏数据已保存到 {nested_output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}") 
import random
import re
import uuid
import argparse
import json
import pathlib
from typing import List, Set, Tuple
from abc import ABC

from games.base.game import Game
from base.data import Data

class DyckLanguage(Game):
    """
    Dyck Language游戏类
    生成合法的括号序列，并截取部分作为问题
    """
    def __init__(self):
        """
        初始化Dyck Language游戏
        """
        from games.tasks.dyck_language.scripts.dyck_language_verifier import DyckLanguageVerifier
        super().__init__("Dyck Language", DyckLanguageVerifier)
        # 定义所有可能的括号对
        self.brackets = [
            ('(', ')'),
            ('[', ']'),
            ('{', '}'),
            ('<', '>')
        ]
        
    def _check_unique_completion(self, sequence: str, cut_point: int) -> bool:
        """
        检查序列在截取点之后是否只有唯一的完成方式
        
        @param sequence: 完整的序列
        @param cut_point: 截取点
        @return: 是否只有唯一完成方式
        """
        # 获取前缀（问题序列）
        prefix = sequence[:cut_point]
        
        # 统计未配对的左括号
        stack = []
        bracket_pairs = {')': '(', ']': '[', '}': '{', '>': '<'}
        
        for char in prefix:
            if char in '([{<':
                stack.append(char)
            elif char in ')]}>':
                if stack and stack[-1] == bracket_pairs[char]:
                    stack.pop()
        
        # 检查剩余序列是否是唯一的完成方式
        remaining = sequence[cut_point:]
        required_closing = []
        
        # 反转stack以得到正确的闭合顺序
        while stack:
            char = stack.pop()
            for close, open in bracket_pairs.items():
                if open == char:
                    required_closing.append(close)
                    break
        
        # 检查剩余序列是否完全匹配所需的闭合括号
        return ''.join(required_closing) == remaining

    def _generate_valid_sequence_with_unique_completion(self, total_length: int, cut_point: int, nesting_depth: int = 0) -> str:
        """
        生成在指定截取点具有唯一完成方式的合法括号序列
        
        @param total_length: 目标总长度
        @param cut_point: 截取点
        @param nesting_depth: 要求的嵌套深度
        @return: 生成的序列
        """
        max_attempts = 100  # 最大尝试次数
        
        for _ in range(max_attempts):
            try:
                # 确保长度为偶数
                if total_length % 2 != 0:
                    total_length -= 1
                
                # 初始化序列生成
                sequence = []
                stack = []
                current_depth = 0
                max_depth = 0
                
                # 计算需要生成的左括号数量
                left_count = total_length // 2
                
                # 如果需要达到特定的嵌套深度，先生成嵌套结构
                if nesting_depth > 0:
                    # 生成嵌套结构
                    for _ in range(nesting_depth):
                        bracket = random.choice(self.used_brackets)
                        sequence.append(bracket[0])
                        stack.append(bracket)
                        current_depth += 1
                        max_depth = max(max_depth, current_depth)
                        left_count -= 1
                
                # 生成剩余的序列
                while left_count > 0 or stack:
                    if left_count > 0 and (len(stack) == 0 or random.random() < 0.5):
                        # 添加左括号
                        bracket = random.choice(self.used_brackets)
                        sequence.append(bracket[0])
                        stack.append(bracket)
                        current_depth += 1
                        max_depth = max(max_depth, current_depth)
                        left_count -= 1
                    elif stack:
                        # 添加右括号
                        bracket = stack.pop()
                        sequence.append(bracket[1])
                        current_depth -= 1
                
                # 验证序列长度和嵌套深度
                if len(sequence) != total_length:
                    raise ValueError("生成的序列长度不符合要求")
                if nesting_depth > 0 and max_depth < nesting_depth:
                    raise ValueError("生成的序列嵌套深度不足")
                
                # 验证cut_point的位置是否合适
                if len(sequence) < cut_point:
                    raise ValueError("截取点超出序列长度")
                
                result = ''.join(sequence)
                
                # 验证是否具有唯一完成方式
                if not self._check_unique_completion(result, cut_point):
                    raise ValueError("序列不具有唯一完成方式")
                
                return result
                
            except ValueError:
                continue
        
        raise ValueError("无法生成满足要求的序列")

    def _verify_unique_completion(self, prefix: str) -> bool:
        """
        验证前缀是否只有一种完成方式
        
        @param prefix: 需要验证的前缀
        @return: 是否只有一种完成方式
        """
        # 统计每种括号的未配对数量
        stack = []
        bracket_pairs = {')': '(', ']': '[', '}': '{', '>': '<'}
        
        for char in prefix:
            if char in '([{<':
                # 添加左括号
                stack.append(char)
            elif char in ')]}>':
                # 尝试配对右括号
                if stack and stack[-1] == bracket_pairs[char]:
                    stack.pop()
                else:
                    # 错误的配对
                    return False
        
        # 检查是否存在已经配对的括号
        # 如果在前缀中有完整的括号对，那么就可能有多种完成方式
        balanced_pairs = 0
        for i in range(len(prefix)-1):
            for left, right in self.brackets:
                if prefix[i] == left and prefix[i+1] == right:
                    balanced_pairs += 1
                    
        # 如果存在完整的括号对，并且还有未配对的括号，那么可能有多种完成方式
        return balanced_pairs == 0 or len(stack) == 0

    def generate(self, num_of_questions: int = 100, max_attempts: int = 100,
                 n_types: int = 3, total_length: int = 0, to_fill_length: int = 0,
                 nesting_depth: int = 0):
        """
        生成Dyck Language游戏的题目
        
        @param num_of_questions: 要生成的题目数量
        @param max_attempts: 每个题目的最大尝试次数
        @param n_types: 使用的括号类型数量（1-6）
        @param total_length: 完整序列的总长度，如果为0则随机生成
        @param to_fill_length: 需要填充的长度，如果为0则随机生成
        @param nesting_depth: 要求的嵌套深度，如果为0则不限制
        @return: 生成的题目列表
        """
        from games.tasks.dyck_language.scripts.dyck_language_prompt import prompt_dyck_language
        # 参数校验
        if n_types < 1 or n_types > 6:
            raise ValueError("括号类型数量必须在1-6之间")
        if total_length < 0:
            raise ValueError("总长度不能为负数")
        if to_fill_length < 0:
            raise ValueError("填充长度不能为负数")
        if nesting_depth < 0:
            raise ValueError("嵌套深度不能为负数")
        if nesting_depth > 0 and total_length > 0 and nesting_depth > total_length // 2:
            raise ValueError("嵌套深度不能大于总长度的一半")
            
        # 选择要使用的括号类型
        self.used_brackets = self.brackets[:n_types]
        
        game_data_list = []
        generated_sequences = set()
        total_attempts = 0
        
        while len(game_data_list) < num_of_questions and total_attempts < max_attempts:
            try:
                total_attempts += 1
                
                # 确定序列长度
                current_total_length = total_length
                if current_total_length <= 0:
                    current_total_length = random.randint(4 * n_types, 8 * n_types) * 2  # 确保是偶数
                elif current_total_length % 2 != 0:
                    current_total_length -= 1  # 如果是奇数，减一使其成为偶数
                
                # 确定填充长度（右序列长度）
                current_fill_length = to_fill_length
                if current_fill_length <= 0:
                    current_fill_length = random.randint(
                        max(1, int(current_total_length * 0.2)),  # 至少要有1个右括号
                        min(int(current_total_length * 0.5), current_total_length // 2)
                    )
                
                # 计算截取点
                cut_point = current_total_length - current_fill_length
                
                # 生成序列
                sequence = self._generate_valid_sequence_with_unique_completion(
                    current_total_length, cut_point, nesting_depth
                )
                
                # 检查序列是否重复
                if sequence in generated_sequences:
                    continue
                    
                generated_sequences.add(sequence)
                
                # 截取序列
                question_sequence = sequence[:cut_point]
                
                # 生成问题描述
                question = prompt_dyck_language(question_sequence, random.choice([True, False]))
                
                # 创建游戏数据
                game_data = Data(
                    question=question,
                    answer=sequence,
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "full_sequence": sequence,
                        "question_sequence": question_sequence,
                        "n_types": n_types,
                        "total_length": current_total_length,  # 使用调整后的长度
                        "fill_length": current_fill_length,
                        "nesting_depth": nesting_depth,
                    }
                )
                
                game_data_list.append(game_data)
                
            except Exception as e:
                print(f"生成题目时出错: {e}")
                continue
                
        if len(game_data_list) < num_of_questions:
            print(f"警告: 只能生成 {len(game_data_list)}/{num_of_questions} 条游戏数据")
        
        return game_data_list
            
    def extract_answer(self, test_solution: str) -> str:
        """
        从模型的回答中提取括号序列答案
        
        @param test_solution: 模型的完整回答
        @return: 提取的答案
        """
        if not test_solution:
            return ""
            
        print(f"原始回答:\n{test_solution}")
            
        def clean_text(text: str) -> str:
            """清理文本，处理转义字符和空白字符"""
            # 移除所有空白字符（包括换行符、制表符等）
            text = ''.join(text.split())
            
            # 处理转义序列
            text = text.replace('\\n', '')
            text = text.replace('\\t', '')
            text = text.replace('\\r', '')
            text = text.replace('\\\\', '\\')
            
            # 如果文本被引号包围，且引号不是括号序列的一部分，则移除外层引号
            if len(text) >= 2:
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1]
                elif text.startswith("'") and text.endswith("'"):
                    text = text[1:-1]
            
            return text
            
        def is_valid_sequence(text: str) -> bool:
            """检查是否是有效的括号序列"""
            if not text:
                return False
                
            # 检查是否只包含括号字符
            bracket_chars = set('()[]{}<>')
            if not all(c in bracket_chars for c in text):
                return False
                
            # 检查括号匹配
            stack = []
            bracket_pairs = {')': '(', ']': '[', '}': '{', '>': '<'}
            
            for char in text:
                if char in '([{<':
                    stack.append(char)
                elif char in ')]}>':
                    if stack and stack[-1] == bracket_pairs[char]:
                        stack.pop()
                    else:
                        return False
                        
            return len(stack) == 0
        
        # 在清理后的文本中查找最长的有效括号序列
        print("尝试在清理后的文本中查找有效括号序列")
        cleaned_text = clean_text(test_solution)
        
        # 使用滑动窗口查找最长的有效括号序列
        max_length = 0
        best_sequence = ""
        
        for i in range(len(cleaned_text)):
            for j in range(i + 2, len(cleaned_text) + 1):  # 至少需要两个字符
                potential_sequence = cleaned_text[i:j]
                if is_valid_sequence(potential_sequence) and len(potential_sequence) > max_length:
                    max_length = len(potential_sequence)
                    best_sequence = potential_sequence
                    
        if best_sequence:
            print(f"找到有效的括号序列: {best_sequence}")
            return best_sequence
            
        print("未找到有效答案")
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dyck Language游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个题目的最大尝试次数")
    parser.add_argument("--n_types", type=int, default=3, help="使用的括号类型数量（1-6）")
    parser.add_argument("--total_length", type=int, default=0, help="完整序列的总长度，如果为0则随机生成")
    parser.add_argument("--to_fill_length", type=int, default=0, help="需要填充的长度，如果为0则随机生成")
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建游戏实例
    game = DyckLanguage()
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts,
        n_types=args.n_types,
        total_length=args.total_length,
        to_fill_length=args.to_fill_length,
    )
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据")
    
    # 创建嵌套目录结构
    nested_dir = data_dir / f"num_of_data_{args.num_of_data}" / f"n_types_{args.n_types}" / f"total_length_{args.total_length}" / f"to_fill_length_{args.to_fill_length}"
    if not nested_dir.exists():
        nested_dir.mkdir(parents=True, exist_ok=True)

    # 设置输出文件名
    output_file = nested_dir / f"dyck_language_{args.num_of_data}.jsonl"
    
    # 将数据保存到文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"游戏数据已保存到 {output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}") 
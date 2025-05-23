import random
import re
import uuid
import argparse
import json
import pathlib
import os
from typing import List, Tuple, Dict, Any, Set
import string

from games.base.game import Game
from base.data import Data
from games.tasks.dyck_language_reasoning_errors.scripts.dyck_language_reasoning_errors_verifier import DyckLanguageReasoningErrorsVerifier
from games.tasks.dyck_language_reasoning_errors.scripts.dyck_language_reasoning_errors_prompt import prompt_dyck_language_reasoning_errors

class DyckLanguageReasoningErrors(Game):
    """
    Dyck语言推理错误识别游戏类
    """
    def __init__(self):
        """
        初始化Dyck语言推理错误识别游戏
        """
        super().__init__("Dyck Language Reasoning Errors", DyckLanguageReasoningErrorsVerifier)
        # 括号对定义
        self.brackets = [
            ('(', ')'),
            ('[', ']'),
            ('{', '}'),
            ('<', '>')
        ]
        
    def generate(self, num_of_questions: int = 100, max_attempts: int = 100,
                 n_types: int = 3, total_length: int = 20, n_errors: int = None):
        """
        生成Dyck语言推理错误识别游戏的题目
        
        @param num_of_questions: 要生成的题目数量
        @param max_attempts: 每个题目的最大尝试次数
        @param n_types: 括号种类数量 (1-4)
        @param total_length: 括号序列的总长度
        @param n_errors: 错误思考过程的数量，如果为None则随机1-5个错误
        @return: 生成的题目列表
        """
        # 参数校验
        if n_types < 1 or n_types > 4:
            raise ValueError("括号种类数量必须在1到4之间")
        if total_length < 2:
            raise ValueError("括号序列的总长度必须至少为2")
        if n_errors is not None and (n_errors < 0 or n_errors > 10):
            raise ValueError("错误思考过程的数量必须在0到10之间")
        
        game_data_list = []
        generated_sequences = set()
        attempts = 0
        
        while len(game_data_list) < num_of_questions and attempts < max_attempts:
            try:
                attempts += 1
                
                # 选择括号种类
                selected_brackets = random.sample(self.brackets[:n_types], n_types)
                
                # 生成有效的Dyck语言序列
                dyck_sequence = self._generate_valid_dyck_sequence(selected_brackets, total_length)
                
                # 检查是否重复
                if dyck_sequence in generated_sequences:
                    continue
                
                generated_sequences.add(dyck_sequence)
                
                # 生成包含错误的推理步骤
                thoughts, error_indices = self._generate_thoughts_with_errors(dyck_sequence, n_errors, selected_brackets)
                
                # 生成问题描述
                question = prompt_dyck_language_reasoning_errors(dyck_sequence, thoughts)
                
                # 将错误索引转换为答案字符串
                answer = self._format_answer(error_indices)
                
                # 创建游戏数据
                game_data = Data(
                    question=question,
                    answer=answer,  # 保存正确答案
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "dyck_sequence": dyck_sequence,
                        "thoughts": thoughts,
                        "error_indices": error_indices,
                        "n_types": n_types,
                        "total_length": total_length,
                        "n_errors": len(error_indices),
                    }
                )
                
                game_data_list.append(game_data)
                
            except Exception as e:
                print(f"生成题目时出错: {e}")
                continue
                
        if len(game_data_list) < num_of_questions:
            print(f"警告: 只能生成 {len(game_data_list)}/{num_of_questions} 条游戏数据")
        
        return game_data_list
    
    def _generate_valid_dyck_sequence(self, selected_brackets: List[Tuple[str, str]], total_length: int) -> str:
        """
        生成有效的Dyck语言序列
        
        @param selected_brackets: 选择的括号种类列表
        @param total_length: 序列的总长度
        @return: 生成的Dyck语言序列
        """
        # 确保长度为偶数
        if total_length % 2 != 0:
            total_length += 1
        
        # 初始化空序列
        sequence = []
        stack = []
        
        # 记录剩余需要添加的字符数
        remaining = total_length
        
        while remaining > 0:
            # 如果栈为空或者随机决定添加开括号（且剩余长度允许）
            if not stack or (random.random() < 0.5 and remaining > len(stack) * 2):
                # 随机选择一种括号类型
                bracket_type = random.choice(selected_brackets)
                # 添加开括号
                sequence.append(bracket_type[0])
                # 将对应的闭括号压入栈
                stack.append(bracket_type[1])
            else:
                # 弹出栈顶的闭括号并添加到序列中
                sequence.append(stack.pop())
            
            remaining -= 1
        
        # 处理栈中剩余的闭括号
        while stack:
            sequence.append(stack.pop())
        
        return ''.join(sequence)
    
    def _generate_thoughts_with_errors(self, dyck_sequence: str, n_errors: int = None, selected_brackets: List[Tuple[str, str]] = None) -> Tuple[List[str], List[int]]:
        """
        生成包含错误的推理步骤
        
        @param dyck_sequence: Dyck语言序列
        @param n_errors: 需要生成的错误数量，如果为None则随机1-5个
        @param selected_brackets: 选择的括号种类列表
        @return: (思考步骤列表, 错误步骤索引列表)
        """
        # 确定错误数量
        if n_errors is None:
            n_errors = random.randint(1, 5)
        
        # 初始化思考步骤列表
        thoughts = []
        error_indices = []
        
        # 添加初始思考
        thoughts.append("我们应该逐个处理输入并跟踪栈的配置。")
        thoughts.append("栈: 空")
        
        # 用于正确处理序列的栈
        correct_stack = []
        # 用于生成可能包含错误的思考步骤的栈
        current_stack = []
        
        # 遍历序列中的每个字符
        chars_with_indices = list(enumerate(dyck_sequence))
        
        # 如果n_errors大于0且小于序列长度，选择指定数量的位置添加错误
        if n_errors > 0 and n_errors <= len(chars_with_indices):
            # 选择在哪些位置添加错误
            error_positions = random.sample(range(len(chars_with_indices)), min(n_errors, len(chars_with_indices)))
        else:
            error_positions = []
        
        for i, char in enumerate(dyck_sequence):
            # 正确的处理逻辑
            if char in "([{<":
                correct_stack.append(char)
            else:
                if correct_stack:
                    last_char = correct_stack.pop()
                    # 检查是否匹配
                    if not self._is_matching_bracket(last_char, char):
                        # 这不应该发生，因为我们生成的是有效序列
                        correct_stack.append(last_char)
                        correct_stack.append(char)
            
            # 判断当前位置是否需要添加错误
            should_add_error = i in error_positions
            
            # 复制当前步骤的处理栈
            current_stack = correct_stack.copy()
            
            # 生成描述当前步骤的思考
            if should_add_error:
                # 生成错误的思考步骤
                error_thought, current_stack = self._generate_error_thought(char, current_stack, i, selected_brackets)
                # 检查错误是否导致栈状态变化
                if self._format_stack(current_stack) != self._format_stack(correct_stack):
                    thoughts.append(f"{char} ; 栈: {self._format_stack(current_stack)}")
                    error_indices.append(len(thoughts) - 1)  # 记录错误步骤的索引
                else:
                    # 如果错误没有导致栈状态变化，则使用正确的思考步骤
                    thoughts.append(f"{char} ; 栈: {self._format_stack(correct_stack)}")
            else:
                # 生成正确的思考步骤
                thoughts.append(f"{char} ; 栈: {self._format_stack(correct_stack)}")
        
        # 添加最终思考步骤
        if len(error_indices) < n_errors and random.random() < 0.5:
            # 有时添加错误的最终思考
            if correct_stack:
                thoughts.append(f"现在，我们已经到达结尾。最终栈是空的。")
                error_indices.append(len(thoughts) - 1)
            else:
                thoughts.append(f"现在，我们已经到达结尾。最终栈是不为空的。")
                error_indices.append(len(thoughts) - 1)
        else:
            # 添加正确的最终思考
            if correct_stack:
                thoughts.append(f"现在，我们已经到达结尾。最终栈是不为空的。")
            else:
                thoughts.append(f"现在，我们已经到达结尾。最终栈是空的。")
        
        # 确保至少有一个错误
        if len(error_indices) == 0 and n_errors > 0:
            # 如果没有错误，强制添加一个
            error_index = random.randint(2, len(thoughts) - 2)  # 避免修改第一个和最后一个思考
            thoughts[error_index] = self._make_error_in_thought(thoughts[error_index])
            error_indices.append(error_index)
        elif len(error_indices) > n_errors:
            # 如果错误太多，随机保留指定数量
            error_indices = random.sample(error_indices, n_errors)
        
        # 添加思考步骤编号
        numbered_thoughts = []
        for i, thought in enumerate(thoughts):
            numbered_thoughts.append(f"Thought {i+1}: {thought}")
        
        # 更新错误索引以匹配思考编号
        error_indices = [i+1 for i in error_indices]
        
        return numbered_thoughts, error_indices
    
    def _generate_error_thought(self, char: str, stack: List[str], position: int, selected_brackets: List[Tuple[str, str]]) -> Tuple[str, List[str]]:
        """
        生成错误的思考步骤
        
        @param char: 当前处理的字符
        @param stack: 当前栈状态的副本
        @param position: 字符在序列中的位置
        @param selected_brackets: 选择的括号种类列表
        @return: (错误的思考步骤, 修改后的栈)
        """
        error_type = random.choice([
            "wrong_pop",        # 错误地弹出栈顶元素
            "no_pop",           # 没有弹出应该弹出的元素
            "wrong_push",       # 错误地压入元素
            "stack_corruption"  # 栈状态损坏
        ])
        
        # 保存原始栈，以便检查是否确实引入了错误
        original_stack = stack.copy()
        max_attempts = 5
        
        # 从选定的括号类型中提取开括号和闭括号
        open_brackets = [bracket[0] for bracket in selected_brackets]
        close_brackets = [bracket[1] for bracket in selected_brackets]
        all_brackets = open_brackets + close_brackets
        
        for _ in range(max_attempts):
            # 复制原始栈进行修改
            modified_stack = original_stack.copy()
            
            if error_type == "wrong_pop" and modified_stack:
                # 错误地弹出栈顶元素
                modified_stack.pop()  # 移除实际元素
                if len(modified_stack) > 0:
                    # 确保栈不为空，再添加一个错误元素
                    modified_stack[-1] = random.choice(open_brackets)
                
            elif error_type == "no_pop" and char in close_brackets:
                # 没有弹出应该弹出的元素
                # 确保栈中至少有一个元素被修改
                if modified_stack:
                    modified_stack[-1] = random.choice(open_brackets)
                else:
                    modified_stack.append(random.choice(open_brackets))
                
            elif error_type == "wrong_push":
                # 错误地压入不应该压入的元素
                wrong_char = random.choice(all_brackets)
                modified_stack.append(wrong_char)
                
            elif error_type == "stack_corruption":
                # 栈状态损坏
                if modified_stack:
                    # 随机替换栈中的一个元素
                    idx = random.randint(0, len(modified_stack) - 1)
                    modified_stack[idx] = random.choice(all_brackets)
                else:
                    modified_stack.append(random.choice(open_brackets))
            
            # 检查是否确实引入了错误
            if self._format_stack(modified_stack) != self._format_stack(original_stack):
                return f"引入错误", modified_stack
            
            # 如果没有引入错误，尝试其他错误类型
            error_type = random.choice([
                "wrong_pop", "no_pop", "wrong_push", "stack_corruption"
            ])
        
        # 如果多次尝试后仍未引入明显错误，强制修改栈
        if original_stack:
            # 替换所有元素为随机括号
            modified_stack = [random.choice(all_brackets) for _ in original_stack]
            return f"强制引入错误", modified_stack
        else:
            # 栈为空，添加随机元素
            modified_stack = [random.choice(all_brackets)]
            return f"强制引入错误", modified_stack
    
    def _make_error_in_thought(self, thought: str) -> str:
        """
        在思考步骤中引入错误
        
        @param thought: 原始思考步骤
        @return: 包含错误的思考步骤
        """
        # 解析思考步骤
        parts = thought.split(" ; 栈: ")
        
        if len(parts) != 2:
            # 如果不是标准格式，直接返回
            return thought
        
        char, stack_str = parts
        
        # 获取所有可能的括号字符
        open_brackets = [bracket[0] for bracket in self.brackets]
        close_brackets = [bracket[1] for bracket in self.brackets]
        all_brackets = open_brackets + close_brackets
        
        # 修改栈状态
        if stack_str == "空":
            # 如果栈为空，添加一个随机字符
            new_stack = random.choice(open_brackets)
        elif stack_str == "":
            # 如果栈为空字符串，改为非空
            new_stack = random.choice(open_brackets)
        else:
            # 如果栈不为空，可能删除一个字符或添加一个字符
            if random.random() < 0.5 and len(stack_str) > 0:
                # 删除一个字符
                pos = random.randint(0, len(stack_str) - 1)
                new_stack = stack_str[:pos] + stack_str[pos+1:]
            else:
                # 添加一个随机字符
                pos = random.randint(0, len(stack_str))
                new_stack = stack_str[:pos] + random.choice(all_brackets) + stack_str[pos:]
        
        return f"{char} ; 栈: {new_stack}"
    
    def _is_matching_bracket(self, open_bracket: str, close_bracket: str) -> bool:
        """
        检查开闭括号是否匹配
        
        @param open_bracket: 开括号
        @param close_bracket: 闭括号
        @return: 是否匹配
        """
        bracket_pairs = dict([self.brackets[i] for i in range(len(self.brackets))])
        return bracket_pairs.get(open_bracket) == close_bracket
    
    def _format_stack(self, stack: List[str]) -> str:
        """
        格式化栈以供显示
        
        @param stack: 栈
        @return: 格式化的栈字符串
        """
        if not stack:
            return "空"
        return ''.join(stack)
    
    def _format_answer(self, error_indices: List[int]) -> str:
        """
        格式化答案字符串
        
        @param error_indices: 错误步骤的索引列表
        @return: 格式化的答案字符串
        """
        if not error_indices:
            return ""
        
        # 按照数字大小排序
        error_indices.sort()
        
        # 转换为字符串，使用英文逗号分隔
        return ",".join(map(str, error_indices))
    
    def extract_answer(self, test_solution: str) -> str:
        """
        从模型的回答中提取答案
        
        @param test_solution: 模型的完整回答
        @return: 提取的答案
        """
        if not test_solution:
            return ""
        
        # 标准化输入文本
        solution = test_solution.strip()
        
        # 检查是否为空答案或表示无问题的答案
        if solution == "" or solution.lower() in ["无问题", "no", "无错误", "none", "no errors", "no mistakes"]:
            return ""
            
        # 首先检查是否整个答案就是简单的数字列表（如 "7,9,12"）
        if re.match(r'^[0-9,，]+$', solution):
            return solution.replace('，', ',')
        
        # 提取数字列表
        # 查找最可能的数字列表答案
        num_list_pattern = r'([0-9]+(?:[,，][0-9]+)+)'
        num_list_match = re.search(num_list_pattern, solution)
        if num_list_match:
            answer = num_list_match.group(1).strip()
            answer = answer.replace('，', ',')
            return answer
            
        # 检查是否只有单个数字
        single_num_pattern = r'(?<!\d)([0-9]+)(?!\d)'
        single_num_match = re.search(single_num_pattern, solution)
        if single_num_match:
            return single_num_match.group(1)
            
        # 如果整个答案很短并且只包含一些基本字符，可能是一个格式不太规范的答案
        if len(solution) < 20:
            # 移除所有非数字和逗号的字符
            cleaned = re.sub(r'[^0-9,，]', '', solution)
            if cleaned:
                return cleaned.replace('，', ',')
                
        # 查找所有单独的数字
        all_nums = re.findall(r'(?<!\d)([1-9]\d*)(?!\d)', solution)
        if all_nums:
            # 去重并排序
            unique_nums = sorted(set(map(int, all_nums)))
            return ','.join(map(str, unique_nums))
            
        # 如果没有匹配到任何模式，返回空字符串
        return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dyck语言推理错误识别游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个题目的最大尝试次数")
    parser.add_argument("--n_types", type=int, default=3, help="括号种类数量 (1-4)")
    parser.add_argument("--total_length", type=int, default=20, help="括号序列的总长度")
    parser.add_argument("--n_errors", type=int, default=None, help="错误思考过程的数量，默认随机1-5个")
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建游戏实例
    game = DyckLanguageReasoningErrors()
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts,
        n_types=args.n_types,
        total_length=args.total_length,
        n_errors=args.n_errors
    )
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据")
    
    # 创建层级嵌套的数据目录
    base_data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not base_data_dir.exists():
        base_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建嵌套目录结构
    n_errors_part = f"n_errors_{args.n_errors}" if args.n_errors is not None else "n_errors_random"
    nested_dir = base_data_dir / f"num_of_data_{args.num_of_data}" / f"n_types_{args.n_types}" / f"total_length_{args.total_length}" / n_errors_part
    if not nested_dir.exists():
        nested_dir.mkdir(parents=True, exist_ok=True)
    
    # 嵌套目录中的输出文件
    nested_output_file = nested_dir / f"dyck_language_reasoning_errors_{args.num_of_data}.jsonl"
    
    # 将数据保存到文件
    try:
        
        # 同时保存到嵌套目录
        with open(nested_output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"游戏数据同时保存到 {nested_output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}") 
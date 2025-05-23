import random
import re
import uuid
import json
import argparse
import pathlib
import os
import itertools
import string
from typing import List, Tuple, Dict, Set
import operator

from games.base.game import Game
from base.data import Data
from games.tasks.cryptarithm.scripts.cryptarithm_verifier import CryptarithmVerifier
from games.tasks.cryptarithm.scripts.cryptarithm_prompt import prompt_cryptarithm

class Cryptarithm(Game):
    """
    密码算术游戏类，生成形如 word1 op1 word2 op2 ... wordn = result 的字母等式
    每个字母代表一个数字，不同字母代表不同数字
    """
    def __init__(self):
        """
        初始化密码算术游戏
        """
        super().__init__("Cryptarithm", CryptarithmVerifier)
        self.operators = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul
        }
        self.operator_symbols = {
            1: ['+', '-'],
            2: ['+', '-'],
            3: ['+', '-', '*']
        }
        
    def generate(self, num_of_questions: int = 100, max_attempts: int = 1000,
                 num_letter: int = 8, operator_num: int = 1, 
                 operator_level: int = 1):
        """
        生成密码算术游戏的题目
        
        @param num_of_questions: 要生成的题目数量
        @param max_attempts: 生成题目的最大尝试次数
        @param num_letter: 题目中不同字母的数量（1-9之间）
        @param operator_num: 等式中的计算次数
        @param operator_level: 计算字符难度 (1=加减, 2=加减, 3=加减乘)
        @return: 生成的题目列表
        """
        # 参数校验
        if num_letter < 1 or num_letter > 9:
            raise ValueError("不同字母的数量必须在1-9之间")
        if operator_num < 1:
            raise ValueError("操作符数量必须为正整数")
        if operator_level < 1 or operator_level > 3:
            raise ValueError("操作符难度必须在1-3之间")
            
        game_data_list = []
        attempts = 0
        
        while len(game_data_list) < num_of_questions and attempts < max_attempts:
            try:
                attempts += 1
                
                # 1. 随机选择num_letter个不同的数字
                digits = random.sample(range(10), min(num_letter, 10))
                
                # 2. 随机生成一个有效的密码算术等式（数字形式）
                equation_data = self._generate_valid_equation(
                    digits, operator_num, operator_level, max_attempts)
                
                if not equation_data:
                    continue
                    
                numbers, operators, used_digits_list = equation_data
                
                # 3. 验证等式中使用的数字数量是否满足要求
                all_digits_str = []
                for num in numbers:
                    all_digits_str.extend(list(str(num)))
                
                unique_digits = set(all_digits_str)
                if len(unique_digits) != num_letter:
                    continue
                
                # 4. 验证解的唯一性
                if not self._verify_unique_solution(numbers, operators):
                    continue
                
                # 5. 将数字转换为字母
                letter_words, digit_map = self._convert_to_letters(numbers)
                
                # 6. 生成问题描述（随机选择中文或英文）
                is_chinese = random.choice([True, False])
                question = self._generate_prompt(letter_words, operators, is_chinese)
                
                # 7. 构造答案字符串（数字形式的等式）
                answer = self._construct_answer(numbers, operators)
                
                # 8. 创建游戏数据
                game_data = Data(
                    question=question,
                    answer=answer,
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "numbers": numbers,
                        "letter_words": letter_words,
                        "operators": operators,
                        "digit_map": digit_map,
                        "num_letter": num_letter,
                        "operator_num": operator_num,
                        "operator_level": operator_level
                    }
                )
                
                game_data_list.append(game_data)
                
            except Exception as e:
                print(f"生成题目时出错: {e}")
                continue
                
        if len(game_data_list) < num_of_questions:
            print(f"警告: 只能生成 {len(game_data_list)}/{num_of_questions} 条游戏数据")
        
        return game_data_list
    
    def _generate_valid_equation(self, digits: List[int], operator_num: int, 
                                operator_level: int, max_attempts: int = 100) -> Tuple:
        """
        生成有效的密码算术等式
        
        算法流程:
        1. 根据操作符数量和难度随机生成操作符序列
        2. 为每个操作数生成一个多位数（确保没有前导零）
        3. 按照运算优先级计算结果
        4. 验证结果是否有效，包括:
           - 结果是正整数
           - 结果中的每个数字都在可用数字集合中
           - 确保使用了足够多的不同数字
        
        @param digits: 可用的数字列表
        @param operator_num: 操作符数量
        @param operator_level: 操作符难度
        @param max_attempts: 最大尝试次数
        @return: (numbers_list, operators_list, used_digits_list) 或 None，其中numbers_list包含所有参与计算的数字，operators_list包含所有操作符
        """
        # 最大尝试次数的计数器
        local_attempts = 0
        
        while local_attempts < max_attempts:
            local_attempts += 1
            
            available_operators = self.operator_symbols[operator_level]
            
            # 选择操作符
            operators = [random.choice(available_operators) for _ in range(operator_num)]
            
            # 跟踪每个数字的使用情况
            digit_usage_count = {digit: 0 for digit in digits}
            used_digits_list = []
            
            # 生成参与计算的数字列表
            numbers = []
            
            # 需要生成 operator_num + 1 个数字
            for i in range(operator_num + 1):
                # 随机决定数字长度
                # 10%概率随机1-2位，90%概率随机3-6位
                if random.random() < 0.1:
                    num_length = random.randint(1, 2)  # 10%概率随机1-2位
                else:
                    num_length = random.randint(3, 6)  # 90%概率随机3-6位
                
                # 生成一个n位数，确保第一位不是0
                number_digits = []
                
                # 先选择第一位（非零）
                non_zero_digits = [d for d in digits if d != 0]
                if not non_zero_digits:
                    continue  # 没有可用的非零数字，尝试下一次循环
                    
                first_digit = random.choice(non_zero_digits)
                number_digits.append(first_digit)
                digit_usage_count[first_digit] += 1
                used_digits_list.append(first_digit)
                
                # 选择剩余位数
                remaining_length = num_length - 1
                if remaining_length > 0:
                    for _ in range(remaining_length):
                        digit = random.choice(digits)  # 可以重复使用数字
                        number_digits.append(digit)
                        digit_usage_count[digit] += 1
                        used_digits_list.append(digit)
                
                # 将数字位转换为整数
                number = int(''.join(map(str, number_digits)))
                numbers.append(number)
            
            # 构建左式表达式
            left_expr = f"{numbers[0]}"
            for i in range(operator_num):
                left_expr += f" {operators[i]} {numbers[i+1]}"
            
            # 按照运算优先级计算结果（先乘除后加减）
            try:
                result = self._calculate_equation(numbers[:operator_num+1], operators)
            except Exception as e:
                print(f"计算等式时出错: {e}")
                continue
            
            # 检查结果是否合理（正整数）
            if result <= 0:
                continue
                
            # 将结果转换为数字列表并更新使用计数
            result_digits = [int(d) for d in str(result)]
            
            # 检查结果的数字是否都在可用数字集合中
            valid_result = True
            for d in result_digits:
                if d not in digits:
                    valid_result = False
                    break
                digit_usage_count[d] += 1
                used_digits_list.append(d)
            
            if not valid_result:
                continue
            
            # 添加结果到数字列表
            numbers.append(result)  # 添加结果
            
            # 完整等式
            equation = left_expr + f" = {result}"
            
            # 检查是否使用了足够多的不同数字（而不是要求所有数字都使用）
            unique_used_digits = set(used_digits_list)
            if len(unique_used_digits) < min(len(digits), 4):  # 至少使用4个不同的数字或所有可用数字
                continue
                
            # 成功生成有效等式
            print(f"尝试次数: {local_attempts}，成功生成等式: {equation}")
            print(f"使用的不同数字: {list(unique_used_digits)}，总共: {len(unique_used_digits)}个")
            
            # 返回用于构建等式的数字列表和操作符列表
            return (numbers, operators, used_digits_list)
        
        # 达到最大尝试次数仍未成功
        print(f"达到最大尝试次数({max_attempts})仍未能生成有效等式")
        return None
    
    def _convert_to_letters(self, numbers: List[int]) -> Tuple[List[str], Dict[str, int]]:
        """
        将数字转换为字母
        
        算法流程:
        1. 收集所有使用的数字
        2. 随机选择不同的字母与每个数字对应
        3. 构建每个数字对应的字母单词
        4. 创建字母到数字的映射（用于验证和答案）
        
        @param numbers: 数字列表
        @return: (字母单词列表, 字母到数字的映射)
        """
        # 收集所有用到的数字
        all_digits = set()
        for num in numbers:
            for digit in str(num):
                all_digits.add(int(digit))
                
        # 随机选择字母
        alphabet = random.sample(string.ascii_uppercase, len(all_digits))
        
        # 创建数字到字母的映射
        digit_to_letter = {digit: letter for digit, letter in zip(all_digits, alphabet)}
        
        # 转换每个数字为字母单词
        letter_words = []
        for num in numbers:
            word = ''.join(digit_to_letter[int(d)] for d in str(num))
            letter_words.append(word)
            
        # 创建字母到数字的映射（用于验证和答案）
        letter_to_digit = {letter: digit for digit, letter in digit_to_letter.items()}
        
        return letter_words, letter_to_digit
    
    def _generate_prompt(self, letter_words: List[str], operators: List[str], is_chinese: bool) -> str:
        """
        根据字母单词和操作符生成问题描述
        
        @param letter_words: 字母单词列表
        @param operators: 操作符列表
        @param is_chinese: 是否生成中文提示
        @return: 生成的问题描述
        """
        from games.tasks.cryptarithm.scripts.cryptarithm_prompt import prompt_cryptarithm
        return prompt_cryptarithm(letter_words, operators, is_chinese)
    
    def _verify_unique_solution(self, numbers: List[int], operators: List[str]) -> bool:
        """
        验证密码算术等式是否有唯一解
        
        采用完全枚举的方式，遍历所有可能的字母到数字的映射，
        检查是否只有一种映射方式使得等式成立
        
        算法流程:
        1. 收集等式中所有唯一的数字字符（视为字母）
        2. 为每个字母尝试分配0-9的数字，确保不同字母对应不同数字
        3. 对于每种可能的映射，测试等式是否成立
        4. 如果只有一种映射使等式成立，则解唯一
        
        @param numbers: 参与计算的数字列表
        @param operators: 操作符列表
        @return: 解是否唯一
        """
        # 检查当前等式是否成立
        result = self._calculate_equation(numbers[:-1], operators)
        if result != numbers[-1]:
            return False
            
        # 收集所有使用到的数字字符，并确定字母集合
        all_digits_str = []
        for num in numbers:
            all_digits_str.extend(list(str(num)))
            
        # 提取所有唯一的数字字符（等同于字母）
        unique_letters = set(all_digits_str)
        letter_list = list(unique_letters)  # 将字母集合转换为列表以便于索引
        letter_count = len(letter_list)
        
        # 提取每个数字的第一个字符位置（用于检查前导零限制）
        first_positions = {}
        for num in numbers:
            num_str = str(num)
            if len(num_str) > 1:  # 只有多位数才有前导零限制
                first_char = num_str[0]
                if first_char not in first_positions:
                    first_positions[first_char] = True
        
        # 将数字字符串转换为具体的数字
        def evaluate_number(num_str, digit_map):
            result = 0
            for c in num_str:
                result = result * 10 + digit_map[c]
            return result
        
        # 检查等式是否成立
        def is_equation_valid(digit_map):
            # 构建各个部分的数字
            equation_numbers = []
            for num in numbers:
                num_str = str(num)
                equation_numbers.append(evaluate_number(num_str, digit_map))
            
            # 检查等式计算结果
            result = self._calculate_equation(equation_numbers[:-1], operators)
            return result == equation_numbers[-1]
        
        # 使用回溯算法遍历所有可能的数字组合
        def backtrack(index, used_digits, digit_map):
            nonlocal valid_mappings
            
            # 如果找到两个以上的有效解，直接返回False
            if len(valid_mappings) > 1:
                return
                
            # 如果已经为所有字母都分配了数字
            if index == letter_count:
                # 检查当前映射是否构成有效等式
                if is_equation_valid(digit_map):
                    valid_mappings.append(digit_map.copy())
                return
                
            current_letter = letter_list[index]
            
            # 如果当前字母是某个多位数的第一个字符，不能为0
            if current_letter in first_positions:
                start_digit = 1  # 跳过0
            else:
                start_digit = 0
                
            # 尝试所有可能的数字（0-9）
            for digit in range(start_digit, 10):
                # 如果该数字尚未被使用
                if digit not in used_digits:
                    # 将字母映射到数字
                    digit_map[current_letter] = digit
                    used_digits.add(digit)
                    
                    # 递归处理下一个字母
                    backtrack(index + 1, used_digits, digit_map)
                    
                    # 回溯，移除当前映射
                    used_digits.remove(digit)
                    digit_map.pop(current_letter)
        
        # 存储所有有效的字母到数字的映射
        valid_mappings = []
        
        # 从第一个字母开始回溯
        backtrack(0, set(), {})
        
        # 如果只有一种有效的映射方式，则解唯一
        return len(valid_mappings) == 1
    
    def _calculate_equation(self, operands: List[int], operators: List[str]) -> int:
        """
        计算等式的结果，遵循标准数学运算优先级（先乘除后加减）
        
        算法流程:
        1. 先处理所有乘法操作
        2. 然后从左到右处理加减法操作
        
        @param operands: 操作数列表
        @param operators: 操作符列表
        @return: 计算结果
        """
        if len(operands) != len(operators) + 1:
            raise ValueError("操作数数量必须比操作符数量多1")
            
        # 按照优先级计算（先乘法，后加减法）
        # 复制操作数和操作符列表
        ops = operators.copy()
        nums = operands.copy()
        
        # 先处理乘法
        i = 0
        while i < len(ops):
            if ops[i] == '*':
                # 执行乘法并替换结果
                nums[i] = nums[i] * nums[i+1]
                # 移除已使用的操作数
                nums.pop(i+1)
                # 移除已处理的操作符
                ops.pop(i)
            else:
                i += 1
                
        # 然后从左到右处理加减法
        result = nums[0]
        for i in range(len(ops)):
            if ops[i] == '+':
                result += nums[i+1]
            elif ops[i] == '-':
                result -= nums[i+1]
                
        return result
    
    def _construct_answer(self, numbers: List[int], operators: List[str]) -> str:
        """
        构造答案字符串（数字形式的等式）
        
        @param numbers: 参与计算的数字列表
        @param operators: 操作符列表
        @return: 数字形式的等式
        """
        equation = str(numbers[0])
        
        for i, op in enumerate(operators):
            equation += f" {op} {numbers[i+1]}"
            
        equation += f" = {numbers[-1]}"
        
        return equation
        
    def extract_answer(self, test_solution: str):
        """
        从模型的回答中提取答案
        
        @param test_solution: 模型的完整回答
        @return: 提取的答案
        """
        if not test_solution:
            return ""
        
        # 首先规范化空格和其他格式
        # 处理全大写的情况
        test_solution = test_solution.replace("THE ANSWER IS", "The answer is")
        test_solution = test_solution.replace("答案是：", "答案是:")
        test_solution = test_solution.replace("答案：", "答案:")
        
        # 尝试匹配数字等式模式（支持多个操作符和负数）
        # 例如：123 + 456 = 579 或 12 + 34 - 5 = 41 或 123 + 456 - 789 = -210
        equation_patterns = [
            r'(\d+(?:\s*(?:\+|\-|\*)\s*\d+)+\s*=\s*-?\d+)',  # 匹配包含多个操作符的等式，结果可能为负
            r'(\d+(?:\s*(?:\+|\-|\*)\s*\d+)+\s*=\s*-?\d+)[.。]*$',  # 结尾的等式，结果可能为负
            r'(\d+\s*(?:\+|\-|\*)\s*\d+\s*=\s*-?\d+)'  # 匹配简单等式，结果可能为负
        ]
        
        for pattern in equation_patterns:
            matches = re.findall(pattern, test_solution)
            if matches:
                # 取最后一个匹配结果
                return matches[-1].strip()
        
        # 中文答案提取模式
        cn_patterns = [
            r'答案是[：:]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'答案[：:]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'我的答案是[：:]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'正确答案[：:]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'数字等式是[：:]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'数字等式为[：:]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'等式为[：:]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'等式是[：:]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'结果是[：:]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'结果为[：:]\s*([0-9\s\+\-\*=]+)[.。]*$'
        ]
        
        # 英文答案提取模式
        en_patterns = [
            r'[Tt]he answer is[：:=]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'[Tt]he answer[：:=]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'[Aa]nswer[：:=]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'[Mm]y answer is[：:=]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'[Tt]he final answer is[：:=]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'[Tt]he equation is[：:=]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'[Tt]he result is[：:=]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'[Tt]he numeric equation is[：:=]\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'[Tt]herefore,\s*([0-9\s\+\-\*=]+)[.。]*$',
            r'[Ss]o,\s*([0-9\s\+\-\*=]+)[.。]*$'
        ]
        
        # 尝试匹配所有模式
        patterns = cn_patterns + en_patterns
        
        for pattern in patterns:
            matches = re.findall(pattern, test_solution, re.DOTALL)
            if matches:
                answer = matches[-1].strip()
                # 移除美元符号（常用于标记LaTeX数学表达式）和句号
                answer = answer.replace("$", "").replace("。", "").replace(".", "")
                
                # 检查是否是有效等式（结果可能为负）
                if re.match(r'\d+(?:\s*(?:\+|\-|\*)\s*\d+)+\s*=\s*-?\d+', answer):
                    return answer
                
        # 如果上述模式都没有匹配到，尝试从最后一行提取等式
        lines = test_solution.strip().split('\n')
        for line in reversed(lines):  # 从最后一行开始向上查找
            equation_match = re.search(r'\d+(?:\s*(?:\+|\-|\*)\s*\d+)+\s*=\s*-?\d+', line)
            if equation_match:
                return equation_match.group(0)
        
        # 尝试从文本中提取任何看起来像等式的内容
        general_equation_pattern = r'\d+\s*(?:\+|\-|\*)\s*\d+\s*=\s*-?\d+'
        all_equations = re.findall(general_equation_pattern, test_solution)
        if all_equations:
            # 返回最后一个找到的等式
            return all_equations[-1]
        
        # 如果没有匹配到任何模式，返回空字符串
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="密码算术游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个题目的最大尝试次数")
    parser.add_argument("--num_letter", type=int, default=8, help="题目中不同字母的数量(1-9)")
    parser.add_argument("--operator_num", type=int, default=1, help="等式中的计算次数")
    parser.add_argument("--operator_level", type=int, default=1, help="计算字符难度(1=加减,2=加减,3=加减乘)")
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建输出目录
    output_dir = data_dir / f"num_letter_{args.num_letter}/operator_num_{args.operator_num}/operator_level_{args.operator_level}/num_of_data_{args.num_of_data}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置输出文件名
    output_file = output_dir / "data.jsonl"
    
    # 创建游戏实例
    game = Cryptarithm()
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts,
        num_letter=args.num_letter,
        operator_num=args.operator_num,
        operator_level=args.operator_level
    )
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据")
    
    # 将数据保存到文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"游戏数据已保存到 {output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}") 
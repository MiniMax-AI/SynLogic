
import random
import numpy as np
import re
import uuid
import json
import argparse
import pathlib
import os
from typing import List, Tuple, Optional

from games.base.game import Game
from base.data import Data
from games.tasks.math_path.scripts.math_path_verifier import MathPathVerifier
from games.tasks.math_path.scripts.math_path_prompt import prompt_mathPath

class MathPath(Game):
    """
    MathPath游戏类
    """
    def __init__(self):
        """
        初始化MathPath游戏
        """
        super().__init__("Math_Path", MathPathVerifier)
        
    def generate(self, num_of_questions: int = 100, max_attempts: int = 10000,
                 n: int = 4, x_prob: int=100):
        """
        生成MathPath游戏的题目
        
        @param num_of_questions: 要生成的题目数量
        @param max_attempts: 每个题目的最大尝试次数
        @param n: 运算表达式中的运算符号数量
        @param x_prob: 将运算表达式中的数字替换为?的概率，x_prob越大，表达式中的?数量越多，题目难度越大
        @return: 生成的题目列表
        """
        # 参数校验
        if n <= 2:
            raise ValueError("运算符号数量必须大于2")
        if x_prob<=0 or x_prob>100:
            raise ValueError("x_prob难度系数必须大于0，小于等于100.")
            
        game_data_list = []
        generated_matrices = set()
        attempts = 0
        
        while len(game_data_list) < num_of_questions and attempts < max_attempts:
            try:
                attempts += 1
                # 生成表达式与替换后的表达式
                ref_expr, query_expr = self._generate_valid_expr(n=n, x_prob=x_prob)
                
                # 检查重复
                if ref_expr in generated_matrices:
                    continue
                generated_matrices.add(ref_expr)
                
                # 随机选择中文或英文提示
                is_chinese = random.choice([True, False])
                
                # 生成问题描述
                question = prompt_mathPath(query_expr=query_expr, is_chinese=is_chinese)
                
                # 创建游戏数据
                game_data = Data(
                    question=question,
                    answer=ref_expr,  # 保存正确答案
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "ref_expr": ref_expr,
                        "query_expr": query_expr,
                        "n": n,
                        "x_prob": x_prob
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
    
    def _generate_valid_expr(self, n:int=3, x_prob:int=100):
        """
        生成一条游戏数据
        @param n: 运算表达式中的运算符号数量
        @param x_prob: 将运算表达式中的数字替换为?的概率，x_prob越大，表达式中的?数量越多，题目难度越大
        @return: 游戏数据
        """
        class ParserError(Exception):
            pass

        def generate_equation(num_operations: int) -> str:
            while True:
                numbers = [str(random.randint(0, 9)) for _ in range(num_operations + 1)]
                operators = [random.choice(['+', '-', '*', '/', '%']) for _ in range(num_operations)]
                expr_parts = [numbers[0]]
                for op, num in zip(operators, numbers[1:]):
                    expr_parts.extend([op, num])
                expr = ' '.join(expr_parts)
                expr = add_parentheses(expr)
                try:
                    value = evaluate_expression(expr)
                    return expr, value
                except ParserError:
                    continue

        def add_parentheses(expr: str) -> str:
            tokens = tokenize(expr)
            for _ in range(random.randint(0, 2)):  # Add up to 2 pairs of parentheses
                tokens = attempt_add_parentheses(tokens)
            return remove_redundant_parentheses(detokenize(tokens))

        def remove_redundant_parentheses(expr):
            if '((' in expr and '))' in expr:
                expr = expr.replace('((', '(')
                expr = expr.replace('))', ')')
                return expr
            return expr

        def attempt_add_parentheses(tokens: List[str]) -> List[str]:
            valid_ops = [i for i, t in enumerate(tokens) if t in '+-*/%' and i > 0 and i < len(tokens)-1]
            if not valid_ops:
                return tokens
            pos = random.choice(valid_ops)
            left_pos = pos - 1
            right_pos = pos + 1
            if left_pos < 0 or right_pos >= len(tokens):
                return tokens
            if not tokens[left_pos].isdigit() or not tokens[right_pos].isdigit():
                return tokens
            new_tokens = tokens[:left_pos] + ['('] + tokens[left_pos:right_pos+1] + [')'] + tokens[right_pos+1:]
            return new_tokens

        def tokenize(expr: str) -> List[str]:
            tokens = []
            current = []
            for c in expr:
                if c.isspace():
                    if current:
                        tokens.append(''.join(current))
                        current = []
                elif c in '()+-*/%':
                    if current:
                        tokens.append(''.join(current))
                        current = []
                    tokens.append(c)
                else:
                    current.append(c)
            if current:
                tokens.append(''.join(current))
            return tokens

        def detokenize(tokens: List[str]) -> str:
            expr = []
            for i, token in enumerate(tokens):
                if token in '()':
                    expr.append(token)
                else:
                    if expr and expr[-1] not in '+-*/%(':
                        expr.append(' ')
                    expr.append(token)
            return ''.join(expr).replace('( ', '(').replace(' )', ')')

        class Tokenizer:
            def __init__(self, tokens: List[str]):
                self.tokens = tokens
                self.pos = 0

            def next_token(self) -> Optional[str]:
                if self.pos < len(self.tokens):
                    token = self.tokens[self.pos]
                    self.pos += 1
                    return token
                return None

            def peek_token(self) -> Optional[str]:
                if self.pos < len(self.tokens):
                    return self.tokens[self.pos]
                return None

        def evaluate_expression(expr: str) -> int:
            tokens = tokenize(expr)
            tokenizer = Tokenizer(tokens)
            try:
                value = parse_expression(tokenizer)
                if tokenizer.peek_token() is not None:
                    raise ParserError("Unexpected tokens")
                return value
            except (ParserError, ValueError) as e:
                raise ParserError() from e

        def parse_expression(tokenizer: Tokenizer) -> int:
            value = parse_term(tokenizer)
            while True:
                op = tokenizer.peek_token()
                if op in ('+', '-'):
                    tokenizer.next_token()
                    right = parse_term(tokenizer)
                    value = value + right if op == '+' else value - right
                else:
                    break
            return value

        def parse_term(tokenizer: Tokenizer) -> int:
            value = parse_factor(tokenizer)
            while True:
                op = tokenizer.peek_token()
                if op in ('*', '/', '%'):
                    tokenizer.next_token()
                    right = parse_factor(tokenizer)
                    if op == '*':
                        value *= right
                    elif op == '/':
                        if right == 0:
                            raise ParserError("Division by zero")
                        if value % right != 0:
                            raise ParserError("Non-integer division")
                        value = value // right
                    elif op == '%':
                        if right == 0:
                            raise ParserError("Mod by zero")
                        value %= right
                else:
                    break
            return value

        def parse_factor(tokenizer: Tokenizer) -> int:
            token = tokenizer.next_token()
            if token is None:
                raise ParserError("Unexpected end of expression")
            if token == '(':
                value = parse_expression(tokenizer)
                if tokenizer.next_token() != ')':
                    raise ParserError("Missing closing parenthesis")
                return value
            elif token.isdigit():
                return int(token)
            else:
                raise ParserError(f"Unexpected token: {token}")

        def replace_num(expr, value, x_prob):
            x_prob /= 100
            replaced_expr = ''
            for s in expr:
                if s==' ':
                    continue
                elif '0'<=s<='9':
                    if random.random()<=x_prob:
                        replaced_expr += '?'
                    else:
                        replaced_expr += s
                else:
                    replaced_expr += s
            return f"{expr} = {value}", f"{replaced_expr} = {value}"
        
        expr, value = generate_equation(n)
        ref_expr, query_expr = replace_num(expr, value, x_prob)
        return ref_expr, query_expr

        
    def extract_answer(self, test_solution: str):
        """
        从模型的回答中提取答案（字符表达式）
        
        @param test_solution: 模型的完整回答
        @return: 提取的矩阵答案字符串
        """
        if not test_solution:
            return ""
        
        # 尝试提取Python代码块中的矩阵
        code_block_pattern = r'\[\[(.*?)\]\]'
        code_matches = re.findall(code_block_pattern, test_solution)
        
        if code_matches:
            # 使用最后一个匹配内容
            operation_expression = code_matches[-1].strip()
            return operation_expression
        
        # 如果所有方法都失败，返回空字符串
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Math_Path游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=10000, help="每个题目的最大尝试次数")
    parser.add_argument("--n", type=int, default=4, help="运算符号的数量")
    parser.add_argument("--x_prob", type=int, default=1, help="难度系数")
    args = parser.parse_args()
    
    # 创建数据目录
    base_data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not base_data_dir.exists():
        base_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建游戏实例
    game = MathPath()
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts,
        n=args.n,
        x_prob=args.x_prob,
    )
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据")

    # 创建嵌套目录结构
    nested_dir = base_data_dir / f"num_of_data_{args.num_of_data}" / f"n_{args.n}" / f"x_{args.x_prob}"
    if not nested_dir.exists():
        nested_dir.mkdir(parents=True, exist_ok=True)

    # 设置输出文件名
    output_file = nested_dir / f"math_path_{args.num_of_data}.jsonl"
    
    if os.path.exists(output_file):
        print(f"使用已有数据！")
    else:
        # 将数据保存到文件
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for game_data in game_data_list:
                    f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
            print(f"游戏数据已保存到 {output_file}")
        except Exception as e:
            print(f"保存数据时出错: {e}") 


#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import json
import os
import argparse
import pathlib
import re
import math
from collections import defaultdict
from base.data import Data
from tqdm import tqdm
from games.base.game import Game
from games.tasks.operation.scripts.operation_verifier import OperationVerifier
import sympy as sp  # 添加sympy库用于表达式检查
import time
from games.tasks.operation.scripts.operation_prompt import chinese_prompts, english_prompts
class Operation(Game):
    def __init__(self, num_symbols_range=(1, 3), max_operands=5,condition_rate=0.5,bracket_rate=0.3,abs_rate=0.4,definition_num_symbols_max=4,language="mixed"):
        """
        初始化符号重定义游戏
        
        @param num_symbols_range: 使用的符号数量范围 [最小值, 最大值]
        @param max_operands: 表达式中最大操作数数量
        """
        super().__init__("Operation", OperationVerifier)
        self.condition_rate = condition_rate
        self.bracket_rate = bracket_rate
        self.abs_rate = abs_rate
        self.num_symbols_min = num_symbols_range[0]
        self.num_symbols_max = num_symbols_range[1]
        self.max_operands = max_operands
        self.language = language
        self.definition_num_symbols_max = definition_num_symbols_max
        # 可用于重定义的符号池
        self.symbols = ["△", "▽", "◇", "○", "☆", "◎", "□", "♡", "♢", "⊕", "⊗", "⊙"]
        
        # 基础运算符号
        self.base_operations = ["+", "-", "*", "/", "%", "**"]
        
        # 可用条件类型
        self.condition_types = [
            "x和y都是偶数", 
            "x和y都是奇数",
            "x是偶数", 
            "x是奇数",
            "y是偶数", 
            "y是奇数",
            "x大于y", 
            "x小于y", 
            "x等于y",
            "x是3的倍数", 
            "y是3的倍数",
            "x是5的倍数", 
            "y是5的倍数",
            "x和y的和是偶数",
            "x和y的和是奇数"
        ]
        self.condition2english = {
            "x和y都是偶数": "x and y are both even",
            "x和y都是奇数": "x and y are both odd",
            "x是偶数": "x is even",
            "x是奇数": "x is odd",
            "y是偶数": "y is even",
            "y是奇数": "y is odd",
            "x大于y": "x is greater than y",
            "x小于y": "x is less than y",
            "x等于y": "x is equal to y",
            "x是3的倍数": "x is a multiple of 3",
            "y是3的倍数": "y is a multiple of 3",
            "x是5的倍数": "x is a multiple of 5",
            "y是5的倍数": "y is a multiple of 5",
            "x和y的和是偶数": "the sum of x and y is even",
            "x和y的和是奇数": "the sum of x and y is odd"
        }
        # 条件检查函数
        self.condition_checks = {
            "x和y都是偶数": lambda x, y: x % 2 == 0 and y % 2 == 0,
            "x和y都是奇数": lambda x, y: x % 2 != 0 and y % 2 != 0,
            "x是偶数": lambda x, y: x % 2 == 0,
            "x是奇数": lambda x, y: x % 2 != 0,
            "y是偶数": lambda x, y: y % 2 == 0,
            "y是奇数": lambda x, y: y % 2 != 0,
            "x大于y": lambda x, y: x > y,
            "x小于y": lambda x, y: x < y,
            "x等于y": lambda x, y: x == y,
            "x是3的倍数": lambda x, y: x % 3 == 0,
            "y是3的倍数": lambda x, y: y % 3 == 0,
            "x是5的倍数": lambda x, y: x % 5 == 0,
            "y是5的倍数": lambda x, y: y % 5 == 0,
            "x和y的和是偶数": lambda x, y: (x + y) % 2 == 0,
            "x和y的和是奇数": lambda x, y: (x + y) % 2 != 0
        }
        
    
    def generate(self, num_of_questions=100,max_attempts=1000):
        """
        生成多个符号重定义问题
        
        @param num_of_questions: 要生成的问题数量
        @return: 数据列表
        """
        outputs = []
        
        total_attempts = 0
        tqdm_bar = tqdm(total=num_of_questions,desc="生成题目")
        while len(outputs) < num_of_questions and total_attempts < max_attempts:
            total_attempts += 1

            # 生成一个问题
            result = self.generate_problem()
            
            # 如果生成成功，添加到输出列表
            if result is not None:
                try:
                    if abs(float(result['answer']))<100000:
                        outputs.append(Data(
                            question=result["question"],
                            answer=result["answer"],
                            difficulty=1,  # 固定难度值为1
                            metadata=result["metadata"]
                        ))
                        tqdm_bar.update(1)
                    else:
                        print(f"答案超出范围: {result['answer']}")
                        continue
                except Exception as e:
                    print(f"生成问题出错: {e}")
        
        tqdm_bar.close()
        
        print(f"成功生成 {len(outputs)}/{num_of_questions} 个问题，总尝试次数: {total_attempts}")
        return outputs
    
    def generate_problem(self):
        """
        生成一个符号重定义问题，有超时限制
        
        @return: 问题数据字典或None（超时时）
        """
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("生成问题超时")
        
        # 设置超时处理
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(3)  # 3秒超时
        
        try:
            # 1. 确定使用的符号数量
            num_symbols = random.randint(self.num_symbols_min, self.num_symbols_max)
            
            # 2. 从符号池中随机选择符号
            selected_symbols = random.sample(self.symbols, num_symbols)
            # 3. 为每个符号构造计算函数和定义规则
            symbol_definitions = {}
            for symbol in selected_symbols:
                symbol_definitions[symbol] = self._create_symbol_definition(symbol_definitions)
            # 4. 设置符号的优先级
            for i, symbol in enumerate(selected_symbols):
                precedence = random.randint(1, 5)
                symbol_definitions[symbol]["precedence"] = precedence
            # 5. 生成表达式
            expression, operands = self._generate_expression(list(symbol_definitions.keys()))
            # 6. 计算表达式结果
            result,simplified_expr = self._evaluate_expression(expression, symbol_definitions)
            
            # 检查是否计算成功
            if isinstance(result, str) and (result == "计算超时" or result == "计算错误"):
                raise TimeoutError("计算结果超时或错误")
            
            # 7. 构建题目文本
            question = self._format_question(expression, symbol_definitions)
            
            # 取消超时设置
            signal.alarm(0)
            
            return {
                "question": question,
                "answer": str(result),
                "metadata": {
                    "expression": expression,
                    "symbol_definitions": symbol_definitions,
                    "result": result,
                    "simplified_expr": simplified_expr
                }
            }
        except TimeoutError:
            # 取消超时设置
            signal.alarm(0)
            print("生成问题超时，跳过")
            return None
        except Exception as e:
            # 取消超时设置
            signal.alarm(0)
            print(f"生成问题出错: {e}")
            return None
    
    def _create_symbol_definition(self, symbol_definitions = None):
        """
        为一个符号创建定义规则
        
        @return: 符号定义字典
        """
        if symbol_definitions is None:
            symbol_definitions = {}
        
        # 创建基础定义
        definition = {
            "conditions": [],
            "associativity": "left",  
            "precedence": 0  # 优先级将在后面设置
        }
        if random.random() < self.condition_rate:
            # 选择条件并创建条件分支
            selected_conditions = random.choice(self.condition_types)
            # 为每个条件随机生成一个操作
            operation = self._generate_random_operation(symbol_definitions)
            definition["conditions"].append({
                "condition": selected_conditions,
                "operation": operation
            })

        # 添加默认操作 (当所有条件都不满足时)
        definition["default_operation"] = self._generate_random_operation(symbol_definitions)
        return definition
    
    def _generate_random_operation(self, symbol_definitions=None):
        """
        随机生成一个操作表达式，确保含有变量x和y且不会简化为常数
        
        @param custom_symbols: 可以在表达式中使用的自定义符号列表
        @return: 操作表达式字符串
        """
        
        # 定义基本运算符
        basic_ops = ['+', '-', '*', '/', '**']
        weights = [0.3, 0.3, 0.25, 0.1, 0.05]  # 加权概率
        
        # 如果没有传入自定义符号则初始化为空列表
        if symbol_definitions is None:
            symbol_definitions = {}
        
        custom_symbols = list(symbol_definitions.keys())
        
        while True:
            # 决定表达式中变量和常数的数量
            num_variables = random.randint(2, self.definition_num_symbols_max)
            num_constants = random.randint(0, self.definition_num_symbols_max-num_variables)
            total_elements = num_variables + num_constants
            
            # 创建元素列表
            elements = []
            for _ in range(num_variables):
                elements.append(random.choice(['x', 'y']))
            for _ in range(num_constants):
                elements.append(str(random.randint(1, 5)))
            
            # 随机打乱元素顺序
            random.shuffle(elements)
            
            # 插入运算符

            operators = []

            is_custom = False
            for _ in range(len(elements) - 1 - len(operators)):
                # 有一定概率使用自定义符号
                if custom_symbols and random.random() < 0.2 and not is_custom:
                    is_custom = True
                    operators.append(random.choice(custom_symbols))
                else:
                    operators.append(random.choices(basic_ops, weights=weights)[0])
            random.shuffle(operators)

            operators = [""]+operators

            if random.random() < self.bracket_rate:
                position1 = random.choice(range(len(operators)))
                position2 = random.choice(range(len(operators)))
                left_position = min(position1,position2)
                right_position = max(position1,position2)
                elements[left_position] = "(" + elements[left_position]
                elements[right_position] = elements[right_position] + ")"
                if random.random()<self.abs_rate:
                    elements[left_position] = "abs" + elements[left_position]

            # 组合成表达式
            expression = ""
            for i in range(len(operators)):
                expression += f" {operators[i]} {elements[i]}"
            
            if is_custom:
                original_expression = expression
                expression = self._simplify_mix_expression(expression, symbol_definitions)
            # 创建sympy符号变量并解析表达式
            x, y = sp.symbols('x y')
            
            # 处理函数
            expr_str = expression
            if "abs(" in expr_str:
                expr_str = expr_str.replace("abs(", "Abs(")
            
            # 将表达式字符串转换为sympy表达式
            expr = sp.sympify(expr_str)
            
            # 化简表达式
            simplified = sp.simplify(expr)
            
            # 检查表达式是否包含变量x和y
            variables = simplified.free_symbols
            has_x_y = sp.Symbol('x') in variables and sp.Symbol('y') in variables
            
            # 检查表达式是否为常数
            is_constant = simplified.is_constant()
            
            # 如果包含x和y且不是常数表达式，则返回
            if has_x_y and not is_constant:
                if is_custom:
                    return original_expression
                else:
                    return str(simplified)
                
    def check_number(self,token):
        try:
            return float(token)
        except:
            return "Not number"

    def _simplify_mix_expression(self, expression, symbol_definitions):
        """
        将包含自定义符号的表达式转换为基本运算符的等价表达式
        
        @param expression: 包含自定义符号的表达式字符串
        @param symbol_definitions: 符号定义的字典
        @return: 转换后的表达式字符串
        """
        if not expression:
            return expression
        
        # 将abs(替换为特殊标记，便于处理
        expression = expression.replace("abs(", "Abs(")
        
        # 使用正则表达式进行分词，支持负数、小数、科学计数法等
        tokens = re.findall(r'Abs\(|\*\*|\-?\d+\.\d+(?:[eE][\+\-]?\d+)?|\-?\d+(?:[eE][\+\-]?\d+)?|\(|\)|[a-zA-Z]+|[\+\-\*/\^%]|[^\s\w\+\-\*/\^%\(\)]+', expression)
        # 定义操作符优先级
        precedence = {
            '+': 1, '-': 1,
            '*': 2, '/': 2, '%': 2,
            '^': 3, '**': 3
        }
        
        # 添加自定义符号的优先级
        for symbol, definition in symbol_definitions.items():
            precedence[symbol] = definition["precedence"]
        # 初始化两个栈
        operand_stack = []    # 存储操作数(数字、变量、表达式)
        operator_stack = []   # 存储操作符
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # 处理操作数(数字、变量)
            if self.check_number(token) != "Not number" or token.isalpha():
                operand_stack.append(token)
            
            # 处理ABS_FUNC(和左括号
            elif token == "Abs(" or token == "(":
                operator_stack.append(token)
            
            # 处理右括号
            elif token == ")":
                while operator_stack and operator_stack[-1] not in ["(", "Abs("]:
                    self._process_top_operator(operand_stack, operator_stack, symbol_definitions)
                
                # 弹出左括号
                if operator_stack:
                    left_bracket = operator_stack.pop()
                    
                    # 如果是ABS_FUNC(，则添加abs函数
                    if left_bracket == "Abs(":
                        top_operand = operand_stack.pop()
                        operand_stack.append(f"Abs({top_operand})")
                else:
                    # 括号不匹配
                    raise ValueError("括号不匹配")
            
            # 处理操作符(包括自定义符号)
            else:
                # 处理前面优先级更高或相等的操作符
                while (operator_stack and operator_stack[-1] not in ["(", "Abs("] and 
                      (token not in precedence or 
                       (operator_stack[-1] in precedence and 
                        precedence[operator_stack[-1]] >= precedence[token]))):
                    self._process_top_operator(operand_stack, operator_stack, symbol_definitions)
                
                # 将当前操作符入栈
                operator_stack.append(token)
            i += 1
        # 处理剩余的操作符
        while operator_stack:
            if operator_stack[-1] in ["(", "Abs("]:
                operator_stack.pop()  # 丢弃剩余的左括号（通常是表达式错误导致的）
            else:
                self._process_top_operator(operand_stack, operator_stack, symbol_definitions)
        
        # 最终结果应该只有一个元素在操作数栈中
        if len(operand_stack) == 1:
            return operand_stack[0]
        else:
            raise ValueError(f"表达式解析错误: {operand_stack}")

    def _check_operator(self,operand,operators):
        for operator in operators:
            if operator in operand:
                return True
        return False

    def eval_operation(self,operation):
        try:
            return eval(operation)
        except:
            return "Can't eval"

    def _check_custom_operator(self,operand,operators):
        for operator in operators:
            if operator in operand:
                return True
        return False

    def check_int(self,operand):
        try:
            return int(operand)
        except:
            return "Not int"
    def _process_top_operator(self, operand_stack, operator_stack, symbol_definitions):
        """
        处理操作符栈顶的操作符
        
        @param operand_stack: 操作数栈
        @param operator_stack: 操作符栈
        @param symbol_definitions: 符号定义字典
        """
        operators = ["+", "-", "*", "/", "%", "^", "**"] + list(symbol_definitions.keys())
        if len(operator_stack) == 0 or len(operand_stack) < 2:
            return
        
        operator = operator_stack.pop()
        right_operand = operand_stack.pop()
        left_operand = operand_stack.pop()
        if self._check_operator(right_operand,operators):
            right_operand = f"({right_operand})"
        if self._check_operator(left_operand,operators):
            left_operand = f"({left_operand})"
        
        # 处理基本操作符
        if operator in ['+', '-', '*', '/', '%', '^', '**']:

            # 根据操作符组合表达式
            if operator == '+':
                result = f"{left_operand} + {right_operand}"
            elif operator == '-':
                result = f"{left_operand} - {right_operand}"
            elif operator == '*':
                result = f"{left_operand} * {right_operand}"
            elif operator == '/':
                result = f"{left_operand} / {right_operand}"
            elif operator == '%':
                result = f"{left_operand} % {right_operand}"
            elif operator in ['^', '**']:
                result = f"{left_operand} ** {right_operand}"
            

        
        # 处理自定义符号
        elif operator in symbol_definitions:
            # 获取操作定义
            definition = symbol_definitions[operator]
            if self.eval_operation(left_operand)!="Can't eval" and self.eval_operation(right_operand)!="Can't eval" and definition['conditions'] != []:
                left_operand = str(self.eval_operation(left_operand))
                right_operand = str(self.eval_operation(right_operand))
                condition = definition['conditions'][0]['condition']
                if self.check_int(left_operand) == "Not int" or self.check_int(right_operand) == "Not int":
                    operation = definition["default_operation"]
                else:
                    if self._check_condition(int(left_operand),int(right_operand),condition):
                        operation = definition["conditions"][0]["operation"]
                    else:
                        operation = definition["default_operation"]
            else:
                operation = definition["default_operation"]
            # 替换x和y
            result = operation.replace("x", "LEFT").replace("y", "RIGHT")
            result = result.replace("LEFT", left_operand).replace("RIGHT", right_operand)
            if self._check_custom_operator(result,symbol_definitions):
                result = self._simplify_mix_expression(result,symbol_definitions)
        # 添加括号以保持优先级
        result = f"({result})"
        
        # 入栈结果
        operand_stack.append(result)
    
    def _generate_expression(self, symbols):
        """
        生成包含给定符号的表达式
        
        @param symbols: 要使用的符号列表
        @return: (表达式字符串, 操作数列表)
        """
        # 确定操作数数量 (2-max_operands个操作数)
        num_operands = random.randint(len(symbols), len(symbols)+3)
        
        # 生成操作数
        operands = [random.randint(1, 10) for _ in range(num_operands)]
        
        # 生成表达式组件
        components = []
        operators = symbols
        for i in range(num_operands-len(symbols)-1):
            operators.append(random.choice(self.base_operations+symbols))
        random.shuffle(operators)

        for i in range(num_operands):
            components.append(str(operands[i]))
            # 不在最后一个操作数后添加符号
            if i < num_operands - 1:
                components.append(operators[i])
        
        # 组合成完整表达式
        expression = " ".join(components)
        
        return expression, operands
    
    def _evaluate_expression(self, expression, symbol_definitions):
        """
        计算表达式的值
        
        @param expression: 表达式字符串
        @param symbol_definitions: 符号定义字典
        @return: 计算结果
        """
        # 首先将自定义符号表达式转换为基础运算符表达式
        simplified_expr = self._simplify_mix_expression(expression, symbol_definitions)
        
        try:
            # 替换任何abs函数
            if "Abs(" in simplified_expr:
                simplified_expr = simplified_expr.replace("Abs(", "abs(")
            
            # 使用超时机制避免长时间计算
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("计算超时")
            
            # 设置5秒超时
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
            
            try:
                # 直接使用eval计算表达式
                result = eval(simplified_expr)
                # 取消超时
                signal.alarm(0)
                
                # 如果结果是整数，转换为整数类型
                if isinstance(result, float) and result.is_integer():
                    return int(result),simplified_expr
                elif isinstance(result, float):
                    return result,simplified_expr
                else:
                    return result,simplified_expr
                
            except TimeoutError:
                print(f"计算表达式超时: {simplified_expr}")
                return "计算超时",""
            finally:
                # 确保取消超时
                signal.alarm(0)
        
        except Exception as e:
            print(f"计算表达式时出错: {e}")
            print(f"原始表达式: {expression}")
            print(f"简化表达式: {simplified_expr}")
            
            # 如果计算失败，返回一个默认值
            return "计算错误",""
    

    
    def _check_condition(self, x, y, condition):
        """
        检查x和y是否满足给定条件
        
        @param x: 第一个操作数
        @param y: 第二个操作数
        @param condition: 条件字符串
        @return: 是否满足条件
        """
        if condition in self.condition_checks:
            return self.condition_checks[condition](x, y)
        return False
    
    
    def _format_question(self, expression, symbol_definitions):
        """
        格式化问题文本
        
        @param expression: 表达式字符串
        @param symbol_definitions: 符号定义字典
        @return: 格式化的问题文本
        """
        if self.language == "mixed":
            language = random.choice(["chinese", "english"])
        else:
            language = self.language
        if language == "chinese":
            question = f"定义 "
        else:
            question = f"Define "
        
        # 添加每个符号的定义说明
        for i, (symbol, definition) in enumerate(symbol_definitions.items()):
            if i > 0:
                if language == "chinese":
                    question += "和 "
                else:
                    question += "and "
            question += f"{symbol}"
            
            # 添加条件和操作
            if language == "chinese":
                question += "，规则如下：\n"
            else:
                question += "，the rules are as follows:\n"
            
            for j, condition_def in enumerate(definition["conditions"]):
                condition = condition_def["condition"]
                operation = condition_def["operation"]
                if language == "chinese":
                    question += f"当{condition}时，x {symbol} y = {operation}；\n"
                else:
                    question += f"when {self.condition2english[condition]}, x {symbol} y = {operation}；\n"
            
            # 添加默认操作
            default_operation = definition["default_operation"]
            if len(definition["conditions"]) == 0:
                if language == "chinese":
                    question += f"实数域上，x {symbol} y = {default_operation}。\n"
                else:
                    question += f"on the real number field, x {symbol} y = {default_operation}。\n"
            else:
                if language == "chinese":
                    question += f"其他情况下，x {symbol} y = {default_operation}。\n"
                else:
                    question += f"otherwise, x {symbol} y = {default_operation}。\n"
        
        # 添加优先级和结合性信息
        if len(symbol_definitions) > 0:
            # 创建包括自定义符号和基础运算符的完整优先级列表
            all_operators = [
                {"symbol": "**", "precedence": 3},
                {"symbol": "*", "precedence": 2},
                {"symbol": "/", "precedence": 2},
                {"symbol": "%", "precedence": 2},
                {"symbol": "+", "precedence": 1},
                {"symbol": "-", "precedence": 1}
            ]
            
            # 添加自定义符号
            for symbol, definition in symbol_definitions.items():
                all_operators.append({
                    "symbol": symbol,
                    "precedence": definition["precedence"]
                })
            
            # 按优先级排序（从高到低）
            all_operators.sort(key=lambda x: x["precedence"], reverse=True)
            
            # 构建优先级说明
            if language == "chinese":
                question += "运算优先级："
            else:
                question += "The precedence of operations："
            current_precedence = all_operators[0]["precedence"]
            question += all_operators[0]["symbol"]
            
            for op in all_operators[1:]:
                if op["precedence"] == current_precedence:
                    question += " = " + op["symbol"]
                else:
                    question += " > " + op["symbol"]
                    current_precedence = op["precedence"]
            
            question += "。\n"
        
        # 添加括号说明
        if language == "chinese":
            question += "括号具有最高优先级，先计算括号内的表达式。\n"
        else:
            question += "Parentheses have the highest priority, and the expression inside the parentheses is calculated first.\n"
        
        # 添加要计算的表达式
        if language == "chinese":
            question += f"请计算表达式的值: {expression}"
        else:
            question += f"Please calculate the value of the expression: {expression}"
        
        if language == "chinese":
            question = random.choice(chinese_prompts).format(question=question)
        else:
            question = random.choice(english_prompts).format(question=question)
        return question
    
    def extract_answer(self,test_answer):
        return self.verifier.extract_answer(test_answer)
    def verify(self,data,test_answer):
        return self.verifier.verify(data,test_answer)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成符号重定义游戏数据")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--num_symbols_range", type=int, nargs=2, default=[4, 4], help="使用的符号数量范围 [最小值, 最大值]")
    parser.add_argument("--definition_num_symbols_max", type=int, default=5, help="定义中使用的符号数量最大值")
    parser.add_argument("--max_operands", type=int, default=5, help="表达式中最大操作数数量")
    parser.add_argument("--condition_rate", type=float, default=0.5, help="条件定义的概率")
    parser.add_argument("--debug", action="store_true", help="运行调试模式")
    parser.add_argument("--output", type=str, default="symbol_redefinition_data.json", help="输出文件名")
    parser.add_argument("--max_attempts", type=int, default=3000, help="每个题目的最大尝试次数")
    parser.add_argument("--language", type=str, default="mixed", help="语言")
    args = parser.parse_args()
    # 创建游戏实例
    game = Operation(
        num_symbols_range=args.num_symbols_range,
        max_operands=args.max_operands,
        definition_num_symbols_max=args.definition_num_symbols_max,
        condition_rate=args.condition_rate
    )
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"创建数据目录: {data_dir}")
    
    # 使用参数缩写构建文件名
    filename = f"data_sl{args.num_symbols_range[0]}-{args.num_symbols_range[1]}_op{args.max_operands}_dnm{args.definition_num_symbols_max}_cr{args.condition_rate}_{args.language}_n{args.num_of_data}.jsonl"
    output_file = data_dir / filename
    game_data_list = game.generate(num_of_questions=args.num_of_data, max_attempts=args.max_attempts)
    
    # 将数据保存到文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
    except Exception as e:
        print(e)

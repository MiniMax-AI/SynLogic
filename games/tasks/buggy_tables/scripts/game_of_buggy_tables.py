from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
import random
import copy
import os
import sys
import re
import uuid

# 移除任何手动添加的sys.path修改
from games.base.game import Game
from base.data import Data
from base.verifier import Verifier
from games.tasks.buggy_tables.scripts.handlers.tables_handler import generate_random_table, transform_to_column_major, transform_to_row_major
from games.tasks.buggy_tables.scripts.handlers.error_generator import apply_error_makers
from games.tasks.buggy_tables.scripts.handlers.calculate_req_generator import generate_and_execute_query
from games.tasks.buggy_tables.scripts.game_of_buggy_tables_verifier import BuggyTableVerifier
from games.tasks.buggy_tables.scripts.buggy_tables_prompt import get_bug_description, format_question_template

class GameOfBuggyTables(Game):
    """
    GameOfBuggyTables: Generates tables with bugs and queries to solve
    
    This game generates:
    1. Original correct tables
    2. Buggy versions of these tables with specific error types
    3. Query tasks to run on the corrected tables
    4. Expected answers for these queries
    """
    
    # Constants for the game
    VALID_BUG_TYPES = [
        'error',           # Replace values with ERROR
        'merge_rows',      # Merge two rows with '&&'
        'rotate_columns',  # Rotate each column i by i positions
        'rotate_rows',     # Rotate each row i by i positions
        'add_end_row',     # Add random values at the end of rows
        'add_end_column',  # Add random values at the end of columns
        'null'             # Replace values with NULL/None
    ]
    
    VALID_MAJOR_TYPES = ['col', 'row']
    
    def __init__(self, name="buggy_tables"):
        """
        Initialize the GameOfBuggyTables
        
        @param name: Name of the game
        """
        super().__init__(name, BuggyTableVerifier)
    
    def generate(self, num_of_questions: int = 100, max_attempts: int = 100, 
               bug_types: List[str] = None, num_rows_range: List[int] = None,
               bug_rate_range: List[float] = None, bug_weights: Dict[str, float] = None) -> List[Data]:
        """
        Generate game questions and answers
        
        @param num_of_questions: Number of questions to generate
        @param max_attempts: Maximum number of attempts to generate a valid question
        @param bug_types: List of bug types to use (defaults to all valid bug types)
        @param num_rows_range: Range for number of rows [min, max] (defaults to [25, 40])
        @param bug_rate_range: Range for bug rate [min, max] for 'error' and 'null' types (defaults to [0.05, 0.2])
        @param bug_weights: Dictionary of bug types to weights for weighted selection
        @return: List of Data objects containing question data
        """
        game_data_list = []
        zero_answer_list = []  # 存储答案为0.00的问题
        
        # Set of questions to ensure uniqueness
        question_set = set()
        
        # Use provided bug types or default to all valid types
        valid_bug_types = bug_types if bug_types is not None else self.VALID_BUG_TYPES
        
        # Use provided num_rows_range or default to [25, 40]
        min_rows, max_rows = (25, 40) if num_rows_range is None else (num_rows_range[0], num_rows_range[1])
        
        # Use provided bug_rate_range or default to [0.05, 0.2]
        min_bug_rate, max_bug_rate = (0.05, 0.2) if bug_rate_range is None else (bug_rate_range[0], bug_rate_range[1])
        
        # Validate the bug types
        for bug_type in valid_bug_types:
            if bug_type not in self.VALID_BUG_TYPES:
                raise ValueError(f"Invalid bug type: {bug_type}. Valid types are: {', '.join(self.VALID_BUG_TYPES)}")
        
        # 定义可以使用 col-major 格式的类型
        col_major_types = ['error', 'merge_rows', 'rotate_columns', 'rotate_rows']
        
        # Setup weighted bug type selection if provided
        if bug_weights is not None and valid_bug_types:
            # Filter bug_weights to only include valid bug types
            filtered_weights = {bt: bug_weights.get(bt, 0) for bt in valid_bug_types}
            # Ensure all weights are positive, otherwise ignore the bug type
            filtered_weights = {bt: w for bt, w in filtered_weights.items() if w > 0}
            
            if filtered_weights:
                # Create list of bug types and weights for random.choices()
                weighted_bug_types = list(filtered_weights.keys())
                weights = list(filtered_weights.values())
            else:
                # If no valid weights, revert to uniform selection
                weighted_bug_types = None
                weights = None
        else:
            weighted_bug_types = None
            weights = None
        
        # Generate num_of_questions unique questions
        attempts = 0
        while len(game_data_list) < num_of_questions and attempts < max_attempts:
            attempts += 1
            
            # Generate random parameters
            num_rows = random.randint(min_rows, max_rows)
            
            # 选择bug类型，可能是加权的
            if weighted_bug_types and weights:
                bug_type = random.choices(weighted_bug_types, weights=weights, k=1)[0]
            else:
                bug_type = random.choice(valid_bug_types)
            
            # 对于特定类型的错误，必须使用 row-major 格式
            if bug_type in col_major_types:
                major_type = random.choice(self.VALID_MAJOR_TYPES)
            else:
                major_type = 'row'  # 强制使用 row-major 格式
            
            # 对于 null 类型，只使用 row-major 格式
            if bug_type == 'null' and major_type == 'col':
                major_type = 'row'
                
            # 使用指定范围生成bug_rate
            bug_rate = round(random.uniform(min_bug_rate, max_bug_rate), 2) if bug_type in ['error', 'null'] else None
            
            # Generate a sample
            result = self._generate_sample(
                num_rows=num_rows,
                major_type=major_type,
                bug_type=bug_type,
                bug_rate=bug_rate
            )
            
            # Check if the question is unique
            question_key = result['buggy_table']
            if question_key not in question_set:
                question_set.add(question_key)
                
                # Construct the question
                question = self._create_question(
                    num_rows=num_rows,
                    major_type=major_type,
                    bug_type=bug_type,
                    buggy_table=result['buggy_table'],
                    bug_description=result['bug_description'],
                    queries=result['queries'],
                    target_answer=result['target_answer']
                )
                
                # Create metadata
                metadata = {
                    'trace_id': str(uuid.uuid4()),
                    'num_rows': num_rows,
                    'major_type': major_type,
                    'bug_type': bug_type,
                    'bug_rate': bug_rate,
                    'queries': result['queries'],
                    'buggy_table': result['buggy_table'],
                    'bug_description': result['bug_description'],
                    'target_answer': result['target_answer'],
                    'original_table': result['original_table'],
                    'query_result': result['query_result']
                }
                
                # Create a Data object
                game_data = Data(
                    question=question,
                    answer=result['target_answer'],
                    metadata=metadata
                )
                
                # 控制"0.00"答案的比例在10%以下
                if result['target_answer'] == "0.00":
                    # 计算当前"0.00"答案的比例
                    current_zero_count = sum(1 for data in game_data_list if data.answer == "0.00")
                    # 如果添加这个"0.00"答案会导致比例超过10%，则加入zero_answer_list
                    if (current_zero_count + 1) / (len(game_data_list) + 1) >= 0.1:
                        zero_answer_list.append(game_data)
                        continue
                
                game_data_list.append(game_data)
                
                # 重置尝试次数计数器，因为我们已经添加了一个问题
                attempts = 0
            
        # 如果生成的问题不够，从zero_answer_list中补充
        if len(game_data_list) < num_of_questions and zero_answer_list:
            remaining = num_of_questions - len(game_data_list)
            game_data_list.extend(zero_answer_list[:remaining])
        
        return game_data_list
    
    def extract_answer(self, test_solution: str) -> str:
        """
        Extract the answer from the test solution
        
        @param test_solution: Solution provided by the LLM
        @return: Extracted answer
        """
        # Convert to string and normalize
        normalized = str(test_solution).strip().lower()
        
        # If the answer contains uncertainty words, return empty string
        uncertainty_words = ['around', 'about', 'between', 'approximately', 'roughly', 'maybe', 'might', 'could', 'possibly']
        if any(word in normalized for word in uncertainty_words):
            return ""
        
        # First try to find numbers in the text
        numbers = re.findall(r'-?\d+\.\d+|-?\d+', normalized)
        if numbers:
            # If we have numbers, take the last one as it's most likely to be the answer
            number = numbers[-1].strip()
            # Ensure exactly 2 decimal places for numerical answers
            try:
                num_value = float(number)
                return f"{num_value:.2f}"
            except ValueError:
                return number
        
        # If no numbers found, try to find an answer after common indicators
        indicators = [
            r'answer\s*[=:]\s*([^.,;]+)',
            r'result\s*[=:]\s*([^.,;]+)',
            r'final\s+answer\s*[=:]\s*([^.,;]+)',
            r'the\s+answer\s+is\s*[=:]\s*([^.,;]+)',
            r'calculated\s+value\s*[=:]\s*([^.,;]+)',
            r'value\s*[=:]\s*([^.,;]+)',
            r'output\s*[=:]\s*([^.,;]+)',
            r'is\s*[=:]\s*([^.,;]+)',
            r'equals\s*[=:]\s*([^.,;]+)',
            r'=\s*([^.,;]+)'
        ]
        
        for pattern in indicators:
            match = re.search(pattern, normalized)
            if match:
                result = match.group(1).strip()
                # Remove any trailing punctuation
                result = result.rstrip('.,:;')
                return result
        
        # If no indicators found, split by common delimiters and take the last meaningful part
        parts = re.split(r'[.,;]', normalized)
        parts = [p.strip() for p in parts if p.strip()]
        if parts:
            return parts[-1].rstrip('.,:;')
        
        return normalized.rstrip('.,:;')
    
    def _generate_sample(self, num_rows: int, major_type: str, bug_type: str, bug_rate: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate a sample for the game
        
        @param num_rows: Number of rows in the table
        @param major_type: Column-major ('col') or row-major ('row') format
        @param bug_type: Type of bug to introduce
        @param bug_rate: Rate of errors for 'error' or 'null' bug types
        @return: Dictionary with buggy table, bug description, query, and target answer
        """
        # Generate a random table
        original_df = generate_random_table(num_rows, order_type='random')
        
        # Create a copy of the original DataFrame
        df_copy = original_df.copy()
        
        # Apply the specified error to create a buggy version
        if bug_type in ['error', 'null'] and bug_rate is not None:
            # These bug types require an error rate
            buggy_df, affected_values, error_positions = apply_error_makers(df_copy, bug_type, error_rate=bug_rate)
        else:
            # Other bug types don't need an error rate
            buggy_df, affected_values, error_positions = apply_error_makers(df_copy, bug_type)
        
        # Transform to the specified major type format
        if major_type == 'col':
            buggy_table = transform_to_column_major(buggy_df)
        else:  # 'row'
            buggy_table = transform_to_row_major(buggy_df)
        
        # 始终按列顺序输出错误描述，无论表格类型如何
        bug_description = self._generate_bug_description(bug_type, affected_values, error_positions, "column")
        
        # Generate a single query task and get its answer
        # null type is special, because the query should be made on the bugggy table, not the original table
        if bug_type == 'null':
            query_result = generate_and_execute_query(buggy_df)
        else:
            query_result = generate_and_execute_query(original_df)

        
        # Convert set to list if conditions is a set
        if 'conditions' in query_result and isinstance(query_result['conditions'], set):
            query_result['conditions'] = list(query_result['conditions'])
        
        query = query_result['query']
        target_answer = query_result['result']
        
        # 确保目标答案有两位小数
        if target_answer.replace('.', '', 1).replace('-', '', 1).isdigit():
            try:
                target_answer = f"{float(target_answer):.2f}"
            except ValueError:
                pass
        
        return {
            'buggy_table': buggy_table,
            'bug_description': bug_description,
            'queries': [query],  # Keep as list for backward compatibility
            'target_answer': target_answer,
            'original_table': original_df.to_dict(orient='records'),
            'query_result': query_result
        }
    
    def _generate_bug_description(self, bug_type: str, affected_values: List, error_positions=None, order="column") -> str:
        """
        Generate a description of the bug in the table
        
        @param bug_type: Type of bug introduced
        @param affected_values: List of affected values or coordinates
        @param error_positions: List of error positions (row, col) tuples
        @param order: Order to list values - "column" or "row"
        @return: String describing the bug
        """
        # Randomly choose language (50% English, 50% Chinese)
        language = random.choice(["en", "zh"])
        
        # Use our template system to generate the bug description
        return get_bug_description(bug_type, affected_values, error_positions, language, order)
    
    def _create_question(self, num_rows: int, major_type: str, bug_type: str, 
                          buggy_table: str, bug_description: str, queries: List[str],
                          target_answer: str) -> str:
        """
        Create a question from the generated sample
        
        @param num_rows: Number of rows in the table
        @param major_type: Column-major ('col') or row-major ('row') format
        @param bug_type: Type of bug introduced
        @param buggy_table: The buggy table content
        @param bug_description: Description of the bug
        @param queries: List of query tasks to perform
        @param target_answer: The expected answer for the query
        @return: Formatted question string
        """
        # Different format for row-major and column-major
        if major_type == 'row':
            table_format = "row-major"
            table_section = f"{buggy_table}"
        else:
            table_format = "markdown"
            table_section = f"{buggy_table}"
        
        # Count the number of columns (18 for our predefined table)
        num_columns = 18
        
        # Randomly choose language (50% English, 50% Chinese)
        # Note: This should match the language used in bug_description if possible
        # Check for Chinese characters in bug_description to determine its language
        if any('\u4e00' <= c <= '\u9fff' for c in bug_description):
            language = "zh"
        else:
            language = "en"
        
        # Create question data dictionary
        question_data = {
            'num_rows': num_rows,
            'num_columns': num_columns,
            'bug_type': bug_type,
            'table_format': table_format,
            'table_section': table_section,
            'bug_description': bug_description,
            'query': queries[0]
        }
        
        # Use our template system to generate the question
        question = format_question_template(question_data, language)
        
        # Add the required answer format instruction
        answer_format = """

- Your response must strictly follow the JSON format below. All content must be in English and enclosed in double quotes. If you need to use double quotes within your content, replace them with single quotes to avoid parsing errors.

- Response format example:
```json
{
  "result": [
    {
      "answer": <your answer>
    }
  ]
}
```

- Your response must start with ```json and end with ```.
"""
        
        return question + answer_format

def main():
    import argparse
    import pathlib
    import json
    from tqdm import tqdm
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_of_data", type=int, default=100)
    parser.add_argument("--max_attempts", type=int, default=1000)
    parser.add_argument("--bug_types", type=str, nargs="+", choices=GameOfBuggyTables.VALID_BUG_TYPES,
                        help="Specific bug types to generate (defaults to all types)")
    parser.add_argument("--num_rows_range", type=int, nargs=2, default=[25, 40], 
                        help="Range for number of rows [min, max] (default: [25, 40])")
    parser.add_argument("--bug_rate_range", type=float, nargs=2, default=[0.05, 0.2],
                        help="Range for bug rate [min, max] for 'error' and 'null' types (default: [0.05, 0.2])")
    parser.add_argument("--bug_types_ratio", type=str, default=None,
                        help="Ratio for bug types generation in format 'type1:weight1,type2:weight2,...' (e.g., 'error:3,null:2,rotate_rows:1')")
    parser.add_argument("--output_name", type=str, default=None,
                        help="Custom base name for output file (default: 'buggy_tables')")
    args = parser.parse_args()
    
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # Set the base filename
    base_filename = args.output_name if args.output_name else "buggy_tables"
    
    # Create filename suffix based on parameters
    bug_type_suffix = ""
    if args.bug_types:
        bug_type_suffix = f"_{'_'.join(args.bug_types)}"
    
    num_rows_suffix = ""
    if args.num_rows_range != [25, 40]:  # only add suffix if different from default
        num_rows_suffix = f"_rows_{args.num_rows_range[0]}_{args.num_rows_range[1]}"
    
    bug_rate_suffix = ""
    if args.bug_rate_range != [0.05, 0.2]:  # only add suffix if different from default
        bug_rate_suffix = f"_rate_{args.bug_rate_range[0]}_{args.bug_rate_range[1]}"
    
    ratio_suffix = ""
    if args.bug_types_ratio:
        ratio_suffix = "_custom_ratio"
    
    output_file = data_dir / f"{base_filename}_{args.num_of_data}{bug_type_suffix}{num_rows_suffix}{bug_rate_suffix}{ratio_suffix}.jsonl"
    
    # Parse bug_types_ratio if provided
    bug_weights = None
    if args.bug_types_ratio:
        bug_weights = {}
        try:
            for item in args.bug_types_ratio.split(','):
                bug_type, weight = item.split(':')
                if bug_type in GameOfBuggyTables.VALID_BUG_TYPES:
                    bug_weights[bug_type] = float(weight)
                else:
                    print(f"Warning: Ignoring invalid bug type '{bug_type}' in ratio")
            
            # Validate that we have at least one valid bug type with weight
            if not bug_weights:
                print("Warning: No valid bug types found in ratio, using uniform distribution")
                bug_weights = None
        except (ValueError, AttributeError) as e:
            print(f"Error parsing bug_types_ratio: {e}. Format should be 'type1:weight1,type2:weight2,...'")
            print("Using uniform distribution instead")
            bug_weights = None
    
    game = GameOfBuggyTables()
    print("Generating buggy tables...")
    game_data_list = game.generate(
        args.num_of_data, 
        args.max_attempts, 
        args.bug_types, 
        num_rows_range=args.num_rows_range,
        bug_rate_range=args.bug_rate_range,
        bug_weights=bug_weights
    )
    
    if len(game_data_list) == 0:
        print(f"Failed to generate any buggy tables after {args.max_attempts} attempts")
        exit(1)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    print("Saving generated data...")
    with open(output_file, "w") as f:
        for game_data in tqdm(game_data_list, desc="Writing data"):
            f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
    
    print(f"Successfully generated {len(game_data_list)} buggy tables questions and saved to {output_file}")

if __name__ == "__main__":
    main()
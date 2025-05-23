import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Add parent directory to path to import the prompt module
sys.path.append(str(Path(__file__).parent.parent))
from buggy_tables_prompt import format_query_template

def generate_query():
    """
    生成随机数据查询
    
    返回:
    query_info - 包含查询信息的字典
    """
    # 所有可用的数据列 (只选择数值型列进行统计计算)
    numeric_columns = [
        "num_steps", "study_minutes", "exercise_minutes", "sleep_minutes",
        "num_messages", "num_emails", "num_calls", "calories_burned",
        "calories_consumed", "num_meetings", "coding_minutes", 
        "num_tasks_completed", "water_intake_ml", "phone_screen_time_minutes", 
        "music_listening_minutes"
    ]
    
    # 选择两个不同的列进行统计比较
    cols_to_compare = random.sample(numeric_columns, 2)
    
    # 扩展统计指标类型
    basic_stats = ["mean", "median", "stdev", "sum", "max", "min", "variance"]
    # 暂时注释掉扩展的统计指标
    # compound_stats = ["range", "ratio", "percent_change"]
    # all_stats = basic_stats + compound_stats
    all_stats = basic_stats
    stat_type = random.choice(all_stats)
    
    # 生成合理的过滤条件
    filter_conditions = {}
    for column in numeric_columns:
        # 扩展操作符选择
        basic_operators = [">", "<", ">=", "<=", "==", "!="]
        range_operator = ["between"]
        operators = basic_operators + (range_operator if random.random() < 0.2 else [])
        operator = random.choice(operators)
        
        # 根据列名设置合理的值范围
        if column == "num_steps":
            base_value = random.randint(10000, 20000)
            value = [base_value - 1000, base_value + 1000] if operator == "between" else base_value
        elif column == "study_minutes":
            base_value = random.randint(15, 30)
            value = [base_value - 5, base_value + 5] if operator == "between" else base_value
        elif column == "exercise_minutes":
            base_value = random.randint(40, 60)
            value = [base_value - 10, base_value + 10] if operator == "between" else base_value
        elif column == "sleep_minutes":
            base_value = random.randint(300, 400)
            value = [base_value - 30, base_value + 30] if operator == "between" else base_value
        elif column == "num_messages":
            base_value = random.randint(3, 8)
            value = [base_value - 1, base_value + 1] if operator == "between" else base_value
        elif column == "num_emails":
            base_value = random.randint(1, 5)
            value = [base_value - 1, base_value + 1] if operator == "between" else base_value
        elif column == "num_calls":
            base_value = random.randint(1, 4)
            value = [base_value - 1, base_value + 1] if operator == "between" else base_value
        elif column == "calories_burned":
            base_value = random.randint(600, 1000)
            value = [base_value - 100, base_value + 100] if operator == "between" else base_value
        elif column == "calories_consumed":
            base_value = random.randint(1600, 2000)
            value = [base_value - 200, base_value + 200] if operator == "between" else base_value
        elif column == "num_meetings":
            base_value = random.randint(1, 4)
            value = [base_value - 1, base_value + 1] if operator == "between" else base_value
        elif column == "coding_minutes":
            base_value = random.randint(15, 30)
            value = [base_value - 5, base_value + 5] if operator == "between" else base_value
        elif column == "num_tasks_completed":
            base_value = random.randint(2, 5)
            value = [base_value - 1, base_value + 1] if operator == "between" else base_value
        elif column == "water_intake_ml":
            base_value = random.randint(2000, 3000)
            value = [base_value - 200, base_value + 200] if operator == "between" else base_value
        elif column == "phone_screen_time_minutes":
            base_value = random.randint(20, 30)
            value = [base_value - 5, base_value + 5] if operator == "between" else base_value
        elif column == "music_listening_minutes":
            base_value = random.randint(20, 30)
            value = [base_value - 5, base_value + 5] if operator == "between" else base_value
        
        filter_conditions[column] = {"op": operator, "value": value}
    
    # 从所有可能的条件中随机选择两个或三个不同的条件
    all_columns = list(filter_conditions.keys())
    num_conditions = random.choice([2, 3])
    filter_cols = random.sample(all_columns, num_conditions)
    
    # 创建查询数据字典
    query_data = {
        "cols_to_compare": cols_to_compare,
        "stat_type": stat_type,
        "conditions": {col: filter_conditions[col] for col in filter_cols}
    }
    
    # 随机选择语言 (50% 英文, 50% 中文)
    language = random.choice(["en", "zh"])
    
    # 使用格式化函数生成查询描述
    query = format_query_template(query_data, language)
    
    # 返回完整的查询信息
    return {
        "query": query,
        "cols_to_compare": cols_to_compare,
        "stat_type": stat_type,
        "conditions": {col: filter_conditions[col] for col in filter_cols}
    }

def execute_query(df, query_info):
    """
    在提供的DataFrame上执行查询
    
    参数:
    df - pandas DataFrame，包含所有必要的数据列
    query_info - 由generate_query函数生成的查询信息字典
    
    返回:
    result_info - 包含查询结果的字典
    """
    cols_to_compare = query_info["cols_to_compare"]
    stat_type = query_info["stat_type"]
    conditions = query_info["conditions"]
    
    # 确保所选列在DataFrame中存在
    available_columns = [col for col in cols_to_compare if col in df.columns]
    if len(available_columns) < 2:
        return {
            "query": query_info["query"],
            "result": "0",
            "filtered_rows": 0,
            "total_rows": len(df),
            "conditions": {f"{col} {conditions[col]['op']} {conditions[col]['value']}" 
                         for col in conditions.keys()},
            "columns_compared": cols_to_compare,
            "statistic": stat_type
        }
    
    # 执行查询计算
    # 步骤1: 应用过滤条件
    filtered_df = df.copy()
    
    # 应用所有条件
    for condition, cond_info in conditions.items():
        if condition not in df.columns:
            continue
            
        operator = cond_info['op']
        value = cond_info['value']
        
        try:
            # 数值列的条件
            if operator == "between":
                if isinstance(value, list) and len(value) == 2:
                    # 确保null值被视为不满足条件，而不是直接删除
                    filtered_df = filtered_df[
                        filtered_df[condition].notna() & 
                        (filtered_df[condition] >= value[0]) & 
                        (filtered_df[condition] <= value[1])
                    ]
            else:
                op_map = {
                    ">": "__gt__",
                    "<": "__lt__",
                    ">=": "__ge__",
                    "<=": "__le__",
                    "==": "__eq__",
                    "!=": "__ne__"
                }
                if operator in op_map:
                    # 确保null值被视为不满足条件，而不是直接删除
                    if operator == "!=":
                        # 对于不等条件，null值仍然视为不满足条件
                        filtered_df = filtered_df[
                            filtered_df[condition].notna() & 
                            getattr(filtered_df[condition], op_map[operator])(value)
                        ]
                    else:
                        # 对于其他条件，null值视为不满足条件
                        filtered_df = filtered_df[
                            filtered_df[condition].notna() & 
                            getattr(filtered_df[condition], op_map[operator])(value)
                        ]
        except Exception as e:
            print(f"过滤条件应用错误: {e}")
            # 根据指导原则：假设条件不满足，返回空的DataFrame
            filtered_df = pd.DataFrame(columns=filtered_df.columns)
    
    # 步骤2: 计算统计量
    result = "0"
    try:
        if len(filtered_df) > 0:
            col1, col2 = cols_to_compare
            
            # 基础统计量计算
            def calculate_basic_stat(series, stat_type):
                if len(series) == 0 or series.isna().all():
                    return 0
                if stat_type == "mean":
                    return series.mean()
                elif stat_type == "median":
                    return series.median()
                elif stat_type == "stdev":
                    return 0 if len(series.dropna()) <= 1 else series.std()
                elif stat_type == "sum":
                    return series.sum()
                elif stat_type == "max":
                    return series.max()
                elif stat_type == "min":
                    return series.min()
                elif stat_type == "variance":
                    return 0 if len(series.dropna()) <= 1 else series.var()
                return 0
            
            # 通用处理所有统计类型
            # 首先检查是否有足够的非空值来计算统计量
            if len(filtered_df[col1].dropna()) == 0 or len(filtered_df[col2].dropna()) == 0:
                # 如果任意列全为空值，则直接返回"0.00"
                result = "0.00"
            # 特殊处理标准差和方差（需要至少2个值）
            elif stat_type in ["stdev", "variance"] and (len(filtered_df[col1].dropna()) <= 1 or len(filtered_df[col2].dropna()) <= 1):
                # 如果任一列的非空值数量不足，则直接返回"0.00"
                result = "0.00"
            # 处理其他统计类型
            else:
                stat1 = calculate_basic_stat(filtered_df[col1], stat_type)
                stat2 = calculate_basic_stat(filtered_df[col2], stat_type)
                if pd.notna(stat1) and pd.notna(stat2):
                    result = f"{abs(stat1 - stat2):.2f}"
    
    except Exception as e:
        print(f"计算错误: {e}")
    
    # 确保结果是两位小数
    if result == "0":
        result = "0.00"
    elif result.replace('.', '', 1).replace('-', '', 1).isdigit():
        try:
            # 尝试转换为浮点数，然后格式化为两位小数
            result = f"{float(result):.2f}"
        except ValueError:
            pass
    
    return {
        "query": query_info["query"],
        "result": result,
        "filtered_rows": len(filtered_df),
        "total_rows": len(df),
        "conditions": {f"{col} {conditions[col]['op']} {conditions[col]['value']}" 
                     for col in conditions.keys()},
        "columns_compared": cols_to_compare,
        "statistic": stat_type
    }

def generate_and_execute_query(df):
    """
    生成随机数据查询并在提供的DataFrame上执行该查询
    
    参数:
    df - pandas DataFrame，包含所有必要的数据列
    
    返回:
    result_info - 包含查询和结果的字典
    """
    query_info = generate_query()
    result_info = execute_query(df, query_info)
    return result_info

# # 测试函数 - 创建一个示例DataFrame
# def create_sample_df(rows=30):
#     """创建一个示例DataFrame用于测试"""
#     np.random.seed(42)  # 设置随机种子以确保可重复性
    
#     # 创建日期范围
#     dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(rows)]
    
#     # 生成随机数据
#     df = pd.DataFrame({
#         'date': dates,
#         'num_steps': np.random.randint(5000, 25000, rows),
#         'study_minutes': np.random.randint(0, 120, rows),
#         'exercise_minutes': np.random.randint(0, 90, rows),
#         'sleep_minutes': np.random.randint(300, 540, rows),
#         'num_messages': np.random.randint(0, 50, rows),
#         'num_emails': np.random.randint(0, 30, rows),
#         'num_calls': np.random.randint(0, 10, rows),
#         'calories_burned': np.random.randint(400, 1200, rows),
#         'calories_consumed': np.random.randint(1200, 2500, rows),
#         'num_meetings': np.random.randint(0, 8, rows),
#         'coding_minutes': np.random.randint(0, 180, rows),
#         'num_tasks_completed': np.random.randint(0, 15, rows),
#         'water_intake_ml': np.random.randint(500, 4000, rows),
#         'phone_screen_time_minutes': np.random.randint(10, 240, rows),
#         'music_listening_minutes': np.random.randint(0, 120, rows),
#     })
    
#     # 添加一些空值以模拟真实数据
#     for col in df.columns:
#         if col != 'date':
#             mask = np.random.random(rows) < 0.05  # 5%的概率产生空值
#             df.loc[mask, col] = np.nan
    
#     return df

# # 生成示例数据
# sample_df = create_sample_df(50)
# # print and save the sample_df
# print(sample_df)
# sample_df.to_csv('sample_df_4_gen_calculate.csv', index=False)

# # 执行多个查询并显示结果
# for i in range(1):
#     result = generate_and_execute_query(sample_df)
#     print(f"Query {i+1}:")
#     print(result["query"])
#     print(f"Result: {result['result']}")
#     print(f"Filtered rows: {result['filtered_rows']} out of {result['total_rows']}")
#     print(f"Conditions: {result['conditions']}")
#     print(f"Columns compared: {result['columns_compared']} using {result['statistic']}")
#     print("-" * 80)
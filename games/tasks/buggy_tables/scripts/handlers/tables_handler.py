import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import markdown

def generate_random_table(row_num, order_type='random'):
    """
    Generate a random table as a pandas DataFrame with all 18 predefined columns.
    
    Parameters:
    row_num (int): Number of rows in the table
    order_type (str): Type of ordering for the data ('random', 'ascending', 'descending')
    
    Returns:
    pandas.DataFrame: Generated table with all 18 columns
    """
    # Define all columns with their data generation functions
    all_columns = {
        'date': lambda n: [(datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d') for _ in range(n)],
        'num_steps': lambda n: [random.randint(1000, 20000) for _ in range(n)],
        'study_minutes': lambda n: [random.randint(0, 360) for _ in range(n)],
        'exercise_minutes': lambda n: [random.randint(0, 120) for _ in range(n)],
        'sleep_minutes': lambda n: [random.randint(300, 600) for _ in range(n)],
        'bed_time': lambda n: [f"{random.randint(21, 23)}:{random.randint(0, 59):02d}" for _ in range(n)],
        'num_messages': lambda n: [random.randint(0, 200) for _ in range(n)],
        'num_emails': lambda n: [random.randint(0, 50) for _ in range(n)],
        'num_calls': lambda n: [random.randint(0, 15) for _ in range(n)],
        'calories_burned': lambda n: [random.randint(1500, 3500) for _ in range(n)],
        'weekday': lambda n: [random.choice(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']) for _ in range(n)],
        'calories_consumed': lambda n: [random.randint(1200, 3000) for _ in range(n)],
        'num_meetings': lambda n: [random.randint(0, 8) for _ in range(n)],
        'coding_minutes': lambda n: [random.randint(0, 480) for _ in range(n)],
        'num_tasks_completed': lambda n: [random.randint(0, 20) for _ in range(n)],
        'water_intake_ml': lambda n: [random.randint(500, 3000) for _ in range(n)],
        'phone_screen_time_minutes': lambda n: [random.randint(30, 360) for _ in range(n)],
        'music_listening_minutes': lambda n: [random.randint(0, 240) for _ in range(n)]
    }
    
    # Always use all columns
    selected_columns = list(all_columns.keys())
    
    # Generate data for each column
    data = {col: all_columns[col](row_num) for col in selected_columns}
    df = pd.DataFrame(data)
    
    # Apply ordering if specified
    if order_type == 'ascending' and 'date' in df.columns:
        df = df.sort_values('date')
    elif order_type == 'descending' and 'date' in df.columns:
        df = df.sort_values('date', ascending=False)
    
    return df

def transform_to_column_major(df):
    """
    Convert a pandas DataFrame to a column-major Markdown table string.
    
    Parameters:
    df (pandas.DataFrame): The DataFrame to convert
    
    Returns:
    str: Markdown representation of the table in column-major format
    """
    # 判断是否有额外的列（通过命名规则识别）
    has_extra_cols = any(col.startswith('extra_col_') for col in df.columns)
    
    # 获取原始列（非extra_col_列）
    if has_extra_cols:
        # 创建一个新的DataFrame，只包含原始列
        original_cols = [col for col in df.columns if not col.startswith('extra_col_')]
        df_display = df[original_cols].copy()
    else:
        df_display = df.copy()
    
    # Create header row
    header = "| " + " | ".join(df_display.columns) + " |"
    
    # Create separator row
    separator = "| " + " | ".join(["---" for _ in range(len(df_display.columns))]) + " |"
    
    # Create data rows
    rows = []
    for _, row in df_display.iterrows():
        # 替换 None 为空字符串
        values = [str(val) if pd.notna(val) else "" for val in row.values]
        rows.append("| " + " | ".join(values) + " |")
    
    # Combine all rows into a Markdown table
    markdown_table = "\n".join([header, separator] + rows)
    
    return markdown_table

def transform_to_row_major(df):
    """
    Convert a pandas DataFrame to a row-major format as a flat list.
    
    Parameters:
    df (pandas.DataFrame): The DataFrame to convert
    
    Returns:
    str: Row-major representation of the table as a flat list
    """
    # 获取所有列名，区分原始列和额外列
    original_cols = [col for col in df.columns if not col.startswith('extra_col_')]
    extra_cols = [col for col in df.columns if col.startswith('extra_col_')]
    
    # 首先添加所有列名（只包含原始列）
    row_major_list = list(original_cols)
    
    # 添加所有行的非空数据
    for i in range(len(df)):
        row = df.iloc[i]
        
        # 添加原始列中的非空数据
        for col in original_cols:
            val = row[col]
            if not pd.isna(val):  # 只添加非空值
                row_major_list.append(str(val))
        
        # 添加额外列中的非空数据
        for col in extra_cols:
            val = row[col]
            if not pd.isna(val):  # 只添加非空值
                row_major_list.append(str(val))
    
    # 转换为字符串表示
    row_major_str = "[" + ", ".join(row_major_list) + "]"
    
    return row_major_str

# Example usage
if __name__ == "__main__":
    # Generate a table with 5 rows
    row_num = 5
    df = generate_random_table(row_num)
    
    # Print the DataFrame
    print("DataFrame:")
    print(df)
    
    # Save to file
    df.to_csv('table.csv', index=False)
    
    # Choose format type
    major_type = 'row'  # 'col' or 'row'
    
    if major_type == 'col':
        output = transform_to_column_major(df)
    elif major_type == 'row':
        output = transform_to_row_major(df)
    
    print(f"\n{major_type}-major Table:")
    print(output)
    
    # Save formatted table to file
    with open(f'{major_type}_table.md', 'w') as f:
        f.write(output)
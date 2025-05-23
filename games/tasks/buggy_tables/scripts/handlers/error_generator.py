import pandas as pd
import numpy as np
import random
from typing import List, Tuple, Optional, Union
from datetime import datetime, timedelta

def make_error(df: pd.DataFrame, error_rate: float, error_order: Optional[str] = None) -> Tuple[pd.DataFrame, List, List[Tuple[int, int]]]:
    """
    在表格中随机位置插入ERROR，根据指定错误率
    
    Args:
        df: 输入的DataFrame
        error_rate: 错误率，0.0-1.0之间的浮点数
        error_order: 替换为的错误标记，默认为'ERROR'
    
    Returns:
        修改后的DataFrame、原始值列表和错误位置列表
    """
    if error_order is None:
        error_order = 'ERROR'
        
    # 深拷贝以避免修改原始DataFrame
    df_copy = df.copy(deep=True)
    
    # 计算需要替换的单元格数量
    total_cells = df.size
    num_errors = int(total_cells * error_rate)
    
    # 随机选择单元格位置
    rows, cols = df_copy.shape
    positions = [(i, j) for i in range(rows) for j in range(cols)]
    error_positions = random.sample(positions, num_errors)
    
    # 保存错误的原始值
    original_values = []
    
    # 替换为ERROR，先转换列类型为object，避免类型警告
    for col in df_copy.columns:
        df_copy[col] = df_copy[col].astype(object)
        
    # 替换为ERROR
    for pos in error_positions:
        i, j = pos
        original_value = df_copy.iloc[i, j]
        original_values.append(original_value)  # 只保存原始值，不保存坐标
        df_copy.iloc[i, j] = error_order
    
    return df_copy, original_values, error_positions

def merge_rows(df: pd.DataFrame) -> Tuple[pd.DataFrame, List]:
    """
    将原表的每两行合并为一行
    
    Args:
        df: 输入的DataFrame
    
    Returns:
        行合并后的DataFrame和空列表（保持返回格式一致）
    """
    df_copy = df.copy(deep=True)
    rows = df_copy.shape[0]
    
    # 创建新的DataFrame来保存合并结果
    merged_rows = []
    
    for i in range(0, rows, 2):
        if i + 1 < rows:  # 确保有下一行可以合并
            merged_row = []
            for j in range(df_copy.shape[1]):
                # 合并两行中对应位置的值
                merged_row.append(f"{df_copy.iloc[i, j]} && {df_copy.iloc[i+1, j]}")
            merged_rows.append(merged_row)
        else:  # 如果行数为奇数，最后一行保持不变
            merged_rows.append(df_copy.iloc[i].tolist())
    
    return pd.DataFrame(merged_rows, columns=df_copy.columns), []

def rotate_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List]:
    """
    列转：对于每一列i，向下旋转i次
    
    Args:
        df: 输入的DataFrame
    
    Returns:
        列旋转后的DataFrame和空列表（保持返回格式一致）
    """
    df_copy = df.copy(deep=True)
    
    # 先将所有列转换为object类型，避免类型不兼容的警告
    for col in df_copy.columns:
        df_copy[col] = df_copy[col].astype(object)
    
    for i in range(df_copy.shape[1]):
        col_values = df_copy.iloc[:, i].tolist()
        # 向下旋转i次
        rotated_values = col_values[-i:] + col_values[:-i] if i > 0 else col_values
        df_copy.iloc[:, i] = rotated_values
    
    return df_copy, []

def rotate_rows(df: pd.DataFrame) -> Tuple[pd.DataFrame, List]:
    """
    行转：对于每一行i，向右旋转i次
    
    Args:
        df: 输入的DataFrame
    
    Returns:
        行旋转后的DataFrame和空列表（保持返回格式一致）
    """
    df_copy = df.copy(deep=True)
    
    # 先将所有列转换为object类型，避免类型不兼容的警告
    for col in df_copy.columns:
        df_copy[col] = df_copy[col].astype(object)
    
    for i in range(df_copy.shape[0]):
        row_values = df_copy.iloc[i, :].tolist()
        # 向右旋转i次
        rotated_values = row_values[-i:] + row_values[:-i] if i > 0 else row_values
        df_copy.iloc[i, :] = rotated_values
    
    return df_copy, []

def add_end_row(df: pd.DataFrame, min_val: float = -10, max_val: float = 10) -> Tuple[pd.DataFrame, List]:
    """
    第i行末尾追加i个随机值
    
    Args:
        df: 输入的DataFrame
        min_val: 随机值的最小值
        max_val: 随机值的最大值
    
    Returns:
        添加随机值后的DataFrame和空列表（保持返回格式一致）
    """
    df_copy = df.copy(deep=True)
    rows, cols = df_copy.shape
    
    # 确定新的列数(最后一行会增加rows-1个元素)
    new_cols = cols + rows - 1
    
    # 创建新的列名
    original_columns = list(df_copy.columns)
    new_columns = original_columns.copy()
    for i in range(cols, new_cols):
        new_columns.append(f"extra_col_{i-cols+1}")
    
    # 为每列创建符合其特征的随机值生成方法，复用 add_end_column 中定义的函数
    def generate_random_for_column(column_name, column_values):
        # 针对不同类型的列生成不同的随机值
        if column_name == 'date':
            # 日期格式应保持YYYY-MM-DD格式
            return [(datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')]
        
        elif column_name == 'bed_time':
            # 时间应保持HH:MM格式
            return [f"{random.randint(21, 23)}:{random.randint(0, 59):02d}"]
        
        elif column_name == 'weekday':
            # 工作日应是Mon-Sun中的一个
            return [random.choice(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])]
        
        elif 'minutes' in column_name.lower():
            # 分钟值通常是正数且在一个合理范围内
            non_null_values = [v for v in column_values if pd.notna(v)]
            if non_null_values:
                # 从现有数据学习范围
                min_minutes = max(0, min(non_null_values) * 0.8)
                max_minutes = max(non_null_values) * 1.2
                return [round(random.uniform(min_minutes, max_minutes), 2)]
            else:
                # 默认分钟值范围
                return [round(random.uniform(0, 240), 2)]
        
        elif 'num_' in column_name.lower():
            # 数量通常是较小的整数
            non_null_values = [v for v in column_values if pd.notna(v)]
            if non_null_values:
                # 从现有数据学习范围
                min_num = max(0, min(non_null_values) * 0.8)
                max_num = max(non_null_values) * 1.2
                return [round(random.uniform(min_num, max_num), 2)]
            else:
                # 默认数量范围
                return [round(random.uniform(0, 50), 2)]
        
        elif 'calories' in column_name.lower():
            # 卡路里通常在某个范围内
            non_null_values = [v for v in column_values if pd.notna(v)]
            if non_null_values:
                # 从现有数据学习范围
                min_cal = max(0, min(non_null_values) * 0.8)
                max_cal = max(non_null_values) * 1.2
                return [round(random.uniform(min_cal, max_cal), 2)]
            else:
                # 默认卡路里范围
                return [round(random.uniform(1000, 3000), 2)]
        
        else:
            # 其他类型列，生成在数据范围内的随机值
            non_null_values = [v for v in column_values if pd.notna(v)]
            if non_null_values and all(isinstance(v, (int, float)) for v in non_null_values):
                # 从现有数值数据学习范围
                min_val = min(non_null_values) * 0.8
                max_val = max(non_null_values) * 1.2
                return [round(random.uniform(min_val, max_val), 2)]
            else:
                # 默认范围
                return [round(random.uniform(-10, 10), 2)]
    
    # 创建新的DataFrame，包含额外的列
    new_df = pd.DataFrame(columns=new_columns, index=range(rows))
    
    # 复制原始数据
    for i in range(rows):
        for j in range(cols):
            new_df.iloc[i, j] = df_copy.iloc[i, j]
    
    # 对于每行i添加i个随机值
    for i in range(rows):
        # 获取该行需要添加的额外值数量
        num_extra_values = i
        
        # 添加额外的列
        for j in range(num_extra_values):
            # 获取要添加随机值的列名
            col_idx = cols + j
            col_name = new_columns[col_idx]
            
            # 生成随机值 - 这里使用第一列的类型作为参考
            # 实际应用中可能需要更复杂的逻辑来决定这些额外列的数据类型
            ref_col_name = original_columns[0]  # 使用第一列作为参考
            ref_col_values = df_copy[ref_col_name].values.tolist()
            
            # 生成符合参考列特征的随机值
            random_val = generate_random_for_column(ref_col_name, ref_col_values)[0]
            
            # 设置随机值
            new_df.iloc[i, col_idx] = random_val
    
    return new_df, []

def add_end_column(df: pd.DataFrame, min_val: float = -10, max_val: float = 10) -> Tuple[pd.DataFrame, List]:
    """
    第j列末尾追加j个随机值
    
    Args:
        df: 输入的DataFrame
        min_val: 随机值的最小值
        max_val: 随机值的最大值
    
    Returns:
        添加随机值后的DataFrame和空列表（保持返回格式一致）
    """
    df_copy = df.copy(deep=True)
    rows, cols = df_copy.shape
    
    # 确定新的行数(最后一列会增加cols-1个元素)
    new_rows = rows + cols - 1
    
    # 为每列创建符合其特征的随机值生成方法
    def generate_random_for_column(column_name, column_values):
        # 针对不同类型的列生成不同的随机值
        if column_name == 'date':
            # 日期格式应保持YYYY-MM-DD格式
            return [(datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')]
        
        elif column_name == 'bed_time':
            # 时间应保持HH:MM格式
            return [f"{random.randint(21, 23)}:{random.randint(0, 59):02d}"]
        
        elif column_name == 'weekday':
            # 工作日应是Mon-Sun中的一个
            return [random.choice(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])]
        
        elif 'minutes' in column_name.lower():
            # 分钟值通常是正数且在一个合理范围内
            non_null_values = [v for v in column_values if pd.notna(v)]
            if non_null_values:
                # 从现有数据学习范围
                min_minutes = max(0, min(non_null_values) * 0.8)
                max_minutes = max(non_null_values) * 1.2
                return [round(random.uniform(min_minutes, max_minutes), 2)]
            else:
                # 默认分钟值范围
                return [round(random.uniform(0, 240), 2)]
        
        elif 'num_' in column_name.lower():
            # 数量通常是较小的整数
            non_null_values = [v for v in column_values if pd.notna(v)]
            if non_null_values:
                # 从现有数据学习范围
                min_num = max(0, min(non_null_values) * 0.8)
                max_num = max(non_null_values) * 1.2
                return [round(random.uniform(min_num, max_num), 2)]
            else:
                # 默认数量范围
                return [round(random.uniform(0, 50), 2)]
        
        elif 'calories' in column_name.lower():
            # 卡路里通常在某个范围内
            non_null_values = [v for v in column_values if pd.notna(v)]
            if non_null_values:
                # 从现有数据学习范围
                min_cal = max(0, min(non_null_values) * 0.8)
                max_cal = max(non_null_values) * 1.2
                return [round(random.uniform(min_cal, max_cal), 2)]
            else:
                # 默认卡路里范围
                return [round(random.uniform(1000, 3000), 2)]
        
        else:
            # 其他类型列，生成在数据范围内的随机值
            non_null_values = [v for v in column_values if pd.notna(v)]
            if non_null_values and all(isinstance(v, (int, float)) for v in non_null_values):
                # 从现有数值数据学习范围
                min_val = min(non_null_values) * 0.8
                max_val = max(non_null_values) * 1.2
                return [round(random.uniform(min_val, max_val), 2)]
            else:
                # 默认范围
                return [round(random.uniform(-10, 10), 2)]
    
    # 对于每列j添加j个随机值
    for j in range(cols):
        # 获取当前列的名称和值
        col_name = df_copy.columns[j]
        col_values = df_copy.iloc[:, j].values.tolist()
        
        # 计算需要添加的行数
        num_extra_values = j
        
        # 为该列添加特定的随机值
        for i in range(num_extra_values):
            # 计算在原始行数后面的索引
            row_idx = rows + i
            
            # 如果索引超出了当前DataFrame的范围，添加新行
            if row_idx >= len(df_copy):
                # 创建一个全NaN的新行
                new_row = pd.Series([np.nan] * cols, index=df_copy.columns)
                df_copy = pd.concat([df_copy, pd.DataFrame([new_row])], ignore_index=True)
            
            # 生成符合列特征的随机值
            random_val = generate_random_for_column(col_name, col_values)[0]
            
            # 设置随机值
            df_copy.iloc[row_idx, j] = random_val
    
    return df_copy, []

def add_null_values(df: pd.DataFrame, error_rate: float = 0.1) -> Tuple[pd.DataFrame, List[Tuple[int, int]]]:
    """
    根据提供的错误率设置空值
    
    Args:
        df: 输入的DataFrame
        error_rate: 错误率，表示需要设置为空值的单元格比例
    
    Returns:
        设置空值后的DataFrame和使用的坐标列表，格式为[(row, col), ...]
    """
    df_copy = df.copy(deep=True)
    rows, cols = df_copy.shape
    
    # 计算需要设置为空值的单元格数量
    total_cells = rows * cols
    num_nulls = int(total_cells * error_rate)
    
    # 生成所有可能的坐标
    all_coordinates = [(i, j) for i in range(rows) for j in range(cols)]
    
    # 随机选择坐标
    coordinates = random.sample(all_coordinates, min(num_nulls, len(all_coordinates)))
    
    # 设置空值
    for row, col in coordinates:
        # 检查坐标是否在DataFrame的范围内
        if 0 <= row < df_copy.shape[0] and 0 <= col < df_copy.shape[1]:
            df_copy.iloc[row, col] = None
    
    # 确保坐标格式正确，按照(row, col)的元组列表返回
    formatted_coordinates = [(int(row), int(col)) for row, col in coordinates]
    
    return df_copy, formatted_coordinates

def apply_error_makers(
    df: pd.DataFrame,
    error_type: str,
    error_rate: float = 0.1,
    error_order: str = 'ERROR',
    null_coordinates: List[Tuple[int, int]] = None,
    random_value_range: Tuple[float, float] = (0, 100)
) -> Tuple[pd.DataFrame, List, Optional[List[Tuple[int, int]]]]:
    """
    主函数：应用指定的错误制造方法
    
    Args:
        df: 输入的DataFrame
        error_type: 错误类型，可选值：'error', 'merge_rows', 'rotate_columns', 'rotate_rows', 
                    'add_end_row', 'add_end_column', 'null'
        error_rate: 错误率，用于'error'类型
        error_order: 替换标记，用于'error'类型
        null_coordinates: 空值坐标列表，用于'null'类型
        random_value_range: 随机值范围，用于'add_end_row'和'add_end_column'类型
    
    Returns:
        应用错误后的DataFrame，原始值列表，以及可选的错误位置列表
    """
    
    min_val, max_val = random_value_range
    
    if error_type == 'error':
        df_with_errors, original_values, error_positions = make_error(df, error_rate, error_order)
        return df_with_errors, original_values, error_positions
    elif error_type == 'merge_rows':
        return merge_rows(df) + (None,)
    elif error_type == 'rotate_columns':
        return rotate_columns(df) + (None,)
    elif error_type == 'rotate_rows':
        return rotate_rows(df) + (None,)
    elif error_type == 'add_end_row':
        return add_end_row(df, min_val, max_val) + (None,)
    elif error_type == 'add_end_column':
        return add_end_column(df, min_val, max_val) + (None,)
    elif error_type == 'null':
        df_with_nulls, null_positions = add_null_values(df, error_rate)
        return df_with_nulls, null_positions, null_positions
    else:
        raise ValueError(f"不支持的错误类型: {error_type}")
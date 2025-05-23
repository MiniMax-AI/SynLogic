import random
import numpy as np
from typing import List, Tuple, Dict
from games.tasks.futoshiki.scripts.futoshiki_prompt import get_prompt
import argparse

class FutoshikiGenerator:
    def generate_valid_grid(self, grid_size: int) -> np.ndarray:
        """Generate a valid Sudoku grid."""
        # 创建一个空的网格
        grid = np.zeros((grid_size, grid_size), dtype=int)
        
        # 生成第一行
        first_row = list(range(1, grid_size + 1))
        random.shuffle(first_row)
        grid[0] = first_row
        
        # 生成剩余的行
        for row in range(1, grid_size):
            # 获取当前可用的数字
            available = list(range(1, grid_size + 1))
            # 填充当前行
            for col in range(grid_size):
                # 获取当前列已使用的数字
                used_in_col = set(grid[:row, col])
                # 获取可用的数字
                valid_numbers = [n for n in available if n not in used_in_col]
                if not valid_numbers:
                    return self.generate_valid_grid(grid_size)  # 重新生成
                # 随机选择一个有效数字
                num = random.choice(valid_numbers)
                grid[row, col] = num
                available.remove(num)
        
        return grid
    
    def generate_inequality_constraints(self, grid_size: int, num_constraints: int) -> List[Tuple[Tuple[int, int], Tuple[int, int], str]]:
        """Generate random inequality constraints between grid cells."""
        constraints = []
        # 创建所有可能的相邻单元格对
        possible_pairs = []
        for i in range(grid_size):
            for j in range(grid_size):
                # 检查右边
                if j < grid_size - 1:
                    possible_pairs.append(((i, j), (i, j + 1)))
                # 检查下边
                if i < grid_size - 1:
                    possible_pairs.append(((i, j), (i + 1, j)))
        
        # 随机选择指定数量的约束
        selected_pairs = random.sample(possible_pairs, min(num_constraints, len(possible_pairs)))
        
        # 为每对生成随机的不等式符号
        for pair in selected_pairs:
            sign = random.choice(['>', '<'])
            constraints.append((pair[0], pair[1], sign))
        
        return constraints
    
    def select_prefilled_coordinates(self, grid_size: int, num_prefilled: int) -> List[Tuple[int, int]]:
        """Select random coordinates to be pre-filled."""
        # 创建所有可能的坐标
        all_coords = [(i, j) for i in range(grid_size) for j in range(grid_size)]
        # 随机选择指定数量的坐标
        return random.sample(all_coords, min(num_prefilled, len(all_coords)))
    
    def generate_prompt(self, 
                       grid: np.ndarray,
                       prefilled_coords: List[Tuple[int, int]],
                       constraints: List[Tuple[Tuple[int, int], Tuple[int, int], str]],
                       grid_size: int,
                       is_chinese: bool = False) -> str:
        """Generate the prompt string for the puzzle."""
        # 创建一个显示网格，未填充的位置用X表示
        display_grid = np.full((grid_size, grid_size), 'X')
        for row, col in prefilled_coords:
            display_grid[row, col] = str(grid[row, col])
        
        # 格式化网格
        formatted_grid = ""
        for row in display_grid:
            formatted_row = " ".join(row)
            formatted_grid += formatted_row + "\n"
        formatted_grid = formatted_grid.rstrip()
        
        # 格式化约束
        formatted_constraints = ""
        for (coord1, coord2, sign) in constraints:
            row1, col1 = coord1
            row2, col2 = coord2
            formatted_constraints += f"({row1+1},{col1+1}) {sign} ({row2+1},{col2+1})\n"
        formatted_constraints = formatted_constraints.rstrip()
        
        # 使用prompt模板生成提示语
        return get_prompt(formatted_grid, formatted_constraints, grid_size, is_chinese)
    
    def generate_sample(self,
                       grid_size: int,
                       num_inequality_signs: int,
                       num_prefilled_coords: int,
                       is_chinese: bool = False) -> Dict:
        """Generate a complete puzzle sample."""
        # 生成有效的网格
        grid = self.generate_valid_grid(grid_size)
        
        # 生成不等式约束
        constraints = self.generate_inequality_constraints(grid_size, num_inequality_signs)
        
        # 选择预填充坐标
        prefilled_coords = self.select_prefilled_coordinates(grid_size, num_prefilled_coords)
        
        # 生成提示语
        prompt = self.generate_prompt(grid, prefilled_coords, constraints, grid_size, is_chinese)
        
        # 将numpy数组转换为简单的嵌套列表
        answer = [[int(x) for x in row] for row in grid.tolist()]
        
        return {
            "question": prompt,
            "answer": answer,
            "metadata": {
                "grid_size": grid_size,
                "num_inequality_signs": num_inequality_signs,
                "num_prefilled_coords": num_prefilled_coords,
                "prefilled_coords": prefilled_coords,
                "constraints": constraints
            }
        }

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='Generate Futoshiki puzzle samples')
    parser.add_argument('--grid_size', type=int, default=4, help='Size of the grid (default: 4)')
    parser.add_argument('--num_inequality_signs', type=int, default=4, help='Number of inequality signs (default: 4)')
    parser.add_argument('--num_prefilled_coords', type=int, default=2, help='Number of pre-filled coordinates (default: 2)')
    parser.add_argument('--num_samples', type=int, default=10, help='Number of samples to generate (default: 10)')
    parser.add_argument('--is_chinese', action='store_true', help='Generate Chinese prompts (default: False)')
    parser.add_argument('--output', type=str, help='Specify the output file name (optional)')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 创建生成器实例
    generator = FutoshikiGenerator()
    
    # 生成样本
    samples = []
    for i in range(args.num_samples):
        sample = generator.generate_sample(
            grid_size=args.grid_size,
            num_inequality_signs=args.num_inequality_signs,
            num_prefilled_coords=args.num_prefilled_coords,
            is_chinese=args.is_chinese
        )
        samples.append(sample)
    
    # 保存样本到文件
    import json
    import os
    from datetime import datetime
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名
    if args.output:
        # 使用指定的文件名
        output_file = os.path.join(output_dir, args.output)
    else:
        # 使用时间戳生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"futoshiki_samples_{timestamp}.jsonl")
    
    # 保存样本为JSONL格式
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            # 将每个样本转换为一行JSON
            json_line = json.dumps(sample, ensure_ascii=False)
            f.write(json_line + "\n")
    
    print(f"已生成 {args.num_samples} 个样本并保存到: {output_file}")
    print(f"参数设置:")
    print(f"- 网格大小: {args.grid_size}x{args.grid_size}")
    print(f"- 不等式符号数量: {args.num_inequality_signs}")
    print(f"- 预填充数字数量: {args.num_prefilled_coords}")
    print(f"- 语言: {'中文' if args.is_chinese else '英文'}")

if __name__ == "__main__":
    main() 
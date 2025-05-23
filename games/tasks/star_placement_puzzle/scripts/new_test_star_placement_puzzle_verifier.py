import unittest
from games.tasks.star_placement_puzzle.scripts.star_placement_puzzle_verifier import StarPlacementPuzzleVerifier
from base.data import Data

class NewTestStarPlacementPuzzleVerifier(unittest.TestCase):
    """
    星星放置游戏验证器的新单元测试
    """
    
    def setUp(self):
        # 初始化验证器
        self.verifier = StarPlacementPuzzleVerifier()
        
        # 构建一个5x5的测试网格，有5个区域，每个区域需要放置星星
        self.test_region_grid = [
            ["B", "B", "A", "E", "E"],
            ["B", "A", "A", "A", "C"],
            ["B", "B", "A", "C", "C"],
            ["D", "D", "D", "D", "C"],
            ["E", "D", "E", "E", "C"]
        ]
        
        # 创建测试数据对象 - 每行每列每区域都有1颗星星
        self.test_data = Data(
            question="在每个区域放置星星，满足每行每列每区域有1颗星星，且星星不相邻",
            answer="",
            metadata={
                "n": 5,  # 5x5网格
                "k": 1,  # 每行/列/区域1颗星星
                "region_grid": self.test_region_grid
            }
        )
    
    def test_coordinates_standard_format(self):
        """
        测试标准格式的坐标数据
        """
        # 直接使用提取后的坐标格式
        coords = {
            "A": [(0, 0), (2, 2), (4, 4)],  # (1,1), (3,3), (5,5) -> 0索引
            "B": [(1, 3), (3, 1), (5, 5)],  # (2,4), (4,2), (6,6) -> 0索引
            "C": [(0, 4), (2, 0), (4, 2)]   # (1,5), (3,1), (5,3) -> 0索引
        }
        
        self.assertEqual(len(coords), 3, "应有3个区域的坐标")
        self.assertEqual(len(coords["A"]), 3, "A区域应有3个坐标")
        self.assertEqual(len(coords["B"]), 3, "B区域应有3个坐标")
        self.assertEqual(len(coords["C"]), 3, "C区域应有3个坐标")
        
        # 检查具体坐标值
        self.assertIn((0, 0), coords["A"])
        self.assertIn((2, 2), coords["A"])
        self.assertIn((4, 4), coords["A"])
        
        self.assertIn((1, 3), coords["B"])
        self.assertIn((3, 1), coords["B"])
        self.assertIn((5, 5), coords["B"])
    
    def test_coordinates_with_extra_data(self):
        """
        测试包含额外数据的坐标字典
        """
        # 直接使用提取后的坐标格式
        coords = {
            "A": [(0, 1), (3, 4)],  # (1,2), (4,5) -> 0索引
            "B": [(1, 2), (4, 5)],  # (2,3), (5,6) -> 0索引
            "C": [(2, 0), (5, 3)]   # (3,1), (6,4) -> 0索引
        }
        
        self.assertEqual(len(coords), 3, "应有3个区域的坐标")
        self.assertEqual(len(coords["A"]), 2, "A区域应有2个坐标")
        self.assertEqual(len(coords["B"]), 2, "B区域应有2个坐标")
        self.assertEqual(len(coords["C"]), 2, "C区域应有2个坐标")
    
    def test_valid_5x5_solution(self):
        """
        测试5x5网格的有效解决方案
        """
        # 5x5网格，每行每列每区域有1颗星星
        valid_coords = {
            "A": [(1, 2)],  # (2,3) -> (1,2)
            "B": [(0, 0)],  # (1,1) -> (0,0)
            "C": [(2, 4)],  # (3,5) -> (2,4)
            "D": [(3, 1)],  # (4,2) -> (3,1)
            "E": [(4, 3)]   # (5,4) -> (4,3)
        }
        
        result = self.verifier.verify(self.test_data, valid_coords)
        self.assertTrue(result, "应验证为有效解决方案")
    
    def test_invalid_row_constraint(self):
        """
        测试违反行约束的解决方案
        """
        # 第1行有2颗星星，违反每行只能有1颗星星的约束
        invalid_coords = {
            "A": [(0, 2)],  # (1,3) -> (0,2)
            "B": [(0, 0)],  # (1,1) -> (0,0) - 与上面在同一行
            "C": [(2, 4)],  # (3,5) -> (2,4)
            "D": [(3, 1)],  # (4,2) -> (3,1)
            "E": [(4, 3)]   # (5,4) -> (4,3)
        }
        
        result = self.verifier.verify(self.test_data, invalid_coords)
        self.assertFalse(result, "应验证为无效解决方案：违反行约束")
    
    def test_invalid_column_constraint(self):
        """
        测试违反列约束的解决方案
        """
        # 第1列有2颗星星，违反每列只能有1颗星星的约束
        invalid_coords = {
            "A": [(1, 2)],  # (2,3) -> (1,2)
            "B": [(0, 0)],  # (1,1) -> (0,0)
            "C": [(2, 0)],  # (3,1) -> (2,0) - 与上面在同一列
            "D": [(3, 1)],  # (4,2) -> (3,1)
            "E": [(4, 3)]   # (5,4) -> (4,3)
        }
        
        result = self.verifier.verify(self.test_data, invalid_coords)
        self.assertFalse(result, "应验证为无效解决方案：违反列约束")
    
    def test_invalid_region_constraint(self):
        """
        测试违反区域约束的解决方案
        """
        # A区域有2颗星星，违反每区域只能有1颗星星的约束
        invalid_coords = {
            "A": [(1, 2), (2, 2)],  # A区域2颗星星
            "B": [(0, 0)],
            "C": [(2, 4)],
            "D": [(3, 1)],
            "E": []  # E区域没有星星
        }
        
        result = self.verifier.verify(self.test_data, invalid_coords)
        self.assertFalse(result, "应验证为无效解决方案：违反区域约束")
    
    def test_invalid_adjacency_constraint(self):
        """
        测试违反相邻约束的解决方案
        """
        # 包含相邻的星星：(0,0)和(0,1)
        invalid_coords = {
            "A": [(1, 2)],
            "B": [(0, 0)],
            "C": [(2, 4)],
            "D": [(3, 1)],
            "E": [(0, 1)]  # 与B区域(0,0)相邻
        }
        
        result = self.verifier.verify(self.test_data, invalid_coords)
        self.assertFalse(result, "应验证为无效解决方案：存在相邻星星")
    
    def test_invalid_diagonal_adjacency(self):
        """
        测试违反对角线相邻约束的解决方案
        """
        # 包含对角线相邻的星星：(0,0)和(1,1)
        invalid_coords = {
            "A": [(1, 1)],  # 与B区域(0,0)对角线相邻
            "B": [(0, 0)],
            "C": [(2, 4)],
            "D": [(3, 2)],
            "E": [(4, 3)]
        }
        
        result = self.verifier.verify(self.test_data, invalid_coords)
        self.assertFalse(result, "应验证为无效解决方案：存在对角线相邻星星")
    
    def test_out_of_bounds_coordinates(self):
        """
        测试超出网格范围的坐标
        """
        # 包含超出5x5网格范围的坐标
        invalid_coords = {
            "A": [(1, 2)],
            "B": [(0, 0)],
            "C": [(2, 4)],
            "D": [(3, 1)],
            "E": [(5, 3)]  # 超出范围
        }
        
        result = self.verifier.verify(self.test_data, invalid_coords)
        self.assertFalse(result, "应验证为无效解决方案：坐标超出范围")
    
    def test_duplicate_coordinates(self):
        """
        测试重复坐标的情况
        """
        # 包含重复坐标(1,2)
        invalid_coords = {
            "A": [(1, 2)],
            "B": [(0, 0)],
            "C": [(1, 2)],  # 与A区域重复
            "D": [(3, 1)],
            "E": [(4, 3)]
        }
        
        result = self.verifier.verify(self.test_data, invalid_coords)
        self.assertFalse(result, "应验证为无效解决方案：存在重复坐标")

if __name__ == "__main__":
    unittest.main() 
import unittest
from games.tasks.skyscraper_puzzle.scripts.skyscraper_puzzle_verifier import SkyscraperPuzzleVerifier
from base.data import Data

class TestSkyscraperPuzzleVerifier(unittest.TestCase):
    """
    测试摩天楼游戏验证器功能
    """
    def setUp(self):
        """初始化测试环境"""
        self.verifier = SkyscraperPuzzleVerifier()
        
        # 创建一个简单的4x4游戏实例
        self.game_data = Data(
            question="摩天楼游戏示例",
            answer="",
            metadata={
                "n": 4,
                "top": [1, 3, 2, 3],
                "bottom": [3, 1, 3, 2],
                "left": [1, 3, 2, 2],
                "right": [3, 2, 1, 2]
            }
        )
    
    def test_verify_correct_answer(self):
        """测试验证正确答案"""
        # 一个正确的4x4解答
        correct_grid = [
            [4, 2, 3, 1],
            [1, 3, 4, 2],
            [3, 1, 2, 4],
            [2, 4, 1, 3]
        ]
        
        # 验证结果应该为True
        self.assertTrue(self.verifier.verify(self.game_data, correct_grid))
    
    def test_verify_incorrect_answer_wrong_height(self):
        """测试验证高度错误的答案"""
        # 一个高度不在范围内的错误解答
        wrong_grid = [
            [4, 3, 2, 1],
            [3, 2, 5, 4], # 注意这里的5超出了范围
            [1, 4, 3, 2],
            [2, 1, 4, 3]
        ]
        
        # 验证结果应该为False
        self.assertFalse(self.verifier.verify(self.game_data, wrong_grid))
    
    def test_verify_incorrect_answer_duplicate_in_row(self):
        """测试验证行内有重复数字的答案"""
        # 一个行内有重复数字的错误解答
        wrong_grid = [
            [4, 3, 2, 1],
            [3, 2, 1, 3], # 注意这一行有两个3
            [1, 4, 3, 2],
            [2, 1, 4, 3]
        ]
        
        # 验证结果应该为False
        self.assertFalse(self.verifier.verify(self.game_data, wrong_grid))
    
    def test_verify_incorrect_answer_duplicate_in_column(self):
        """测试验证列内有重复数字的答案"""
        # 一个列内有重复数字的错误解答
        wrong_grid = [
            [4, 3, 2, 1],
            [3, 2, 1, 4],
            [1, 3, 3, 2], # 注意这里第二列和第三列都有重复
            [2, 1, 4, 3]
        ]
        
        # 验证结果应该为False
        self.assertFalse(self.verifier.verify(self.game_data, wrong_grid))
    
    def test_verify_incorrect_answer_wrong_visibility(self):
        """测试验证可见性错误的答案"""
        # 一个可见性与提示不符的错误解答
        wrong_grid = [
            [1, 3, 2, 4], # 从上看第一列可见摩天楼数量为4，而期望是1
            [3, 2, 1, 4],
            [1, 4, 3, 2],
            [2, 1, 4, 3]
        ]
        
        # 验证结果应该为False
        self.assertFalse(self.verifier.verify(self.game_data, wrong_grid))
    
    def test_verify_string_input(self):
        """测试验证器处理字符串输入（提取失败的情况）"""
        # 提供一个无法提取网格的字符串
        invalid_answer = "我无法解决这个问题"
        
        # 验证结果应该为False
        self.assertFalse(self.verifier.verify(self.game_data, invalid_answer))

if __name__ == "__main__":
    unittest.main() 
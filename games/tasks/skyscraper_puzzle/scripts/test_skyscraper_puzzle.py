import unittest
from games.tasks.skyscraper_puzzle.scripts.skyscraper_puzzle import SkyscraperPuzzle

class TestSkyscraperPuzzle(unittest.TestCase):
    """
    测试摩天楼游戏生成功能
    """
    def setUp(self):
        """初始化测试环境"""
        self.game = SkyscraperPuzzle(n=4)
    
    def test_generate_single_game(self):
        """测试生成单个游戏数据"""
        game_data_list = self.game.generate(num_of_questions=1)
        
        # 验证生成了一条游戏数据
        self.assertEqual(len(game_data_list), 1)
        
        # 验证游戏数据的元数据
        game_data = game_data_list[0]
        metadata = game_data.metadata
        
        # 检查必要的元数据字段
        self.assertIn('n', metadata)
        self.assertIn('solved_grid', metadata)
        self.assertIn('top', metadata)
        self.assertIn('bottom', metadata)
        self.assertIn('left', metadata)
        self.assertIn('right', metadata)
        
        # 验证网格大小
        n = metadata['n']
        self.assertTrue(3 <= n <= 5)
        
        # 验证解答网格
        solved_grid = metadata['solved_grid']
        self.assertEqual(len(solved_grid), n)
        for row in solved_grid:
            self.assertEqual(len(row), n)
        
        # 验证提示数字
        self.assertEqual(len(metadata['top']), n)
        self.assertEqual(len(metadata['bottom']), n)
        self.assertEqual(len(metadata['left']), n)
        self.assertEqual(len(metadata['right']), n)
    
    def test_generate_multiple_games(self):
        """测试生成多个游戏数据"""
        game_data_list = self.game.generate(num_of_questions=3)
        
        # 验证生成了三条游戏数据
        self.assertEqual(len(game_data_list), 3)
        
        # 检查每条数据的基本结构
        for game_data in game_data_list:
            metadata = game_data.metadata
            n = metadata['n']
            
            # 验证基本元数据
            self.assertTrue(3 <= n <= 5)
            self.assertEqual(len(metadata['solved_grid']), n)
            self.assertEqual(len(metadata['top']), n)
            self.assertEqual(len(metadata['bottom']), n)
            self.assertEqual(len(metadata['left']), n)
            self.assertEqual(len(metadata['right']), n)
    
    def test_skyscraper_visibility(self):
        """测试摩天楼可见性计算是否正确"""
        # 测试一个简单的例子
        heights = [3, 1, 4, 2]
        visible_count = self.game._count_visible_skyscrapers(heights)
        
        # 从左往右看，能看到3、4两座摩天楼（1被3挡住，2被4挡住）
        self.assertEqual(visible_count, 2)
        
        # 再测试一个例子
        heights = [2, 1, 5, 3, 4]
        visible_count = self.game._count_visible_skyscrapers(heights)
        
        # 从左往右看，能看到2、5两座摩天楼（1被2挡住，3和4被5挡住）
        self.assertEqual(visible_count, 2)

if __name__ == "__main__":
    unittest.main() 
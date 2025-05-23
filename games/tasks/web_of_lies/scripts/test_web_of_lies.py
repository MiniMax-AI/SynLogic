import unittest
import random
import sys
import os

# 添加项目根目录到路径，以便正确导入模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from games.tasks.web_of_lies.scripts.web_of_lies import WebOfLies

class TestWebOfLies(unittest.TestCase):
    """
    谎言之网游戏测试类
    """
    def setUp(self):
        """
        测试前的准备工作
        """
        # 设置随机种子，使测试结果可重现
        random.seed(42)
        self.game = WebOfLies()
    
    def test_simple_statement_type(self):
        """
        测试基础陈述类型（statement_type=0）
        """
        # 生成一个游戏实例，使用基础陈述类型
        try:
            game_data_list = self.game.generate(
                num_of_questions=1,
                max_attempts=100,
                num_person=6,
                difficulty=2,
                statement_type=0
            )
            
            # 验证是否成功生成
            self.assertEqual(len(game_data_list), 1, "应该成功生成一个游戏实例")
            
            # 获取元数据
            metadata = game_data_list[0].metadata
            people_metadata = metadata["people"]
            
            # 验证所有陈述都是 SimpleStatement
            all_simple = True
            for person in people_metadata:
                for statement in person["statements"]:
                    if statement["type"] != "simple":
                        all_simple = False
                        print(f"发现非简单陈述: {statement['type']}")
                        break
                if not all_simple:
                    break
            
            self.assertTrue(all_simple, "当 statement_type=0 时，所有陈述应该是 SimpleStatement")
            print("基础陈述类型测试通过！")
        except Exception as e:
            self.fail(f"测试基础陈述类型时出错: {str(e)}")
    
    def test_extended_statement_types(self):
        """
        测试扩展陈述类型（statement_type=1）
        """
        # 生成多个游戏实例，增加找到高级陈述类型的概率
        attempts = 0
        max_attempts = 5
        
        for _ in range(max_attempts):
            try:
                game_data_list = self.game.generate(
                    num_of_questions=1,
                    max_attempts=100,
                    num_person=8,  # 使用更多人物增加生成高级陈述的概率
                    difficulty=3,
                    statement_type=1
                )
                
                print(f"成功生成扩展陈述类型游戏实例")
                
                # 统计不同类型的陈述数量
                statement_types = {"simple": 0, "at_least_one": 0, "same_type": 0}
                
                for person in game_data_list[0].metadata["people"]:
                    for statement in person["statements"]:
                        if statement["type"] in statement_types:
                            statement_types[statement["type"]] += 1
                
                print(f"陈述类型统计: {statement_types}")
                
                # 游戏逻辑保证唯一解
                valid_solutions = game_data_list[0].metadata["valid_solutions"]
                self.assertEqual(len(valid_solutions), 1, "游戏应该有唯一解")
                
                return  # 成功生成后退出循环
                
            except Exception as e:
                print(f"尝试 {attempts+1} 失败: {str(e)}")
                attempts += 1
        
        self.fail(f"在 {max_attempts} 次尝试中未能成功生成游戏实例")

if __name__ == "__main__":
    unittest.main() 
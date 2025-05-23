import random
import json
import uuid
import argparse
import pathlib
import os
import re
import copy
from typing import List, Dict, Tuple, Any

from games.base.game import Game
from base.data import Data
from games.tasks.goods_exchange.scripts.goods_exchange_verifier import GoodsExchangeVerifier
from games.tasks.goods_exchange.scripts.goods_exchange_prompt import (
    prompt_goods_exchange, 
    chinese_names, english_names,
    chinese_colors, english_colors,
    chinese_categories, english_categories,
    chinese_operations, english_operations
)

class GoodsExchange(Game):
    """
    物品交换游戏类
    """
    def __init__(self):
        """
        初始化物品交换游戏
        """
        super().__init__("Goods Exchange", GoodsExchangeVerifier)
        
    def generate(self, num_of_questions: int = 100, max_attempts: int = 100,
                 num_people: int = 5, operator_num: int = 3):
        """
        生成物品交换游戏的题目
        
        @param num_of_questions: 要生成的题目数量
        @param max_attempts: 每个题目的最大尝试次数
        @param num_people: 人物数量
        @param operator_num: 交换操作数量
        @return: 生成的题目列表
        """
        # 参数校验
        if num_people <= 1:
            raise ValueError("人物数量必须大于1")
        if operator_num <= 0:
            raise ValueError("交换操作数量必须为正整数")
            
        game_data_list = []
        attempts = 0
        
        while len(game_data_list) < num_of_questions and attempts < max_attempts:
            try:
                attempts += 1
                
                # 选择语言（中文/英文）
                is_chinese = random.choice([True, False])
                
                # 生成人物名称
                names = self._generate_names(num_people, is_chinese)
                
                # 生成物品
                objects = self._generate_objects(num_people, is_chinese)
                
                # 初始化物品归属
                owns_before = self._initialize_ownership(names, objects)
                
                # 生成交换操作，并计算最终归属
                operations, owns_after = self._generate_operations(names, objects, owns_before, operator_num, is_chinese)
                
                # 生成题目描述
                question = prompt_goods_exchange(
                    n=num_people,
                    names=names,
                    objects=objects,
                    owns_before=owns_before,
                    operations=operations,
                    is_chinese=is_chinese
                )
                
                # 格式化最终归属关系为答案字符串
                answer = self._format_ownership_as_answer(owns_after)
                
                # 创建游戏数据
                game_data = Data(
                    question=question,
                    answer=answer,
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "num_people": num_people,
                        "operator_num": operator_num,
                        "names": names,
                        "objects": objects,
                        "owns_before": owns_before,
                        "operations": operations,
                        "owns_after": answer,
                        "is_chinese": is_chinese
                    }
                )
                
                game_data_list.append(game_data)
                
            except Exception as e:
                print(f"生成题目时出错: {e}")
                continue
                
        if len(game_data_list) < num_of_questions:
            print(f"警告: 只能生成 {len(game_data_list)}/{num_of_questions} 条游戏数据")
        
        return game_data_list
    
    def _generate_names(self, num_people: int, is_chinese: bool = False) -> List[str]:
        """
        生成人物名称
        
        @param num_people: 需要的人物数量
        @param is_chinese: 是否生成中文名称
        @return: 人物名称列表
        """
        name_pool = chinese_names if is_chinese else english_names
        return random.sample(name_pool, num_people)
    
    def _generate_objects(self, num_objects: int, is_chinese: bool = False) -> List[str]:
        """
        生成物品列表
        
        @param num_objects: 需要的物品数量
        @param is_chinese: 是否生成中文物品名称
        @return: 物品列表
        """
        colors = chinese_colors if is_chinese else english_colors
        categories = chinese_categories if is_chinese else english_categories
        
        # 为了增加难度，增加物品中存在相同颜色或者相同品类的概率
        # 策略：选择较少的颜色和品类范围，导致重复概率增加
        color_range = min(len(colors), num_objects + random.randint(0, 2))
        category_range = min(len(categories), num_objects + random.randint(0, 2))
        
        selected_colors = random.sample(colors, color_range)
        selected_categories = random.sample(categories, category_range)
        
        objects = []
        for _ in range(num_objects):
            color = random.choice(selected_colors)
            category = random.choice(selected_categories)
            obj = f"{color}{category}" if is_chinese else f"{color} {category}"
            
            # 确保没有完全重复的物品
            while obj in objects:
                color = random.choice(selected_colors)
                category = random.choice(selected_categories)
                obj = f"{color}{category}" if is_chinese else f"{color} {category}"
                
            objects.append(obj)
            
        return objects
    
    def _initialize_ownership(self, names: List[str], objects: List[str]) -> Dict[str, str]:
        """
        初始化人物与物品的归属关系
        
        @param names: 人物列表
        @param objects: 物品列表
        @return: 初始归属关系字典 {人名: 物品}
        """
        # 随机打乱物品顺序
        shuffled_objects = random.sample(objects, len(objects))
        return {name: obj for name, obj in zip(names, shuffled_objects)}
    
    def _generate_operations(self, names: List[str], objects: List[str], 
                            initial_ownership: Dict[str, str], num_operations: int,
                            is_chinese: bool = False) -> Tuple[List[str], Dict[str, str]]:
        """
        生成交换操作和计算最终归属关系
        
        @param names: 人物列表
        @param objects: 物品列表
        @param initial_ownership: 初始归属关系
        @param num_operations: 操作数量
        @param is_chinese: 是否使用中文
        @return: (操作描述列表, 最终归属关系)
        """
        operations = []
        current_ownership = copy.deepcopy(initial_ownership)
        
        # 获取人物到物品和物品到人物的映射
        person_to_item = current_ownership
        item_to_person = {item: person for person, item in current_ownership.items()}
        
        # 获取操作模板
        op_templates = chinese_operations if is_chinese else english_operations
        
        for _ in range(num_operations):
            # 随机选择操作类型
            operation_type = random.choice(list(op_templates.keys()))
            
            # 根据操作类型执行不同的交换逻辑
            if operation_type == "operation1":  # 两人互换所有物品
                name1, name2 = random.sample(names, 2)
                
                # 执行交换
                item1 = person_to_item[name1]
                item2 = person_to_item[name2]
                
                person_to_item[name1] = item2
                person_to_item[name2] = item1
                
                item_to_person[item1] = name2
                item_to_person[item2] = name1
                
                # 生成操作描述
                operations.append(op_templates[operation_type].format(
                    name1=name1, name2=name2
                ))
                
            elif operation_type == "operation2":  # 两个物品的主人互换这些物品
                obj1, obj2 = random.sample(objects, 2)
                
                # 获取物品的主人
                owner1 = item_to_person[obj1]
                owner2 = item_to_person[obj2]
                
                # 执行交换
                person_to_item[owner1] = obj2
                person_to_item[owner2] = obj1
                
                item_to_person[obj1] = owner2
                item_to_person[obj2] = owner1
                
                # 生成操作描述
                operations.append(op_templates[operation_type].format(
                    object1=obj1, object2=obj2
                ))
                
            elif operation_type == "operation3":  # 持有物品的人和指定人互换
                obj1 = random.choice(objects)
                name1 = random.choice([name for name in names if name != item_to_person[obj1]])
                
                # 获取obj1的主人和name1的物品
                owner1 = item_to_person[obj1]
                item1 = person_to_item[name1]
                
                # 执行交换
                person_to_item[owner1] = item1
                person_to_item[name1] = obj1
                
                item_to_person[obj1] = name1
                item_to_person[item1] = owner1
                
                # 生成操作描述
                operations.append(op_templates[operation_type].format(
                    object1=obj1, name1=name1
                ))
                
            elif operation_type == "operation4":  # name1用object1换取object2
                name1 = random.choice(names)
                obj1 = person_to_item[name1]
                obj2 = random.choice([obj for obj in objects if obj != obj1])
                
                # 获取obj2的主人
                owner2 = item_to_person[obj2]
                
                # 执行交换
                person_to_item[name1] = obj2
                person_to_item[owner2] = obj1
                
                item_to_person[obj1] = owner2
                item_to_person[obj2] = name1
                
                # 生成操作描述
                operations.append(op_templates[operation_type].format(
                    name1=name1, object1=obj1, object2=obj2
                ))
                
            elif operation_type == "operation5":  # name1把object1送给name2，name2把object2送给name1
                name1, name2 = random.sample(names, 2)
                obj1 = person_to_item[name1]
                obj2 = person_to_item[name2]
                
                # 执行交换
                person_to_item[name1] = obj2
                person_to_item[name2] = obj1
                
                item_to_person[obj1] = name2
                item_to_person[obj2] = name1
                
                # 生成操作描述
                operations.append(op_templates[operation_type].format(
                    name1=name1, name2=name2, object1=obj1, object2=obj2
                ))
                
            elif operation_type == "operation6":  # name1把object1和name2的object2交换
                name1, name2 = random.sample(names, 2)
                obj1 = person_to_item[name1]
                obj2 = person_to_item[name2]
                
                # 执行交换
                person_to_item[name1] = obj2
                person_to_item[name2] = obj1
                
                item_to_person[obj1] = name2
                item_to_person[obj2] = name1
                
                # 生成操作描述
                operations.append(op_templates[operation_type].format(
                    name1=name1, name2=name2, object1=obj1, object2=obj2
                ))
                
            elif operation_type == "operation7":  # 拥有object1的人和拥有object2的人交换
                obj1, obj2 = random.sample(objects, 2)
                
                # 获取物品的主人
                owner1 = item_to_person[obj1]
                owner2 = item_to_person[obj2]
                
                # 执行交换
                person_to_item[owner1] = obj2
                person_to_item[owner2] = obj1
                
                item_to_person[obj1] = owner2
                item_to_person[obj2] = owner1
                
                # 生成操作描述
                operations.append(op_templates[operation_type].format(
                    object1=obj1, object2=obj2
                ))
                
            elif operation_type in ["operation8", "operation9", "operation10"]:  # 干扰操作，不执行实际交换
                if operation_type == "operation8":  # name1想和name2交换，但是name2拒绝了
                    name1, name2 = random.sample(names, 2)
                    operations.append(op_templates[operation_type].format(
                        name1=name1, name2=name2
                    ))
                elif operation_type == "operation9":  # name1很喜欢object2
                    name1 = random.choice(names)
                    obj2 = random.choice([obj for obj in objects if obj != person_to_item[name1]])
                    operations.append(op_templates[operation_type].format(
                        name1=name1, object2=obj2
                    ))
                elif operation_type == "operation10":  # name1正在寻找object1，但是找不到
                    name1 = random.choice(names)
                    obj1 = random.choice([obj for obj in objects if obj != person_to_item[name1]])
                    operations.append(op_templates[operation_type].format(
                        name1=name1, object1=obj1
                    ))
                    
                elif operation_type == "operation11":  # name1主动和拥有object1的人交换
                    obj1 = random.choice(objects)
                    owner1 = item_to_person[obj1]
                    
                    # 选择一个不是object1拥有者的人
                    name1 = random.choice([name for name in names if name != owner1])
                    obj2 = person_to_item[name1]
                    
                    # 执行交换
                    person_to_item[owner1] = obj2
                    person_to_item[name1] = obj1
                    
                    item_to_person[obj1] = name1
                    item_to_person[obj2] = owner1
                    
                    # 生成操作描述
                    operations.append(op_templates[operation_type].format(
                        name1=name1, object1=obj1
                    ))
                    
                elif operation_type == "operation13":  # 三方物品交换
                    if len(names) >= 3:  # 确保有足够的人
                        # 随机选择三个不同的人
                        name1, name2, name3 = random.sample(names, 3)
                        
                        # 获取每个人的物品
                        obj1 = person_to_item[name1]
                        obj2 = person_to_item[name2]
                        obj3 = person_to_item[name3]
                        
                        # 执行三方交换：name1 -> name2 -> name3 -> name1
                        person_to_item[name2] = obj1
                        person_to_item[name3] = obj2
                        person_to_item[name1] = obj3
                        
                        item_to_person[obj1] = name2
                        item_to_person[obj2] = name3
                        item_to_person[obj3] = name1
                        
                        # 生成操作描述
                        operations.append(op_templates[operation_type].format(
                            name1=name1, name2=name2, name3=name3
                        ))
                    else:
                        # 如果人数不足，回退到简单的两人交换
                        name1, name2 = random.sample(names, 2)
                        
                        # 执行交换
                        item1 = person_to_item[name1]
                        item2 = person_to_item[name2]
                        
                        person_to_item[name1] = item2
                        person_to_item[name2] = item1
                        
                        item_to_person[item1] = name2
                        item_to_person[item2] = name1
                        
                        # 生成操作描述
                        operations.append(op_templates["operation1"].format(
                            name1=name1, name2=name2
                        ))
        
        # 返回操作列表和最终归属关系
        return operations, person_to_item
    
    def _format_ownership_as_answer(self, ownership: Dict[str, str]) -> str:
        """
        将归属关系格式化为答案字符串
        
        @param ownership: 归属关系字典 {人名: 物品}
        @return: 格式化的答案字符串，格式为 tuple 结构：(('人1','物品1'),('人2','物品2'),...)
        """
        formatted_pairs = []
        for person, item in ownership.items():
            formatted_pairs.append(f"('{person}','{item}')")
        return f"({','.join(formatted_pairs)})"
        
    def extract_answer(self, text):
        """从文本中提取答案。
        
        Args:
            text (str): 输入文本
            
        Returns:
            str: 提取的答案，格式为 "(('人1','物品1'),('人2','物品2'),...)"
        """
        if not text:
            return ""
        
        # 尝试从 Python markdown 代码块中提取
        code_block_pattern = r'```python\s*\n(.*?)\n```'
        code_blocks = re.findall(code_block_pattern, text, re.DOTALL)
        if code_blocks:
            # 使用最后一个代码块
            last_block = code_blocks[-1].strip()
            if last_block.startswith("(") and last_block.endswith(")"):
                return last_block
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="物品交换游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个题目的最大尝试次数")
    parser.add_argument("--num_people", type=int, default=5, help="人物数量")
    parser.add_argument("--operator_num", type=int, default=3, help="交换操作数量")
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置输出文件名
    output_dir = data_dir / f"num_people_{args.num_people}/operator_num_{args.operator_num}/num_of_data_{args.num_of_data}"
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "data.jsonl"
    
    # 创建游戏实例
    game = GoodsExchange()
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts,
        num_people=args.num_people,
        operator_num=args.operator_num
    )
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据")
    
    # 将数据保存到文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"游戏数据已保存到 {output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}") 
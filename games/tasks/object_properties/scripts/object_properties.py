#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import json
import os
import argparse
from pathlib import Path
import inflect
import uuid
from games.base.game import Game
from games.tasks.object_properties.scripts.object_properties_verifier import ObjectPropertiesVerifier
from games.tasks.object_properties.scripts.object_properties_prompt import *
from base.data import Data
import pathlib
"""
物品属性游戏生成器
生成包含多个属性的物品集合，并通过一系列变换后提出计数问题
"""
class ObjectProperties(Game):
    def __init__(self, transformation_range=[2,3], feature_num=7, num_range=[10,15], language_type="mixed"):
        super().__init__("object_properties", ObjectPropertiesVerifier)
        self.transformation_low = transformation_range[0]
        self.transformation_high = transformation_range[1]
        self.feature_num = feature_num
        self.num_low = num_range[0]
        self.num_high = num_range[1]
        self.language_type = language_type
        # 物品属性
        self.total_sizes = ["extra-extra-small", "extra-small", "small", "medium", "large", "extra-large", "extra-extra-large"]
        self.total_sizes_cn = ["超超小", "超小", "小", "中", "大", "超大", "超超大"]
        self.total_countries = ["Turkish", "German", "French", "Italian", "Japanese", "Chinese", "Russian", "British", 
                         "Polish", "Brazilian", "Mexican", "Canadian", "Afghan", "Iranian", "Portuguese"]
        self.total_countries_cn = ["土耳其", "德国", "法国", "意大利", "日本", "中国", "俄罗斯", "英国", "波兰", "巴西", "墨西哥", "加拿大", "阿富汗", "伊朗", "葡萄牙"]
        self.items = ["pen", "ball", "ruler", "hammer", "shoe", "bag", "bicycle", "screwdriver", "book", 
                      "umbrella", "key", "scissors", "fork", "speaker", "candle", "vase", "brush", "bird", 
                      "pencil", "drill", "lamp", "bottle", "house", "bowl", "sunglasses", "earring", "clock", 
                      "trash can", "plate", "chair"]
        self.items_cn = ["笔", "球", "尺子", "锤子", "鞋", "包", "自行车", "螺丝刀", "书", "伞", "钥匙", "剪刀", "叉子", "扬声器", "蜡烛", "花瓶", "刷子", "鸟", "铅笔", "钻头", "灯", "瓶子", "房子", "碗", "太阳镜", "耳环", "钟", "垃圾桶", "盘子", "椅子"]
        self.total_materials = ["plastic", "glass", "steel", "ceramic", "concrete","wood", "metal", "fabric", "leather", "paper", "rubber", "diamond", "gold", "silver", "platinum", "titanium"]
        self.total_materials_cn = ["塑料", "玻璃", "钢", "陶瓷", "混凝土", "木头", "金属", "布", "皮革", "纸", "橡胶", "钻石", "金", "银", "铂金", "钛"]
        self.total_smells = ["wet dog", "baking bread", "pine needles", "burning wood", "garlic", "vinegar", 
                      "rose", "popcorn", "coconut", "vanilla", "coffee", "chocolate", "gasoline", 
                      "citrus fruits", "lavender", "leather"]
        self.total_smells_cn = ["湿狗", "烤面包", "松针", "燃烧的木头", "大蒜", "醋", "玫瑰", "爆米花", "椰子", "香草", "咖啡", "巧克力", "汽油", "柑橘", "薰衣草", "皮革"]
        self.total_colors = ["beige", "black", "blue", "brown", "crimson", "cyan", "gold", "gray", "green", 
                      "indigo", "magenta", "maroon", "orange", "purple", "red", "silver", "teal", 
                      "turquoise", "violet", "white", "yellow"]
        self.total_colors_cn = ["米色", "黑色", "蓝色", "棕色", "深红色", "青色", "金色", "灰色", "绿色", "靛蓝色", "品红色", "栗色", "橙色", "紫色", "红色", "银色", "青绿色", "绿松石色", "紫罗兰色", "白色", "黄色"]
        self.person = ["my aunt", "my brother", "my sister", "my mom", "my fiance", "my cousin", "my neighbor"]
        self.person_cn = ["我阿姨", "我哥哥", "我姐姐", "我妈妈", "我未婚夫", "我表亲", "我邻居"]
        
        # 初始化inflect引擎
        self.p = inflect.engine()
        
        # 定义变化语料库
        self.transformations = [
            {
                "description": "Then, for each item of size {sizes} in my collection, {person} took it but then gave me another one of the same item made of her favorite material {new_materials} and with a smell of {new_smells} (all other properties the same).",
                "description_cn": "然后，对于我收藏中每一个尺寸为{sizes}的物品，{person}拿走了它，但又给了我同样物品的另一个版本，材质是{new_materials}，气味是{new_smells}（其他属性相同）。",
                "apply": self.aunt_transform
            },
            {
                "description": "Then, {person} replaced any item of size {sizes} in my new collection with an exact copy but with size {new_sizes} and another exact copy but with color {new_colors}.",
                "description_cn": "然后，{person}用两个副本替换了我新收藏中所有尺寸为{sizes}的物品，一个副本尺寸变为{new_sizes}，另一个副本颜色变为{new_colors}。",
                "apply": self.brother_transform
            },
            {
                "description": "Then, for any item made of {materials} in my new collection, {person} changed their color to {new_colors} and changed their smell to {new_smells}.",
                "description_cn": "然后，对于我新收藏中所有由{materials}制成的物品，{person}将它们的颜色改为{new_colors}，气味改为{new_smells}。",
                "apply": self.sister_transform
            },
            {
                "description": "Then, for any item of color {colors} in my new collection, {person} gave me another one of the same item, but with color {new_colors}, {new_countries} origin, {new_sizes} size, {new_smells} smell, and made of {new_materials}.",
                "description_cn": "然后，对于我新收藏中所有颜色为{colors}的物品，{person}给了我同样物品的另一个版本，但颜色是{new_colors}，产地是{new_countries}，尺寸是{new_sizes}，气味是{new_smells}，材质是{new_materials}。",
                "apply": self.mom_transform
            },
            {
                "description": "Then, {person} compared my new collection with my initial collection and if there was an item in my new collection with a (smell, color) pair that was different from all items in my initial collection, she added another copy of that to my new collection.",
                "description_cn": "然后，{person}比较了我的新收藏和初始收藏，如果在我的新收藏中有一个物品的(气味,颜色)组合与初始收藏中所有物品都不同，她就在我的新收藏中添加了该物品的另一个副本。",
                "apply": self.fiance_transform
            },
            {
                "description": "Then, I lost all of the {sizes} items in my collection.", 
                "description_cn": "然后，我丢失了收藏中所有尺寸为{sizes}的物品。",
                "apply": self.lost_item_transform
            },
            {
                "description": "Then, {person} picked all {colors} item and changed its material to {new_materials}.", 
                "description_cn": "然后，{person}挑选了所有{colors}颜色的物品，并将它们的材质改为{new_materials}。",
                "apply": self.cousin_transform
            },
            {
                "description": "Then, {person} traded me all items of {countries} origin for the same number of items with {new_sizes} size and {new_materials} material.",
                "description_cn": "然后，{person}用同等数量的尺寸为{new_sizes}、材质为{new_materials}的物品，交换了我收藏中所有{countries}产地的物品。",
                "apply": self.neighbor_transform
            },
            {
                "description": "Then, for every item with {smells} smell, I decided to add a twin item but with {new_colors} color instead.",
                "description_cn": "然后，对于每一个气味为{smells}的物品，我决定添加一个副本物品，但颜色改为{new_colors}。",
                "apply": self.twin_item_transform
            },
            {
                "description": "Then, I accidentally spilled paint on all my {sizes} items, changing their colors to {new_colors}.",
                "description_cn": "然后，我不小心在所有尺寸为{sizes}的物品上洒了颜料，将它们的颜色变成了{new_colors}。",
                "apply": self.spill_paint_transform
            }
        ]
    
    def aunt_transform(self, collection, original_collection, params):
        """阿姨替换物品"""
        size = params["sizes"]
        material = params["new_materials"]
        smell = params["new_smells"]
        
        for i, item in enumerate(collection):
            if item["sizes"] == size:
                collection[i]["materials"] = material
                collection[i]["smells"] = smell
        
        return collection
    
    def brother_transform(self, collection, original_collection, params):
        """兄弟替换物品"""
        size = params["sizes"]
        new_size = params["new_sizes"]
        color = params["new_colors"]
        
        # 找出所有指定尺寸的物品
        size_items = []
        for i, item in enumerate(collection):
            if item["sizes"] == size:
                size_items.append(item.copy())
                item["sizes"] = new_size
        
        # 添加新颜色的副本
        for item in size_items:
            color_copy = item.copy()
            color_copy["colors"] = color
            collection.append(color_copy)
        
        return collection
    
    def sister_transform(self, collection, original_collection, params):
        """姐姐改变特定材质物品"""
        material = params["materials"]
        color = params["new_colors"]
        smell = params["new_smells"]
        
        for item in collection:
            if item["materials"] == material:
                item["colors"] = color
                item["smells"] = smell
        
        return collection
    
    def mom_transform(self, collection, original_collection, params):
        """妈妈添加特定物品"""
        color = params["colors"]
        new_color = params["new_colors"]
        origin = params["new_countries"]
        size = params["new_sizes"]
        smell = params["new_smells"]
        material = params["new_materials"]
        
        items_to_copy = []
        for item in collection:
            if item["colors"] == color:
                items_to_copy.append(item)
        
        for item in items_to_copy:
            new_item = item.copy()
            new_item["colors"] = new_color
            new_item["countries"] = origin
            new_item["sizes"] = size
            new_item["smells"] = smell
            new_item["materials"] = material
            collection.append(new_item)
        
        return collection
    
    def fiance_transform(self, collection, original_collection, params):
        """未婚夫比较添加"""
        # 获取原始集合中所有的(smell, color)对
        original_smell_color_pairs = set()
        for item in original_collection:
            original_smell_color_pairs.add((item["smells"], item["colors"]))
        
        # 检查新集合中的(smell, color)对，如果是新的，添加副本
        items_to_add = []
        for item in collection:
            if (item["smells"], item["colors"]) not in original_smell_color_pairs:
                items_to_add.append(item.copy())
        
        collection.extend(items_to_add)
        return collection
    
    def lost_item_transform(self, collection, original_collection, params):
        """丢失所有特定尺寸物品"""
        size = params["sizes"]
        
        new_collections = [item for item in collection if item["sizes"] != size]
        
        return new_collections
    
    def cousin_transform(self, collection, original_collection, params):
        """表亲改变特定颜色物品的材质"""
        color = params["colors"]
        material = params["new_materials"]
        
        for item in collection:
            if item["colors"] == color:
                item["materials"] = material
        
        return collection
    
    def neighbor_transform(self, collection, original_collection, params):
        """邻居交换物品"""
        origin = params["countries"]
        size = params["new_sizes"]
        material = params["new_materials"]
        
        # 找出所有具有特定原产地的物品
        origin_items = [i for i, item in enumerate(collection) if item["countries"] == origin]
        num_to_replace = len(origin_items)
        
        # 移除这些物品
        origin_items.sort(reverse=True)  # 从后往前删除，避免索引问题
        for idx in origin_items:
            collection.pop(idx)
        
        # 添加新物品
        for _ in range(num_to_replace):
            new_item = {
                "sizes": size,
                "countries": random.choice(self.countries),
                "name": random.choice(self.items),
                "materials": material,
                "smells": random.choice(self.smells),
                "colors": random.choice(self.colors)
            }
            collection.append(new_item)
        
        return collection
    
    def twin_item_transform(self, collection, original_collection, params):
        """为特定气味的物品添加双胞胎"""
        smell = params["smells"]
        color = params["new_colors"]
        
        items_to_twin = []
        for item in collection:
            if item["smells"] == smell:
                items_to_twin.append(item)
        
        for item in items_to_twin:
            twin = item.copy()
            twin["colors"] = color
            collection.append(twin)
        
        return collection
    
    def spill_paint_transform(self, collection, original_collection, params):
        """颜料洒落事件"""
        size = params["sizes"]
        color = params["new_colors"]
        
        for item in collection:
            if item["sizes"] == size:
                item["colors"] = color
        
        return collection
        
    def generate_initial_collection(self, num_items=42):
        """生成初始物品集合"""
        collection = []
        
        # 随机选择一个要单独分配的属性
        attributes = ["sizes", "colors", "countries", "materials", "smells"]
        special_attribute = random.choice(attributes)
        
        # 为每个物品随机分配非特殊属性
        for _ in range(num_items):
            item = {}
            for attr in attributes:
                if attr != special_attribute:
                    attr_list = getattr(self, attr)
                    item[attr] = random.choice(attr_list)
                else:
                    item[attr] = None
            # 单独分配名称属性
            item["name"] = random.choice(self.items)
            collection.append(item)
        # 获取特殊属性的可用值列表
        attr_values = getattr(self, special_attribute)
        
        # 随机决定要分配的不同值的数量(3-7个不同的值)
        num_distinct_values = random.randint(3, min(self.feature_num, len(attr_values)))
        
        # 随机选择要使用的值
        selected_values = random.sample(attr_values, num_distinct_values)
        
        # 生成分割点
        total_items = len(collection)
        # 生成(值数量-1)个分割点
        split_points = sorted(random.sample(range(1, total_items), num_distinct_values - 1))
        split_points = [0] + split_points + [total_items]
        
        # 为每段分配相同的值
        for i in range(num_distinct_values):
            start = split_points[i]
            end = split_points[i+1]
            current_value = selected_values[i]
            
            for j in range(start, end):
                collection[j][special_attribute] = current_value
        
        return collection, special_attribute

    def count2str(self, count):
        count_dic = {
            1:"one",
            2:"two",
            3:"three",
            4:"four",
            5:"five",
            6:"six",
            7:"seven",
            8:"eight",
            9:"nine",
            10:"ten",
            11:"eleven",
            12:"twelve",
            13:"thirteen",
            14:"fourteen",
            15:"fifteen",
            16:"sixteen",
            17:"seventeen",
            18:"eighteen",
            19:"nineteen",
            20:"twenty",
            21:"twenty-one",
            22:"twenty-two",
            23:"twenty-three",
            24:"twenty-four",
            25:"twenty-five",
            26:"twenty-six",
            27:"twenty-seven",
            28:"twenty-eight",
            29:"twenty-nine",
            30:"thirty",
            31:"thirty-one",
            32:"thirty-two",
            33:"thirty-three",
            34:"thirty-four",
            35:"thirty-five",
            36:"thirty-six",
            37:"thirty-seven",
            38:"thirty-eight",
            39:"thirty-nine",
            40:"forty",
        }
        return count_dic[count]
    
    def count2str_cn(self, count):
        count_dic = {
            1:"一",
            2:"两",
            3:"三",
            4:"四",
            5:"五",
            6:"六",
            7:"七",
            8:"八",
            9:"九",
            10:"十",
            11:"十一",
            12:"十二",
            13:"十三",
            14:"十四",
            15:"十五",
            16:"十六",
            17:"十七",
            18:"十八",
            19:"十九",
            20:"二十",
            21:"二十一",
            22:"二十二",
            23:"二十三",
            24:"二十四",
            25:"二十五",
            26:"二十六",
            27:"二十七",
            28:"二十八",
            29:"二十九",
            30:"三十",
            31:"三十一",
            32:"三十二",
            33:"三十三",
            34:"三十四",
            35:"三十五",
            36:"三十六",
            37:"三十七",
            38:"三十八",
            39:"三十九",
            40:"四十",
        }
        return count_dic[count]

    def describe_collection_changes(self, original_collection, special_attribute,language):
        """描述集合的变化过程，并返回最终集合和问题"""
        # 复制原始集合以进行修改
        collection = [item.copy() for item in original_collection]
        
        # 记录变化过程的描述
        story = []
        
        if language == "english":
            story.append(f"I had a collection of {len(collection)} weird items that went through a few changes. Initially, I had ")
        else:  # 中文
            story.append(f"我有一个包含{len(collection)}个奇怪物品的收藏，经历了几次变化。最初，我有")
        
        # 描述初始集合
        items_desc = []
        for item in collection:
            if language == "english":
                desc = ""
                for key, value in item.items():
                    if key != special_attribute and key != "name":
                        if key == "materials":
                            desc += f"made of {value} "
                        elif key == "smells":
                            sub_desc = [f'with a smell of {value} ', f'smelled like {value} ']
                            desc += random.choice(sub_desc)
                        elif key == "countries":
                            desc += f"from {value} "
                        else:
                            desc += f"{value} "
                desc += item["name"]
                desc = self.p.a(desc)
                items_desc.append(desc)
            else:  # 中文
                desc = ""
                for key, value in item.items():
                    if key != special_attribute and key != "name":
                        if key == "materials":
                            desc += f"由{value}制成的"
                        elif key == "smells":
                            desc += f"散发{value}气味的"
                        elif key == "countries":
                            desc += f"{value}产的"
                        elif key == "colors":
                            desc += f"{value}的"
                        elif key == "sizes":
                            desc += f"{value}尺寸的"
                desc += item["name"]
                items_desc.append(f"一个{desc}")
        
        if language == "english":
            story.append(", ".join(items_desc) + ".")
        else:  # 中文
            story.append("，".join(items_desc) + "。")
        
        # 描述特殊属性分布
        attribute_count = {}
        for item in collection:
            attr_value = item[special_attribute]
            if attr_value in attribute_count:
                attribute_count[attr_value] += 1
            else:
                attribute_count[attr_value] = 1
        
        # 描述特殊属性的分布
        if language == "english":
            special_attr_descriptors = {
                "sizes": "The size of the items was respectively as follows: ",
                "countries": "The origin of the items was respectively as follows: ",
                "materials": "The material of the items was respectively as follows: ",
                "smells": "The smell of the items was respectively as follows: ", 
                "colors": "The color of the items was respectively as follows: "
            }
            story.append(special_attr_descriptors[special_attribute])
        else:  # 中文
            special_attr_descriptors = {
                "sizes": "这些物品的尺寸依次如下：",
                "countries": "这些物品的产地依次如下：",
                "materials": "这些物品的材质依次如下：",
                "smells": "这些物品的气味依次如下：", 
                "colors": "这些物品的颜色依次如下："
            }
            story.append(special_attr_descriptors[special_attribute])
        
        # 构建每个值的描述
        attribute_desc = []
        current_count = 0
        
        for value, count in attribute_count.items():
            if language == "english":
                if special_attribute == "materials":
                    value_text = f"made of {value}"
                elif special_attribute == "smells":
                    value_text = f"smelled like {value}"
                elif special_attribute == "countries":
                    value_text = f"from {value}"
                else:
                    value_text = value
                
                count_str = self.count2str(count)
                if current_count == 0:
                    if count == 1:
                        attribute_desc.append(f"the first {count_str} was {value_text}")
                    else:
                        attribute_desc.append(f"the first {count_str} were {value_text}")
                else:
                    if count == 1:
                        attribute_desc.append(f"the next {count_str} was {value_text}")
                    else:
                        attribute_desc.append(f"the next {count_str} were {value_text}")
            else:  # 中文
                if special_attribute == "materials":
                    value_text = f"由{value}制成"
                elif special_attribute == "smells":
                    value_text = f"散发{value}气味"
                elif special_attribute == "countries":
                    value_text = f"来自{value}"
                else:
                    value_text = value
                
                count_str = self.count2str_cn(count)
                if current_count == 0:
                    attribute_desc.append(f"前{count_str}个是{value_text}")
                else:
                    attribute_desc.append(f"接下来的{count_str}个是{value_text}")
            
            current_count += count
        
        if language == "english":
            story.append(", ".join(attribute_desc) + ".")
        else:  # 中文
            story.append("，".join(attribute_desc) + "。")
        
        # 随机选择2-5个变化
        num_transformations = random.randint(self.transformation_low, self.transformation_high)
        selected_transformations = random.sample(self.transformations, num_transformations)
        
        # 应用每个变化并添加到故事中
        for transformation in selected_transformations:
            # 为变化准备参数
            now_sizes = random.choice(list(set([item["sizes"] for item in collection])))
            now_colors = random.choice(list(set([item["colors"] for item in collection])))
            now_materials = random.choice(list(set([item["materials"] for item in collection])))
            now_smells = random.choice(list(set([item["smells"] for item in collection])))
            now_countries = random.choice(list(set([item["countries"] for item in collection])))
            new_sizes = random.choice([s for s in self.sizes if s != now_sizes])
            new_materials = random.choice([m for m in self.materials if m != now_materials])
            new_colors = random.choice([c for c in self.colors if c != now_colors])
            new_smells = random.choice([s for s in self.smells if s != now_smells])
            new_countries = random.choice([c for c in self.countries if c != now_countries])
            
            if language == "english":
                person = random.choice(self.person)
                desc_key = "description"
            else:  # 中文
                person = random.choice(self.person_cn)
                desc_key = "description_cn"
                
            params = {
                "sizes": now_sizes,
                "colors": now_colors,
                "materials": now_materials,
                "smells": now_smells,
                "countries": now_countries,
                "person": person,
                "new_sizes": new_sizes,
                "new_materials": new_materials,
                "new_colors": new_colors,
                "new_smells": new_smells,
                "new_countries": new_countries,
            }
            
            # 格式化描述并添加到故事
            description = transformation[desc_key].format(**params)
            story.append(description + " ")
            
            # 应用变化到集合
            collection = transformation["apply"](collection, original_collection, params)
            
            # 选择性添加状态描述
            if random.random() < 0.3:  # 30%的概率添加状态描述
                if language == "english":
                    if "materials" in params:
                        # 统计材料分布
                        material_count = {}
                        for item in collection:
                            material = item["materials"]
                            if material in material_count:
                                material_count[material] += 1
                            else:
                                material_count[material] = 1
                        
                        material_desc = []
                        for material, count in material_count.items():
                            material_desc.append(f"{count} item(s) made of {material}")
                        
                        story.append("After this, my collection had: " + ", ".join(material_desc) + ". ")
                    
                    elif "sizes" in params:
                        # 统计尺寸分布
                        size_count = {}
                        for item in collection:
                            size = item["sizes"]
                            if size in size_count:
                                size_count[size] += 1
                            else:
                                size_count[size] = 1
                        
                        size_desc = []
                        for size, count in size_count.items():
                            size_desc.append(f"{count} {size} item(s)")
                        
                        story.append("After this, my collection had: " + ", ".join(size_desc) + ". ")
                    
                    elif "colors" in params:
                        # 统计颜色分布
                        color_count = {}
                        for item in collection:
                            color = item["colors"]
                            if color in color_count:
                                color_count[color] += 1
                            else:
                                color_count[color] = 1
                        
                        color_desc = []
                        for color, count in color_count.items():
                            color_desc.append(f"{count} {color} item(s)")
                        
                        story.append("After this, my collection had: " + ", ".join(color_desc) + ". ")
                
                else:  # 中文
                    if "materials" in params:
                        # 统计材料分布
                        material_count = {}
                        for item in collection:
                            material = item["materials"]
                            if material in material_count:
                                material_count[material] += 1
                            else:
                                material_count[material] = 1
                        
                        material_desc = []
                        for material, count in material_count.items():
                            material_desc.append(f"{count}个由{material}制成的物品")
                        
                        story.append("在此之后，我的收藏有：" + "，".join(material_desc) + "。")
                    
                    elif "sizes" in params:
                        # 统计尺寸分布
                        size_count = {}
                        for item in collection:
                            size = item["sizes"]
                            if size in size_count:
                                size_count[size] += 1
                            else:
                                size_count[size] = 1
                        
                        size_desc = []
                        for size, count in size_count.items():
                            size_desc.append(f"{count}个{size}尺寸的物品")
                        
                        story.append("在此之后，我的收藏有：" + "，".join(size_desc) + "。")
                    
                    elif "colors" in params:
                        # 统计颜色分布
                        color_count = {}
                        for item in collection:
                            color = item["colors"]
                            if color in color_count:
                                color_count[color] += 1
                            else:
                                color_count[color] = 1
                        
                        color_desc = []
                        for color, count in color_count.items():
                            color_desc.append(f"{count}个{color}色物品")
                        
                        story.append("在此之后，我的收藏有：" + "，".join(color_desc) + "。")
        
        # 生成问题
        now_sizes = random.choice(list(set([item["sizes"] for item in collection])))
        now_colors = random.choice(list(set([item["colors"] for item in collection])))
        now_materials = random.choice(list(set([item["materials"] for item in collection])))
        now_smells = random.choice(list(set([item["smells"] for item in collection])))
        now_countries = random.choice(list(set([item["countries"] for item in collection])))
        
        attribute_num = random.randint(2, 5)
        # 抽取特征
        attributes = ["sizes", "colors", "materials", "smells", "countries"]
        random.shuffle(attributes)
        question_attribute = attributes[:attribute_num]
        selected_attributes = []
        
        if language == "english":
            for attr in question_attribute:
                if attr == "sizes":
                    selected_attributes.append(f"size is {now_sizes}")
                elif attr == "colors":
                    selected_attributes.append(f"color is {now_colors}")
                elif attr == "materials":   
                    selected_attributes.append(f"material is {now_materials}")
                elif attr == "smells":
                    selected_attributes.append(f"smell is {now_smells}")
                elif attr == "countries":   
                    selected_attributes.append(f"origin is {now_countries}")
            
            question = f"In my current collection, how many items have the following attributes: either {' or '.join(selected_attributes)}? If the exact number cannot be computed, the answer must be \"unknown\"."
        
        else:  # 中文
            for attr in question_attribute:
                if attr == "sizes":
                    selected_attributes.append(f"尺寸是{now_sizes}")
                elif attr == "colors":
                    selected_attributes.append(f"颜色是{now_colors}")
                elif attr == "materials":   
                    selected_attributes.append(f"材质是{now_materials}")
                elif attr == "smells":
                    selected_attributes.append(f"气味是{now_smells}")
                elif attr == "countries":   
                    selected_attributes.append(f"产地是{now_countries}")
            
            question = f"在我当前的收藏中，有多少物品具有以下属性：{'或'.join(selected_attributes)}？"
        
        # 计算答案
        answer = 0
        for item in collection:
            matches = False
            for attr in question_attribute:
                if attr == "sizes" and item["sizes"] == now_sizes:
                    matches = True
                    break
                elif attr == "colors" and item["colors"] == now_colors:
                    matches = True
                    break
                elif attr == "materials" and item["materials"] == now_materials:
                    matches = True
                    break
                elif attr == "smells" and item["smells"] == now_smells:
                    matches = True
                    break
                elif attr == "countries" and item["countries"] == now_countries:
                    matches = True
                    break
            if matches:
                answer += 1
        
        # 合并故事
        full_story = "".join(story)
        
        return {
            "story": full_story,
            "question": question,
            "answer": str(answer),
            "initial_collection": original_collection,
            "final_collection": collection
        }
    
    def generate(self, num_of_questions: int = 100, max_attempts: int = 100):
        """生成示例问题和答案"""
        outputs = []
        
        for i in range(num_of_questions):
            if self.language_type == "mixed":
                language = random.choice(["english", "chinese"])
            else:
                language = self.language_type
            if language == "english":
                self.colors = random.sample(self.total_colors, min(self.feature_num, len(self.total_colors)))
                self.sizes = random.sample(self.total_sizes, min(self.feature_num, len(self.total_sizes)))
                self.materials = random.sample(self.total_materials, min(self.feature_num, len(self.total_materials)))
                self.smells = random.sample(self.total_smells, min(self.feature_num, len(self.total_smells)))
                self.countries = random.sample(self.total_countries, min(self.feature_num, len(self.total_countries)))
            else:
                self.colors = random.sample(self.total_colors_cn, min(self.feature_num, len(self.total_colors_cn)))
                self.sizes = random.sample(self.total_sizes_cn, min(self.feature_num, len(self.total_sizes_cn)))
                self.materials = random.sample(self.total_materials_cn, min(self.feature_num, len(self.total_materials_cn)))
                self.smells = random.sample(self.total_smells_cn, min(self.feature_num, len(self.total_smells_cn)))
                self.countries = random.sample(self.total_countries_cn, min(self.feature_num, len(self.total_countries_cn)))
                self.items = random.sample(self.items_cn, min(self.feature_num, len(self.items_cn)))
            num_items = random.randint(self.num_low, self.num_high)
            initial_collection, special_attribute = self.generate_initial_collection(num_items)
                 
            result = self.describe_collection_changes(initial_collection, special_attribute,language)
            if language == "english":
                prompt = random.choice(en_prompts).format(context=result["story"], problem=result["question"])
            else:
                prompt = random.choice(cn_prompts).format(context=result["story"], problem=result["question"])
            outputs.append(Data(
                question=prompt,
                answer=result["answer"],
                difficulty=1,
                metadata={
                    "story": result["story"],
                    "question": result["question"],
                    "answer": result["answer"],
                    "initial_collection": result["initial_collection"],
                    "final_collection": result["final_collection"],
                    "language": language
                }
            ))
        
        return outputs
        
    def extract_answer(self, test_solution: str):
        return self.verifier.extract_answer(test_solution)

    def verify(self, data: Data, test_solution: str):
        return self.verifier.verify(data, test_solution)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="物品属性游戏生成器")
    parser.add_argument("--num_range", type=int, nargs=2, default=[10, 15], help="初始物品数量范围")
    parser.add_argument("--feature_num", type=int, default=7, help="特征数量")
    parser.add_argument("--transformation_range", type=int, nargs=2, default=[2, 3], help="变换数量范围")
    parser.add_argument("--language", type=str, default="mixed", choices=["english", "chinese", "mixed"], help="语言")
    parser.add_argument("--num_of_data", type=int, default=1000, help="生成数据数量")
    parser.add_argument("--max_attempts", type=int, default=100, help="最大尝试次数")
    parser.add_argument("--output", type=str, default="test", help="输出文件路径")
    
    args = parser.parse_args()
    
    # 创建游戏实例
    game = ObjectProperties(
        feature_num=args.feature_num,
        transformation_range=args.transformation_range,
        num_range=args.num_range,
        language_type=args.language
    )
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts
    )
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用参数缩写构建文件名
    language_suffix = f"_{args.language}" if args.language else "_mixed"
    filename = f"data_fp{args.feature_num}_nr{args.num_range[0]}-{args.num_range[1]}_nt{args.transformation_range[0]}-{args.transformation_range[1]}{language_suffix}_n{args.num_of_data}.jsonl"
    output_file = data_dir / filename
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据")
    
    # 将数据保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for data in game_data_list:
            f.write(json.dumps(data.__dict__, ensure_ascii=False) + '\n')
    
    print(f"数据已保存到 {output_file}")
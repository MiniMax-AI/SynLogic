import random
import json
import uuid
from games.base.game import Game
from base.data import Data
from games.tasks.object_counting.scripts.object_counting_verifier import ObjectCountingVerifier
from games.tasks.object_counting.scripts.object_counting_prompt import CHINESE_PROMPTS, ENGLISH_PROMPTS
import argparse
import pathlib

class ObjectCounting(Game):
    def __init__(self, 
                 min_sequence_length=3, 
                 max_sequence_length=6,
                 min_count=5, 
                 max_count=100,
                 min_my_items_per_category=2,
                 max_my_items_per_category=5,
                 min_others_possessions=25,
                 max_others_possessions=40,
                 available_categories=None,
                 min_categories=3,
                 max_categories=7,
                 story_type_probs=(0.4, 0.4, 0.2),  # 无故事, 简单故事, 复杂故事的概率
                 language=None):  # 新增语言参数，None表示随机选择
        """
        初始化物品计数问题生成器
        
        参数:
            min_sequence_length: 故事中数字序列的最小长度
            max_sequence_length: 故事中数字序列的最大长度
            min_count: 生成的数字最小值
            max_count: 生成的数字最大值
            min_my_items_per_category: 我在每个类别中拥有的最少物品数
            max_my_items_per_category: 我在每个类别中拥有的最多物品数
            min_others_possessions: 其他人拥有的最少物品总数
            max_others_possessions: 其他人拥有的最多物品总数
            available_categories: 要使用的物品类别列表，默认值为None表示每次生成问题时随机选择
            min_categories: 随机选择时的最小类别数
            max_categories: 随机选择时的最大类别数
            story_type_probs: 三元组 (无故事概率, 简单故事概率, 复杂故事概率)，总和应为1
            language: 使用的语言，可选 'en' 或 'zh'，None 表示随机选择
        """
        super().__init__("Object Counting", ObjectCountingVerifier)
        # 验证故事类型概率
        if sum(story_type_probs) != 1.0:
            raise ValueError("故事类型概率总和必须为1.0")
        self.no_story_prob = story_type_probs[0]
        self.simple_story_prob = story_type_probs[1]
        self.complex_story_prob = story_type_probs[2]
        
        # 初始化序列和数字范围
        self.min_sequence_length = min_sequence_length
        self.max_sequence_length = max_sequence_length
        self.min_count = min_count
        self.max_count = max_count
        self.min_my_items_per_category = min_my_items_per_category
        self.max_my_items_per_category = max_my_items_per_category
        self.min_others_possessions = min_others_possessions
        self.max_others_possessions = max_others_possessions
        self.min_categories = min_categories
        self.max_categories = max_categories
        
        # 保存用户指定的类别（如果有）
        self.specified_categories = available_categories
        
        # 存储当前使用的语言
        self.language = language
        
        # 定义英文人物列表
        self.en_people = ["I", "My aunt", "My uncle", "My brother", "My sister", "My mother", "My father", 
                      "My grandmother", "My grandfather", "My cousin", "My friend", "My colleague",
                      "My neighbor", "My teacher", "My professor", "My roommate", "My boss"]
        
        # 定义中文人物列表
        self.zh_people = ["我", "我的阿姨", "我的叔叔", "我的哥哥", "我的姐姐", "我的母亲", "我的父亲", 
                      "我的奶奶", "我的爷爷", "我的表兄弟", "我的朋友", "我的同事",
                      "我的邻居", "我的老师", "我的教授", "我的室友", "我的老板"]
        
        # 英文物品类别
        self.en_fruits = ["apples", "bananas", "oranges", "grapes", "strawberries", "watermelons", 
                      "pineapples", "mangoes", "kiwis", "peaches", "plums", "cherries", 
                      "breadfruits", "nectarines", "apricots", "lemons", "guavas", "dates",
                      "plantains", "envy apples", "jonagold apples", "dragonfruit", "lychee",
                      "persimmons", "pomegranates", "raspberries", "blueberries", "blackberries"]
        
        self.en_animals = ["dogs", "cats", "birds", "hamsters", "rabbits", "turtles", "fish", 
                       "snakes", "lizards", "frogs", "monkeys", "opossums", "wolves", 
                       "beavers", "falcons", "ducks", "parrots", "tarantulas", "scorpions",
                       "hedgehogs", "ferrets", "chinchillas", "guinea pigs", "mice", "rats",
                       "geckos", "iguanas", "chameleons", "crabs", "shrimps"]
        
        self.en_cars = ["toyota corolla", "honda civic", "ford mustang", "tesla model 3", 
                    "nissan altima", "chevrolet camaro", "hyundai elantra", "mazda cx-5",
                    "kia niro", "jeep gladiator", "toyota tundra", "honda element",
                    "nissan sentra", "mazda cx-90", "hyundai santa fe", "nissan armada",
                    "nissan pathfinder", "toyota highlander", "nissan kicks", "mazda cx-50",
                    "bmw x5", "audi a4", "mercedes c-class", "lexus rx", "volvo xc90", 
                    "subaru outback", "volkswagen golf", "porsche 911", "jaguar f-type"]
        
        self.en_electronics = ["smartphones", "laptops", "tablets", "smartwatches", "headphones", 
                          "bluetooth speakers", "digital cameras", "video game consoles", "drones",
                          "e-readers", "smart TVs", "VR headsets", "wireless earbuds", "monitors",
                          "desktop computers", "routers", "hard drives", "graphics cards", "keyboards"]
        
        self.en_books = ["mystery novels", "sci-fi books", "fantasy books", "history books", 
                     "biographies", "cookbooks", "self-help books", "poetry collections",
                     "graphic novels", "children's books", "textbooks", "encyclopedias",
                     "travel guides", "art books", "reference books", "comics", "magazines"]
        
        self.en_furniture = ["chairs", "tables", "sofas", "bookshelves", "desks", "beds", 
                        "coffee tables", "dining tables", "nightstands", "dressers", "ottomans",
                        "bean bags", "rocking chairs", "benches", "armchairs", "recliners", "stools"]
        
        self.en_clothes = ["t-shirts", "jeans", "dresses", "sweaters", "jackets", "hoodies", 
                      "skirts", "shorts", "suits", "ties", "scarves", "hats", "gloves",
                      "socks", "shoes", "boots", "sneakers", "coats", "pajamas", "swimsuits"]
        
        # 中文物品类别
        self.zh_fruits = ["苹果", "香蕉", "橙子", "葡萄", "草莓", "西瓜", 
                      "菠萝", "芒果", "猕猴桃", "桃子", "李子", "樱桃", 
                      "面包果", "油桃", "杏子", "柠檬", "番石榴", "枣",
                      "芭蕉", "爱妃苹果", "乔纳金苹果", "火龙果", "荔枝",
                      "柿子", "石榴", "覆盆子", "蓝莓", "黑莓"]
        
        self.zh_animals = ["狗", "猫", "鸟", "仓鼠", "兔子", "乌龟", "鱼", 
                       "蛇", "蜥蜴", "青蛙", "猴子", "负鼠", "狼", 
                       "海狸", "猎鹰", "鸭子", "鹦鹉", "狼蛛", "蝎子",
                       "刺猬", "雪貂", "龙猫", "豚鼠", "老鼠", "大鼠",
                       "壁虎", "鬣蜥", "变色龙", "螃蟹", "虾"]
        
        self.zh_cars = ["丰田卡罗拉", "本田思域", "福特野马", "特斯拉Model 3", 
                    "日产天籁", "雪佛兰科迈罗", "现代伊兰特", "马自达CX-5",
                    "起亚Niro", "吉普角斗士", "丰田坦途", "本田Element",
                    "日产轩逸", "马自达CX-90", "现代胜达", "日产Armada",
                    "日产途达", "丰田汉兰达", "日产劲客", "马自达CX-50",
                    "宝马X5", "奥迪A4", "奔驰C级", "雷克萨斯RX", "沃尔沃XC90", 
                    "斯巴鲁傲虎", "大众高尔夫", "保时捷911", "捷豹F-Type"]
        
        self.zh_electronics = ["智能手机", "笔记本电脑", "平板电脑", "智能手表", "耳机", 
                          "蓝牙音箱", "数码相机", "游戏机", "无人机",
                          "电子阅读器", "智能电视", "VR头盔", "无线耳塞", "显示器",
                          "台式电脑", "路由器", "硬盘", "显卡", "键盘"]
        
        self.zh_books = ["推理小说", "科幻书籍", "奇幻书籍", "历史书籍", 
                     "传记", "烹饪书", "自助书籍", "诗集",
                     "图画小说", "儿童书籍", "教科书", "百科全书",
                     "旅游指南", "艺术书籍", "参考书", "漫画", "杂志"]
        
        self.zh_furniture = ["椅子", "桌子", "沙发", "书架", "书桌", "床", 
                        "咖啡桌", "餐桌", "床头柜", "梳妆台", "脚凳",
                        "豆袋", "摇椅", "长凳", "扶手椅", "躺椅", "凳子"]
        
        self.zh_clothes = ["T恤", "牛仔裤", "连衣裙", "毛衣", "夹克", "卫衣", 
                      "裙子", "短裤", "西装", "领带", "围巾", "帽子", "手套",
                      "袜子", "鞋子", "靴子", "运动鞋", "外套", "睡衣", "泳装"]
        
        # 英文物品类别集合
        self.en_all_categories = {
            "fruit": self.en_fruits,
            "animal": self.en_animals,
            "car": self.en_cars,
            "electronic": self.en_electronics,
            "book": self.en_books,
            "furniture": self.en_furniture,
            "clothes": self.en_clothes
        }
        
        # 中文物品类别集合
        self.zh_all_categories = {
            "fruit": self.zh_fruits,
            "animal": self.zh_animals,
            "car": self.zh_cars,
            "electronic": self.zh_electronics,
            "book": self.zh_books,
            "furniture": self.zh_furniture,
            "clothes": self.zh_clothes
        }
        
        # 英文简单故事描述
        self.en_simple_descriptions = [
            "(happy to have them)",
            "(they are very delicious)",
            "(I bought them yesterday)",
            "(they are my favorite)",
            "(they were on sale at the market)",
            "(I collect them as a hobby)",
            "(they are organic/eco-friendly)",
            "(I plan to use them for a project)",
            "(perfect for my needs)",
            "(my neighbors gave them to me)",
            "(I won them in a contest)",
            "(they were a birthday gift)",
            "(I inherited them from my grandparents)",
            "(I got a great deal on them)",
            "(they are quite rare nowadays)"
        ]
        
        # 中文简单故事描述
        self.zh_simple_descriptions = [
            "(很高兴拥有它们)",
            "(它们非常美味)",
            "(我昨天买的)",
            "(它们是我最喜欢的)",
            "(它们在市场上打折)",
            "(我把收集它们作为爱好)",
            "(它们是有机/环保的)",
            "(我打算用它们做个项目)",
            "(非常适合我的需求)",
            "(我的邻居给了我这些)",
            "(我在比赛中赢得了它们)",
            "(它们是生日礼物)",
            "(这些是我从祖父母那里继承的)",
            "(我买到了很划算的价格)",
            "(现在它们相当稀有)"
        ]

    def get_item_category(self, item, language='en'):
        """确定物品属于哪个类别"""
        if language == 'en':
            categories = self.en_all_categories
        else:
            categories = self.zh_all_categories
            
        for category_name, items in categories.items():
            if any(specific_item == item for specific_item in items):
                return category_name
        return ""

    def generate_complex_story(self, count, complexity="simple", language="en", category=None):
        """
        生成带有数字和故事的复杂描述
        
        参数:
            count: 物品数量
            complexity: 故事复杂度，可选 'simple' 或 'complex'
            language: 语言，可选 'en' 或 'zh'
            category: 物品类别，确保故事与类别匹配
        """
        if complexity not in ["simple", "complex"]:
            raise ValueError("复杂度必须是 'simple' 或 'complex'")
        
        # 根据类别选择相应的故事模板
        if language == "en":
            # 英文故事模板 - 使用英文括号
            fruit_stories = [
                " (which are organic)", 
                " (which are fresh from the market)", 
                " (which are ripe and juicy)", 
                " (which I bought yesterday)", 
                " (which are for a fruit salad)"
            ]
            
            animal_stories = [
                " (which are very friendly)", 
                " (which I'm taking care of)", 
                " (which need to be fed)", 
                " (which are in the backyard)", 
                " (which belong to the shelter)"
            ]
            
            car_stories = [
                " (which are in the garage)", 
                " (which need maintenance)", 
                " (which I'm selling)", 
                " (which are vintage models)", 
                " (which have low mileage)"
            ]
            
            electronic_stories = [
                " (which need charging)", 
                " (which are brand new)", 
                " (which I use for work)", 
                " (which have high specs)", 
                " (which were on sale)"
            ]
            
            book_stories = [
                " (which I haven't read yet)", 
                " (which are bestsellers)", 
                " (which are on my bookshelf)", 
                " (which I borrowed from the library)", 
                " (which have interesting plots)"
            ]
            
            furniture_stories = [
                " (which are antique)", 
                " (which need assembly)", 
                " (which match the decor)", 
                " (which I just purchased)", 
                " (which are handcrafted)"
            ]
            
            clothes_stories = [
                " (which are in my closet)", 
                " (which need washing)", 
                " (which are my favorite)", 
                " (which are for special occasions)", 
                " (which are brand new)"
            ]
            
            default_stories = [
                " (which I recently acquired)", 
                " (which are quite useful)", 
                " (which I keep at home)", 
                " (which I like very much)", 
                " (which are valuable to me)"
            ]
            
        else:
            # 中文故事模板 - 使用中文括号
            fruit_stories = [
                "（都是有机的）", 
                "（都是从市场新鲜购买的）", 
                "（都很新鲜多汁）", 
                "（是我昨天买的）", 
                "（准备用来做水果沙拉的）"
            ]
            
            animal_stories = [
                "（它们都很友好）", 
                "（我正在照顾它们）", 
                "（需要喂食）", 
                "（在后院活动）", 
                "（来自收容所）"
            ]
            
            car_stories = [
                "（都停在车库里）", 
                "（需要维修保养）", 
                "（我打算出售的）", 
                "（都是古董车型）", 
                "（行驶里程很少）"
            ]
            
            electronic_stories = [
                "（需要充电）", 
                "（都是全新的）", 
                "（我用来工作的）", 
                "（配置很高）", 
                "（是打折时买的）"
            ]
            
            book_stories = [
                "（我还没读过）", 
                "（都是畅销书）", 
                "（放在我的书架上）", 
                "（是从图书馆借的）", 
                "（情节很有趣）"
            ]
            
            furniture_stories = [
                "（都是古董）", 
                "（需要组装）", 
                "（与装修风格相配）", 
                "（我刚购买的）", 
                "（是手工制作的）"
            ]
            
            clothes_stories = [
                "（都在我的衣柜里）", 
                "（需要洗涤）", 
                "（是我最喜欢的）", 
                "（是特殊场合穿的）", 
                "（是全新的）"
            ]
            
            default_stories = [
                "（我最近获得的）", 
                "（非常实用的）", 
                "（我放在家里的）", 
                "（我非常喜欢的）", 
                "（对我很有价值的）"
            ]
        
        # 根据类别选择合适的故事模板
        if category == "fruit":
            simple_stories = fruit_stories
        elif category == "animal":
            simple_stories = animal_stories
        elif category == "car":
            simple_stories = car_stories
        elif category == "electronic":
            simple_stories = electronic_stories
        elif category == "book":
            simple_stories = book_stories
        elif category == "furniture":
            simple_stories = furniture_stories
        elif category == "clothes":
            simple_stories = clothes_stories
        else:
            simple_stories = default_stories
        
        # 根据复杂度选择故事
        if complexity == "simple":
            # 简单故事：随机选择一个简单故事
            return random.choice(simple_stories)
        else:  # 合并complex和calculation为一种灵活的故事类型
            # 生成随机的数量序列，最后一个数量必须是count
            sequence_length = random.randint(self.min_sequence_length, self.max_sequence_length)
            
            # 直接生成非负数字序列
            sequence = []
            
            # 第一个数字随机生成
            sequence.append(random.randint(self.min_count, self.max_count))
            
            # 生成中间数字，确保和前一个不同
            for i in range(sequence_length - 2):
                # 生成与前一个不同的随机数
                while True:
                    new_value = random.randint(self.min_count, self.max_count)
                    if new_value != sequence[-1]:
                        break
                sequence.append(new_value)
            
            # 最后一个数字必须是count
            sequence.append(count)
            
            # 构建故事，根据语言选择不同的模板
            if language == 'en':
                story = f"(here's how I ended up with {count} of them: initially I had {sequence[0]}"
                
                for i in range(1, len(sequence)):
                    change = sequence[i] - sequence[i-1]
                    if change > 0:
                        story += f", then I got {change} more making it {sequence[i]}"
                    elif change < 0:
                        story += f", then I lost {abs(change)} of them leaving me with {sequence[i]}"
            else:
                story = f"(我是这样拥有这{count}个的：最初我有{sequence[0]}个"
                
                for i in range(1, len(sequence)):
                    change = sequence[i] - sequence[i-1]
                    if change > 0:
                        story += f"，然后我又获得了{change}个，总共有{sequence[i]}个"
                    elif change < 0:
                        story += f"，然后我失去了{abs(change)}个，剩下{sequence[i]}个"
            
            story += ")"
            return story

    def get_category_display_name(self, category, language='en'):
        """获取类别的显示名称（包含复数形式处理）"""
        if language == 'en':
            if category == "fruit":
                return "fruits"
            elif category == "animal":
                return "animals"
            elif category == "car":
                return "cars"
            elif category == "electronic":
                return "electronics"
            elif category == "book":
                return "books"
            elif category == "furniture":
                return "furniture items"  # furniture通常没有简单的复数形式
            elif category == "clothes":
                return "clothing items"  # clothes已经是复数
            return category + "s"  # 默认添加s作为复数
        else:
            # 中文类别显示名称
            if category == "fruit":
                return "水果"
            elif category == "animal":
                return "动物"
            elif category == "car":
                return "汽车"
            elif category == "electronic":
                return "电子产品"
            elif category == "book":
                return "书籍"
            elif category == "furniture":
                return "家具"
            elif category == "clothes":
                return "衣物"
            return category  # 默认直接返回类别名

    def generate_problem(self):
        """生成物品计数问题"""
        # 决定使用的语言
        if self.language == "mixed":
            current_language = random.choice(['en', 'zh'])
        else:
            current_language = self.language
        # 根据语言选择对应的人物和类别
        if current_language == 'en':
            people = self.en_people
            all_categories = self.en_all_categories
            i_pronoun = "I"
        else:
            people = self.zh_people
            all_categories = self.zh_all_categories
            i_pronoun = "我"
            
        # 每次生成问题时选择可用类别
        if self.specified_categories is None:
            # 随机选择类别
            num_categories = random.randint(self.min_categories, self.max_categories)
            available_categories = random.sample(list(all_categories.keys()), num_categories)
        else:
            # 使用用户指定的类别
            for category in self.specified_categories:
                if category not in all_categories:
                    raise ValueError(f"Invalid category: {category}")
            available_categories = self.specified_categories
            
        # 创建嵌套字典结构，格式为 {人物: {物品种类: [(具体物品, 数量, 描述), ...], ...}, ...}
        possessions = {
            person: {
                category: [] for category in available_categories
            } for person in people
        }
        
        # 为"我"生成各类物品，包含复杂描述
        for category in available_categories:
            items_list = all_categories[category]
            for _ in range(random.randint(self.min_my_items_per_category, self.max_my_items_per_category)):
                # 获取还没分配给"我"的物品
                assigned_items = [item for item, _, _ in possessions[i_pronoun][category]]
                available_items = [item for item in items_list if item not in assigned_items]
                
                if available_items:
                    item = random.choice(available_items)
                    count = random.randint(self.min_count, self.max_count)
                    
                    # 根据概率决定故事类型
                    story_type_rand = random.random()
                    if story_type_rand < self.no_story_prob:
                        description = ""  # 无故事
                    elif story_type_rand < self.no_story_prob + self.simple_story_prob:
                        description = self.generate_complex_story(count, "simple", current_language, category)
                    else:
                        description = self.generate_complex_story(count, "complex", current_language, category)
                    
                    possessions[i_pronoun][category].append((item, count, description))
        
        # 生成其他人拥有的物品
        for _ in range(random.randint(self.min_others_possessions, self.max_others_possessions)):
            person = random.choice([p for p in people if p != i_pronoun])  # 除了"我"以外的人
            category = random.choice(available_categories)
            items_list = all_categories[category]
            
            # 获取还没分配给这个人的物品
            assigned_items = [item for item, _, _ in possessions[person][category]]
            available_items = [item for item in items_list if item not in assigned_items]
            
            if available_items:
                item = random.choice(available_items)
                count = random.randint(self.min_count, self.max_count)
                possessions[person][category].append((item, count, ""))
        
        # 将所有物品描述整合为一个列表，用于随机穿插
        all_statements = []
        
        # 将其他人的物品添加到列表
        for person in [p for p in people if p != i_pronoun]:
            for category in available_categories:
                for item, count, _ in possessions[person][category]:
                    all_statements.append((person, item, count, ""))
        
        # 将"我"的物品添加到列表
        for category in available_categories:
            for item, count, description in possessions[i_pronoun][category]:
                all_statements.append((i_pronoun, item, count, description))
        
        # 随机打乱所有物品的顺序
        random.shuffle(all_statements)
        
        # 记录每个人是否已经提到过物品
        person_mentioned = {person: False for person in people}
        
        # 构建问题文本
        problem_text = ""
        
        # 按混合后的顺序添加所有物品描述
        for person, item, count, description in all_statements:
            category = self.get_item_category(item, current_language)

            if current_language == 'en':
                if person == "I":
                    if person_mentioned["I"]:
                        problem_text += f"I also have {count} {item}{description}. "
                    else:
                        problem_text += f"I have {count} {item}{description}. "
                        person_mentioned["I"] = True
                else:
                    if person_mentioned[person]:
                        problem_text += f"{person} also has {count} {item}{description}. "
                    else:
                        problem_text += f"{person} has {count} {item}{description}. "
                        person_mentioned[person] = True
            else:
                if person == "我":
                    if person_mentioned["我"]:
                        problem_text += f"我还有{count}个{item}{description}。"
                    else:
                        problem_text += f"我有{count}个{item}{description}。"
                        person_mentioned["我"] = True
                else:
                    if person_mentioned[person]:
                        problem_text += f"{person}还有{count}个{item}{description}。"
                    else:
                        problem_text += f"{person}有{count}个{item}{description}。"
                        person_mentioned[person] = True
        
        # 确定我拥有物品的类别
        my_categories = [cat for cat in available_categories if possessions[i_pronoun][cat]]
        
        if len(my_categories) >= 2:
            # 随机选择问题类型
            question_type = random.randint(1, 3)
            
            if question_type <= 2:  # 两个类别的问题
                # 随机选择两个不同的类别
                cat1, cat2 = random.sample(my_categories, 2)
                
                # 计算每个类别的总数
                total_1 = sum(count for _, count, _ in possessions[i_pronoun][cat1])
                total_2 = sum(count for _, count, _ in possessions[i_pronoun][cat2])
                
                # 使用正确的复数形式
                cat1_name = self.get_category_display_name(cat1, current_language)
                cat2_name = self.get_category_display_name(cat2, current_language)
                
                if question_type == 1:  # 求和
                    answer = total_1 + total_2
                    if current_language == 'en':
                        question = f"What is the total number of {cat1_name} and {cat2_name} that I have?"
                    else:
                        question = f"我总共有多少个{cat1_name}和{cat2_name}？"
                else:  # 求差的绝对值
                    answer = abs(total_1 - total_2)
                    if current_language == 'en':
                        question = f"What is the absolute difference between the number of {cat1_name} and {cat2_name} that I have?"
                    else:
                        question = f"我拥有的{cat1_name}和{cat2_name}的数量差的绝对值是多少？"
            
            else:  # 一个类别求总数
                # 随机选择一个类别
                cat = random.choice(my_categories)
                
                # 计算这个类别的总数
                total = sum(count for _, count, _ in possessions[i_pronoun][cat])
                answer = total
                
                # 使用正确的复数形式
                cat_name = self.get_category_display_name(cat, current_language)
                if current_language == 'en':
                    question = f"How many {cat_name} do I have in total?"
                else:
                    question = f"我总共有多少个{cat_name}？"
        
        elif len(my_categories) == 1:
            # 只有一个类别，就问这个类别的总数
            cat = my_categories[0]
            total = sum(count for _, count, _ in possessions[i_pronoun][cat])
            answer = total
            
            # 使用正确的复数形式
            cat_name = self.get_category_display_name(cat, current_language)
            if current_language == 'en':
                question = f"How many {cat_name} do I have in total?"
            else:
                question = f"我总共有多少个{cat_name}？"
        
        else:
            # 没有类别，出错了
            raise ValueError("No categories with items assigned to me!")
        
        # 随机选择一个对应语言的提示模板
        if current_language == 'en':
            prompt_template = random.choice(ENGLISH_PROMPTS)
        else:
            prompt_template = random.choice(CHINESE_PROMPTS)
            
        # 用问题文本和问题替换提示模板中的占位符
        formatted_prompt = prompt_template.format(context=problem_text, problem=question)
        
        return formatted_prompt, str(answer), possessions, available_categories, current_language

    def create_data_entry(self):
        """创建一个DATA"""
        problem, answer, possessions, used_categories, language = self.generate_problem()
        trace_id = uuid.uuid4()
        return Data(
                question=problem,
                answer=answer,
                difficulty=1,
                metadata={
                    "possessions": possessions,
                    "used_categories": used_categories,
                    "language": language
                }
            )

    def generate(self, num_of_questions: int = 100, max_attempts: int = 100):
        """生成多个问题并可选择性地写入文件"""
        problems = []
        for _ in range(num_of_questions):
            problem_data = self.create_data_entry()
            problems.append(problem_data)
        return problems

    def extract_answer(self, test_solution: str):
        return self.verifier.extract_answer(test_solution)

    def verify(self, data: Data, test_solution: str):
        return self.verifier.verify(data, test_solution)




# 使用示例
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="物品计数游戏生成器")
    parser.add_argument("--num_of_data", type=int, default=1000, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个题目的最大尝试次数")
    parser.add_argument("--min_sequence_length", type=int, default=3, help="故事中数字序列的最小长度")
    parser.add_argument("--max_sequence_length", type=int, default=6, help="故事中数字序列的最大长度")
    parser.add_argument("--min_count", type=int, default=5, help="生成的数字最小值")
    parser.add_argument("--max_count", type=int, default=100, help="生成的数字最大值")
    parser.add_argument("--min_my_items_per_category", type=int, default=2, help="我在每个类别中拥有的最少物品数")
    parser.add_argument("--max_my_items_per_category", type=int, default=5, help="我在每个类别中拥有的最多物品数")
    parser.add_argument("--min_categories", type=int, default=3, help="随机选择时的最小类别数")
    parser.add_argument("--max_categories", type=int, default=7, help="随机选择时的最大类别数")
    parser.add_argument("--language", type=str, choices=["en", "zh"], default="mixed", help="使用的语言，不指定则随机选择")
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用参数缩写构建文件名
    language_suffix = f"_{args.language}" if args.language else "_mixed"
    filename = f"data_sl{args.min_sequence_length}-{args.max_sequence_length}_ct{args.min_count}-{args.max_count}_cat{args.min_categories}-{args.max_categories}_mic{args.min_my_items_per_category}-{args.max_my_items_per_category}{language_suffix}_n{args.num_of_data}.jsonl"
    output_file = data_dir / filename
    
    # 创建游戏实例
    game = ObjectCounting(
        min_sequence_length=args.min_sequence_length,
        max_sequence_length=args.max_sequence_length,
        min_count=args.min_count,
        max_count=args.max_count,
        min_my_items_per_category=args.min_my_items_per_category,
        max_my_items_per_category=args.max_my_items_per_category,
        min_categories=args.min_categories,
        max_categories=args.max_categories,
        language=args.language
    )
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts
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
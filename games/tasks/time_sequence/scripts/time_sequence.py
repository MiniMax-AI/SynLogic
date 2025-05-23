import random
import numpy as np
import re
import uuid
import json
import argparse
import pathlib
import os
from typing import List, Tuple
import copy
from games.base.game import Game
from base.data import Data
from games.tasks.time_sequence.scripts.time_sequence_verifier import TimeSequenceVerifier
from games.tasks.time_sequence.scripts.time_sequence_prompt import prompt_timeSequence

class TimeSequence(Game):
    """
    TimeSequence任务类
    """
    def __init__(self):
        """
        初始化 time sequece 任务
        """
        super().__init__("TimeSequence", TimeSequenceVerifier)
        
    def generate(self, num_of_questions: int = 100, max_attempts: int = 100,
                 n: int = 3, rule_prob:int=50):
        """
        生成 time sequence 的题目
        
        @param num_of_questions: 要生成的题目数量
        @param max_attempts: 每个题目的最大尝试次数
        @param n: 题目中的人物数量
        @param rule_prob: 为人物生成额外规则的概率
        @return: 生成的题目列表
        """
        if n <= 1:
            raise ValueError("人数n必须大于1")
        if rule_prob<0 or rule_prob>100:
            raise ValueError("概率值必须在[0,1]之间")
        rule_prob /= 100
        game_data_list = []
        generated_matrices = set()
        attempts = 0

        # 使用自定义的游戏生成类
        generator = Generate_Task()
        
        while len(game_data_list) < num_of_questions and attempts < max_attempts:
            try:
                attempts += 1
                # 随机选择中文或英文提示
                is_chinese = random.choice([True, False])

                # 生成游戏相关数据
                game_data = generator.generate_main(n=n, rule_prob=rule_prob, is_chinese=is_chinese)

                # 将游戏数据转为字符串以检查重复
                game_data_str = json.dumps(game_data)
                if game_data_str in generated_matrices:
                    continue
                generated_matrices.add(game_data_str)
                
                # 生成问题描述
                question = prompt_timeSequence(raw_schedule=game_data['raw_schedule'], rules_desc=game_data['rules_desc'], is_chinese=is_chinese)
                
                # 创建游戏数据
                game_data = Data(
                    question=question,
                    answer=[game_data['answers']['answer_maxLen'], game_data['answers']['answer_nums']],  # 保存正确答案
                    metadata={
                        "trace_id": str(uuid.uuid4()),
                        "n": n,
                        "rule_prob": rule_prob,
                        "records": game_data
                    }
                )
                
                game_data_list.append(game_data)
                
            except Exception as e:
                print(f"生成题目时出错: {e}")
                # 添加调试信息
                import traceback
                print(f"错误详情: {traceback.format_exc()}")
                continue
                
        if len(game_data_list) < num_of_questions:
            print(f"警告: 只能生成 {len(game_data_list)}/{num_of_questions} 条游戏数据")
        
        return game_data_list
    
    def extract_answer(self, test_solution: str):
        """
        从模型的回答中提取答案（矩阵）
        
        @param test_solution: 模型的完整回答
        @return: 提取答案列表
        """
        if not test_solution:
            return ""
        
        # 尝试提取列表
        matrix_pattern = r'\[.*?\]'
        matrix_matches = re.findall(matrix_pattern, test_solution, re.DOTALL)
        if matrix_matches:
            # 使用最后一个匹配的列表
            print(matrix_matches)
            return matrix_matches[-1].strip()
        
        # 如果失败，返回空字符串
        return ""

class Generate_Task():
    def __init__(self):
        self.rules_desc, self.rules_desc_english = self.add_special_rules()
        self.rule_names = list(self.rules_desc.keys())
        pass

    def generate_main(self, n:int=3, rule_prob:float=0.5, is_chinese=True):
        """
        生成任务相关数据

        @para n: 人物数量，数量越多，难度越大
        @para rule_prob: 为人物添加额外规则的概率
        @return: 返回人物名称、初始日程安排信息、规则限制、转换后的日程安排、最终答案
        """
        final_result = {'raw_schedule':{}, 'trans_schedule':{}, 'rules':{}, 'rules_desc':{}, 'schedule_withRule':{}, 'answers':{}}
        # 随机选择人名
        choosed_names = self.choose_names(n=n, is_chinese=is_chinese)
        # 为每个人物生成一周的日程安排，并进行转换
        for name in choosed_names:
            raw_days_schedules, trans_days_schedules = self.relation_intergration()
            final_result['raw_schedule'][name] = raw_days_schedules
            final_result['trans_schedule'][name] = trans_days_schedules

        # print('----------------------------------')
        # print(final_result)
        # 为每个人物按照rule_prob的概率添加规则
        for name in choosed_names:
            if random.random()<=rule_prob:
                choosed_rule = random.choice(self.rule_names)
                final_result['rules'][name] = choosed_rule
                final_result['rules_desc'][name] = self.rules_desc[choosed_rule] if is_chinese else self.rules_desc_english[choosed_rule]
            else:
                final_result['rules'][name] = ''
                final_result['rules_desc'][name] = ''
        # print('================================')
        # 按照规则描述，更新日程安排，用于计算答案
        for name in choosed_names:
            new_schedule = self.add_special_rules(
                days_schedules=final_result['trans_schedule'][name], 
                choosed_rule=final_result['rules'][name]
                )
            final_result['schedule_withRule'][name] = new_schedule
        # print('*'*20)
        # print(final_result)

        # 根据规则，获取最长会议时间限制
        time_limit = self.cal_maxLen_time(rules=final_result['rules'])

        # 计算最终答案
        answer_record, answer_nums, answer_maxLen = self.cal_answers(final_result['schedule_withRule'], time_limit=time_limit)
        final_result['answers'] = {'answer_record':answer_record, 'answer_nums':answer_nums, 'answer_maxLen':answer_maxLen}
        return final_result

    def choose_names(self, n:int=3, is_chinese=True):
        candidate_names_english = [
            'Kaitlyn', 'Gerald', 'Jocelyn', 'Sara', 'Edwin', 'Savannah', 'Brian', 'Angela', 'Albert', 'Sean', 'Walter', 
            'Bailey', 'Helen', 'Sierra', 'Henry', 'Wayne', 'Kayla', 'Janice', 'Timothy', 'Tyler', 'Cindy', 'Julie', 'Tiffany', 
            'Robert', 'Chelsea', 'Joan', 'Benjamin', 'Raymond', 'Tammy', 'Kristen', 'Ashley', 'Mariah', 'Alyssa', 'Taylor', 
            'Thomas', 'Rose', 'Alexa', 'Rebecca', 'Sophia', 'Juan', 'Kenneth', 'Eric', 'Joe', 'Melanie', 'Ronnie', 'Leonard', 
            'Teresa', 'Patricia', 'Sydney', 'Paige', 'Morris', 'Katherine', 'Lauren', 'Judy', 'Stephen', 'Caleb', 'Gregory', 
            'Danny', 'Catherine', 'Martha', 'Abigail', 'Joshua', 'Carol', 'Christine', 'Jeremy', 'Arthur', 'Willie', 'Norman', 
            'Rodney', 'Larry', 'Luis', 'Casey', 'Amy', 'Gary', 'Philip', 'Melissa', 'Nicholas', 'Todd', 'Jean', 'Vanessa', 
            'Isabella', 'Ruth', 'Dylan', 'Michael', 'Roger', 'Frances', 'Craig', 'Glenn', 'Austin', 'Dale', 'Elizabeth', 'Allen', 
            'Deborah', 'Steven', 'Jack', 'Nathan', 'Terry', 'Theresa', 'Clarence', 'Manuel', 'Megan', 'Brittany', 'Johnny', 'Diane', 
            'Alfred', 'Harvey', 'Amanda', 'Emma', 'Morgan', 'Crystal', 'Tony', 'Faith', 'Samuel', 'Keith', 'Gabriel', 'Francis', 
            'Anthony', 'Victoria', 'Mark', 'Jesse', 'Makayla', 'Isaac', 'Allison', 'Rachel', 'Billy', 'Lindsey', 'Brenda', 'Rylee', 
            'Sabrina', 'Kylie', 'Stanley', 'Olivia', 'Jasmine', 'Edgar', 'Betty', 'Sandra', 'Floyd', 'James', 'Zoey', 'Susan', 'Jacob', 
            'Grace', 'Ronald', 'Justin', 'Randy', 'Marilyn', 'Vincent', 'Andrea', 'Autumn', 'Dorothy', 'Ernest', 'Jane', 'Brandon', 'Maria', 
            'Lisa', 'Patrick', 'William', 'Diana', 'Jimmy', 'Theodore', 'Carolyn', 'Alexander', 'Christina', 'Lloyd', 'Amber', 'Mikayla', 'Brooke', 
            'Jason', 'Samantha', 'Hugh', 'Aaron', 'Donna', 'Tommy', 'Dennis', 'Kyle', 'Kelsey', 'Erin', 'Charlotte', 'Jerome', 'Marissa', 
            'Alice', 'Leon', 'Jeffrey', 'Kathryn', 'Cory', 'Madeline', 'Alan', 'Carl', 'Kimberly', 'Joyce', 'Curtis', 'Michelle', 'Marvin', 
            'Jose', 'Daniel', 'Virginia', 'Shawn', 'Marie', 'Sarah', 'Karen', 'Earl', 'Brianna', 'Gloria', 'Lionel', 'Madison', 'John', 'Linda', 
            'Sharon', 'Anna', 'Cynthia', 'Beverly', 'Ann', 'Margaret', 'Denise', 'Bradley', 'Nathaniel', 'Michaela', 'Dustin', 'Logan', 'George', 
            'Frank', 'Donald', 'Glen', 'Stephanie', 'Shirley', 'Douglas', 'Bryan', 'Jordan', 'Bruce', 'Ryan', 'Eugene', 'Alexis', 'Andrew', 'Paul', 
            'Christopher', 'Nancy', 'Heather', 'Debra', 'Peter', 'Kelly', 'Danielle', 'Oscar', 'Joel', 'Otis', 'Gabriella', 'Lawrence', 'Jennifer', 
            'Evelyn', 'Lori', 'Hannah', 'Adam', 'Ethan', 'Kathleen', 'Cheryl', 'Emily', 'Barbara', 'Sophie', 'Pamela', 'Nicole', 'Martin', 'Zachary', 
            'Edward', 'Doris', 'Ralph', 'Mary', 'Noah', 'Christian', 'Russell', 'Joseph', 'Natalie', 'Jay', 'Laura', 'Harold', 'Julia', 'Jacqueline', 
            'Roy', 'Frederick', 'Judith', 'Matthew', 'Andre', 'Louis', 'Jessica', 'Kim', 'Valerie', 'Richard', 'Clifford', 'Amelia', 'Charles', 
            'Janet', 'Howard', 'Molly', 'Jonathan', 'Derek', 'David', 'Jerry', 'Jared', 'Bobby', 'Shane', 'Scott', 'Kevin', 'Haley'
            ]
        candidate_names_chinese = [
                "张伟", "王芳", "李娜", "刘洋", "陈强", "杨静", "黄磊", "赵敏", "周涛", "吴昊",
                "徐磊", "孙浩", "胡娟", "朱丽", "高峰", "马超", "董倩", "冯伟", "程琳", "宋刚",
                "何敏", "梁涛", "许倩", "邓超", "曹阳", "沈丽", "田野", "韩冰", "龚涛", "金鑫",
                "薛伟", "贾磊", "戴琳", "孟凡", "方婷", "邵明", "于波", "姚辉", "熊杰", "郑浩",
                "任涛", "陶亮", "卢伟", "白雪", "马丽", "钱峰", "汪静", "严磊", "戴强", "阎涛",
                "谭敏", "贺丽", "罗杰", "夏阳", "石磊", "史娟", "姜涛", "左娜", "冉亮", "章伟",
                "蒋倩", "莫凡", "丁浩", "易波", "覃峰", "尤静", "韦超", "庄敏", "庞磊", "武杰",
                "管霞", "蓝涛", "皮娜", "封伟", "栗倩", "党超", "池娜", "辛伟", "昌磊", "支昊",
                "边静", "黎涛", "湛亮", "丰杰", "候丽", "满伟", "滕静", "隆磊", "蔺倩", "温涛",
                "雷浩", "谷超", "左丽", "宁峰", "沙倩", "郁磊", "鲍娜", "佟涛", "仇伟", "栾敏",
                "甘磊", "那超", "殷静", "井伟", "伊倩", "仲涛", "乐丽", "虞峰", "沃超", "俞娜",
                "靳伟", "岳涛", "郜磊", "阮倩", "党丽", "慕超", "荆娜", "花涛", "帅伟", "占浩",
                "钟涛", "邝磊", "迟倩", "冶超", "拓静", "宫伟", "宓涛", "仝磊", "督倩", "郏丽",
                "甄超", "幸娜", "门涛", "来伟", "覃磊", "化倩", "厚丽", "买超", "年娜", "伊涛",
                "阴伟", "侯磊", "暴倩", "封丽", "白超", "乐娜", "全涛", "贝伟", "简磊", "车倩",
                "敖丽", "满超", "勾娜", "类涛", "桑伟", "谭磊", "师倩", "詹丽", "池超", "原娜",
                "东涛", "斐伟", "富磊", "漆倩", "达丽", "西超", "晁娜", "巨涛", "言伟", "普磊",
                "翦倩", "湛丽", "年超", "霜娜", "桑涛", "邸伟", "米磊", "阿倩", "义丽", "秋超",
                "区娜", "里涛", "满伟", "詹磊", "红倩", "豆丽", "纵超", "全娜", "闻涛", "赫伟",
                "左磊", "岳倩", "理丽", "白涛", "鲁伟", "周磊", "冀倩", "东丽", "冷超", "党娜",
                "钱涛", "冉伟", "印磊", "殷倩", "宇丽", "关超", "糜娜", "朱涛", "吉伟", "胡磊"
            ]
        if is_chinese:
            return random.sample(candidate_names_chinese, k=n)
        return random.sample(candidate_names_english, k=n)
    
    def generate_schedule(self):
        """
        为单个人物随机生成日称安排表
        
        从早上9点到晚上5点，每5分钟作为一个时间段进行分割。

        @para name：任务名称
        @return：一个长度为5的列表，代表周一到周五，每个元素是一个子列表，代表一天的日程安排
        """
        def generate_day_schedule(max_sche_nums):
            """
            随机生成一天的日程安排。将早上9点到晚上5点，分为96个时间段，每个时间段为5分钟。
            result中的子列表，第一个元素为起始时间，第二个元素为结束时间。
            """
            result = []
            pre_end = 0
            cur_nums=0
            while(cur_nums<max_sche_nums):
                weights = [1 / (i + 5) for i in range(36)]
                start_time = pre_end + random.choices(range(36), weights=weights, k=1)[0]
                weights = [1 / (i + 3) for i in range(24)]
                duration = random.choices(range(1, 25), weights=weights, k=1)[0]
                end_time = start_time + duration
                if end_time>96:
                    break
                result.append([start_time, end_time])
                pre_end = end_time
            return result
        days_schedules = []
        for i in range(5):
            days_schedules.append(generate_day_schedule(random.choice([2,3,4,5])))
        return days_schedules

    def relation_intergration(self):
        """
        日程安排生成与转换
        """
        # 1. 为人物生成每天的日程安排
        days_schedules = self.generate_schedule()
        # 2. 为人物的每一天，随机选择日程类型为 空闲、占用
        days_schedules_types = {}
        for day, day_schedule in zip(['一', '二', '三', '四', '五'], days_schedules):
            sche_type = random.choice(['空闲', '占用'])
            days_schedules_types[day] = [sche_type, day_schedule]
        
        raw_days_schedules_types = copy.deepcopy(days_schedules_types)

        # 3. 将空闲时间，转为占用时间
        days_schedules_types_trans = self.trans_free_2_booked(days_schedules_types)
        return raw_days_schedules_types, days_schedules_types_trans

    def trans_free_2_booked(self, days_schedules_types:dict):
        """
        将空闲日程，转为占用日程，方便求解答案
        """
        for key in days_schedules_types:
            if days_schedules_types[key][0]=='空闲':
                new_day_schedule = []
                start_time = 0
                for sche in days_schedules_types[key][1]:
                    new_day_schedule.append([start_time, sche[0]])
                    start_time = sche[1]
                new_day_schedule.append([start_time, 96])
                days_schedules_types[key][1] = new_day_schedule
                days_schedules_types[key][0] = '占用'
        return days_schedules_types

    def add_special_rules(self, days_schedules:dict={}, choosed_rule:str=''):
        """
        添加一些特殊的规则限制
        """
        rules_english = {
                '会议前的空闲时间限制': ' requires at least 10 minutes of free time before a meeting, and the free time must be between 9:00 AM and 5:00 PM.',
                '会议后的空闲时间限制': ' requires at least 10 minutes of free time after a meeting, and the free time must be between 9:00 AM and 5:00 PM.',
                '结束时间限制': ' feels tired and requires meetings to end before 4:00 PM.',
                '星期三午饭时间': ' needs to have lunch between 12:30 PM and 1:00 PM on Wednesdays.',
                '清空早上日程': ' can cancel the schedule between 9:00 AM and 9:45 AM each day (only those ending before 9:45 AM can be cancelled).',
                '时区差异': ' is in a time zone that is one hour ahead of others.',
                '时间偏好二四': ' prefers to hold short meetings on Tuesdays and Thursdays and only accepts new meetings on these two days, with a maximum duration of 1 hour.',
                '30分钟短会议清除': ' can remove any meetings of 30 minutes or less from the schedule.',
                '10分钟短会议清除': ' can be flexible and miss up to 10 minutes of a meeting.',
                '时间偏好二五': ' prefers to hold long meetings on Tuesdays and Fridays and only accepts new meetings on these two days, but the meeting duration must not exceed 30 minutes.',
        }

        rules = {
            '会议前的空闲时间限制': '要求在会议前至少有10分钟的空闲时间，并且空闲时间必须在上午9点到下午5点之间',
            '会议后的空闲时间限制': '要求在会议结束后至少有 10 分钟的空闲时间（空闲时间必须在她上午 9 点到下午 5 点之间）',
            '结束时间限制': '感到疲倦，要求会议在下午4点之前结束',
            '星期三午饭时间': '星期三需要在12:30到1:00之间吃午饭',
            '清空早上日程': '可以取消每天上午9:00到9:45之间的日程安排，（9:45之前结束的才可以取消）',
            '时区差异': '所处的时区，比其他时区要早一个小时',
            '时间偏好二四': '喜欢在周二和周四举行简短的会议，并且只在这两天接受新的会议，会议时间不超过1小时',
            '30分钟短会议清除': '可以从日程安排中清除任何30分钟或更短的会议',
            '10分钟短会议清除': '可以灵活缺席最多10分钟的会议',
            '时间偏好二五': '喜欢在周二和周五举行长时间的会议，并且只有在这两天接受新的会议，但会议时间不得超过 30 分钟',
        }
        if not days_schedules:
            return rules, rules_english
        def change_schedule(rule:str, days_schedules:dict):
            """
            根据规则，修改日程安排
            """
            def remove_duration_sche(days_schedules, max_duration):
                for key in days_schedules:
                    new_day_schedule = []
                    for sche in days_schedules[key][1]:
                        if sche[1]-sche[0]<=max_duration:
                            continue
                        new_day_schedule.append(sche)
                    days_schedules[key][1] = new_day_schedule
                return days_schedules

            if rule=='会议前的空闲时间限制':
                for key in days_schedules:
                    for sche in days_schedules[key][1]:
                        sche[1] += 2
            elif rule=='会议后的空闲时间限制':
                for key in days_schedules:
                    for sche in days_schedules[key][1]:
                        sche[0] -= 2
            elif rule=='星期三午饭时间':
                days_schedules['三'][1].append([42, 48])
            elif rule=='结束时间限制':
                for key in days_schedules:
                    days_schedules[key][1].append([84, 96])
            elif rule=='清空早上日程':
                for key in days_schedules:
                    new_day_schedule = []
                    for sche in days_schedules[key][1]:
                        if sche[0]<9 and sche[1]<=9:
                            continue
                        new_day_schedule.append(sche)
                    days_schedules[key][1] = new_day_schedule
            elif rule=='时区差异':
                for key in days_schedules:
                    days_schedules[key][1].append([84, 96])
            elif rule=='30分钟短会议清除':
                days_schedules = remove_duration_sche(days_schedules, 6)
            elif rule=='时间偏好二四':
                days_schedules['一'][1].append([0, 96])
                days_schedules['三'][1].append([0, 96])
                days_schedules['五'][1].append([0, 96])
            elif rule=='10分钟短会议清除':
                days_schedules = remove_duration_sche(days_schedules, 2)
            elif rule=='时间偏好二五':
                days_schedules['一'][1].append([0, 96])
                days_schedules['三'][1].append([0, 96])
                days_schedules['四'][1].append([0, 96])
            return days_schedules
        if not choosed_rule:
            return days_schedules
        days_schedules_copy = copy.deepcopy(days_schedules)
        days_schedules_copy = change_schedule(choosed_rule, days_schedules_copy)
        return days_schedules_copy
    
    def cal_maxLen_time(self, rules:dict):
        """
        根据特殊规则的限制，获取最长会议时间

        时间偏好二四：限制一小时以内
        时间偏好二五：限制30分钟以内
        """
        maxLen_time = 480
        for name in rules:
            if rules[name]=='时间偏好二四':
                maxLen_time = min(maxLen_time, 60)
            elif rules[name]=='时间偏好二五':
                maxLen_time = min(maxLen_time, 30)
        return maxLen_time

    def cal_answers(self, schedule_withRule:dict, time_limit:int=480):
        """
        根据日程安排表，计算最终答案

        限制要求：
        1、会议必须在整点或半点开始；
        2、有些规则中，存在最长会议时间的限制

        @param schedule_withRule: 引入规则限制之后的日程安排，可以直接计算答案
        @param time_limit: 最长会议时间限制
        @return [最长会议时间， 可选择的选项数]
        """

        record = np.zeros((96, 5))
        map_dict = {'一':0, '二':1, '三':2, '四':3, '五':4}
        for name in schedule_withRule.keys():
            days_schedules = schedule_withRule[name]
            for key in days_schedules:
                map_id = map_dict[key]
                for sche in days_schedules[key][1]:
                    for tmp in range(max(0, sche[0]), min(sche[1], 96)):
                        record[tmp, map_id] = 1
        answer_maxLen = 0
        answer_record = []
        for col in range(5):
            for row in range(0, 96, 6):    # 以整点或半点开始查找
                if record[row, col]==1:
                    continue
                cur_end = row
                length = 0
                while(cur_end<96 and record[cur_end, col]==0 and length<time_limit):
                    cur_end += 1
                    length += 5
                answer_record.append([row, cur_end])
                answer_maxLen = max(answer_maxLen, length)
        answer_nums = 0
        for tmp in answer_record:
            if (tmp[1]-tmp[0])*5==answer_maxLen:
                answer_nums += 1
        return answer_record, answer_nums, answer_maxLen
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Time Sequence任务生成器")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--max_attempts", type=int, default=1000, help="每个题目的最大尝试次数")
    parser.add_argument("--n", type=int, default=3, help="人物数量")
    parser.add_argument("--rule_prob", type=int, default=50, help="额外规则生成概率")
    args = parser.parse_args()
    
    # 创建数据目录
    base_data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not base_data_dir.exists():
        base_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建游戏实例
    game = TimeSequence()
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_questions=args.num_of_data,
        max_attempts=args.max_attempts,
        n=args.n,
        rule_prob=args.rule_prob
    )
    
    print(f"成功生成 {len(game_data_list)} 条游戏数据")

    # 创建嵌套目录结构
    nested_dir = base_data_dir / f"num_of_data_{args.num_of_data}" / f"n_{args.n}" / f"rule_prob_{args.rule_prob}"
    if not nested_dir.exists():
        nested_dir.mkdir(parents=True, exist_ok=True)

    # 设置输出文件名
    output_file = nested_dir / f"time_sequence_{args.num_of_data}.jsonl"
    
    # 将数据保存到文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"游戏数据已保存到 {output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}") 
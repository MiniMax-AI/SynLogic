#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import json
import os
import argparse
import pathlib
import re
from collections import defaultdict
from base.data import Data
import uuid
from games.base.game import Game
from games.tasks.word_sorting.scripts.word_sorting_verifier import WordSortingVerifier
from games.tasks.word_sorting.scripts.word_sorting_prompt import english_prompts, chinese_prompts

class WordSorting(Game):
    def __init__(self, front_letters_range=[1, 3], word_count_range=[15, 25]):
        """
        初始化WordSorting游戏
        
        @param front_letters_range: 前置字母数量范围 [最小值, 最大值]
        @param word_count_range: 生成单词数量范围 [最小值, 最大值]
        """
        super().__init__("Word Sorting", WordSortingVerifier)
        self.front_letters_min = front_letters_range[0]
        self.front_letters_max = front_letters_range[1]
        self.word_count_min = word_count_range[0]
        self.word_count_max = word_count_range[1]
        
        # 英文字母表
        self.english_alphabet = list('abcdefghijklmnopqrstuvwxyz')
        
        # 加载英文单词列表
        self.english_words = self.load_words()
        
        # 按首字母分组的单词
        self.words_by_first_letter = self.group_words_by_first_letter()
        
    def load_words(self):
        """加载英文单词列表"""
        current_dir = pathlib.Path(__file__).parent.resolve()
        
        # 加载英文单词列表
        words_path = current_dir / "words_alpha.txt"

        with open(words_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    
    def group_words_by_first_letter(self):
        """将单词按首字母分组"""
        grouped = defaultdict(list)
        for word in self.english_words:
            if word and len(word) > 0:
                first_letter = word[0].lower()
                grouped[first_letter].append(word)
        return grouped
    
    def create_new_alphabet(self):
        """
        创建新的字母顺序，将随机选取的字母放在最前面
        
        @return: 新的字母顺序列表, 前置字母列表
        """
        # 确定要放在前面的字母数量
        front_letters_count = random.randint(self.front_letters_min, self.front_letters_max)
        
        # 随机选择要放在前面的字母
        all_letters = list(self.english_alphabet)
        front_letters = random.sample(all_letters, front_letters_count)
        
        # 创建新的字母顺序
        remaining_letters = [letter for letter in all_letters if letter not in front_letters]
        new_alphabet = front_letters + remaining_letters
        
        return new_alphabet, front_letters
    
    def sort_words(self, words, alphabet):
        """
        使用新的字母顺序对单词列表进行排序
        
        @param words: 单词列表
        @param alphabet: 新的字母顺序
        @return: 排序后的单词列表
        """
        letter_order = {letter: i for i, letter in enumerate(alphabet)}
        
        def get_word_key(word):
            """获取单词的排序键"""
            # 将单词转换为小写并获取每个字母的顺序值
            return [letter_order.get(c, len(alphabet)) for c in word.lower()]
        
        return sorted(words, key=get_word_key)
    
    def select_words(self, count):
        """
        以均匀分布的方式选择单词
        
        首先随机选择一个字母组，然后从该组中随机选择一个单词
        
        @param count: 要选择的单词数量
        @return: 选择的单词列表
        """
        selected_words = []
        # 创建可用字母组的副本
        available_groups = [letter for letter in self.words_by_first_letter if self.words_by_first_letter[letter]]
        
        # 创建单词分组的深拷贝，防止修改原始数据
        words_by_first_letter_copy = {}
        for letter in self.words_by_first_letter:
            words_by_first_letter_copy[letter] = self.words_by_first_letter[letter].copy()
        
        # 继续选择直到达到所需数量或没有更多可用的组
        while len(selected_words) < count and available_groups:
            # 随机选择一个字母组
            group = random.choice(available_groups)
            word = random.choice(words_by_first_letter_copy[group])
            # 从组中移除这个单词以避免重复
            words_by_first_letter_copy[group].remove(word)
            selected_words.append(word)
        
        # 打乱单词顺序
        random.shuffle(selected_words)
        
        return selected_words
    
    def generate_problem(self):
        """
        生成单个题目
        
        @return: 包含问题、答案和元数据的字典
        """
        # 创建新的字母顺序
        new_alphabet, front_letters = self.create_new_alphabet()
        
        # 选择单词数量
        word_count = random.randint(self.word_count_min, self.word_count_max)
        
        # 选择单词 - 使用新的均衡选择方法
        selected_words = self.select_words(word_count)
        
        # 排序单词
        sorted_words = self.sort_words(selected_words, new_alphabet)
        
        # 创建问题

        selected_words_str = ",".join(selected_words)
        order = random.choice([1,-1])
        order_str = {
            "english": {
                1: "increasing",
                -1: "decreasing"
            },
            "chinese": {
                1: "升序",
                -1: "降序"
            }
        }
        prompt_dic = {"english": english_prompts, "chinese": chinese_prompts}
        language = random.choice(["english", "chinese"])
        if language == "english":
            front_letters_str = ",".join(front_letters[:-1]) + " and " + front_letters[-1]
        else:
            front_letters_str = "，".join(front_letters[:-1]) + "和" + front_letters[-1]
        question = random.choice(prompt_dic[language]).format(front_letters=front_letters_str, order=order_str[language][order], words=selected_words_str)
        # 创建答案
        if order == 1:
            answer = ", ".join(sorted_words)
        else:
            answer = ", ".join(sorted_words[::-1])
        
        return {
            "question": question,
            "answer": answer,
            "words": selected_words,
            "sorted_words": sorted_words,
            "new_alphabet": new_alphabet,
            "front_letters": front_letters,
            "order": order
        }
    
    def verify(self, data, response):
        """验证答案是否正确"""
        return self.verifier.verify(data, response)
    
    def extract_answer(self, response):
        return self.verifier.extract_answer(response)
    
    def generate(self, num_of_questions=100, max_attempts=100):
        """生成示例问题和答案"""
        outputs = []
        
        for i in range(num_of_questions):
            result = game.generate_problem()
         
            # 添加到输出
            outputs.append(Data(
                question=result["question"],
                answer=result["answer"],
                difficulty=1,
                metadata={
                    "words": result["words"],
                    "sorted_words": result["sorted_words"],
                    "front_letters": ",".join(result["front_letters"]),
                    "order": result["order"]
                }
            ))
        
        return outputs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成单词排序游戏数据")
    parser.add_argument("--num_of_data", type=int, default=1000, help="生成的题目数量")
    parser.add_argument("--front_letters_range", type=int, nargs=2, default=[2, 5], help="前置字母数量范围 [最小值, 最大值]")
    parser.add_argument("--word_count_range", type=int, nargs=2, default=[15, 25], help="生成单词数量范围 [最小值, 最大值]")
    args = parser.parse_args()
    
    # 创建游戏实例
    game = WordSorting(
        front_letters_range=args.front_letters_range,
        word_count_range=args.word_count_range
    )
    
    # 生成数据
    data_list = game.generate(num_of_questions=args.num_of_data)
    
    # 保存数据
    current_dir = pathlib.Path(__file__).parent.parent.resolve()
    data_dir = current_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 构建文件名
    fl_min, fl_max = args.front_letters_range
    wc_min, wc_max = args.word_count_range
    filename = f"data_fl{fl_min}-{fl_max}_wc{wc_min}-{wc_max}_n{args.num_of_data}.jsonl"
    file_path = data_dir / filename
    
    # 写入数据
    with open(file_path, 'w', encoding='utf-8') as f:
        for data in data_list:
            f.write(json.dumps({
                "question": data.question,
                "answer": data.answer,
                "difficulty": data.difficulty,
                "metadata": data.metadata
            }, ensure_ascii=False) + '\n')
    
    print(f"生成了 {args.num_of_data} 个单词排序游戏题目，保存到 {file_path}")

# coding: utf-8
import random
from typing import List, Dict, Tuple, Set, Optional, Any
from games.base.game import Game
from base.data import Data
import re
import json
import pathlib
import argparse

# 导入物品集合模块
from games.tasks.space_reasoning_tree.scripts.items_collection import get_random_items
from games.tasks.space_reasoning_tree.scripts.space_reasoning_tree_verifier import SpaceReasoningTreeVerifier
# 导入提示语模板
from games.tasks.space_reasoning_tree.scripts.space_reasoning_tree_prompt import prompts_zh, prompts_en

class TreeNode:
    """表示树结构中的一个节点"""
    def __init__(self, item: str = None):
        self.item = item          # 节点上的物品
        self.parent = None        # 父节点
        self.children = []        # 子节点列表
    
    def add_child(self, node: 'TreeNode'):
        """添加子节点"""
        self.children.append(node)
        node.parent = self
    
    def get_siblings(self) -> List['TreeNode']:
        """获取兄弟节点（共享同一父节点的节点）"""
        if not self.parent:
            return []
        return [node for node in self.parent.children if node != self]
    
    def get_cousins(self) -> List['TreeNode']:
        """获取堂兄弟节点（父节点的兄弟节点的子节点）"""
        if not self.parent or not self.parent.parent:
            return []
        
        cousins = []
        for uncle in self.parent.get_siblings():
            cousins.extend(uncle.children)
        
        return cousins
    
    def get_grandchildren(self) -> List['TreeNode']:
        """获取孙子节点"""
        grandchildren = []
        for child in self.children:
            grandchildren.extend(child.children)
        return grandchildren
    
    def get_grandfather(self) -> Optional['TreeNode']:
        """获取祖父节点"""
        if not self.parent or not self.parent.parent:
            return None
        return self.parent.parent

class SpaceReasoningTree(Game):
    """树结构空间推理游戏类"""
    def __init__(self, min_nodes=50, max_nodes=300):
        super().__init__("SpaceReasoningTree", SpaceReasoningTreeVerifier)
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
    
    def extract_answer(self, test_solution: str):
        return self.verifier.extract_answer(test_solution)
    
    def verify(self, data: Data, test_solution: str):
        return self.verifier.verify(data, test_solution)

    def build_five_layer_tree(self, num_nodes: int, language: str = "cn") -> Tuple[TreeNode, List[TreeNode]]:
        """
        构建五层的树结构并分配物品
        
        Args:
            num_nodes: 树中的节点总数
            language: 物品语言，"cn"为中文，"en"为英文
            
        Returns:
            根节点和所有节点的列表
        """
        # 创建节点列表
        nodes = [TreeNode() for _ in range(num_nodes)]
        
        # 从物品集合中随机选择物品
        items = get_random_items(num_nodes, language)
        
        # 分配物品给节点
        for i, node in enumerate(nodes):
            node.item = items[i]
        
        # 设置根节点
        root = nodes[0]
        remaining_nodes = nodes[1:]
        
        # 第一层：根节点已设置
        
        # 第二层：分配根节点的子节点（3-6个）
        level2_count = min(random.randint(3, 6), len(remaining_nodes))
        level2_nodes = remaining_nodes[:level2_count]
        remaining_nodes = remaining_nodes[level2_count:]
        
        for node in level2_nodes:
            root.add_child(node)
        
        # 第三层：给第二层的每个节点分配2-5个子节点
        level3_nodes = []
        for parent in level2_nodes:
            child_count = min(random.randint(2, 5), len(remaining_nodes))
            if child_count == 0:
                continue
                
            children = remaining_nodes[:child_count]
            remaining_nodes = remaining_nodes[child_count:]
            
            for child in children:
                parent.add_child(child)
                level3_nodes.append(child)
        
        # 第四层：给第三层的节点分配1-4个子节点
        level4_nodes = []
        for parent in level3_nodes:
            # 75%的概率添加子节点
            if random.random() < 0.75 and remaining_nodes:
                child_count = min(random.randint(1, 4), len(remaining_nodes))
                if child_count == 0:
                    continue
                    
                children = remaining_nodes[:child_count]
                remaining_nodes = remaining_nodes[child_count:]
                
                for child in children:
                    parent.add_child(child)
                    level4_nodes.append(child)
        
        # 第五层：给第四层的一些节点分配1-3个子节点
        for parent in level4_nodes:
            # 60%的概率添加子节点
            if random.random() < 0.6 and remaining_nodes:
                child_count = min(random.randint(1, 3), len(remaining_nodes))
                if child_count == 0:
                    continue
                    
                children = remaining_nodes[:child_count]
                remaining_nodes = remaining_nodes[child_count:]
                
                for child in children:
                    parent.add_child(child)
        
        # 如果还有剩余节点，将它们添加到随机位置
        while remaining_nodes:
            # 选择第二层到第四层的节点作为父节点
            potential_parents = level2_nodes + level3_nodes + level4_nodes
            if not potential_parents:
                break
                
            parent = random.choice(potential_parents)
            child = remaining_nodes.pop(0)
            parent.add_child(child)
        
        return root, nodes

    def find_valid_cousin_target(self, nodes: List[TreeNode]) -> Optional[TreeNode]:
        """
        找到一个有堂兄弟的有效目标节点
        
        Args:
            nodes: 所有节点列表
            
        Returns:
            有堂兄弟的节点，如果找不到则返回None
        """
        valid_targets = []
        
        for node in nodes:
            cousins = node.get_cousins()
            
            # 确保节点有堂兄弟，有父亲，有祖父
            if cousins and node.parent and node.parent.parent:
                valid_targets.append(node)
        
        if valid_targets:
            return random.choice(valid_targets)
        return None

    def generate_tree_description(self, nodes: List[TreeNode], target_node: TreeNode, language: str = "en") -> str:
        """
        生成树结构的描述，重点描述与目标节点相关的堂兄弟关系信息
        
        Args:
            nodes: 所有节点列表
            target_node: 目标节点（要询问其堂兄弟）
            language: 语言类型
            
        Returns:
            描述树结构的字符串
        """
        descriptions = []
        
        # 确保有祖父节点
        grandfather = target_node.get_grandfather()
        if not grandfather:
            return "无效的目标节点，没有祖父节点"
        
        # 决定使用哪种方式提供信息
        info_method = random.choice(["method1", "method2"])
        
        if info_method == "method1":
            # 方式1：提供目标节点爷爷的所有孙子以及目标节点父亲的所有孩子
            grandchildren = grandfather.get_grandchildren()
            children_of_parent = target_node.parent.children
            
            grandchildren_items = [node.item for node in grandchildren]
            parent_children_items = [node.item for node in children_of_parent]
            
            # 描述祖父的所有孙子
            if language == "cn":
                descriptions.append(f"{grandfather.item}的孙子是：{', '.join(grandchildren_items)}。")
            else:
                descriptions.append(f"{grandfather.item} has {len(grandchildren_items)} grandchildren: {', '.join(grandchildren_items)}.")
            
            # 描述父亲的所有孩子
            if language == "cn":
                descriptions.append(f"{target_node.parent.item}的孩子是：{', '.join(parent_children_items)}。")
            else:
                descriptions.append(f"{target_node.parent.item} has {len(parent_children_items)} {'child' if len(parent_children_items) == 1 else 'children'}: {', '.join(parent_children_items)}.")
                
        else:
            # 方式2：提供目标节点爷爷的所有孩子及各自的所有孩子
            grandfather_children = grandfather.children
            descriptions.append(f"{grandfather.item}的孩子是：{', '.join([node.item for node in grandfather_children])}。")
            for uncle in grandfather_children:
                children_items = [node.item for node in uncle.children]
                
                if children_items:
                    if language == "cn":
                        descriptions.append(f"{uncle.item}的孩子是：{', '.join(children_items)}。")
                    else:
                        descriptions.append(f"{uncle.item} has {len(children_items)} {'child' if len(children_items) == 1 else 'children'}: {', '.join(children_items)}.")
                else:
                    if language == "cn":
                        descriptions.append(f"{uncle.item}没有孩子。")
                    else:
                        descriptions.append(f"{uncle.item} has no children.")
        
        # 添加更多随机节点信息以增加复杂度
        additional_nodes = random.sample([n for n in nodes if n != target_node and n != grandfather and n != target_node.parent], 
                                         random.randint(len(nodes)//3, len(nodes)//2))
        
        for node in additional_nodes:
            info_type = random.choice(["children", "grandchildren", "no_children", "no_grandchildren", "siblings"])
            
            if info_type == "children" and node.children:
                children_items = [child.item for child in node.children]
                if language == "cn":
                    descriptions.append(f"{node.item}有{len(children_items)}个孩子：{', '.join(children_items)}。")
                else:
                    descriptions.append(f"{node.item} has {len(children_items)} {'child' if len(children_items) == 1 else 'children'}: {', '.join(children_items)}.")
            
            elif info_type == "grandchildren":
                grandchildren = node.get_grandchildren()
                if grandchildren:
                    gc_items = [gc.item for gc in grandchildren]
                    if language == "cn":
                        descriptions.append(f"{node.item}有{len(gc_items)}个孙子：{', '.join(gc_items)}。")
                    else:
                        if len(gc_items) > 4:
                            # 按父亲分组描述孙子
                            gc_by_parent = {}
                            for child in node.children:
                                if child.children:
                                    gc_by_parent[child.item] = [gc.item for gc in child.children]
                            
                            gc_descriptions = []
                            for parent, children in gc_by_parent.items():
                                gc_descriptions.append(f"{', '.join(children[:-1])}{' and ' if len(children) > 1 else ''}{children[-1]} (whose parent is {parent})")
                            
                            descriptions.append(f"{node.item} has {len(gc_items)} grandchildren: {' and '.join(gc_descriptions)}.")
                        else:
                            descriptions.append(f"{node.item} has {len(gc_items)} grandchildren: {', '.join(gc_items)}.")
            
            elif info_type == "no_children" and not node.children:
                if language == "cn":
                    descriptions.append(f"{node.item}没有孩子。")
                else:
                    descriptions.append(f"{node.item} has no children.")
            
            elif info_type == "no_grandchildren" and not node.get_grandchildren():
                if language == "cn":
                    if node.children:
                        children_items = [child.item for child in node.children]
                        descriptions.append(f"{node.item}没有孙子，但有{len(children_items)}个孩子：{', '.join(children_items)}。")
                    else:
                        descriptions.append(f"{node.item}没有孙子。")
                else:
                    if node.children:
                        children_items = [child.item for child in node.children]
                        descriptions.append(f"{node.item} has no grandchildren but has {len(children_items)} {'child' if len(children_items) == 1 else 'children'}: {', '.join(children_items)}.")
                    else:
                        descriptions.append(f"{node.item} has no grandchildren.")
            
            elif info_type == "siblings":
                siblings = node.get_siblings()
                if siblings:
                    sibling_items = [sib.item for sib in siblings]
                    if language == "cn":
                        descriptions.append(f"{node.item}与{', '.join(sibling_items)}是兄弟节点。")
                    else:
                        descriptions.append(f"{node.item}{',' if len(sibling_items) > 1 else ''} and {', '.join(sibling_items[:-1])}{' and ' if len(sibling_items) > 1 else ''}{sibling_items[-1]} are siblings.")
        
        # 随机打乱描述顺序
        random.shuffle(descriptions)
        
        return " ".join(descriptions)

    def generate_problem(self, language="en"):
        """
        生成一个树结构空间推理问题，询问目标节点的堂兄弟节点
        
        Args:
            language: 语言，"cn"为中文，"en"为英文
            
        Returns:
            问题描述和答案
        """
        # 随机确定节点数量
        num_nodes = random.randint(self.min_nodes, self.max_nodes)
        
        # 构建五层树结构
        root, nodes = self.build_five_layer_tree(num_nodes, language)
        
        # 寻找一个有堂兄弟的目标节点
        target_node = self.find_valid_cousin_target(nodes)
        
        if not target_node:
            # 如果找不到有效目标，重新生成树
            return self.generate_problem(language)
        
        # 生成树结构描述
        tree_description = self.generate_tree_description(nodes, target_node, language)
        
        # 获取目标节点的堂兄弟作为答案
        cousins = target_node.get_cousins()
        cousin_items = sorted([node.item for node in cousins])
        answer = ", ".join(cousin_items)
        
        # 构建完整问题
        if language == "cn":
            context = f"你被给定了一个有{num_nodes}个节点的树结构。{tree_description}"
            question = f"{target_node.item}的堂兄弟节点是什么？你的最终答案必须只包含物品名称。如果有多个物品，请将它们按字母顺序排列并用逗号分隔。"
            # 随机选择一个中文提示模板
            prompt_template = random.choice(prompts_zh)
        else:
            context = f"You have been given a tree structure with {num_nodes} nodes. {tree_description}"
            question = f"What is the cousin of the {target_node.item}? Your final answer must be only the object name (e.g., laptop). If there are multiple objects, provide them as a comma-separated list in alphabetical order (e.g., laptop, mug)."
            # 随机选择一个英文提示模板
            prompt_template = random.choice(prompts_en)
        
        # 使用提示模板格式化问题
        full_question = prompt_template.format(context=context, question=question)
        
        return full_question, answer

    def generate(self, num_of_data=10, language="mixed"):
        """
        生成多个树结构空间推理问题
        
        Args:
            num_of_data: 生成的问题数量
            language: 语言，"cn"为中文，"en"为英文，"mixed"为混合
            
        Returns:
            Data对象列表
        """
        outputs = []
        for i in range(num_of_data):
            if language == "mixed":
                now_language = random.choice(["cn", "en"])
            else:
                now_language = language
                
            question, answer = self.generate_problem(now_language)
            
            outputs.append(Data(
                question=question,
                answer=answer,
                difficulty=2,
                metadata={"language": now_language, "max_num_nodes": self.max_nodes, "min_num_nodes": self.min_nodes}
            ))
        
        return outputs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成空间推理树结构游戏数据")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--min_nodes", type=int, default=50, help="最小节点数量")
    parser.add_argument("--max_nodes", type=int, default=300, help="最大节点数量")
    parser.add_argument("--language", type=str, default="mixed", help="语言：cn, en, mixed")
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"创建数据目录: {data_dir}")
    
    # 创建游戏实例
    game = SpaceReasoningTree(min_nodes=args.min_nodes, max_nodes=args.max_nodes)
    
    # 使用参数构建文件名
    filename = f"data_nodes{args.min_nodes}-{args.max_nodes}_{args.language}_n{args.num_of_data}.jsonl"
    output_file = data_dir / filename
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_data=args.num_of_data,
        language=args.language
    )
    
    # 将数据保存到文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for game_data in game_data_list:
                f.write(json.dumps(game_data.to_json(), ensure_ascii=False) + "\n")
        print(f"成功生成{len(game_data_list)}条数据，保存至: {output_file}")
    except Exception as e:
        print(f"保存数据时出错: {e}")

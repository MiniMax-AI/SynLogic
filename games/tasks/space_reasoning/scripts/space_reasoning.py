# coding: utf-8
import random
from typing import List, Dict, Tuple, Set, Optional
from games.base.game import Game
from base.data import Data
import random
import re
# 导入物品集合模块
from games.tasks.space_reasoning.scripts.items_collection import distribute_items_to_nodes
from games.tasks.space_reasoning.scripts.space_reasoning_verifier import SpaceReasoningVerifier
# 导入提示语模块
from games.tasks.space_reasoning.scripts.space_reasoning_prompt import prompts_zh, prompts_en
import argparse
import pathlib
import json

class Node:
    """表示网格中的一个节点"""
    def __init__(self, item: str = None):
        self.item = item          # 节点上的物品
        self.connections = {}     # 方向 -> 节点的映射

    def add_connection(self, direction: str, node: 'Node'):
        """添加到其他节点的连接"""
        self.connections[direction] = node

class SpaceReasoning(Game):
    """空间推理游戏类"""
    def __init__(self, jump_ratio = 0.5,n=5):
        super().__init__("SpaceReasoning",SpaceReasoningVerifier)
        self.jump_ratio = jump_ratio
        self.n = n
    
    def extract_answer(self,test_solution: str):
        return self.verifier.extract_answer(test_solution)
    
    def verify(self,data: Data,test_solution: str):
        return self.verifier.verify(data,test_solution)

    def build_square_network(self,n: int, language: str = "cn") -> List[Node]:
        """构建一个正方形网格，并为每个节点分配物品
        
        Args:
            n: 参数n表示网格大小，为n*n的正方形网格（有(n+1)*(n+1)个节点）
            language: 物品语言，"cn"为中文，"en"为英文
            
        Returns:
            包含所有节点的列表
        """
        if n <= 0:
            return []
        
        # 计算节点总数 (n+1) * (n+1)
        total_nodes = (n+1) * (n+1)
        
        # 创建所有节点
        nodes = [Node() for _ in range(total_nodes)]
        
        # 创建二维索引到一维索引的映射函数
        def get_node_index(row, col):
            return row * (n+1) + col
        
        # 建立连接
        for row in range(n+1):
            for col in range(n+1):
                current_idx = get_node_index(row, col)
                
                # 向右连接
                if col < n:
                    right_idx = get_node_index(row, col+1)
                    nodes[current_idx].add_connection("右" if language == "cn" else "right", nodes[right_idx])
                    nodes[right_idx].add_connection("左" if language == "cn" else "left", nodes[current_idx])
                
                # 向下连接
                if row < n:
                    down_idx = get_node_index(row+1, col)
                    nodes[current_idx].add_connection("下" if language == "cn" else "down", nodes[down_idx])
                    nodes[down_idx].add_connection("上" if language == "cn" else "up", nodes[current_idx])

        # 为节点分配物品
        distribute_items_to_nodes(nodes, language)
        
        # 根据语言选择描述
        if language == "cn":
            description = f"你在一个N*N的正方形瓷砖上，每一行都有N个正方形，正方形每个顶点上都有一个独特的物品。你将沿着这些瓷砖的边移动，并在顶点看到物体。"
        else:
            description = f"You are on an N*N square grid where each row has N squares. Each vertex of these squares has a unique item. You will move along the edges of these tiles and see objects at the vertices."
            
        return description, nodes

    def build_diamond_network(self,n: int,language: str = "cn") -> List[Node]:
        """构建一个菱形网络，并为每个节点分配物品
        
        Args:
            n: 参数n表示网络有n+1行，第一行有1个节点，第i行有i个节点
            language: 物品语言，"cn"为中文，"en"为英文
            
        Returns:
            包含所有节点的列表
        """
        if n <= 0:
            return []
        
        # 计算节点总数: 1 + 2 + 3 + ... + (n+1) + n = (n+1)(n+2)/2 + n
        total_nodes = (n+1)*(n+2)//2 + n
        
        # 创建所有节点
        nodes = [Node() for _ in range(total_nodes)]
        
        # 按行组织节点索引
        row_indices = []
        node_index = 0
        for i in range(1, n+2):  # n+1行
            row_indices.append(list(range(node_index, node_index + i)))
            node_index += i
        row_indices.append(range(node_index, node_index + n))
        
        # 建立连接
        for row in range(n+1):  # 对每一行
            row_nodes = row_indices[row]
                        
            # 与下一行的连接
            if row < n:  # 不是最后一行
                next_row_nodes = row_indices[row + 1]
                
                for i in range(len(row_nodes)):
                    nodes[row_nodes[i]].add_connection("左下" if language == "cn" else "bottom-left", nodes[next_row_nodes[i]])
                    nodes[next_row_nodes[i]].add_connection("右上" if language == "cn" else "top-right", nodes[row_nodes[i]])
                
                    nodes[row_nodes[i]].add_connection("右下" if language == "cn" else "bottom-right", nodes[next_row_nodes[i+1]])
                    nodes[next_row_nodes[i+1]].add_connection("左上" if language == "cn" else "top-left", nodes[row_nodes[i]])
        
        for i in range(n+1):
            if i != n:
                nodes[row_indices[-2][i]].add_connection("右下" if language == "cn" else "bottom-right", nodes[row_indices[-1][i]])
                nodes[row_indices[-1][i]].add_connection("左上" if language == "cn" else "top-left", nodes[row_indices[-2][i]])
            if i != 0:
                nodes[row_indices[-2][i]].add_connection("左下" if language == "cn" else "bottom-left", nodes[row_indices[-1][i-1]])
                nodes[row_indices[-1][i-1]].add_connection("右上" if language == "cn" else "top-right", nodes[row_indices[-2][i]])

        # 为节点分配物品
        distribute_items_to_nodes(nodes, language)
        
        # 根据语言选择描述
        if language == "cn":
            description = f"构建了一个N层的菱形网络，其中第1层有一个菱形，第2层有2个菱形，第3层有3个菱形，以此类推，第N层有N个菱形，每个顶点上都有一个独特的物品。你将沿着这些瓷砖的边移动，并在每个顶点看到物体。"
        else:
            description = f"There is an N-layer diamond network where the 1st layer has one diamond, the 2nd layer has 2 diamonds, the 3rd layer has 3 diamonds, and so on. The Nth layer has N diamonds, with each vertex having a unique item. You will move along the edges and see objects at each vertex."
            
        return description, nodes

    def build_triangle_network(self,n: int,language: str = "cn") -> List[Node]:
        """构建一个三角形网络，并为每个节点分配物品
        
        Args:
            n: 参数n表示网络有n+1行，第一行有1个节点，第i行有i个节点
            language: 物品语言，"cn"为中文，"en"为英文
            
        Returns:
            包含所有节点的列表
        """
        if n <= 0:
            return []
        
        # 计算节点总数: 1 + 2 + 3 + ... + (n+1) = (n+1)(n+2)/2
        total_nodes = (n+1)*(n+2)//2
        
        # 创建所有节点
        nodes = [Node() for _ in range(total_nodes)]
        
        # 按行组织节点索引
        row_indices = []
        node_index = 0
        for i in range(1, n+2):  # n+1行
            row_indices.append(list(range(node_index, node_index + i)))
            node_index += i
        
        # 建立连接
        for row in range(n+1):  # 对每一行
            row_nodes = row_indices[row]
            
            if row != 0:
                # 同行内的横向连接（左右）
                nodes[row_nodes[0]].add_connection("右" if language == "cn" else "right", nodes[row_nodes[1]])
                nodes[row_nodes[-1]].add_connection("左" if language == "cn" else "left", nodes[row_nodes[-2]])
                for i in range(1, len(row_nodes) - 1):
                    nodes[row_nodes[i]].add_connection("右" if language == "cn" else "right", nodes[row_nodes[i+1]])
                    nodes[row_nodes[i+1]].add_connection("左" if language == "cn" else "left", nodes[row_nodes[i]])
            
            # 与下一行的连接
            if row < n:  # 不是最后一行
                next_row_nodes = row_indices[row + 1]
                
                for i in range(len(row_nodes)):
                    nodes[row_nodes[i]].add_connection("左下" if language == "cn" else "bottom-left", nodes[next_row_nodes[i]])
                    nodes[next_row_nodes[i]].add_connection("右上" if language == "cn" else "top-right", nodes[row_nodes[i]])
                
                    nodes[row_nodes[i]].add_connection("右下" if language == "cn" else "bottom-right", nodes[next_row_nodes[i+1]])
                    nodes[next_row_nodes[i+1]].add_connection("左上" if language == "cn" else "top-left", nodes[row_nodes[i]])
        
        # 为节点分配物品
        distribute_items_to_nodes(nodes, language)
        
        # 根据语言选择描述
        if language == "cn":
            description = f"构建了一个N层的三角形网络，其中第1层有一个三角形，第2层有3个三角形，第3层有5个三角形，以此类推，第N层有2N+1个三角形，每个顶点上都有一个独特的物品。你将沿着这些瓷砖的边移动，并在每个顶点看到物体。"
        else:
            description = f"There is an N-layer triangular network where the 1st layer has one triangle, the 2nd layer has 3 triangles, the 3rd layer has 5 triangles, and so on. The Nth layer has 2N+1 triangles, with each vertex having a unique item. You will move along the edges and see objects at each vertex."
            
        return description, nodes
    
    def find_path(self,nodes: List[Node], start_idx: int, end_idx: int) -> Optional[List[Tuple[int, Optional[str]]]]:
        """
        使用BFS找出两个节点之间的最短路径
        
        Args:
            nodes: 三角形网络的节点列表
            start_idx: 起始节点的索引
            end_idx: 目标节点的索引
            
        Returns:
            路径列表，每个元素是(节点索引, 到达下一个节点的方向)的元组，最后一个元素的方向为None
            如果不存在路径则返回None
        """
        if start_idx == end_idx:
            return [(start_idx, None)]
        
        # 创建节点对象到索引的映射
        node_to_idx = {id(node): idx for idx, node in enumerate(nodes)}
        
        # 初始化队列和已访问集合
        queue = [start_idx]
        visited = {start_idx}
        
        # 记录每个节点的前驱和到达该节点的方向
        predecessors = {}  # {当前节点索引: (前驱节点索引, 到达当前节点的方向)}
        
        while queue:
            current_idx = queue.pop(0)
            current_node = nodes[current_idx]
            
            # 以随机顺序检查所有相邻节点
            directions = list(current_node.connections.keys())
            random.shuffle(directions)  # 随机化方向顺序
            
            for direction in directions:
                next_node = current_node.connections[direction]
                next_idx = node_to_idx[id(next_node)]
                
                if next_idx not in visited:
                    visited.add(next_idx)
                    queue.append(next_idx)
                    
                    # 记录前驱和方向
                    predecessors[next_idx] = (current_idx, direction)
                    
                    # 如果找到目标节点，构建路径并返回
                    if next_idx == end_idx:
                        path = []
                        current = next_idx
                        
                        # 从终点回溯到起点
                        while current != start_idx:
                            prev, direction = predecessors[current]
                            path.append((prev, direction))
                            current = prev
                        
                        # 逆转路径并添加终点
                        path.reverse()
                        path.append((end_idx, None))
                        return path
        
        # 如果没有找到路径
        return None
    
    def generate_multi_node_path(self,nodes: List[Node], waypoint_indices: List[int],language: str = "cn") -> Tuple[List[Tuple[int, Optional[str]]], str]:
        """
        生成经过指定节点的路径
        
        Args:
            nodes: 网络的节点列表
            waypoint_indices: 必须经过的节点索引列表
            
        Returns:
            完整路径列表和描述路径的字符串
        """
        if len(waypoint_indices) < 2:
            return None, "路径点数量不足，至少需要2个节点"
        
        # 生成关键节点之间的路径
        complete_path = []
        path_description = ""
        
        for i in range(len(waypoint_indices) - 1):
            start_idx = waypoint_indices[i]
            end_idx = waypoint_indices[i + 1]
            
            # 找到两个关键节点之间的路径
            segment_path = self.find_path(nodes, start_idx, end_idx)
            if not segment_path:
                return None, "无法找到从节点{start_idx}到节点{end_idx}的路径" if language == "cn" else f"Cannot find a path from node {start_idx} to node {end_idx}"
            
            # 添加路径段
            if i == 0:
                complete_path.extend(segment_path)
            else:
                # 替换前一段的最后一个节点的方向
                if complete_path:
                    next_direction = None
                    # 找到下一段的第一个方向
                    for j in range(len(segment_path) - 1):
                        if segment_path[j][0] == complete_path[-1][0]:
                            next_direction = segment_path[j][1]
                            break
                    
                    # 更新前一段的最后一个节点的方向
                    if next_direction:
                        last_idx = complete_path[-1][0]
                        complete_path[-1] = (last_idx, next_direction)
                    
                    # 添加剩余路径（跳过第一个节点）
                    complete_path.extend(segment_path[1:])
            
            # 生成路径描述
            if i == 0:
                if language == "cn":
                    path_description += f"看到了一个{nodes[start_idx].item}，"
                else:
                    path_description += f"You see a {nodes[start_idx].item}, "
            
            # 优化方向描述，合并相同方向
            directions = []
            curr_dir = None
            dir_count = 0
            
            for j in range(len(segment_path) - 1):
                direction = segment_path[j][1]
                
                if direction != curr_dir:
                    # 添加前一个方向描述
                    if curr_dir and dir_count > 0:
                        if language == "cn":
                            dir_desc = f"然后向{curr_dir}方向{dir_count}步"
                        else:
                            dir_desc = f"then {dir_count} step(s) {curr_dir}"
                        directions.append(dir_desc)
                    
                    # 开始新的方向计数
                    curr_dir = direction
                    dir_count = 1
                else:
                    # 相同方向，增加计数
                    dir_count += 1
            
            # 添加最后一个方向
            if curr_dir and dir_count > 0:
                if language == "cn":
                    dir_desc = f"然后向{curr_dir}方向{dir_count}步"
                else:
                    dir_desc = f"then {dir_count} step(s) {curr_dir}"
                directions.append(dir_desc)
            
            path_description += "，".join(directions) if language == "cn" else ", ".join(directions)
            
            if language == "cn":
                path_description += f"，看到了一个{nodes[end_idx].item}。"
            else:
                path_description += f", and you see a {nodes[end_idx].item}. "
        
        return complete_path, path_description

    def generate_question(self, nodes: List[Node], start_idx: int, end_idx: int, seen_node: List[int],language: str = "cn") -> Tuple[str, str]:
        """
        生成一个空间推理问题
        
        Args:
            nodes: 网络的节点列表
            start_idx: 起始节点的索引
            end_idx: 目标节点的索引
            seen_node: 已经看到的节点索引列表
        Returns:
            问题字符串和答案
        """
        # 找到从起点到终点的路径
        path = self.find_path(nodes, start_idx, end_idx)
        if not path:
            return "无法找到从起点到终点的路径", ""
        
        # 获取所有可用作中间点的候选节点（不在已见节点列表中的节点）
        available_nodes = [i for i in range(len(nodes)) if i not in seen_node and i != start_idx and i != end_idx]
        
        # 随机选择1到3个中间节点
        num_waypoints = min(3, len(available_nodes))
        if num_waypoints > 0 and available_nodes:
            waypoints = random.sample(available_nodes, num_waypoints)
            
            # 创建路径：起点 -> 中间点1 -> 中间点2 -> ... -> 终点
            waypoints = [start_idx] + waypoints + [end_idx]
            
            # 生成经过这些节点的路径
            complete_path, _ = self.generate_multi_node_path(nodes, waypoints)
            
            # 如果生成成功，使用这个更长的路径
            if complete_path:
                path = complete_path
        
        # 生成路径描述
        question = "从当前位置开始，" if language == "cn" else "Starting from your current position, "
        
        # 优化方向描述，合并相同方向
        directions = []
        curr_dir = None
        dir_count = 0
        
        for i in range(len(path) - 1):
            curr_idx, direction = path[i]
            
            if direction != curr_dir:
                # 添加前一个方向描述
                if curr_dir and dir_count > 0:
                    if language == "cn":
                        dir_desc = f"往{curr_dir}{dir_count}步"
                    else:
                        dir_desc = f"go {dir_count} step(s) {curr_dir}"
                    directions.append(dir_desc)
                
                # 开始新的方向计数
                curr_dir = direction
                dir_count = 1
            else:
                # 相同方向，增加计数
                dir_count += 1
        
        # 添加最后一个方向
        if curr_dir and dir_count > 0:
            if language == "cn":
                dir_desc = f"往{curr_dir}{dir_count}步"
            else:
                dir_desc = f"go {dir_count} step(s) {curr_dir}"
            directions.append(dir_desc)
        
        # 构建问题
        question += "，".join(directions) if language == "cn" else ", ".join(directions)
        
        # 添加问题的结尾
        if language == "cn":
            question += "，看到的物品是什么？"
        else:
            question += ", what item do you see?"
        
        # 答案是终点节点的物品
        answer = nodes[end_idx].item
        
        return question, answer

    def get_random_waypoints(self,node_count: int, num_waypoints: int = 3) -> List[int]:
        """
        随机选择路径关键点
        
        Args:
            node_count: 节点总数
            num_waypoints: 需要选择的关键点数量
            
        Returns:
            节点索引列表
        """
        # 确保关键节点数量合理
        num_waypoints = min(num_waypoints, node_count)
        if num_waypoints < 2:
            num_waypoints = 2
            
        # 随机选择关键节点
        return random.sample(range(node_count), num_waypoints)

    def jump2unknown(self,nodes,seen_node,unknown_node_num,language: str = "cn"):
        node1 = random.sample(seen_node, 1)[0]
        other_indices = random.sample([i for i in range(len(nodes)) if i not in seen_node], unknown_node_num)
        other_indices.append(node1)
        random.shuffle(other_indices)
        paths,path_description = self.generate_multi_node_path(nodes, other_indices,language)
        seen_node = seen_node + other_indices
        return seen_node,path_description


    def generate_problem(self,shape = "build_triangle_network",language='cn',num_waypoints = 10,unknown_node_num = 5):
        description,nodes = eval(f"self.{shape}(self.n,language)")
        path_description = f"{description}"
        
        if language == "cn":
            path_description += "你从其中某一个点开始，"
        else:
            path_description += "You start from one of the points, "
            
        waypoint_indices = self.get_random_waypoints(len(nodes), num_waypoints)
        paths, description = self.generate_multi_node_path(nodes, waypoint_indices,language)
        path_description += description
        
        if random.random() < self.jump_ratio:
            if language == "cn":
                path_description += "然后你跳到了一个任意的节点，"
            else:
                path_description += "Then you jump to a random node, "
                
            waypoint_indices,description = self.jump2unknown(nodes, waypoint_indices, unknown_node_num,language)
            path_description += description
            
            if random.random() < 0.5:
                if language == "cn":
                    path_description += "然后你回到了那个任意的节点，"
                else:
                    path_description += "Then you return to that random node, "
                    
                waypoint_indices.append(waypoint_indices[-(unknown_node_num+1)])
                
        question,answer = self.generate_question(nodes, waypoint_indices[-1], random.choice(waypoint_indices), waypoint_indices,language)
        return path_description,question,answer

    def generate(self,num_of_data = 10,num_waypoints = 10,unknown_node_num = 5,language = "mixed"):
        outputs = []
        for i in range(num_of_data):
            shape = random.choice(["build_triangle_network","build_diamond_network","build_square_network"])
            if language == "mixed":
                now_language = random.choice(["cn","en"])
            else:
                now_language = language
            path_description,question,answer = self.generate_problem(shape,now_language,num_waypoints,unknown_node_num)
            if now_language == "cn":
                question = random.choice(prompts_zh).format(context=path_description, question=question)
            else:
                question = random.choice(prompts_en).format(context=path_description, question=question)
            
            outputs.append(Data(
                question=question,
                answer=answer,
                difficulty=1,
                metadata={"shape":shape,"language":now_language,"num_waypoints":num_waypoints,"unknown_node_num":unknown_node_num,
                "n":self.n}
            ))
        return outputs



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成空间推理游戏数据")
    parser.add_argument("--jump_ratio", type=float, default=0.5, help="跳跃到未知节点的概率")
    parser.add_argument("--num_of_data", type=int, default=100, help="生成的题目数量")
    parser.add_argument("--num_waypoints", type=int, default=10, help="路径关键点数量")
    parser.add_argument("--unknown_node_num", type=int, default=5, help="未知节点数量")
    parser.add_argument("--language", type=str, default="mixed", help="语言")
    parser.add_argument("--n", type=int, default=5, help="网格大小参数")
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"创建数据目录: {data_dir}")
    
    # 创建游戏实例
    game = SpaceReasoning(jump_ratio=args.jump_ratio, n=args.n)
    # 使用参数构建文件名
    filename = f"data_n{args.n}_wp{args.num_waypoints}_un{args.unknown_node_num}_jr{args.jump_ratio}_{args.language}_n{args.num_of_data}.jsonl"
    output_file = data_dir / filename
    
    # 生成游戏数据
    game_data_list = game.generate(
        num_of_data=args.num_of_data, 
        num_waypoints=args.num_waypoints, 
        unknown_node_num=args.unknown_node_num,
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
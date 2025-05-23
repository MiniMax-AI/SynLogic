from base.data import Data
from base.verifier import Verifier
import re

def _search_brackets(answer_str):
    # Try strict match pattern first
    pattern = r'(?<=[the|The] answer is )(.*)(?=.)'
    match = re.search(pattern, answer_str)
    if match:
        # 提取括号序列，去除多余空格
        brackets = match.group(1).strip()
        return brackets
    return answer_str.strip()
    
class BBHDyckLanguagesVerifier(Verifier):
    """
    Verifier for Dyck Languages tasks
    """
    def verify(self, data: Data, test_solution: str):
        try:
            test_answer = self.extract_answer(test_solution)
            ground_truth = data.answer
            
            # 标准化答案格式：移除多余空格
            test_answer = ' '.join(test_answer.split())
            ground_truth = ' '.join(ground_truth.split())
            
            correct = test_answer == ground_truth
            if correct:
                acc_score = 1.0
            else:
                acc_score = 0

            return acc_score
        except:
            return False
    
    def extract_answer(self, test_solution: str):
        answer_str = test_solution
        return _search_brackets(answer_str=answer_str)

if __name__ == '__main__':
    # Test cases
    test_cases = [
        "The answer is ] } ].",
        "The answer is ] ) ).",
        "The answer is } ] >.",
        "] } ]",  # 直接的括号序列
        "Final answer: ] ) )"  # 其他格式
    ]
    
    for case in test_cases:
        print(f"Input: {case}")
        print(f"Output: {_search_brackets(case)}\n")
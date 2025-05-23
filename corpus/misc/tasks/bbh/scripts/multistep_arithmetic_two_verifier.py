from base.data import Data
from base.verifier import Verifier
import re


def _extract_number(answer_str):
    # 尝试从"The answer is"格式中提取
    strict_pattern = r'(?<=[the|The] answer is )([-0-9]+)(?=.)'
    match = re.search(strict_pattern, answer_str)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    
    # 尝试直接提取数字
    number_pattern = r'([-0-9]+)'
    match = re.search(number_pattern, answer_str)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    
    # 如果无法提取数字，返回原字符串
    return answer_str.strip()
    
class BBHMultistepArithmeticVerifier(Verifier):
    """
    Verifier for Multistep Arithmetic tasks
    """
    def verify(self, data: Data, test_solution: str):
        try:
            test_answer = self.extract_answer(test_solution)
            ground_truth = data.answer
            
            # 将答案转换为整数进行比较
            if isinstance(test_answer, str):
                try:
                    test_answer = int(test_answer)
                except ValueError:
                    return False
                
            if isinstance(ground_truth, str):
                try:
                    ground_truth = int(ground_truth)
                except ValueError:
                    return False
            
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
        return _extract_number(answer_str=answer_str)

if __name__ == '__main__':
    # Test cases
    test_cases = [
        "The answer is 42.",
        "The answer is -15.",
        "The final result is 100",
        "42",
        "-15",
        "The sum equals 100."
    ]
    
    for case in test_cases:
        print(f"Input: {case}")
        print(f"Output: {_extract_number(case)}\n")
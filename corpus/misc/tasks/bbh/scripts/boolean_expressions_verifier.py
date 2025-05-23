from base.data import Data
from base.verifier import Verifier
import re
from sympy.parsing.latex import parse_latex

THOUGHT_DELIMITER_START = "<think>"
THOUGHT_DELIMITER_END = "</think>"

def _extract_answer(text):
    # 定义正则表达式模式，匹配 <answer> 和 </answer> 之间的内容
    pattern = r'<answer>(.*?)</answer>'
    
    # 使用 re.search 查找第一个匹配项
    match = re.search(pattern, text, re.DOTALL)
    
    # 如果找到匹配项，返回匹配的内容
    if match:
        return match.group(1).strip()
    else:
        return None
    
def _extract_solution_with_thought(solution_str):
    
    model_output = solution_str
    
    if THOUGHT_DELIMITER_END in solution_str:
        model_output = solution_str.split(THOUGHT_DELIMITER_END)[1]
    
    predict_answer = _extract_answer(model_output)
    
    
    if predict_answer is not None:
        return predict_answer
    else:
        return model_output

# def _search_boolean(answer_str):
#     match = re.search(r'\b(true|false)\b', answer_str, re.IGNORECASE)
#     if match:
#         # 转换为小写后，再首字母大写
#         return match.group(0).lower().capitalize()
#     else:
#         return ""

def _search_boolean(answer_str):
    # Strict match pattern first
    strict_match = re.search(r'(?<=[the|The] answer is )(.*)(?=.)', answer_str)
    if strict_match:
        result = strict_match.group(1).strip()
        # Check if the extracted result is a boolean
        bool_match = re.search(r'\b(true|false)\b', result, re.IGNORECASE)
        if bool_match:
            return bool_match.group(0)
    
    # Fallback to flexible extraction pattern
    flexible_match = re.search(r'\b(true|false)\b', answer_str, re.IGNORECASE)
    if flexible_match:
        return flexible_match.group(0)
    
    return ""

class BBHBooleanExpressionsVerifier(Verifier):
    """
    Verifier for Cipher
    """
    def verify(self, data: Data, test_solution: str):
        try:
            test_answer = self.extract_answer(test_solution)
            ground_truth = data.answer
            correct = test_answer == ground_truth
            if correct:
                acc_score = 1.0
            else:
                acc_score = 0

            return acc_score
        except:
            return False
    
    def extract_answer(self, test_solution: str):
        answer_str =  _extract_solution_with_thought(solution_str=test_solution)
        return _search_boolean(answer_str=answer_str)
    
if __name__ == '__main__':
    # answer_str = "true? The answer is false."
    answer_str = "true"
    print(_search_boolean(answer_str=answer_str))
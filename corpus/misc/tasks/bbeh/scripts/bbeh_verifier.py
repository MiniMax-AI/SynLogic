from base.data import Data
from base.verifier import Verifier
import re

def _fuzzy_match(prediction: str, reference: str) -> bool:
    """模糊匹配函数"""
    prediction = prediction.strip()
    reference = reference.strip()
    prediction = prediction.lower()
    reference = reference.lower()
    
    if prediction == reference:
        return True
    
    # 处理选项格式: (a) vs a
    if len(prediction) == 3 and prediction[0] == "(" and prediction[-1] == ")":
        if len(reference) == 1:
            return prediction[1].lower() == reference.lower()
        else:
            return prediction[1].lower() == reference[1].lower()
    if len(reference) == 3 and reference[0] == "(" and reference[-1] == ")":
        if len(prediction) == 1:
            return reference[1].lower() == prediction.lower()
        else:
            return reference[1].lower() == prediction[1].lower()

    if reference.startswith("[") and reference.endswith("]"):
        if prediction.startswith("[") and prediction.endswith("]"):
            return reference[1:-1].replace(" ", "").replace("'", "").replace("\"", "") == prediction[1:-1].replace(" ", "").replace("'", "").replace("\"", "")
        else:
            return reference[1:-1].replace(" ", "").replace("'", "").replace("\"", "") == prediction.replace(" ", "").replace("'", "").replace("\"", "")
    
    # 处理数字
    try:
        if float(prediction) == float(reference):
            return True
    except ValueError:
        pass
    
    # 处理空格问题
    if prediction.replace(" ", "") == reference.replace(" ", ""):
        return True

    # 处理引号问题
    if prediction.replace("'", "") == reference.replace("'", ""):
        return True

    # 处理方括号问题
    if f"[{reference}]" == prediction or f"[{prediction}]" == reference:
        return True

    # 处理问号问题
    if prediction.endswith("?") and prediction[:-1] == reference:
        return True

    return False

def _preprocess_answer(answer: str) -> str:
    """预处理答案文本"""
    if not answer:
        return ""
        
    processed = answer.strip().lower()
    processed = processed.split("```python")[-1]
    processed = processed.split("```")[0]
    try:
        processed = eval(processed)
    except:
        return ""
    processed = processed.replace(", ", ",").replace("**", "")
    processed = processed.split("\n")[0]
    processed = processed[0:-1] if processed.endswith(".") else processed
    return processed

class BBEHVerifier(Verifier):
    """BBEH任务的验证器"""
    
    def verify(self, data: Data, test_solution: str) -> float:
        try:
            # 提取和预处理模型答案
            test_answer = self.extract_answer(test_solution)
            
            # 获取并预处理参考答案
            ground_truth = data.answer.strip().lower()
            
            # 进行模糊匹配
            correct = _fuzzy_match(test_answer, ground_truth)
            
            return 1.0 if correct else 0.0
        except:
            return 0.0
    
    def extract_answer(self, test_solution: str) -> str:
        """从完整答案中提取最终答案"""
            
        return _preprocess_answer(test_solution)

if __name__ == '__main__':
    # 测试用例
    test_cases = [
        ("<answer>Alright! The final answer is: 2, 3, 4</answer>", "2,3,4"),
        ("blah blah The final answer is: <answer>2, 3, 4</answer>", "2,3,4"),
        ("Ok The answer is: <answer>(A)</answer>", "a"),
        ("Ok The answer is: (A)", "b"),
        ("Ok The answer is: **<answer>25</answer>**\nHere's why.", "25.0"),
        ("Ok The answer is: **<answer>25</answer>**\nHere's why.", "26.0")
    ]
    
    verifier = BBEHVerifier()
    for test_input, reference in test_cases:
        result = verifier.extract_answer(test_input)
        print(f"Input: {test_input}")
        print(f"Reference: {reference}")
        print(f"Extracted: {result}")
        print(f"Match: {_fuzzy_match(result, reference)}\n")
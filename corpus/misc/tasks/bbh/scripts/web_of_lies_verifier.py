from base.data import Data
from base.verifier import Verifier
import re


def _search_truth_telling(answer_str):
    # Strict match pattern first
    strict_match = re.search(r'(?<=[the|The] answer is )(.*)(?=.)', answer_str)
    if strict_match:
        result = strict_match.group(1).strip()
        # Check for "no" variations in strict match
        no_match = re.search(r'\b(no|does not tell the truth|is not telling the truth)\b', result, re.IGNORECASE)
        if no_match:
            return "no"
        # Check for "yes" variations in strict match
        yes_match = re.search(r'\b(yes|tells the truth|is telling the truth)\b', result, re.IGNORECASE)
        if yes_match:
            return "yes"
    
    # Fallback to flexible pattern
    # Check for "no" variations
    flexible_no_match = re.search(r'\b(no|does not tell the truth|is not telling the truth)\b', answer_str, re.IGNORECASE)
    if flexible_no_match:
        return "no"
    
    # Check for "yes" variations
    flexible_yes_match = re.search(r'\b(yes|tells the truth|is telling the truth)\b', answer_str, re.IGNORECASE)
    if flexible_yes_match:
        return "yes"
    
    return ""

class BBHWebOfLiesVerifier(Verifier):
    """
    Verifier for Web of Lies tasks
    """
    def verify(self, data: Data, test_solution: str):
        try:
            test_answer = self.extract_answer(test_solution)
            ground_truth = data.answer
            
            # 标准化答案格式
            test_answer = test_answer.lower()
            ground_truth = ground_truth.lower()
            
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
        return _search_truth_telling(answer_str=answer_str)

if __name__ == '__main__':
    # Test cases
    test_cases = [
        "no The answer is yes.",
        "The answer is no.",
        "They tell the truth.",
        "They do not tell the truth.",
        "Yes, they are telling the truth.",
        "No, they are not telling the truth.",
        "The person tells the truth.",
        "The person does not tell the truth.",
        "The person is telling the truth.",
        "The person is not telling the truth."
    ]
    
    for case in test_cases:
        print(f"Input: {case}")
        print(f"Output: {_search_truth_telling(case)}\n")
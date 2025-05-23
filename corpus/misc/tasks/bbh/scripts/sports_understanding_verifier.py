from base.data import Data
from base.verifier import Verifier
import re


def _search_plausibility(answer_str):
    # Strict match pattern first
    strict_match = re.search(r'(?<=[the|The] answer is )(.*)(?=.)', answer_str)
    if strict_match:
        result = strict_match.group(1).strip()
        # Check for no/not plausible in strict match
        no_match = re.search(r'\b(no|not plausible)\b', result, re.IGNORECASE)
        if no_match:
            return "no"
        # Check for yes/plausible in strict match
        yes_match = re.search(r'\b(yes|plausible)\b', result, re.IGNORECASE)
        if yes_match:
            return "yes"
    
    # Fallback to flexible pattern
    # Check for no/not plausible
    flexible_no_match = re.search(r'\b(no|not plausible)\b', answer_str, re.IGNORECASE)
    if flexible_no_match:
        return "no"
    
    # Check for yes/plausible
    flexible_yes_match = re.search(r'\b(yes|plausible)\b', answer_str, re.IGNORECASE)
    if flexible_yes_match:
        return "yes"
    
    return ""
 
class BBHSportsUnderstandingVerifier(Verifier):
    """
    Verifier for Sports Understanding tasks
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
        return _search_plausibility(answer_str=answer_str)

if __name__ == '__main__':
    # Test cases
    test_cases = [
        "no The answer is yes.",
        "The answer is plausible.",
        "The answer is no.",
        "The answer is not plausible.",
        "Yes, this makes sense.",
        "No, this is impossible.",
        "This statement is plausible.",
        "This scenario is not plausible."
    ]
    
    for case in test_cases:
        print(f"Input: {case}")
        print(f"Output: {_search_plausibility(case)}\n")
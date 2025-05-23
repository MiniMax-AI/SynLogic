from base.data import Data
from base.verifier import Verifier
import re

def _search_multiple_choice(answer_str):
    # Strict match pattern first
    strict_match = re.search(r'(?<=[the|The] answer is )(.*)(?=.)', answer_str)
    if strict_match:
        result = strict_match.group(1).strip()
        # Check if the extracted result contains a letter in parentheses
        choice_match = re.search(r'\(([A-Z])\)', result)
        if choice_match:
            return f"({choice_match.group(1)})"
    
    # Fallback to flexible extraction pattern
    flexible_match = re.search(r'\(([A-Z])\)', answer_str)
    if flexible_match:
        return f"({flexible_match.group(1)})"
    
    return ""

class BBHDateUnderstandingVerifier(Verifier):
    """
    Verifier for Date Understanding tasks
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
        answer_str = test_solution
        return _search_multiple_choice(answer_str=answer_str)

if __name__ == '__main__':
    # response =  "<think>First, let's list the objects in order as they are described in the row: orange scrunchiephone charger, blue cup, turquoise dog leash, yellow fidget spinner, brown stress ball, and burgundy textbook. Now, the question asks how many non-grey objects are to the left of the blue cup. The blue cup is the second item in the list. The only object to the left of it is the orange scrunchiephone charger, which is not grey. Therefore, there is one non-grey object to the left of the blue cup.</think>\n<answer>(B) one</answer>\nThe answer is (B)."
    # DateUnderstandingVerifier_temp = DateUnderstandingVerifier()
    # extracted_response = DateUnderstandingVerifier_temp.extract_answer(response)
    # print(extracted_response)
    answer_str = "The answer is (B) 01/02/2020."
    print(_search_multiple_choice(answer_str=answer_str))  # 输出: (F)
    answer_str = ": (A)"
    print(_search_multiple_choice(answer_str=answer_str) == "(A)")  # 输出: (F)
    answer_str = "The answer is (B)"
    print(_search_multiple_choice(answer_str=answer_str))  # 输出: (F)
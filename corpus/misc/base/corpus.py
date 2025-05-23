# coding: utf-8
from abc import ABC, abstractmethod
from base.verifier import Verifier
from base.data import Data

class Corpus:
    """
    Base class for corpus
    @param name: name of the corpus
    @param verifier: class of the verifier
    """
    def __init__(self, name: str, verifier: Verifier):
        self.name = name
        self.verifier = verifier()

    @abstractmethod
    def generate(self, num_of_questions: int = 100, max_attempts: int = 100):
        """
        Generate corpus questions and answers
        @param num_of_questions: int
        @return: list of CorpusData
        """
        raise NotImplementedError("Corpus.generate() is not implemented")
    
    def verify(self, corpus_data: Data, test_solution: str):
        """
        Verify whether the test solution is consistent with the answer of the corpus data
        @param corpus_data: CorpusData
        @param test_solution: str
        @return: bool
        """
        test_answer = self.extract_answer(test_solution)
        print(test_answer)
        return self.verifier.verify(corpus_data, test_answer)
    
    @abstractmethod
    def extract_answer(self, test_solution: str):
        """
        Extract the answer from the test solution
        @param test_solution: str
        @return: str
        """
        raise NotImplementedError("Corpus.extract_answer() is not implemented")
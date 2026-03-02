from src.cpp.compiler import Compiler
from src.data.ingestion import get_all_submissions


# problems = get_all_submissions()

# def compile_all_problems(problems):
#     for problem in problems:
#         problem.raw_program.compile()
        
#         if problem.raw_program.is_compiled():
#             print("Successfully compiled!")
#         else:
#             print("Failed to compile!")

# compile_all_problems(problems)

#=====================================================

from src.llm.apicaller import LLMCaller, CodeCorrector

gemma_3_27b = LLMCaller()
# print(gemma_3_27b.generate("What is the mc of jjk"))

prompt = """Problem: Calculate the sum of two numbers.
           Code:
           ```sum.cpp
           #inlcude <bits/stdc++.h>
           using namespace std; //DUCK
           int main{
            int a, b;
            cin >> a >> b;
            cout << a - b;
            return 0;
           }
           ```"""

code_corrector = CodeCorrector(gemma_3_27b)
print(code_corrector.correct(prompt))
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
gemini_31_flash_lite = LLMCaller('gemini-3.1-flash-lite-preview')
# prompt = """A juggler can juggle 16 balls. Half of the balls are golf balls,
# and half of the golf balls are blue. How many blue golf balls are
# there?
# """
# print(gemma_3_27b.generate(prompt))
# print(gemma_3_27b.generate("Give me the code for linear regression in Python using gradient descent, code only, no further explainations or anything"))


# prompt = """Problem: Calculate the sum of two numbers.
#            Code:
#            ```sum.cpp
#            #inlcude <bits/stdc++.h>
#            using namespace std; //DUCK
#            int main{
#             int a, c;
#             cin >> a >> b;
#             cout << a - b;
#             return 0;
#            }
#            ```"""

prompt = """
TASK:
- A basic linear regression to predict outcomes based on input using gradient descent.
- Input:
+ First line: n is the number of training data points (real numbers).
+ n next lines: x_i, and y_i (training data).
+ last line: x_test (return the prediction y for x).
- Output:
+ One line: y_test
CODE:
#include <bits/stdc++.h>

using namespace std;

class LinearRegression(){
    double a, b;

    void calc_gradient
} A;

int main(){    

    int x;
    cin >> x;
    cout << A.predict(x);

    return 0;
}
"""

code_corrector = CodeCorrector(gemini_31_flash_lite)
print(code_corrector.correct(prompt))
"""
// Printed results from Gemini 3.1 Flash Lite Preview:
#include <bits/stdc++.h>

using namespace std;

class LinearRegression {
public:
    double a = 0, b = 0;
    double learning_rate = 0.01;
    int iterations = 1000;

    void train(vector<pair<double, double>>& data) {
        int n = data.size();
        for (int i = 0; i < iterations; i++) {
            double da = 0, db = 0;
            for (auto& p : data) {
                double error = (a * p.first + b) - p.second;
                da += error * p.first;
                db += error;
            }
            a -= (learning_rate * 2 / n) * da;
            b -= (learning_rate * 2 / n) * db;
        }
    }

    double predict(double x) {
        return a * x + b;
    }
} A;

int main(){
    int n;
    cin >> n;
    vector<pair<double, double>> data(n);
    for(int i = 0; i < n; i++) cin >> data[i].first >> data[i].second;
    A.train(data);
    double x_test;
    cin >> x_test;
    cout << A.predict(x_test);

    return 0;
}
"""
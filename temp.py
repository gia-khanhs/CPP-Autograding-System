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


prompt = """
TASK:
As is well known, the beautiful Snow White lives deep in the forest with the seven dwarfs. The dwarfs’ daily work is mining ore. However, what not everyone knows is how the dwarfs, with their small bodies, are able to operate the mine. Interestingly, even in those days, they already used machinery in their work.

The area where the dwarfs mine ore is a rectangular piece of land divided into M rows and N columns, forming an M × N grid of square cells. There are only two types of valuable ore in the area: gold and silver. The amount of gold in cell (i, j) — row i, column j — is worth a_ij USD, while the amount of silver in the same cell is worth b_ij USD. The gold refinery is located to the west of the area (on the left), and the silver refinery is located to the north of the area (above).

There are two types of conveyor belts used to transport ore. Gold conveyor belts run from east to west (right to left); every mine cell that such a belt passes through is used to extract gold. A gold conveyor belt always ends on the western side, where the gold refinery is located. Silver conveyor belts run from south to north (bottom to top); every mine cell that such a belt passes through is used to extract silver. A silver conveyor belt always ends on the northern side. Any cell through which no conveyor belt passes is not mined at all.

Determine the maximum number of USD the dwarfs can obtain from this mining area.

Input

- The first line contains two positive integers M, N (1 ≤ M, N ≤ 500).
- The next M lines each contain n integers a_i1, a_i2, ..., a_in.
- The last M lines each contain n integers b_i1, b_i2, ..., b_in.

The ore values are integers in the range from 0 to 1000.

Output

- Print a single integer: the maximum amount of USD that can be obtained.

Example

Input:
```text
4 4
0 0 10 9
1 3 10 0
4 2 1 3
1 1 20 0
10 0 0 0
1 1 1 30
0 0 5 5
5 10 10 10
```

Output:
```
98
```
#include <bits/stdc++.h>
#define fori(i,a,b) for(int i = a;i <= b;i ++)
using namespace std;
typedef long long ll;
ll const N = 1e3 + 9;
int a[N][N],b[N][N],n,m;
ll dp[N][N][2],col[N][N],row[N][N];
void speed()
{
	ios_base::sync_with_stdio(0);
	cin.tie(NULL);
	cout.tie(NULL);
}
int main()
{
	speed();
	cin >> m >> n;
	fori(i,1,m) fori(j,1,n) cin >> a[i][j],row[i][j] = row[i][j - 1] + a[i][j];//gold
	fori(i,1,m) fori(j,1,n) cin >> b[i][j],col[i][j] = col[i - 1][j] + b[i][j];//silver
	fori(i,1,m)
	{
		fori(j,1,n)
		{
			dp[i][j][0] = max(dp[i - 1][j][0],dp[i - 1][j][1]) + row[i][j]; //row
			dp[i][j][1] = max(dp[i][j - 1][0],dp[i][j - 1][1]) + col[i][j]; //col
		}
	}
	cout << max(dp[m][n][0],dp[m][n][1]);
 }
"""

# prompt = """
# TASK:
# - A basic linear regression to predict outcomes based on input using gradient descent.
# - Input:
# + First line: n is the number of training data points (real numbers).
# + n next lines: x_i, and y_i (training data).
# + last line: x_test (return the prediction y for x).
# - Output:
# + One line: y_test
# CODE:
# #include <bits/stdc++.h>

# using namespace std;

# class LinearRegression(){
#     double a, b;

#     void calc_gradient
# } A;

# int main(){    

#     int x;
#     cin >> x;
#     cout << A.predict(x);

#     return 0;
# }
# """

code_corrector = CodeCorrector(gemma_3_27b)
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
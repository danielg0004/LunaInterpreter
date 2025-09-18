# Minimalistic language Interpreter
An interpreter for a simple programming language with the following features:
1. **Variables** (the identifiers must be lowercase strings) for any non-negative integers
2. Implementation of shunting-yard algorithm for evaluation of complex expressions
5. Control flow through conditionals
6. **Function definition**, function calls, and **recursivity**

# How to use
Requires Python 3.10+.
1. Clone the repository. Use git clone https://github.com/danielg0004/LunaInterpreter to download the code.
2. In the terminal, open the directory where both the main.py file and the .luna file you want to run are
3. Run `python main.py filename.luna`, replacing "filename" with the actual name of the file

# How it works
The code obtains tokens from the .luna file by looking at every line (separated by newlines) and obtaining each term that is separated with whitespace characters. It yields these tokens as an iterator that is saved in the instance variable `token_feed`.

Then, it uses the starting tokens of each statement to determine what type of statement it is, and runs it afterwards. The function `returnToken` is used to return tokens to the stream that were peeked at but shouldn't be consumed.

For if statements, it calculates the value of the condition:
- If it's true, nothing changes, and the following lines are interpreted normally
- If it's false, the instance variable `currently_interpreting` is set to false until the end of the if statement, which makes it so the program consumes every line without looking at it

When interpreting function definitions, the instance variable `reading_function_definition` is set to the identifier of the function, and the code is simply copied to a dictionary that associates it with that name (along with the input variables). When doing function calls, a new instance of the interpreter class is created with this code and the input parameters are set as the values of the input variables, effectively producing the intended result and allowing for recursivity (as all function definitions are copied into the new instance, too).

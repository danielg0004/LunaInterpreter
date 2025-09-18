# Luna: A Minimalistic Interpreter
A from-scratch interpreter for a simple programming language implemented in Python.

# Key Features & Implementation Details
1. **Parsing:** Implemented a tokenizer and parser to handle statement types
2. **Evaluation:** Uses the [Shunting-yard algorithm](https://en.wikipedia.org/wiki/Shunting_yard_algorithm) for handling the evaluation of complex arithmetic expressions
3. **Control flow:** Supports conditional statements
4. **Functions:** Allows user-defined functions, calls with limited scope, and **recursion**
5. **Variables:** Includes a hash map for variable storage and lookup

# How to use
Requires Python 3.10+.
1. Clone the repository. Use git clone https://github.com/danielg0004/LunaInterpreter to download the code.
2. In the terminal, open the directory where both the main.py file and the .luna file you want to run are
3. Run `python main.py filename.luna`, replacing "filename" with the actual name of the file

# How it works
The code obtains tokens from the .luna file by looking at every line (separated by newlines) and obtaining each term that is separated with whitespace characters. It yields these tokens as an iterator that is saved in the instance variable `token_feed`.

Then, it uses the starting tokens of each statement to determine what type of statement it is, and runs it afterwards. The function `returnToken` is used to return tokens to the stream that were peeked at but shouldn't be consumed.

For if statements, it calculates the value of the condition and, if false, the instance variable `currently_interpreting` is set to false until the end of the if statement, which makes it so the program disregards every token until then.

When interpreting function definitions, the instance variable `reading_function_definition` is set to the identifier of the function, and the code is simply copied to a dictionary that associates it with that name (along with the input variables). When doing function calls, a new instance of the interpreter class is created with this code and the input parameters are set as the values of the input variables, effectively producing the intended result and allowing for recursivity (as all function definitions are copied into the new instance, too).

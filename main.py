import sys

class Luna:
    def __init__(self, code):
        self.code = code
        self.line_num = 0
        self.token_feed = self.tokens() # an iterator
        self.returned_tokens = []
        
        self.token_list = ["+", "-", "/", "%", "*", "print", "=", "function", "endfunction", "if", "endif", "(", ")", "==", ">", "<", ">=", "<=", "!=", "return"]
        
        self.parseStatementList = [self.parsePrintStatement, self.parseAssignment, self.parseIfStatement, self.parseEndIfStatement, self.parseFunctionDefinition, self.parseEndFunction, self.parseValueStatement] # list of parse[statement] functions to consider when parsing a statement (except return statements, which are tested for separately first)
    
        self.env_vars = {} # namespace for variables
        self.env_functions = {} # namespace for functions
        
        # these are used for shunting-yard
        self.operator_stack = [] 
        self.output_queue = []
        
        self.operator_precedence = {
            "+": 2,
            "-": 2,
            "*": 3,
            "/": 3,
            "%": 3,
            ">": 1,
            "<": 1,
            "<=": 1,
            ">=": 1,
            "!=": 1,
            "==": 1,
            "function_identifier": 0
        }
        self.operator_functions = {
            "+": lambda a, b: a + b,
            "-": lambda a, b: a - b,
            "*": lambda a, b: a * b,
            "/": lambda a, b: a / b,
            "%": lambda a, b: a % b,
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
            "!=": lambda a, b: a != b,
            "==": lambda a, b: a == b
        }

        self.currently_interpreting = True # Used to handle conditionals
        
        self.reading_function_definition = None # Marks the function whose definition is being read (generally, none)

    # Lexer implementation | Yields the tokens from the code
    def tokens(self):
        # Looping through every line (separated by "\n")
        for line in self.code.strip().split("\n"):
            self.line_num+=1
            # Looping through every token (separated by " ")
            for token in line.strip().split():
                # Each token is either in the token list, a number, or a variable/function identifier
                if token in self.token_list:
                    yield (token,)
                elif token.isdigit(): 
                    yield ("number", int(token))
                elif token.isalnum():
                    if token.upper() == token:
                        yield ("function_identifier", token)
                    elif token.lower() == token:
                        yield ("var", token)
                    else:
                        self.raiseError(f"Syntax Error: Invalid token '{token}'. Identifiers must be fully uppercase (functions) or lowercase (variables).")
                else:
                    self.raiseError(f"Syntax Error: Invalid token '{token}'.")
            yield ("\n",)
    
    # Returns the next token in the stream
    def nextToken(self):
        if self.returned_tokens:
            token = self.returned_tokens.pop()
        else:
            token = next(self.token_feed, None) # gets the next element from the iterator (or None if it's done)
        return token
    
    # Return a token to the stream
    def returnToken(self, token):
        self.returned_tokens.append(token)
    
    # Raises an error
    def raiseError(self, message):
        raise ValueError(f'{self.line_num}: {message}')
    
    # Helper function: Verifies the next token is a line break and consumes it
    def verifyLineBreak(self):
        token = self.nextToken()
        if token[0]!="\n":
            self.raiseError("Expected: line break")
    
    # A wrapper of parseProgram() to handle exceptions
    def run(self):
        try:
            return self.parseProgram()
        except ValueError as exception:
            print(str(exception))
            quit() # Closes all Luna instances, not just the current one (important for error handling in recursion)
 
    # Parses the program and runs each statement sequentially
    def parseProgram(self):
        while True:
            token = self.nextToken()
            if token is None:
                break  # End of input
            self.returnToken(token)  # Put it back so parseStatement can consume it
            
            result = self.parseStatement()
            if result is not None:
                return result # For return statements within function calls

    # Parses the current statement | Any return value from this function aside from None comes from a return statement
    def parseStatement(self):
        
        # Check for empty statement
        token = self.nextToken()
        if token[0]=="\n":
            return None
        self.returnToken(token) 
        
        # If a function is being read
        if self.reading_function_definition:
            while not self.parseEndFunction():
                temp_token = self.nextToken()
                
                # Get the text part of the token
                if temp_token[0]=="number" or temp_token[0]=="function_identifier" or temp_token[0]=="var":
                    element = temp_token[1]
                else:
                    element = temp_token[0]
                    
                # Add the text to the code of the function with an added whitespace to separate tokens
                self.env_functions[self.reading_function_definition][1] += str(element) + " "
            
            self.verifyLineBreak()
            
            return None
        
        # If within an if statement that is not being interpreted
        if not self.currently_interpreting:
            if self.parseEndIfStatement():
                self.verifyLineBreak()
                return None
            # If the current statement isn't an endif one, consume it
            temp_token = self.nextToken()
            while temp_token[0] != "\n":
                temp_token = self.nextToken()
            return None
        
        # If current statement is a return statement, return result
        temp_return_result = self.parseReturnStatement()
        if temp_return_result is not False:
            return temp_return_result
        
        # Go through each type of statement (except the ones within this function above this line) and verify at least one matches the current statement
        parsed_statement = False
        for parseSpecificStatement in self.parseStatementList:
            if parseSpecificStatement():
                parsed_statement = True
                break
        if not parsed_statement:
            self.raiseError("Expected: statement")
        
        self.verifyLineBreak()
            
        return None
    
    # Shunting yard algorithm for parsing an expression
    def parseExpression(self):
        token = (None,)
        while token[0] != "\n":
            token = self.nextToken()
            if token[0]=="number":
                self.outputQueuePush(token)
            elif token[0]=="var":
                try:
                    self.outputQueuePush(self.env_vars[token[1]])
                except KeyError:
                    self.raiseError(f"Variable '{token[1]}' hasn't been defined.")
            elif token[0]=="function_identifier":
                ''' The function call will be treated like a number and evaluated when collapsing the queue
                    It'll be structured with the function identifier at the start followed by all of its parameters
                '''
                res = [token[1]]    
                for _ in range(len(self.env_functions[token[1]][0])):
                    token = self.nextToken()
                    if token[0]=="number":
                        res.append(token)
                    elif token[0]=="var":
                        try:
                            res.append(self.env_vars[token[1]])
                        except KeyError:
                            self.raiseError(f"Variable '{token[1]}' hasn't been defined.")
                self.outputQueuePush(res)
            elif token[0] in ["+", "-", "/", "*", "%", "==", ">", "<", ">=", "<=", "!="]: # operators
                while ((self.operator_stack and self.operator_stack[-1][0]!="(") and self.operator_precedence[self.operator_stack[-1][0]]>self.operator_precedence[token[0]]):
                    self.outputQueuePush(self.operatorStackPop())
                self.operatorStackPush(token)
            elif token[0] == "(":
                self.operatorStackPush(token)
            elif token[0] == ")":
                while self.operator_stack[-1][0] != "(":
                    self.outputQueuePush(self.operatorStackPop())
                self.operatorStackPop()
                if self.operator_stack and self.operator_stack[-1][0] == "function":
                    self.outputQueuePush(self.operatorStackPop())
                    
        self.returnToken(token) # return the \n
        
        while self.operator_stack:
            self.outputQueuePush(self.operatorStackPop())
            
        # Now the output queue has the parsed expression until the end (newline)
    
    # Helper functions to push and pop from the output queue and the operator stack (used for shunting yard)
    def outputQueuePush(self, arg):
        self.output_queue.append(arg)
    def outputQueuePop(self):
        return self.output_queue.pop(0)
    def operatorStackPush(self, arg):
        self.operator_stack.append(arg)
    def operatorStackPop(self):
        return self.operator_stack.pop()
    
    # Collapse the output queue after the expression has been parsed with shunting-yard
    def outputQueueCollapse(self):
        stack = []
        while self.output_queue:
            element = self.outputQueuePop()
            
            if element[0] == "number":
                stack.append(element[1])
            elif isinstance(element, list): # Function (represented as lists)
                sub_instance = Luna(self.env_functions[element[0]][1]) # Get the code of the function and create a new instance of the class with it
                sub_instance.line_num = self.env_functions[element[0]][2] # Offset the line number of the new instance (for error messages)
                
                # Copy upper scope variables/functions to the new branch
                sub_instance.env_vars = self.env_vars.copy()
                sub_instance.env_functions = self.env_functions.copy()
                
                # For every parameter of the function, replace with the corresponding input
                for i in range(len(self.env_functions[element[0]][0])):
                    parameter = self.env_functions[element[0]][0][i][1]
                    sub_instance.env_vars[parameter] = element[i+1]
                stack.append(sub_instance.run()) # Add the return value to the stack
            else: # binary operator
                val1, val2 = stack.pop(), stack.pop()
                res = self.operator_functions[element[0]](val2, val1) # Only supports operators with 2 operators
                stack.append(res)
        return stack.pop()
    
    # The following are all functions to parse different kinds of statements
     
    def parsePrintStatement(self):
        token = self.nextToken()
        # This decides if it's a print statement
        if token[0]!="print":
            self.returnToken(token)
            return False
        # Get the expression and print the result
        self.parseExpression()
        value = self.outputQueueCollapse()
        print(value)
        return True
    
    def parseAssignment(self):
        token = self.nextToken()
        if token[0]!="var":
            self.returnToken(token)
            return False
        identifier = token[1]
        token = self.nextToken()
        if token[0]!="=":
            self.raiseError("Expected: =")
        self.parseExpression()
        self.env_vars[identifier] = ("number", self.outputQueueCollapse())
        return True

    def parseIfStatement(self):
        token = self.nextToken()
        if token[0]!="if":
            self.returnToken(token)
            return False
        self.parseExpression()
        # If the condition is false, stop interpreting lines of the code until an endif statement
        if not self.outputQueueCollapse():
            self.currently_interpreting = False
        return True
    
    def parseEndIfStatement(self):
        token = self.nextToken()
        if token[0]!="endif":
            self.returnToken(token)
            return False
        # If the if has ended, resume interpreting (or keep interpreting)
        self.currently_interpreting = True
        return True
    
    def parseFunctionDefinition(self):
        token = self.nextToken()
        if token[0]!="function":
            self.returnToken(token)
            return False
        identifier = self.nextToken()
        if identifier[0] != "function_identifier":
            self.raiseError("Expected: function identifier (uppercase)")
        
        self.reading_function_definition = identifier[1] # Set this function to the one being currently recorded
        
        # Build the function structure and store in self.env_functions
            
        self.env_functions[identifier[1]] = [[], "", self.line_num] # First element is the parameters, second element is the code, third is for offsetting the line_num when creating a new separated scope
        
        possible_parameter = self.nextToken()
        while possible_parameter[0] != "\n":
            self.env_functions[identifier[1]][0].append(possible_parameter)
            possible_parameter = self.nextToken()
        self.returnToken(possible_parameter)
        return True
    
    def parseEndFunction(self):
        token = self.nextToken()
        if token[0]!="endfunction":
            self.returnToken(token)
            return False
        self.reading_function_definition = None # Stop reading the function and go back to interpreting code
        return True
    
    def parseValueStatement(self):
        # Seems trivial but is important for function calls as they are taken as numbers (e.g. "PRINT 1" is a value statement)
        token = self.nextToken()
        self.returnToken(token)
        if token[0]!="number" and token[0]!="var" and token[0]!="function_identifier":
            return False
        self.parseExpression()
        self.outputQueueCollapse() # The returned value is immediately disregarded
        return True
    
    def parseReturnStatement(self):
        token = self.nextToken()
        if token[0]!="return":
            self.returnToken(token)
            return False
        self.parseExpression()
        return self.outputQueueCollapse()

# Reads the code from the .luna file and runs it
if __name__ == "__main__":
    with open(sys.argv[1], "rt") as f:
        code = f.read()
    program = Luna(code)
    program.run()
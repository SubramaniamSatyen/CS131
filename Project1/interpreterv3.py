from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
import copy

class Interpreter(InterpreterBase):

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        self.variable_name_to_value = []
        self.function_name_to_node = {}
        self.return_flg = []
        self.trace_output = trace_output

    def get_variable_value(self, var_name, args = None):
        for scope in reversed(self.variable_name_to_value):
            if var_name in scope:
                if (args is not None and len(scope[var_name][0].get('args')) != args):
                    super().error(ErrorType.TYPE_ERROR, f"Invalid number of args to function {var_name}")

                return scope[var_name]
            
        return self.get_function_value(var_name, args)
    
    def get_function_value(self, var_name, args = None):
        target_func = list(filter(lambda func: func[0] == var_name, self.function_name_to_node.keys()))
        if (args is not None):
            target_func = list(filter(lambda func: func[1] == args, target_func))

        if (len(target_func) > 1 and args is None):
            super().error(ErrorType.NAME_ERROR, f"Unclear which function {var_name} refers to")
        elif (len(target_func) == 1):
            return self.function_name_to_node[target_func[0]]

        super().error(ErrorType.NAME_ERROR, f"Variable/Function {var_name} has not been defined")    

    def dump_vars(self):
        print("\n--------------------START:Variables--------------------")
        for scope in (self.variable_name_to_value):
            print(scope)
        print("--------------------END:Variables--------------------")
        print("--------------------START:ReturnStack--------------------")
        print(self.return_flg)
        print("--------------------END:ReturnStack--------------------")
        print("--------------------START:ReturnStack--------------------")
        print(self.function_name_to_node)
        print("--------------------END:ReturnStack--------------------\n")

    def do_arithmetic(self, node):
        left = self.evaluate_expression(node.get("op1"))
        right = self.evaluate_expression(node.get("op2"))

        if (node.elem_type == "+"):
            if not (type(left) == type(right) and 
                    type(left) in [str, int] and 
                    type(right) in [str, int]):
                super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation")
            return left + right
        else:
            if not (type(left) in [int] and
                    type(right) in [int]):
                super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation")

            if (node.elem_type == "-"):
                return left - right
            elif (node.elem_type == "*"):
                return left * right
            elif (node.elem_type == "/"):
                return left // right
        
    def do_logical(self, node):
        left = self.evaluate_expression(node.get("op1"))
        right = self.evaluate_expression(node.get("op2"))

        if not type(left) in [bool] or not type(right) in [bool]:
            super().error(ErrorType.TYPE_ERROR, "Incompatible types for logical operation")

        if (node.elem_type == "||"):
            return left or right
        elif (node.elem_type == "&&"):
            return left and right

    def do_unary(self, node):
        op = self.evaluate_expression(node.get("op1"))
        if (node.elem_type == self.NEG_DEF):
            if (not type(op) in [int]):
                super().error(ErrorType.TYPE_ERROR, "Expected integer type for negation operator")
            return -op
        elif (node.elem_type == "!"):
            if (not type(op) in [bool]):
                super().error(ErrorType.TYPE_ERROR, "Expected bool type for not operator")
            return not op
        
    def do_comparison(self, node):
        left = self.evaluate_expression(node.get("op1"))
        right = self.evaluate_expression(node.get("op2"))
        if (node.elem_type == "=="):
            return (left == right and 
                    type(left) == type(right))
        elif (node.elem_type == "!="):
            return (left != right or
                    type(left) != type(right))
        
        if not (type(left) in [int] and type(right) in [int]):
            super().error(ErrorType.TYPE_ERROR, f"Incompatible operator {node.elem_type} for types")
        
        if (node.elem_type == "<"):
            return left < right
        elif (node.elem_type == "<="):
            return left <= right
        elif (node.elem_type == ">"):
            return left > right
        elif (node.elem_type == ">="):
            return left >= right

    def evaluate_expression(self, node):
        # print(node)
        if (node is None or node.elem_type == self.NIL_DEF):
            return None
        # If a value, return value
        elif (node.elem_type in ["int", "string", "bool"]):
            return node.get("val")
        # If a variable, return the value of the variable
        elif (node.elem_type == self.VAR_DEF): 
            var_name = node.get("name")
            val = self.get_variable_value(var_name)
            return val
        # If lambda definition
        elif (node.elem_type == self.LAMBDA_DEF):
            return (node, copy.deepcopy(self.variable_name_to_value))
        # If function call
        elif (node.elem_type == self.FCALL_DEF):
            return self.do_func_call(node)
        # If addition or subtraction
        elif (node.elem_type in ["+", "-", "*", "/"]):
            return self.do_arithmetic(node)

        elif (node.elem_type in ["==", "!=", "<", "<=", ">=", ">"]):
            return self.do_comparison(node)
        
        elif (node.elem_type in ["||", "&&"]):
            return self.do_logical(node)
        
        elif (node.elem_type in [self.NEG_DEF, "!"]):
            return self.do_unary(node)
        
        return None
    
    def do_assignment(self, stat):
        target_var_name = stat.get("name")
        source_node = stat.get("expression")
        resulting_value = self.evaluate_expression(source_node)

        for scope in reversed(self.variable_name_to_value):
            if target_var_name in scope:
                scope[target_var_name] = resulting_value
                return
        
        self.variable_name_to_value[-1][target_var_name] = resulting_value

    def do_while(self, stat):
        self.variable_name_to_value.append({})

        while (True):
            cond = self.evaluate_expression(stat.get('condition'))
            if (not type(cond) in [bool]):
                super().error(ErrorType.TYPE_ERROR, f"Expected boolean input, got {cond}")

            if (not cond):
                break
    
            for statement in stat.get("statements") or []:
                ret = self.run_statement(statement)
        
                if (self.return_flg[-1]):
                    self.variable_name_to_value.pop()
                    return ret
            
        self.variable_name_to_value.pop()

    def do_conditional(self, stat):
        self.variable_name_to_value.append({})
        
        cond = self.evaluate_expression(stat.get('condition'))
        if (not type(cond) in [bool]):
            super().error(ErrorType.TYPE_ERROR, f"Expected boolean input, got {cond}")

        to_execute = "statements" if cond else "else_statements"
        for statement in stat.get(to_execute) or []:
            ret = self.run_statement(statement)
        
            if (self.return_flg[-1]):
                self.variable_name_to_value.pop()
                return ret

        self.variable_name_to_value.pop()

    def do_input(self, params):
        if (len(params) > 1):
            super().error(ErrorType.NAME_ERROR, f"No input() function found that takes > 1 parameter")
        elif (len(params) == 1):
            super().output(self.evaluate_expression(params[0]))
        return super().get_input()

    def printValues(self, params):
        vals = [self.evaluate_expression(p) for p in params]
        super().output(''.join([str(val).lower() if type(val) in [bool] else str(val) for val in vals]))
        return None
    
    def do_func_call(self, stat):
        params = stat.get("args")
        if stat.get("name") == "inputi":
            return int(self.do_input(params))
        elif stat.get("name") == "inputs":
            return str(self.do_input(params))
        elif (stat.get("name") == "print"):
            self.printValues(params)
            return
        else:
            possible_func_info = self.get_variable_value(stat.get("name"), len(params or []))
            possible_func = possible_func_info[0]
            if (possible_func.elem_type == self.FUNC_DEF and 
                (possible_func.get("name"), len(possible_func.get("args"))) in self.function_name_to_node):
                return self.run_func(self.function_name_to_node[(possible_func.get("name"), len(possible_func.get("args")))][0], params)
            elif (possible_func.elem_type == self.LAMBDA_DEF and 
                  len(possible_func.get('args')) == len(params)):
                return self.run_lambda_func(possible_func, params, possible_func_info[1])

        super().error(ErrorType.NAME_ERROR, f"No function found with name {stat.get('name')}")
    
    def load_functions(self, ast):
        for func in ast.get("functions"):
            if func.get("name") != "main":
                self.function_name_to_node[(func.get("name"), len(func.get('args')))] = (func,)

    def get_main_func_node(self, ast):
        main = [func for func in ast.get("functions") if func.get("name") == "main"]
        if (len(main) == 0):
            super().error(ErrorType.NAME_ERROR, "No main() function was found")

        return main[0]

    def run_statement(self, stat):
        if stat.elem_type == "=":
            self.do_assignment(stat)
        elif stat.elem_type == self.FCALL_DEF:
            self.do_func_call(stat)
        elif stat.elem_type == self.IF_DEF:
            return self.do_conditional(stat)
        elif stat.elem_type == self.WHILE_DEF:
            return self.do_while(stat)
        elif stat.elem_type == self.RETURN_DEF:
            self.return_flg[-1] = True
            return copy.deepcopy(self.evaluate_expression(stat.get("expression")))

    def run_lambda_func(self, func, args, scope):
        vars_before = copy.deepcopy(self.variable_name_to_value)
        self.variable_name_to_value += scope

        ret = self.run_func(func, args)
        
        self.variable_name_to_value = vars_before
        return ret

    def run_func(self, func, args):
        if self.trace_output:
            self.dump_vars()
        params = {}

        # Handle mismatched args
        if (len(func.get("args")) != len(args)):
            super().error(ErrorType.NAME_ERROR, f"Incorrect number of args for {func.get('name')}")

        for param, val in zip(func.get("args"), args):
            params[param.get('name')] = self.evaluate_expression(val)
        self.variable_name_to_value.append(params)

        self.return_flg.append(False)
        ret = None
        for statement in func.get("statements"):
            ret = self.run_statement(statement)
        
            if (self.return_flg[-1]):
                break
        
        if self.trace_output:
            self.dump_vars()

        self.variable_name_to_value.pop()
        self.return_flg.pop()

        return ret        

    def run(self, program):
        parsed_program = parse_program(program)
        if (self.trace_output):
            print(parsed_program)
        self.load_functions(parsed_program)
        main_func_node = self.get_main_func_node(parsed_program)
        self.run_func(main_func_node, [])
        return parsed_program
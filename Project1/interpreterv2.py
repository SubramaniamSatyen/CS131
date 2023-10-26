from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
import copy

class Interpreter(InterpreterBase):

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        self.variable_name_to_value = [{}, {}]
        self.function_name_to_node = {}
        self.return_flg = False

    def get_variable_value(self, var_name):
        for scope in reversed(self.variable_name_to_value):
            if var_name in scope:
                return scope[var_name]
            
        super().error(ErrorType.NAME_ERROR, f"Variable {var_name} has not been defined")
    
    def do_arithmetic(self, node):
        left = self.evaluate_expression(node.get("op1"))
        right = self.evaluate_expression(node.get("op2"))

        if (node.elem_type == "+"):
            if not ((isinstance(left, str) and isinstance(right, str)) or 
                    (isinstance(left, int) and isinstance(right, int))):
                super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation")
            return left + right
        else:
            if not isinstance(left, int) or not isinstance(right, int):
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

        if not isinstance(left, bool) or not isinstance(right, bool):
                super().error(ErrorType.TYPE_ERROR, "Incompatible types for logical operation")

        if (node.elem_type == "||"):
            return left or right
        elif (node.elem_type == "&&"):
            return left and right

    def do_unary(self, node):
        op = self.evaluate_expression(node.get("op1"))
        if (node.elem_type == self.NEG_DEF):
            if (not isinstance(op, int)):
                super().error(ErrorType.TYPE_ERROR, "Expected integer type for negation operator")
            return -op
        elif (node.elem_type == "!"):
            if (not isinstance(op, bool)):
                super().error(ErrorType.TYPE_ERROR, "Expected bool type for not operator")
            return not op
        
    def do_comparison(self, node):
        left = self.evaluate_expression(node.get("op1"))
        right = self.evaluate_expression(node.get("op2"))
        if (node.elem_type == "=="):
            return left == right
        elif (node.elem_type == "!="):
            return left != right
        
        if not isinstance(left, int) or not isinstance(right, int):
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

    def do_conditional(self, stat):
        self.variable_name_to_value.append({})
        
        cond = self.evaluate_expression(stat.get('condition'))
        if (not isinstance(cond, bool)):
            super().error(ErrorType.NAME_ERROR, f"Expected boolean input, got {cond}")

        to_execute = "statements" if cond else "else_statements"
        for statement in stat.get(to_execute) or []:
            ret = self.run_statement(statement)
        
            if (self.return_flg):
                self.variable_name_to_value.pop()
                return ret
        
        if to_execute == "statements" and stat.elem_type == self.WHILE_DEF:
            return self.do_conditional(stat)

        self.variable_name_to_value.pop()

    def do_input(self, params):
        if (len(params) > 1):
            super().error(ErrorType.NAME_ERROR, f"No input() function found that takes > 1 parameter")
        elif (len(params) == 1):
            super().output(self.evaluate_expression(params[0]))
        return super().get_input()

    def printValues(self, params):
        vals = [self.evaluate_expression(p) for p in params]
        super().output(''.join([str(val).lower() if isinstance(val, bool) else str(val) for val in vals]))
        return None
    
    def do_func_call(self, stat):
        params = stat.get("args")
        if stat.get("name") == "inputi":
            return int(self.do_input(params))
        elif stat.get("name") == "inputs":
            return str(self.do_input(params))
        elif (stat.get("name") == "print"):
            self.printValues(params)
        elif (stat.get("name"), len(stat.get("args"))) in self.function_name_to_node:
            return self.run_func(self.function_name_to_node[(stat.get("name"), len(stat.get("args")))], params)
        else:
            super().error(ErrorType.NAME_ERROR, f"No function found with name {stat.get('name')}")
    
    def load_functions(self, ast):
        for func in ast.get("functions"):
            if func.get("name") != "main":
                self.function_name_to_node[(func.get("name"), len(func.get('args')))] = func

    def get_main_func_node(self, ast):
        main = [func for func in ast.get("functions") if func.get("name") == "main"]
        if (len(main) == 0):
            super().error(ErrorType.NAME_ERROR, "No main() function was found")
        # TODO: what if more than one main function?
        return main[0]

    def run_statement(self, stat):
        if stat.elem_type == "=":
            self.do_assignment(stat)
        elif stat.elem_type == self.FCALL_DEF:
            self.do_func_call(stat)
        elif stat.elem_type == self.IF_DEF:
            return self.do_conditional(stat)
        elif stat.elem_type == self.WHILE_DEF:
            return self.do_conditional(stat)
        elif stat.elem_type == self.RETURN_DEF:
            self.return_flg = True
            return copy.deepcopy(self.evaluate_expression(stat.get("expression")))

    def run_func(self, func, args):
        params = {}

        # Handle mismatched args
        if (len(func.get("args")) != len(args)):
            super().error(ErrorType.NAME_ERROR, f"Incorrect number of args for {func.get('name')}")

        for param, val in zip(func.get("args"), args):
            params[param.get('name')] = self.evaluate_expression(val)
        self.variable_name_to_value.append(params)

        self.return_flg = False
        ret = None
        for statement in func.get("statements"):
            ret = self.run_statement(statement)
        
            if (self.return_flg):
                break
        
        self.variable_name_to_value.pop()
        self.return_flg = False
        return ret        

    def run(self, program):
        parsed_program = parse_program(program)
        self.load_functions(parsed_program)
        main_func_node = self.get_main_func_node(parsed_program)
        self.run_func(main_func_node, [])
        # return parsed_program
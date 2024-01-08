from intbase import InterpreterBase, ErrorType
from brewparse import parse_program

class Interpreter(InterpreterBase):

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        self.variable_name_to_value = {}

    def evaluate_expression(self, node):
        # If a value, return value
        if (node.elem_type in ["int", "string"]):
            return node.get("val")
        # If a variable, return the value of the variable
        elif (node.elem_type == self.VAR_DEF): 
            var_name = node.get("name")
            if (var_name not in self.variable_name_to_value):
                super().error(
                    ErrorType.NAME_ERROR,
                    f"Variable {var_name} has not been defined",
                )
            else:
                return self.variable_name_to_value[var_name]
        
        # If function call
        elif (node.elem_type == self.FCALL_DEF):
            return self.do_func_call(node)
        # If addition or subtraction
        elif (node.elem_type in ["+", "-"]):
            left = self.evaluate_expression(node.get("op1"))
            right = self.evaluate_expression(node.get("op2"))
            if (isinstance(left, str) or isinstance(right, str)):
                super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for arithmetic operation",
                )
            if (node.elem_type == "+"):
                return left + right
            elif (node.elem_type == "-"):
                return left - right

        return None
    
    def do_assignment(self, stat):
        target_var_name = stat.get("name")
        source_node = stat.get("expression")
        resulting_value = self.evaluate_expression(source_node)
        self.variable_name_to_value[target_var_name] = resulting_value

    def printValues(self, params):
        super().output(''.join([str(self.evaluate_expression(p)) for p in params]))

    def do_func_call(self, stat):
        params = stat.get("args")
        if stat.get("name") == "inputi":
            if (len(params) > 1):
                super().error(
                    ErrorType.NAME_ERROR,
                    f"No inputi() function found that takes > 1 parameter",
                )
            elif (len(params) == 1):
                super().output(self.evaluate_expression(params[0]))
            return int(super().get_input())
        elif (stat.get("name") == "print"):
            self.printValues(params)
        else:
            super().error(
                ErrorType.NAME_ERROR,
                f"No function found with that name",
            )
        

    def get_main_func_node(self, ast):
        main = [func for func in ast.get("functions") if func.get("name") == "main"]
        if (len(main) == 0):
            super().error(
                ErrorType.NAME_ERROR,
                "No main() function was found",
            )
        # TODO: what if more than one main function?
        return main[0]

    def run_statement(self, stat):
        if stat.elem_type == "=":
            self.do_assignment(stat)
        elif stat.elem_type == self.FCALL_DEF:
            self.do_func_call(stat)

    def run_func(self, func):
        for statement in func.get("statements"):
            self.run_statement(statement)

    def run(self, program):
        parsed_program = parse_program(program)
        main_func_node = self.get_main_func_node(parsed_program)
        self.run_func(main_func_node)
        return parsed_program
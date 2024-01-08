from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
import copy

class Interpreter(InterpreterBase):

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        self.variable_name_to_value = []
        self.function_name_to_node = {}
        self.ref_mapping = []
        self.return_flg = []
        self.trace_output = trace_output
        self.this = None

    def get_variable_value(self, var_name, args = None, lambda_scope_index = -1):
        if (lambda_scope_index > 0):
            for scope in reversed(self.variable_name_to_value[:lambda_scope_index]):
                if var_name in scope:
                    if (args is not None):
                        if type(scope[var_name]) not in [tuple]:
                            super().error(ErrorType.TYPE_ERROR, f"Invalid call to undefined function {var_name}")
                        elif len(scope[var_name][0].get('args')) != args:
                            super().error(ErrorType.TYPE_ERROR, f"Invalid number of args to function {var_name}")
                    return scope[var_name]

        for scope in reversed(self.variable_name_to_value):
            if var_name in scope:
                if (args is not None):
                    if type(scope[var_name]) not in [tuple]:
                        super().error(ErrorType.TYPE_ERROR, f"Invalid call to undefined function {var_name}")
                    elif len(scope[var_name][0].get('args')) != args:
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
        print("--------------------START:Variables--------------------")
        for scope in (self.variable_name_to_value):
            print(scope)
        print("--------------------END:Variables--------------------")
        print("--------------------START:ReturnStack--------------------")
        print(self.return_flg)
        print("--------------------END:ReturnStack--------------------")
        print("--------------------START:Functions--------------------")
        print(self.function_name_to_node)
        print("--------------------END:Functions--------------------\n")

    def do_arithmetic(self, node):
        left = self.evaluate_expression(node.get("op1"))
        right = self.evaluate_expression(node.get("op2"))

        if (node.elem_type == "+"):
            if (not (type(left) == type(right) and type(left) in [str, int] and type(right) in [str, int]) and 
                not (type(left) in [int, bool] and type(right) in [int, bool])):
                super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation")
            return left + right
        else:
            if not (type(left) in [int, bool] and type(right) in [int, bool]):
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

        if (type(left) in [int]): 
            left = True if left != 0 else False
        if (type(right) in [int]): 
            right = True if right != 0 else False

        if type(left) not in [bool] or type(right) not in [bool]:
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
            if (not type(op) in [bool, int]):
                super().error(ErrorType.TYPE_ERROR, "Expected bool/int type for not operator")
            return not op
        
    def do_comparison(self, node):
        left = self.evaluate_expression(node.get("op1"))
        right = self.evaluate_expression(node.get("op2"))
        if node.elem_type in ["==", "!="]:
            if (type(left) in [int] and type(right) in [bool]): 
                left = True if left != 0 else False
            if (type(left) in [bool] and type(right) in [int]): 
                right = True if right != 0 else False

            if (type(left) in [list] and type(right) in [list]):
                return left is right if node.elem_type == "==" else left is not right

            if (node.elem_type == "=="):
                return (left == right)
            elif (node.elem_type == "!="):
                return (left != right)
        
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

    def evaluate_expression(self, node, lambda_scope_index = -1, use_proto = False):
        if (node is None or node.elem_type == self.NIL_DEF):
            return None
        # If a value, return value
        elif (node.elem_type in ["int", "string", "bool"]):
            return node.get("val")
        # If a variable, return the value of the variable
        elif (node.elem_type == self.VAR_DEF): 
            var_name = self.get_name(node)
            if var_name[0] == "this" and self.this is not None:
                var_name[0] = self.this
            val = self.get_variable_value(var_name[0], None, lambda_scope_index)

            if (len(var_name) == 2):
                if type(val) not in [list]:
                    super().error(ErrorType.TYPE_ERROR, f"Invalid use of . operator with {'.'.join(var_name)}")
                
                if (var_name[1] == "proto" and use_proto):
                    if (val[0] is None):
                        super().error(ErrorType.NAME_ERROR, f"Field {'.'.join(var_name)} not defined")
                    return val[0]

                found_member = False
                searching = True
                curr_scope = val
                while searching:
                    if var_name[1] in curr_scope[1]:
                        found_member = True
                        searching = False

                        val = curr_scope[1][var_name[1]]
                        break
                    elif curr_scope[0] is not None:
                        curr_scope = curr_scope[0]
                    else:
                        searching = False
                
                if not found_member:
                    super().error(ErrorType.NAME_ERROR, f"Function/Field {var_name[0]}.{var_name[1]} not found")

            return val
        # If object assignment
        elif (node.elem_type == self.OBJ_DEF):
            return [None, dict()]
        # If lambda definition
        elif (node.elem_type == self.LAMBDA_DEF):
            lambda_saved_scopes = []
            for scope in self.variable_name_to_value:
                curr_lambda_scope = {}
                for key in scope.keys():
                    if type(scope[key]) in [int, bool, str]:
                        curr_lambda_scope[key] = copy.deepcopy(scope[key])

                lambda_saved_scopes.append(curr_lambda_scope)
            
            return (node, lambda_saved_scopes)
        # If function call
        elif (node.elem_type == self.FCALL_DEF):
            return self.do_func_call(node)
        # If member function call
        elif (node.elem_type == self.MCALL_DEF):
            return self.do_member_call(node)
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
    
    def get_name(self, node):
        return node.get("name").split(".")

    def handle_proto(self, stat):
        names = self.get_name(stat)

        source_node = stat.get("expression")
        resulting_value = self.evaluate_expression(source_node, -1, True)

        # Handle setting to nil
        if (resulting_value is None):
            for scope in reversed(self.variable_name_to_value):
                if names[0] in scope:
                    scope[names[0]][0] = None
                    return
    
        if type(resulting_value) not in [list]:
            super().error(ErrorType.TYPE_ERROR, f"Invalid assignment to proto with {resulting_value}")

        for scope in reversed(self.variable_name_to_value):
            if names[0] in scope:
                scope[names[0]][0] = resulting_value

    def do_assignment(self, stat, lambda_scope_index = -1):
        names = self.get_name(stat)
        if names[0] == "this" and self.this is not None:
            names[0] = self.this
        target_var_name = names[0]

        member_name = None
        if (len(names) >= 2):
            member_name = names[1]
            if member_name == "proto":
                self.handle_proto(stat)
                return

        source_node = stat.get("expression")
        resulting_value = self.evaluate_expression(source_node)

        # Doing initial assignment
        assigned = False
        for scope in reversed(self.variable_name_to_value):
            if target_var_name in scope:
                # Add variable to end of object prototyping
                if member_name is not None:
                    scope[target_var_name][-1][member_name] = resulting_value
                else:
                    scope[target_var_name] = resulting_value
                assigned = True
                break

        if not assigned and member_name is not None:
            super().error(ErrorType.NAME_ERROR, f"Field {target_var_name}.{member_name} not found")
        elif not assigned:
            self.variable_name_to_value[-1][target_var_name] = resulting_value

        # Determining any ref linked variables
        refs_to_process = set()
        adding_refs = [target_var_name]
        for ref in adding_refs:
            for mapping in reversed(self.ref_mapping):
                if ref in mapping:
                    linked_refs = mapping[ref]
                    for linked_ref in linked_refs:
                        if linked_ref not in refs_to_process:
                            adding_refs.append(linked_ref)
                        
                        refs_to_process.add(linked_ref)

        if target_var_name in refs_to_process:
            refs_to_process.remove(target_var_name)

        # Updating reference vars
        for param in refs_to_process:
            if (lambda_scope_index > 0 and param in self.variable_name_to_value[-1]):
                self.variable_name_to_value[-1][param] = resulting_value

            for scope in reversed(self.variable_name_to_value[:lambda_scope_index] if lambda_scope_index > 0 else self.variable_name_to_value):
                if param in scope:
                    scope[param] = resulting_value

        # If member assignment lambda - update original scope
        if member_name is not None and lambda_scope_index > 0:
            for scope in reversed(self.variable_name_to_value[:lambda_scope_index]):
                if target_var_name in scope:
                    scope[target_var_name][-1][member_name] = resulting_value

    def do_while(self, stat, lambda_scope_index):
        self.variable_name_to_value.append({})

        while (True):
            cond = self.evaluate_expression(stat.get('condition'))
            if (type(cond) in [int]):
                cond = True if cond != 0 else False
            if (not type(cond) in [bool]):
                super().error(ErrorType.TYPE_ERROR, f"Expected boolean/integer input in while, got {cond}")

            if (not cond):
                break
    
            for statement in stat.get("statements") or []:
                ret = self.run_statement(statement, lambda_scope_index)
        
                if (self.return_flg[-1]):
                    self.variable_name_to_value.pop()
                    return ret
            
        self.variable_name_to_value.pop()

    def do_conditional(self, stat, lambda_scope_index):
        self.variable_name_to_value.append({})
        
        cond = self.evaluate_expression(stat.get('condition'))
        if (type(cond) in [int]):
            cond = True if cond != 0 else False
        if (not type(cond) in [bool]):
            super().error(ErrorType.TYPE_ERROR, f"Expected boolean/integer input in for, got {cond}")

        to_execute = "statements" if cond else "else_statements"
        for statement in stat.get(to_execute) or []:
            ret = self.run_statement(statement, lambda_scope_index)
        
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
    
    def do_member_call(self, stat):
        obj_name = stat.get('objref')
        if obj_name == "this" and self.this is not None:
            obj_name = self.this
        obj = self.get_variable_value(obj_name)

        if type(obj) not in [list]:
            super().error(ErrorType.TYPE_ERROR, f"Invalid use of . operator with {stat.get('objref')}.{stat.get('name')}")
        
        found_member = False
        searching = True
        curr_scope = obj
        while searching:
            if stat.get("name") in curr_scope[1]:
                found_member = True
                searching = False

                possible_func_info = curr_scope[1][stat.get('name')]
                break
            elif curr_scope[0] is not None:
                curr_scope = curr_scope[0]
            else:
                searching = False
        
        if not found_member:
            super().error(ErrorType.NAME_ERROR, f"Function {stat.get('objref')}.{stat.get('name')}(...) not found")
        if type(possible_func_info) not in [tuple]:
            super().error(ErrorType.TYPE_ERROR, f"Invalid call to member variable {stat.get('objref')}.{stat.get('name')}")

        possible_func = possible_func_info[0]

        if possible_func.elem_type == self.FUNC_DEF:
            # Function member
            func = possible_func

            args = stat.get('args')
            curr_obj = stat.get('objref')
            update_this = (curr_obj != 'this')
            if update_this:
                temp = self.this
                self.this = curr_obj
            ret = self.run_func(self.function_name_to_node[(func.get("name"), len(func.get("args")))][0], stat.get('args'))
            if update_this:
                self.this = temp

        elif possible_func.elem_type == self.LAMBDA_DEF:
            # Lambda member
            func = possible_func_info[0]
            scope = possible_func_info[1]

            args = stat.get('args')

            # Running code
            vars_before = copy.deepcopy(self.variable_name_to_value)
            self.variable_name_to_value += scope

            curr_obj = stat.get('objref')
            update_this = (curr_obj != 'this')
            if update_this:
                temp = self.this
                self.this = curr_obj
            ret = self.run_func(func, args, len(vars_before))
            if update_this:
                self.this = temp

            # Updating lambda scope for future calls
            lambda_scope = self.variable_name_to_value[len(vars_before):]
            self.variable_name_to_value = self.variable_name_to_value[:len(vars_before)]
            obj[-1][stat.get('name')] = (func, lambda_scope)

        return ret

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
                return self.run_lambda_func(possible_func, params, possible_func_info[1], stat.get("name"))

        super().error(ErrorType.NAME_ERROR, f"No function found with name {stat.get('name')}")
    
    def load_functions(self, ast):
        for func in ast.get("functions"):
            self.function_name_to_node[(func.get("name"), len(func.get('args')))] = (func,)

    def get_main_func_node(self, ast):
        main = [func for func in ast.get("functions") if func.get("name") == "main"]
        if (len(main) == 0):
            super().error(ErrorType.NAME_ERROR, "No main() function was found")

        return main[0]

    def run_statement(self, stat, lambda_scope_index = -1):
        if stat.elem_type == "=":
            self.do_assignment(stat, lambda_scope_index)
        elif stat.elem_type == self.FCALL_DEF:
            self.do_func_call(stat)
        elif stat.elem_type == self.MCALL_DEF:
            self.do_member_call(stat)
        elif stat.elem_type == self.IF_DEF:
            return self.do_conditional(stat, lambda_scope_index)
        elif stat.elem_type == self.WHILE_DEF:
            return self.do_while(stat, lambda_scope_index)
        elif stat.elem_type == self.RETURN_DEF:
            self.return_flg[-1] = True
            return copy.deepcopy(self.evaluate_expression(stat.get("expression")))

    def run_lambda_func(self, func, args, scope, var_name):
        vars_before = copy.deepcopy(self.variable_name_to_value)
        self.variable_name_to_value += scope

        ret = self.run_func(func, args, len(vars_before))
        
        # Updating lambda scope for future calls
        lambda_scope = self.variable_name_to_value[len(vars_before):]
        self.variable_name_to_value = self.variable_name_to_value[:len(vars_before)]

        for scope in reversed(self.variable_name_to_value):
            if var_name in scope:
                scope[var_name] = (scope[var_name][0], lambda_scope)
                break

        return ret

    def run_func(self, func, args, lambda_scope_index = -1):
        if self.trace_output:
            print(f'\nCALLING {func.get("name")}: ')
            self.dump_vars()
        params = {}

        # Handle mismatched args
        if (len(func.get("args")) != len(args)):
            super().error(ErrorType.NAME_ERROR, f"Incorrect number of args for {func.get('name')}")

        # Loading args
        arg_mapping = list(zip(func.get("args"), args))
        for param, val in arg_mapping:
            evaluated_val = self.evaluate_expression(val, lambda_scope_index)
            if (param.elem_type == self.REFARG_DEF):
                params[param.get('name')] = evaluated_val
            else:
                if (type(evaluated_val) in [tuple]):
                    params[param.get('name')] = (copy.deepcopy(evaluated_val[0]), copy.deepcopy(evaluated_val[1])) 
                else:
                    params[param.get('name')] = copy.deepcopy(evaluated_val) 

        self.variable_name_to_value.append(params)

        
        curr_ref_mapping = dict()
        for formal_param, actual_param in arg_mapping:
            if (formal_param.elem_type == self.REFARG_DEF and actual_param.elem_type == self.VAR_DEF):
                actual_name = actual_param.get("name")  
                formal_name = formal_param.get("name")

                if actual_name in curr_ref_mapping:
                    curr_ref_mapping[actual_name].append(formal_name)
                else:
                    curr_ref_mapping[actual_name] = [formal_name]

                if formal_name in curr_ref_mapping:
                    curr_ref_mapping[formal_name].append(actual_name)
                else:
                    curr_ref_mapping[formal_name] = [actual_name]

        self.ref_mapping.append(curr_ref_mapping)


        self.return_flg.append(False)
        ret = None
        for statement in func.get("statements"):
            ret = self.run_statement(statement, lambda_scope_index)
        
            if (self.return_flg[-1]):
                break

        if self.trace_output:
            print(f'After Function {func.get("name")}: ')
            self.dump_vars()

        self.ref_mapping.pop()
        # Handling ref params
        curr_formal_params = self.variable_name_to_value.pop()
        for formal_param, actual_param in arg_mapping:
            if (formal_param.elem_type == self.REFARG_DEF and actual_param.elem_type == self.VAR_DEF):
                target_var_name = actual_param.get("name")  
                # for scope in reversed(self.variable_name_to_value):
                #     if target_var_name in scope:
                #         scope[target_var_name] = curr_formal_params[formal_param.get('name')]
                        
                for scope in reversed(self.variable_name_to_value[:lambda_scope_index] if lambda_scope_index > 0 else self.variable_name_to_value):
                    if target_var_name in scope:
                        scope[target_var_name] = curr_formal_params[formal_param.get('name')]
                        break
                        
        
        if self.trace_output:
            print(f'Ending {func.get("name")}: ')
            self.dump_vars()
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
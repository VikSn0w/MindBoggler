import re
from itertools import groupby
import numpy as np


class Interpreter:
    pointer = 0
    memory = []
    program = ""
    jump_forward = {}
    jump_backward = {}
    stack = []
    bracket_entry_index = 0
    bracket_exit_index = 0
    bracket_pointer = 0

    def __init__(self, memory_size=30000):
        self.pointer = 0
        self.memory = [0] * memory_size

    def loadProgram(self, program):
        self.program = program
        self.pointer = 0

    def resetInterpreter(self):
        self.pointer = 0
        self.memory = [0] * len(self.memory)

    def checkProgramSyntax(self):
        allowed = set("[].,<>+-")
        errors = []
        for idx, char in enumerate(self.program):
            if char not in allowed:
                errors.append((idx, char))
        return errors

    def generatePseudocode(self):
        pseudocode = f""
        pseudocode += f"Program loaded with {len(self.program)} characters.\n"
        pseudocode += f"Memory initialized with {len(self.memory)} cells.\n"
        pseudocode += f"Pointer initialized at position {self.pointer}.\n"
        pseudocode += f"pointer = {self.pointer}\n"
        self.pointer = 0
        pc = 0
        tabber = ""
        while pc < len(self.program):
            char = self.program[pc]
            match char:
                case '>':
                    self.pointer += 1
                    pseudocode += f"{tabber}pointer++ ({self.pointer})\n"
                    break
                case '<':
                    self.pointer -= 1
                    pseudocode += f"{tabber}pointer-- ({self.pointer})\n"
                    break
                case '+':
                    pseudocode += f"{tabber}memory[pointer] += 1 (mod 256)\n"
                    break
                case '-':
                    pseudocode += f"{tabber}memory[pointer] -= 1 (mod 256)\n"
                    break
                case '.':
                    pseudocode += f"{tabber}\nprint(char(memory[pointer]))\n\n"
                    break
                case ',':
                    pseudocode += f"{tabber}\ninput(int(memory[pointer]))\n\n"
                    break
                case '[':
                    pseudocode += f"\n{tabber} while memory[pointer] != 0:\n"
                    tabber += "  "
                    break
                case ']':
                    tabber = tabber[:-2]
                    pseudocode += f"{tabber} end while\n\n"
                    break
            pc += 1
        return pseudocode


    def runProgramSlow(self):
       if self.program == "":
              raise ValueError("No program loaded to run.")
       else:
           errors = self.checkProgramSyntax()
           if errors:
               raise SyntaxError(f"Syntax errors found: {errors}")
           else:
               print(f"Program loaded correctly, {len(self.program)} byte.")
               pc = 0
               while pc < len(self.program):
                   char = self.program[pc]
                   match char:
                       case '>':
                           self.pointer += 1
                           break
                       case '<':
                           self.pointer -= 1
                           break
                       case '+':
                           self.memory[self.pointer] = (self.memory[self.pointer] + 1) % 256
                           break
                       case '-':
                           self.memory[self.pointer] = (self.memory[self.pointer] - 1) % 256
                           break
                       case '.':
                           print(chr(self.memory[self.pointer]), end='')
                           break
                       case ',':
                           self.memory[self.pointer] = ord(input('Please enter a character:')[0])
                           break
                       case '[':
                           if self.memory[self.pointer] == 0:
                               depth = 1
                               while depth > 0:
                                   pc += 1
                                   if pc >= len(self.program):
                                       raise SyntaxError("Unmatched '[' found.")
                                   if self.program[pc] == '[':
                                       depth += 1
                                   elif self.program[pc] == ']':
                                       depth -= 1
                           break
                       case ']':
                           if self.memory[self.pointer] != 0:
                               depth = 1
                               while depth > 0:
                                   pc -= 1
                                   if pc < 0:
                                       raise SyntaxError("Unmatched ']' found.")
                                   if self.program[pc] == ']':
                                       depth += 1
                                   elif self.program[pc] == '[':
                                       depth -= 1
                           break
                   pc += 1

    def runProgramFast(self):
        if self.program == "":
            raise ValueError("No program loaded to run.")

        errors = self.checkProgramSyntax()
        if errors:
            raise SyntaxError(f"Syntax errors found: {errors}")

        code = self.program
        stack = []
        compiled = []
        pc = 0
        length = len(code)

        while pc < length:
            cmd = code[pc]

            if cmd == '[':
                stack.append(len(compiled))
                compiled.append(['[', None])
            elif cmd == ']':
                if not stack:
                    raise SyntaxError("Unmatched ']' found.")
                start_idx = stack.pop()
                end_idx = len(compiled)
                compiled.append([']', start_idx])
                compiled[start_idx][1] = end_idx
            elif cmd in ('>', '<', '+', '-'):
                count = 1
                while pc + 1 < length and code[pc + 1] == cmd:
                    count += 1
                    pc += 1
                compiled.append([cmd, count])
            elif cmd in ('.', ','):
                compiled.append([cmd, None])
            pc += 1

        if stack:
            raise SyntaxError("Unmatched '[' found.")

        print(f"Program compiled to {len(compiled)} instructions.")
        pc = 0
        while pc < len(compiled):
            cmd, arg = compiled[pc]
            match cmd:
                case '>':
                    self.pointer += arg
                    break
                case '<':
                    self.pointer -= arg
                    break
                case '+':
                    self.memory[self.pointer] = (self.memory[self.pointer] + arg) % 256
                    break
                case '-':
                    self.memory[self.pointer] = (self.memory[self.pointer] - arg) % 256
                    break
                case '.':
                    print(chr(self.memory[self.pointer]), end='')
                    break
                case ',':
                    self.memory[self.pointer] = ord(input('Please enter a character:')[0])
                    break
                case '[':
                    if self.memory[self.pointer] == 0:
                        pc = arg
                    break

                case ']':
                    if self.memory[self.pointer] != 0:
                        pc = arg
                    break

            pc += 1







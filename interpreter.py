from enum import Enum


class PointerBehavior(Enum):
    CLAMP = 0  # Stay at boundaries
    WRAP = 1  # Wrap around
    ERROR = 2  # Raise exception


class CellBehavior(Enum):
    WRAP = 0  # Standard Brainfuck wrap around (0-255)
    UNLIMITED = 1  # Allow values beyond 0-255 range
    ERROR = 2  # Raise exception on underflow/overflow


class PointerOverflowError(Exception):
    """Raised when pointer goes out of bounds with ERROR behavior"""
    pass


class CellOverflowError(Exception):
    """Raised when cell value goes out of bounds with ERROR behavior"""
    pass


class Interpreter:
    def __init__(self, memory_size=30000):
        self.memory_size = memory_size
        self.pointer_behavior = PointerBehavior.CLAMP
        self.cell_behavior = CellBehavior.WRAP
        self.reset()

    def configure(self, pointer_behavior: PointerBehavior, cell_behavior: CellBehavior):
        """Configure interpreter behavior settings"""
        self.pointer_behavior = pointer_behavior
        self.cell_behavior = cell_behavior

    def reset(self):
        self.pointer = 0
        self.memory = [0] * self.memory_size
        self.program = ""
        self.pc = 0
        self.output_buffer = ""
        self.input_buffer = []
        self.running = False
        self.compiled_program = []
        self.input_callback = None

    def loadProgram(self, program, input_data=""):
        self.program = program
        self.pc = 0
        self.output_buffer = ""
        self.input_buffer = [ord(c) for c in input_data]
        self.running = True
        self.compiled_program = []

    def setInputCallback(self, callback):
        self.input_callback = callback

    def _move_pointer(self, delta):
        """Handle pointer movement with configured behavior"""
        new_pointer = self.pointer + delta

        if self.pointer_behavior == PointerBehavior.CLAMP:
            self.pointer = max(0, min(new_pointer, self.memory_size - 1))
        elif self.pointer_behavior == PointerBehavior.WRAP:
            self.pointer = new_pointer % self.memory_size
        elif self.pointer_behavior == PointerBehavior.ERROR:
            if new_pointer < 0:
                raise PointerOverflowError(f"Pointer underflow: attempted to move to {new_pointer}")
            elif new_pointer >= self.memory_size:
                raise PointerOverflowError(
                    f"Pointer overflow: attempted to move to {new_pointer} (max: {self.memory_size - 1})")
            else:
                self.pointer = new_pointer

    def _modify_cell(self, delta):
        """Handle cell value modification with configured behavior"""
        new_value = self.memory[self.pointer] + delta

        if self.cell_behavior == CellBehavior.WRAP:
            # Standard Brainfuck behavior: wrap around 0-255
            self.memory[self.pointer] = new_value % 256
        elif self.cell_behavior == CellBehavior.UNLIMITED:
            # Allow values beyond 0-255 range
            self.memory[self.pointer] = new_value
        elif self.cell_behavior == CellBehavior.ERROR:
            # Raise exception on underflow/overflow
            if new_value < 0:
                raise CellOverflowError(f"Cell underflow: attempted to set cell {self.pointer} to {new_value}")
            elif new_value > 255:
                raise CellOverflowError(f"Cell overflow: attempted to set cell {self.pointer} to {new_value}")
            else:
                self.memory[self.pointer] = new_value

    def checkProgramSyntax(self):
        allowed = set("[].,<>+-")
        errors = []
        for idx, char in enumerate(self.program):
            if char not in allowed:
                errors.append((idx, char))
        return errors

    def generatePseudocode(self):
        pseudocode = f"Program loaded with {len(self.program)} characters.\n"
        pseudocode += f"Memory initialized with {len(self.memory)} cells.\n"
        pseudocode += f"Pointer initialized at position {self.pointer}.\n"
        pseudocode += f"pointer = {self.pointer}\n\n"

        # Add behavior information
        behavior_names = {
            CellBehavior.WRAP: "wrap around (0-255)",
            CellBehavior.UNLIMITED: "unlimited range",
            CellBehavior.ERROR: "error on overflow/underflow"
        }
        pseudocode += f"Cell behavior: {behavior_names[self.cell_behavior]}\n\n"

        # Save original pointer
        original_pointer = self.pointer
        self.pointer = 0
        pc = 0
        tabber = ""

        while pc < len(self.program):
            char = self.program[pc]
            match char:
                case '>':
                    self.pointer += 1
                    pseudocode += f"{tabber}pointer++ ({self.pointer})\n"
                case '<':
                    self.pointer -= 1
                    pseudocode += f"{tabber}pointer-- ({self.pointer})\n"
                case '+':
                    if self.cell_behavior == CellBehavior.WRAP:
                        pseudocode += f"{tabber}memory[pointer] += 1 (mod 256)\n"
                    elif self.cell_behavior == CellBehavior.UNLIMITED:
                        pseudocode += f"{tabber}memory[pointer] += 1 (unlimited)\n"
                    else:
                        pseudocode += f"{tabber}memory[pointer] += 1 (0-255, error on overflow)\n"
                case '-':
                    if self.cell_behavior == CellBehavior.WRAP:
                        pseudocode += f"{tabber}memory[pointer] -= 1 (mod 256)\n"
                    elif self.cell_behavior == CellBehavior.UNLIMITED:
                        pseudocode += f"{tabber}memory[pointer] -= 1 (unlimited)\n"
                    else:
                        pseudocode += f"{tabber}memory[pointer] -= 1 (0-255, error on underflow)\n"
                case '.':
                    pseudocode += f"{tabber}print(char(memory[pointer]))\n"
                case ',':
                    pseudocode += f"{tabber}memory[pointer] = input_char()\n"
                case '[':
                    pseudocode += f"{tabber}while memory[pointer] != 0:\n"
                    tabber += "  "
                case ']':
                    tabber = tabber[:-2] if len(tabber) >= 2 else ""
                    pseudocode += f"{tabber}end while\n"
            pc += 1

        # Restore original pointer
        self.pointer = original_pointer
        return pseudocode

    def compileProgram(self):
        if self.program == "":
            raise ValueError("No program loaded to compile.")

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
                # Optimize consecutive operations
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

        self.compiled_program = compiled
        return compiled

    def runProgramFast(self, max_steps=1_000_000):
        if not self.compiled_program:
            self.compileProgram()

        print(f"Program compiled to {len(self.compiled_program)} instructions.")
        pc = 0
        steps = 0

        while pc < len(self.compiled_program) and steps < max_steps:
            cmd, arg = self.compiled_program[pc]

            try:
                match cmd:
                    case '>':
                        self._move_pointer(arg)
                    case '<':
                        self._move_pointer(-arg)
                    case '+':
                        self._modify_cell(arg)
                    case '-':
                        self._modify_cell(-arg)
                    case '.':
                        # Handle output for potentially large cell values
                        cell_value = self.memory[self.pointer]
                        if self.cell_behavior == CellBehavior.UNLIMITED and (cell_value < 0 or cell_value > 255):
                            # For unlimited mode, clamp to valid ASCII range for output
                            output_char = chr(max(0, min(255, cell_value)))
                        else:
                            output_char = chr(cell_value % 256)
                        self.output_buffer += output_char
                    case ',':
                        if self.input_buffer:
                            input_value = self.input_buffer.pop(0)
                            if self.cell_behavior == CellBehavior.ERROR and (input_value < 0 or input_value > 255):
                                raise CellOverflowError(f"Input value {input_value} out of range (0-255)")
                            self.memory[self.pointer] = input_value
                        elif self.input_callback:
                            # Handle input callback
                            input_data = self.input_callback()
                            if input_data:
                                self.input_buffer.extend([ord(c) for c in input_data])
                                if self.input_buffer:
                                    input_value = self.input_buffer.pop(0)
                                    if self.cell_behavior == CellBehavior.ERROR and (input_value < 0 or input_value > 255):
                                        raise CellOverflowError(f"Input value {input_value} out of range (0-255)")
                                    self.memory[self.pointer] = input_value
                                else:
                                    self.memory[self.pointer] = 0
                            else:
                                self.memory[self.pointer] = 0
                        else:
                            self.memory[self.pointer] = 0
                    case '[':
                        if self.memory[self.pointer] == 0:
                            pc = arg
                    case ']':
                        if self.memory[self.pointer] != 0:
                            pc = arg
            except (PointerOverflowError, CellOverflowError):
                # Let overflow errors propagate up
                raise

            pc += 1
            steps += 1

        self.running = False
        return steps

    def runProgramFastInterruptible(self, steps_per_chunk=10000, max_steps=1_000_000):
        if not self.compiled_program:
            self.compileProgram()

        if not hasattr(self, '_fast_pc'):
            self._fast_pc = 0
            self._fast_steps = 0

        chunk_steps = 0
        while (self._fast_pc < len(self.compiled_program) and
               chunk_steps < steps_per_chunk and
               self._fast_steps < max_steps):

            cmd, arg = self.compiled_program[self._fast_pc]

            try:
                match cmd:
                    case '>':
                        self._move_pointer(arg)
                    case '<':
                        self._move_pointer(-arg)
                    case '+':
                        self._modify_cell(arg)
                    case '-':
                        self._modify_cell(-arg)
                    case '.':
                        # Handle output for potentially large cell values
                        cell_value = self.memory[self.pointer]
                        if self.cell_behavior == CellBehavior.UNLIMITED and (cell_value < 0 or cell_value > 255):
                            # For unlimited mode, clamp to valid ASCII range for output
                            output_char = chr(max(0, min(255, cell_value)))
                        else:
                            output_char = chr(cell_value % 256)
                        self.output_buffer += output_char
                    case ',':
                        if self.input_buffer:
                            input_value = self.input_buffer.pop(0)
                            if self.cell_behavior == CellBehavior.ERROR and (input_value < 0 or input_value > 255):
                                raise CellOverflowError(f"Input value {input_value} out of range (0-255)")
                            self.memory[self.pointer] = input_value
                        elif self.input_callback:
                            # Handle input callback
                            input_data = self.input_callback()
                            if input_data:
                                self.input_buffer.extend([ord(c) for c in input_data])
                                if self.input_buffer:
                                    input_value = self.input_buffer.pop(0)
                                    if self.cell_behavior == CellBehavior.ERROR and (input_value < 0 or input_value > 255):
                                        raise CellOverflowError(f"Input value {input_value} out of range (0-255)")
                                    self.memory[self.pointer] = input_value
                                else:
                                    self.memory[self.pointer] = 0
                            else:
                                self.memory[self.pointer] = 0
                        else:
                            self.memory[self.pointer] = 0
                    case '[':
                        if self.memory[self.pointer] == 0:
                            self._fast_pc = arg
                    case ']':
                        if self.memory[self.pointer] != 0:
                            self._fast_pc = arg
            except (PointerOverflowError, CellOverflowError):
                # Let overflow errors propagate up
                raise

            self._fast_pc += 1
            self._fast_steps += 1
            chunk_steps += 1

        # Check if execution completed
        if self._fast_pc >= len(self.compiled_program) or self._fast_steps >= max_steps:
            self.running = False
            self._fast_pc = 0
            self._fast_steps = 0
            return False

        return True

    def step(self):
        if not self.running or self.pc >= len(self.program):
            self.running = False
            return False

        char = self.program[self.pc]
        try:
            match char:
                case '>':
                    self._move_pointer(1)
                case '<':
                    self._move_pointer(-1)
                case '+':
                    self._modify_cell(1)
                case '-':
                    self._modify_cell(-1)
                case '.':
                    # Handle output for potentially large cell values
                    cell_value = self.memory[self.pointer]
                    if self.cell_behavior == CellBehavior.UNLIMITED and (cell_value < 0 or cell_value > 255):
                        # For unlimited mode, clamp to valid ASCII range for output
                        output_char = chr(max(0, min(255, cell_value)))
                    else:
                        output_char = chr(cell_value % 256)
                    self.output_buffer += output_char
                case ',':
                    if self.input_buffer:
                        input_value = self.input_buffer.pop(0)
                        if self.cell_behavior == CellBehavior.ERROR and (input_value < 0 or input_value > 255):
                            raise CellOverflowError(f"Input value {input_value} out of range (0-255)")
                        self.memory[self.pointer] = input_value
                    elif self.input_callback:
                        # Handle input callback
                        input_data = self.input_callback()
                        if input_data:
                            self.input_buffer.extend([ord(c) for c in input_data])
                            if self.input_buffer:
                                input_value = self.input_buffer.pop(0)
                                if self.cell_behavior == CellBehavior.ERROR and (input_value < 0 or input_value > 255):
                                    raise CellOverflowError(f"Input value {input_value} out of range (0-255)")
                                self.memory[self.pointer] = input_value
                            else:
                                self.memory[self.pointer] = 0
                        else:
                            self.memory[self.pointer] = 0
                    else:
                        self.memory[self.pointer] = 0
                case '[':
                    if self.memory[self.pointer] == 0:
                        depth = 1
                        while depth > 0:
                            self.pc += 1
                            if self.pc >= len(self.program):
                                raise SyntaxError("Unmatched '[' found.")
                            if self.program[self.pc] == '[':
                                depth += 1
                            elif self.program[self.pc] == ']':
                                depth -= 1
                case ']':
                    if self.memory[self.pointer] != 0:
                        depth = 1
                        while depth > 0:
                            self.pc -= 1
                            if self.pc < 0:
                                raise SyntaxError("Unmatched ']' found.")
                            if self.program[self.pc] == ']':
                                depth += 1
                            elif self.program[self.pc] == '[':
                                depth -= 1
        except (PointerOverflowError, CellOverflowError):
            # Let overflow errors propagate up
            raise

        self.pc += 1
        return True

    def runUntilEnd(self, max_steps=1_000_000):
        steps = 0
        while self.running and steps < max_steps:
            if not self.step():
                break
            steps += 1
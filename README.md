<a href="url"><img src="https://raw.githubusercontent.com/VikSn0w/MindBoggler/refs/heads/main/gitimg/cover.png" align="center" height="auto" width="100%" ></a>
---
# Mind Boggler - Brainfuck PyIDE

A comprehensive Integrated Development Environment (IDE) for the Brainfuck esoteric programming language, built with Python and PySide6. This IDE provides debugging capabilities, memory visualization, compilation analysis, and configurable interpreter behavior.

## Table of Contents

- [About Brainfuck](#about-brainfuck)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Brainfuck Instructions](#brainfuck-instructions)
- [Interpreter Behavior](#interpreter-behavior)
- [IDE Components](#ide-components)
- [Settings](#settings)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

---

## About Brainfuck

Brainfuck is an esoteric programming language created by Urban Müller in 1993. It is famous for its minimalism and extreme difficulty to use. The language consists of only eight simple commands, a data pointer, and an instruction pointer. Despite its simplicity, Brainfuck is Turing-complete and can theoretically solve any computational problem.

The language operates on an array of memory cells (traditionally 30,000 cells), each initially set to zero. A data pointer begins at the leftmost cell, and commands manipulate the pointer and the data it points to.

More information can be found on the [Brainfuck Wikipedia page](https://en.wikipedia.org/wiki/Brainfuck) and on the Daniel B. Cristofani's [Brainfuck Wiki](https://brainfuck.org).

---

## Features

### Core IDE Features
- **Syntax-aware code editor** with breakpoint support
- **Real-time memory visualization** in hexadecimal grid format
- **Multiple execution modes**: Debug (step-by-step), Slow (2 steps/sec), Fast (optimized)
- **Breakpoint debugging** with F9 toggle support
- **Program compilation and optimization analysis**
- **Pseudocode generation** for better program understanding
- **Input/output handling** with interactive dialogs
- **File operations** (open/save .bf files)

### Advanced Interpreter Features
- **Configurable pointer behavior** (Clamp, Wrap-around, Error on overflow)
- **Configurable cell value behavior** (8-bit wrapping vs unlimited range)
- **Optimized execution engine** with instruction merging
- **Comprehensive error handling** and reporting
- **Program syntax validation**

---

## Installation
#### Binary Releases
Pre-built binaries are available for Windows built with auto-py-to-exe.

### Prerequisites
- Python 3.8 or higher
- PySide6

### Install Dependencies
```bash
pip install PySide6
```

### Run the IDE
```bash
python main.py
```

---

## Usage

1. **Write or load a Brainfuck program** in the code editor
2. **Set execution mode**:
   - Debug: Step-by-step execution with full visualization
   - Slow: Automated execution at 2 steps per second
   - Fast: Optimized execution with minimal overhead
3. **Configure interpreter behavior** via Settings menu
4. **Run the program** using the control buttons
5. **Monitor execution** through memory grid and status bar
6. **Debug with breakpoints** by pressing F9 or using the toolbar

---

## Brainfuck Instructions

Brainfuck uses eight single-character instructions:

| Instruction | Description | Pseudo-Code Interpretation       |
|-------------|-------------|----------------------------------|
| `>` | Move the data pointer one cell to the right | `pointer++`                      |
| `<` | Move the data pointer one cell to the left | `pointer--`                      |
| `+` | Increment the value at the data pointer | `memory[pointer] += 1 (mod 256)` |
| `-` | Decrement the value at the data pointer | `memory[pointer] -= 1 (mod 256)` |
| `.` | Output the character at the data pointer (ASCII) | `print(char(memory[pointer]))`   |
| `,` | Input a character and store it at the data pointer | `input(int(memory[pointer]))`    |
| `[` | Jump forward past matching `]` if value at pointer is zero | `while memory[pointer] != 0:`    |
| `]` | Jump backward to matching `[` if value at pointer is non-zero | `end while`                      |

All other characters are treated as comments and ignored.

---

### Instruction Interpretation

The interpreter processes instructions sequentially:

1. **Pointer Movement** (`>`, `<`): Adjusts the memory pointer according to configured behavior
2. **Value Modification** (`+`, `-`): Changes cell values with optional wrapping
3. **I/O Operations** (`.`, `,`): Handles character input/output with ASCII conversion
4. **Control Flow** (`[`, `]`): Implements loops based on current cell value

### Loop Behavior
- `[` at start of loop: If current cell is 0, skip to instruction after matching `]`
- `]` at end of loop: If current cell is non-zero, jump back to instruction after matching `[`
- Loops can be nested arbitrarily deep

## Interpreter Behavior

### Pointer Behavior Options

The IDE offers three configurable pointer behaviors:

#### 1. Clamp (Default)
```
Memory: [0][1][2][3][4]...[29999]
Pointer at 0: < command → pointer stays at 0
Pointer at 29999: > command → pointer stays at 29999
```
**Use case**: Safest option for beginners, prevents crashes

#### 2. Wrap-around
```
Memory: [0][1][2][3][4]...[29999]
Pointer at 0: < command → pointer moves to 29999
Pointer at 29999: > command → pointer moves to 0
```
**Use case**: Traditional circular memory model

#### 3. Error on Overflow/Underflow
```
Memory: [0][1][2][3][4]...[29999]
Pointer at 0: < command → throws PointerOverflowError
Pointer at 29999: > command → throws PointerOverflowError
```
**Use case**: Strict mode for catching boundary violations

### Cell Value Behavior

#### Standard 8-bit Wrapping (Default)
```
Cell value 255: + command → value becomes 0
Cell value 0: - command → value becomes 255
```

#### Unlimited Range
```
Cell values can exceed 0-255 range
Useful for mathematical operations requiring larger numbers
```

#### Error on underflow/overflow
```
Cell values can't exceed 0-255 range, 
An exception is thrown when cell goes below 0 or above 255
Optimal for strict Brainfuck behavior (in conjuction with Error pointer behavior)
```
---

## IDE Components

### Code Editor
- Syntax highlighting for current instruction
- Breakpoint management (F9 to toggle)
- Line-based editing with standard shortcuts

### Memory Grid
- Hexadecimal visualization of memory around pointer
- Current pointer highlighted in green
- Auto-scrolling to follow pointer movement
- 32x16 grid showing 512 memory cells

### Control Panel
- **Run**: Start execution in selected mode
- **Step**: Execute single instruction
- **Pause**: Pause execution (resume available)
- **Reset**: Reset interpreter state
- **Clear Output**: Clear output display

### Status Bar
Real-time display of:
- Execution mode
- Program counter (pc)
- Memory pointer (ptr)
- Current cell value
- Execution state
- Interpreter configuration

### Toolbar Actions
- File operations (Open/Save)
- Syntax checking
- Compilation analysis
- Pseudocode generation
- Breakpoint toggle
- Settings configuration

---

## Settings

Access via **Settings** button in toolbar:

### Pointer Behavior
- **Clamp**: Pointer stops at boundaries (safe)
- **Wrap-around**: Circular memory access
- **Error**: Exception on boundary violation

### Cell Value Behavior
- **Wrap (0-255)**: Standard Brainfuck behavior (usigned 8 bit range)
- **No Wrap**: Allow values beyond 8-bit range
- **Error on Underflow/Overflow**: Exception on values exceeding unsigned 8-bit range

Settings are applied immediately and persist for the session.

---

## Examples

### Hello World Program
```brainfuck
++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>.
```

This program:
1. Sets up initial values in memory cells
2. Uses loops to multiply values efficiently  
3. Outputs "Hello World!" character by character

### Echo Program
```brainfuck
,+[-.,+]
```

This program:
1. Reads input character
2. Loops while character is not null (0)
3. Outputs the character and reads next

### Cell Value Test
```brainfuck
+[+.+]
```

Useful for testing cell wrapping behavior:
- With wrapping: outputs characters cycling through ASCII values
- Without wrapping: values increase indefinitely

### Pointer Boundary Test
```brainfuck
<<<<<<<<<<
```

Tests pointer behavior:
- Clamp: pointer stays at 0
- Wrap: pointer moves to end of memory  
- Error: throws exception

---

## Compilation and Optimization

The IDE includes a compilation system that:

1. **Validates syntax** (matching brackets, valid characters)
2. **Optimizes instructions** by merging consecutive operations:
   - `+++` becomes `[+, 3]`
   - `>>>>` becomes `[>, 4]`
3. **Generates jump tables** for efficient loop handling
4. **Reports optimization statistics**

### Compilation Analysis
View detailed compilation results including:
- Original vs optimized instruction count
- Optimization efficiency percentage
- Instruction-by-instruction breakdown
- Jump table mapping

---

## Pseudocode Generation

Convert Brainfuck programs into readable pseudocode:

```brainfuck
+++>++<.
```

Becomes:
```
pointer = 0

memory[pointer] += 3 (mod 256)
pointer++ (1)
memory[pointer] += 2 (mod 256)
pointer-- (0)
print(char(memory[pointer]))
```

---

## Development

### File Structure
```
brainfuck-ide/
├── main.py           # Main application and GUI
├── interpreter.py    # Brainfuck interpreter engine
├── README.md         # This file
├── icon.ico          # Application icon
└── icon.png          # Application icon
```

### Key Classes
- `Interpreter`: Core Brainfuck execution engine
- `MainWindow`: Primary GUI application

---

## Error Handling

The IDE provides comprehensive error handling:

- **Syntax Errors**: Unmatched brackets, invalid characters
- **Runtime Errors**: Division by zero, infinite loops (with step limits)
- **Pointer Errors**: Boundary violations (in Error mode)
- **Input Errors**: Invalid input handling

---

## Performance

### Execution Modes
- **Debug Mode**: ~10 instructions/second with full visualization
- **Slow Mode**: ~2 instructions/second for educational purposes  
- **Fast Mode**: Up to 1M+ instructions/second with optimization

### Memory Usage
- Default: 30,000 memory cells
- Memory visualization: Shows 512 cells simultaneously
- Efficient memory allocation and access patterns

---

## Contributing

Contributions are welcome! Areas for improvement:

1. **Enhanced Debugging**: More sophisticated breakpoint conditions
2. **Performance Optimization**: Further execution speed improvements
3. **UI Enhancements**: Additional visualization options
4. **Export Features**: Save execution traces, memory dumps

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Submit a pull request

---

## Acknowledgments

- **Urban Müller**: Creator of the Brainfuck programming language
- **[Daniel B. Cristofani](https://gist.github.com/danielcristofani)**: For providing extensive Brainfuck resources and documentation
## License

---
This project is released under the GNU GENERAL PUBLIC LICENSE Version 3. See LICENSE file for details.

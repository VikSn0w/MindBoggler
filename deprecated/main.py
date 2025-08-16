import time
from datetime import datetime

from interpreter import Interpreter

if __name__ == "__main__":
    interpreter = Interpreter()

    sample_program = "++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>."
    interpreter.loadProgram(sample_program)

    start_time =  time.perf_counter()
    interpreter.runProgramSlow()
    print("--- %s seconds ---" % ( time.perf_counter()- start_time))

    interpreter.resetInterpreter()

    start_time =  time.perf_counter()
    interpreter.runProgramFast()
    print("--- %s seconds ---" % ( time.perf_counter()- start_time))

    print("\nInterpreter has been reset.")
    interpreter.resetInterpreter()

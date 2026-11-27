"""Calculator command table."""

CALCULATOR_COMMANDS: dict[str, tuple[int, str, str]] = {
    "add": (2, "Add two numbers","\nExample: \n> add 1 3 \n> 4"),
    "sub": (2, "Subtract two numbers ","\nExample: \n> sub 5 2 \n> 3"),
    "mul": (2, "Multiply two numbers ","\nExample: \n> mul 5 2 \n> 10"),
    "div": (2, "Divide two numbers ","\nExample: \n> div 10 2 \n> 5"),
    "pow": (2, "Raise a number to a power ","\nExample: \n> pow 2 3 \n> 8"),
    "mod": (2, "Find the remainder of a division ","\nExample: \n> mod 10 3 \n> 1"),
    "sqrt": (1, "Calculate the square root of a number ","\nExample: \n> sqrt 25 \n> 5"),
    "abs": (1, "Calculate the absolute value of a number ","\nExample: \n> abs -10 \n> 10"),
    "help": (0, "Show this help message ","\nExample: \n> help \n> Displays all available commands",),
    "exit": (0, "Exit the calculator ","\nExample: \n> exit \n> Exits the calculator"),
    "ms": (0, "Store the last result in memory ","\nExample: \n> ms \n> Result stored in memory"),
    "mr": (0, "Recall the value from memory ","\nExample: \n> mr \n> 10"),
    "mc": (0, "Clear the memory ","\nExample: \n> mc \n> Memory cleared"),
    "history": (0, "Show the history of calculations ","\nExample: \n> history \n> Displays calculation history"),
    "stats": (0, "Show statistics about the history ","\nExample: \n> stats \n> Displays calculation statistics"),
    "clear": (0, "Clear the history of calculations ","\nExample: \n> clear \n> History cleared"),
    "quit": (0, "Exit the calculator ","\nExample: \n> quit \n> Exits the calculator"),
}

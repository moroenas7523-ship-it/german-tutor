import os
import ollama

def show_menu():
    print("\n" + "="*50)
    print("🤖 Final AI Agent - Ready!")
    print("="*50)
    print("Commands you can use:")
    print("  list                -> show files")
    print("  read <file>         -> read a file")
    print("  calc <expression>   -> calculate (e.g., calc 25*4)")
    print("  ask <question>      -> ask AI anything")
    print("  exit                -> quit")
    print("="*50 + "\n")

def list_files():
    try:
        return "\n".join(f"  {f}" for f in os.listdir("."))
    except Exception as e:
        return f"Error: {e}"

def read_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()[:2000]
    except Exception as e:
        return f"Error: {e}"

def calculate(expr):
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expr):
            return "Only numbers and + - * / ( ) allowed"
        return f"= {eval(expr)}"
    except Exception as e:
        return f"Error: {e}"

def ask_ai(question):
    try:
        print("  [Thinking...]")
        response = ollama.chat(
            model="llama3.2:1b",
            messages=[{"role": "user", "content": question}]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

show_menu()

while True:
    try:
        cmd = input("You: ").strip()
    except (KeyboardInterrupt, EOFError):
        break
    
    if not cmd:
        continue
    
    low = cmd.lower()
    
    if low == "exit" or low == "quit":
        print("Goodbye! 👋")
        break
    elif low == "list" or low == "ls":
        print(list_files())
    elif low.startswith("read "):
        filename = cmd[5:].strip()
        print(read_file(filename))
    elif low.startswith("calc "):
        print(calculate(cmd[5:].strip()))
    elif low.startswith("ask "):
        print(ask_ai(cmd[4:].strip()))
    else:
        print("Unknown command. Type 'list', 'read <file>', 'calc <expr>', 'ask <question>', or 'exit'")

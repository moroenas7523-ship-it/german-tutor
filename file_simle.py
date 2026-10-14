import os

print("Commands: list | read <file> | exit\n")

while True:
    cmd = input("> ").strip()
    if cmd == "exit":
        break
    elif cmd == "list":
        for f in os.listdir("."):
            print(f"  {f}")
    elif cmd.startswith("read "):
        filename = cmd[5:].strip()
        if os.path.exists(filename):
            with open(filename) as f:
                print(f.read()[:2000])
        else:
            print(f"Not found: {filename}")
    else:
        print("Unknown command")

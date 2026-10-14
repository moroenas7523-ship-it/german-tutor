import ollama

messages = [
    {"role": "system", "content": "You are a helpful AI assistant. Answer in the same language the user writes in."}
]

print("AI Agent ready! Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Goodbye!")
        break
    
    messages.append({"role": "user", "content": user_input})
    
    response = ollama.chat(model="llama3.2:1b", messages=messages)
    
    answer = response["message"]["content"]
    print(f"\nAI: {answer}\n")
    
    messages.append({"role": "assistant", "content": answer})

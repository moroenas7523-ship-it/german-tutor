import ollama

response = ollama.chat(
    model="llama3.2:1b",
    messages=[
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Hello, who are you?"}
    ]
)
print(response["message"]["content"])

# # test_ollama_python.py
# import ollama
# import time

# print("🐍 Testing Ollama with Python...")

# # Test basic generation
# print("\n🧪 Testing text generation speed...")

# start_time = time.time()
# response = ollama.generate(
#     model='gemma3n',
#     prompt='Explain AI in simple terms:',
#     stream=False
# )
# generation_time = time.time() - start_time

# print(f"⚡ Generation time: {generation_time:.2f} seconds")
# print(f"📝 Response: {response['response']}")

# # Calculate approximate tokens per second
# response_length = len(response['response'].split())
# tokens_per_sec = response_length / generation_time
# print(f"🎯 Approximate speed: {tokens_per_sec:.1f} words/second")
# ollama_streaming.py
import ollama
import time

print("🌊 Ollama with Streaming...")

start_time = time.time()
print("📝 Response: ", end="", flush=True)

response_text = ""
for chunk in ollama.generate(
    model='gemma3n',
    prompt='How is India using AI in agriculture?',
    stream=True
):
    chunk_text = chunk['response']
    print(chunk_text, end='', flush=True)
    response_text += chunk_text

total_time = time.time() - start_time
print(f"\n\n⚡ Total time: {total_time:.2f}s")
print(f"🎯 Words: {len(response_text.split())}")
print(f"💨 Streaming speed: {len(response_text.split()) / total_time:.1f} words/sec")
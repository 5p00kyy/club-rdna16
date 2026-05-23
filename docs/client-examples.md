# Client Examples

llama.cpp server exposes an OpenAI-compatible API.

## curl

```bash
curl http://127.0.0.1:8088/v1/chat/completions \
  -H 'content-type: application/json' \
  -H "authorization: Bearer ${LLAMA_API_KEY:-test}" \
  -d '{
    "model": "Qwen3.6-35B-A3B",
    "messages": [{"role": "user", "content": "Reply with: rdna16 ok"}],
    "temperature": 0,
    "max_tokens": 64
  }'
```

## Python

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8088/v1", api_key="test")
response = client.chat.completions.create(
    model="Qwen3.6-35B-A3B",
    messages=[{"role": "user", "content": "Reply with: rdna16 ok"}],
    temperature=0,
    max_tokens=64,
)
print(response.choices[0].message.content)
```

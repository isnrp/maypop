import os, httpx

API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

def get_embedding(text: str) -> list[float]:
    response = httpx.post(
        API_URL,
        headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"},
        json={"inputs": text},
    )
    return response.json()
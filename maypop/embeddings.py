import os, httpx, time

API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

def get_embedding(text: str) -> list[float]:
    headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}
    for attempt in range(5):
        response = httpx.post(API_URL, headers=headers, json={"inputs": text})
        if response.status_code == 200:
            return response.json()
        time.sleep(2)
    raise RuntimeError(f"HF API failed after 5 attempts: {response.text}")
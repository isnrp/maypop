import os, httpx, time

API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
def get_embedding(text: str) -> list[float]:
    headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}
    for attempt in range(5):
        response = httpx.post(API_URL, headers=headers, json={"inputs": text})
        if response.status_code == 200:
            result = response.json()
            # HF returns [[...]] for single inputs, flatten it
            if isinstance(result[0], list):
                return result[0]
            return result
        time.sleep(2)
    raise RuntimeError(f"HF API failed after 5 attempts: {response.text}")
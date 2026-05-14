from maypop.db import get_conn
from sentence_transformers import SentenceTransformer

# Load model once (important for performance)
_model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str):
    """Convert text → vector embedding"""
    return _model.encode(text).tolist()


def search(query: str, limit: int = 10):
    conn = get_conn()
    cur = conn.cursor()

    # 1. Convert query → embedding
    vec = get_embedding(query)

    # 2. Vector similarity search (pgvector)
    cur.execute(
        """
        SELECT id, name, content
        FROM apps
        WHERE embedding IS NOT NULL
        ORDER BY embedding <-> %s::vector
        LIMIT %s;
        """,
        (vec, limit)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    # 3. Print results
    if not rows:
        print("No results found.")
        return

    for app_id, name, content in rows:
        print(f"\n[{app_id}] {name}")
        print(f"  {content}")


if __name__ == "__main__":
    # quick local test
    import sys

    if len(sys.argv) < 2:
        print("Usage: python search.py <query>")
    else:
        search(" ".join(sys.argv[1:]))
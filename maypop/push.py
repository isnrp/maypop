from maypop.db import get_conn
from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text):
    return _model.encode(text).tolist()


def push(name, content):
    conn = get_conn()
    cur = conn.cursor()

    # 🔥 THIS is what you're missing or breaking
    embedding = get_embedding(content)

    #print("DEBUG embedding length:", len(embedding))  # optional sanity check

    cur.execute(
        """
        INSERT INTO apps (name, content, embedding)
        VALUES (%s, %s, %s)
        RETURNING id;
        """,
        (name, content, str(embedding))
    )

    app_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    print(f"Pushed app '{name}' with id {app_id}")
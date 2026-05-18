# maypop/push.py
import pathlib, datetime
from maypop.db import get_conn
from maypop.embeddings import get_embedding


def push(name: str, path: str, description: str = "", tags: list[str] = None, uploader: str = ""):
    p = pathlib.Path(path)

    if p.is_dir():
        index = p / "index.html"
    elif p.is_file():
        index = p
    else:
        print(f"Error: '{path}' is not a file or directory.")
        return

    if not index.exists():
        print(f"Error: no index.html found at '{index}'")
        return

    content = index.read_text(encoding="utf-8")
    embed_text = " ".join(filter(None, [name, description] + (tags or [])))
    embedding = get_embedding(embed_text)
    now = datetime.datetime.utcnow()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO apps (name, content, description, embedding, tags, uploader, created_at, uploaded_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (name, content, description, str(embedding), tags or [], uploader, now, now),
    )

    app_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    print(f"Pushed '{name}' → id {app_id}")
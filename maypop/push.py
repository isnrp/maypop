# maypop/push.py
import pathlib, datetime
from maypop.db import get_conn
from maypop.embeddings import get_embedding


def push(name: str, path: str, tags: list[str] = None, uploader: str = ""):
    """
    Push an app by reading its index.html file.
    `path` can be:
      - a directory:  ./myapp/          (reads index.html from inside)
      - a file:       ./myapp/index.html
    """
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
    embedding = get_embedding(content)
    now = datetime.datetime.utcnow()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO apps (name, content, embedding, tags, uploader, created_at, uploaded_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (name, content, str(embedding), tags or [], uploader, now, now),
    )

    app_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    print(f"Pushed '{name}' (index.html, {len(content)} chars) → id {app_id}")
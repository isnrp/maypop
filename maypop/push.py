# maypop/push.py
import pathlib
from maypop.db import get_conn
from maypop.embeddings import get_embedding


def push(name: str, path: str):
    """
    Push an app by reading its index.html file.
    `path` can be:
      - a direct HTML file:   ./myapp/index.html
      - a directory:          ./myapp/          (index.html is read from inside)
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

    conn = get_conn()
    cur = conn.cursor()

    embedding = get_embedding(content)

    cur.execute(
        """
        INSERT INTO apps (name, content, embedding)
        VALUES (%s, %s, %s)
        RETURNING id;
        """,
        (name, content, str(embedding)),
    )

    app_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    print(f"Pushed '{name}' (index.html, {len(content)} chars) → id {app_id}")
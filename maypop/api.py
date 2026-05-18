# maypop/api.py
# Wraps push/search/pull to return data instead of printing.
# Your existing CLI and its modules stay UNTOUCHED.

from maypop.db import get_conn
from maypop.embeddings import get_embedding


def api_search(query: str, limit: int = 50) -> list[dict]:
    """Return list of {id, name, content} dicts ranked by vector similarity."""
    conn = get_conn()
    cur = conn.cursor()

    vec = get_embedding(query)

    cur.execute(
        """
        SELECT id, name, content
        FROM apps
        WHERE embedding IS NOT NULL
        ORDER BY embedding <-> %s::vector
        LIMIT %s;
        """,
        (vec, limit),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{"id": r[0], "name": r[1], "content": r[2]} for r in rows]


def api_pull(app_id: int | str) -> dict | None:
    """Return {id, name, content} for a single app, or None if not found."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, content FROM apps WHERE id = %s;",
        (app_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None
    return {"id": row[0], "name": row[1], "content": row[2]}


def api_push(name: str, content: str) -> int:
    """Insert or update an app. Returns the new app id."""
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

    return app_id


def api_list_all(limit: int = 100) -> list[dict]:
    """Return all apps ordered by id desc (no embedding needed)."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, content FROM apps ORDER BY id DESC LIMIT %s;",
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{"id": r[0], "name": r[1], "content": r[2]} for r in rows]
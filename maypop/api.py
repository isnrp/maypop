# maypop/api.py
import datetime
from maypop.db import get_conn
from maypop.embeddings import get_embedding

COLS = "id, name, tags, uploader, created_at, uploaded_at, content"

def _row(r) -> dict:
    return {
        "id":          r[0],
        "name":        r[1],
        "tags":        r[2] or [],
        "uploader":    r[3] or "",
        "created_at":  r[4],
        "uploaded_at": r[5],
        "content":     r[6],
    }


def api_search(query: str, limit: int = 50) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    vec = get_embedding(query)
    cur.execute(
        f"""
        SELECT {COLS} FROM apps
        WHERE embedding IS NOT NULL
        ORDER BY embedding <-> %s::vector
        LIMIT %s;
        """,
        (vec, limit),
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [_row(r) for r in rows]


def api_pull(app_id: int | str) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT {COLS} FROM apps WHERE id = %s;", (app_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return _row(row) if row else None


def api_push(name: str, content: str, tags: list[str] = None, uploader: str = "") -> int:
    conn = get_conn()
    cur = conn.cursor()
    embedding = get_embedding(content)
    now = datetime.datetime.utcnow()
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
    cur.close(); conn.close()
    return app_id


def api_list_all(limit: int = 100) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        f"SELECT {COLS} FROM apps ORDER BY uploaded_at DESC LIMIT %s;",
        (limit,),
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [_row(r) for r in rows]
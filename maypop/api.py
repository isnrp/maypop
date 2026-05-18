# maypop/api.py
import datetime
from maypop.db import get_conn
from maypop.embeddings import get_embedding

COLS = "id, name, tags, uploader, created_at, uploaded_at, description, content"

def _row(r) -> dict:
    return {
        "id":          r[0],
        "name":        r[1],
        "tags":        r[2] or [],
        "uploader":    r[3] or "",
        "created_at":  r[4],
        "uploaded_at": r[5],
        "description": r[6] or "",
        "content":     r[7],
    }


TAG_PARENTS = {
    "platformer":  ["game"],
    "fps":         ["game", "shooter"],
    "shooter":     ["game"],
    "rpg":         ["game"],
    "puzzle":      ["game"],
    "strategy":    ["game"],
    "tower defense": ["game", "strategy"],
    "racing":      ["game"],
    "sports":      ["game"],
    "arcade":      ["game"],
    "adventure":   ["game"],
    "simulation":  ["game"],
    "horror":      ["game"],
}

# build reverse map: parent → all children
TAG_CHILDREN: dict[str, list[str]] = {}
for child, parents in TAG_PARENTS.items():
    for parent in parents:
        TAG_CHILDREN.setdefault(parent, []).append(child)


def _expand_query_tags(query: str) -> list[str]:
    """Return the query plus any synonym/child tags."""
    q = query.lower().strip()
    extras = TAG_CHILDREN.get(q, [])
    return [q] + extras


def api_search(query: str, limit: int = 50, threshold: float = 1.38) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    vec = get_embedding(query)
    q = f"%{query}%"
    expanded = _expand_query_tags(query)
    # build tag match for all expanded terms
    tag_conditions = " OR ".join(
        ["EXISTS (SELECT 1 FROM unnest(tags) t WHERE t ILIKE %s)"] * len(expanded)
    )
    tag_params = [f"%{t}%" for t in expanded]
    cur.execute(
        f"""
        SELECT {COLS} FROM apps
        WHERE (
            (embedding IS NOT NULL AND embedding <-> %s::vector < %s)
            OR name        ILIKE %s
            OR description ILIKE %s
            OR uploader    ILIKE %s
            OR {tag_conditions}
        )
        ORDER BY
            CASE WHEN embedding IS NOT NULL
                 THEN embedding <-> %s::vector
                 ELSE 1.0
            END
        LIMIT %s;
        """,
        (vec, threshold, q, q, q, *tag_params, vec, limit),
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


def api_push(name: str, content: str, description: str = "", tags: list[str] = None, uploader: str = "") -> int:
    conn = get_conn()
    cur = conn.cursor()
    embed_text = " ".join(filter(None, [name, description] + (tags or [])))
    embedding = get_embedding(embed_text)
    now = datetime.datetime.utcnow()
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
    cur.close(); conn.close()
    return app_id


def api_update(app_id: int | str, name: str, description: str, tags: list[str], uploader: str, content: str = None):
    conn = get_conn()
    cur = conn.cursor()
    embed_text = " ".join(filter(None, [name, description] + (tags or [])))
    embedding = get_embedding(embed_text)
    if content is not None:
        cur.execute(
            """
            UPDATE apps
            SET name        = %s,
                description = %s,
                tags        = %s,
                uploader    = %s,
                embedding   = %s,
                content     = %s,
                uploaded_at = NOW()
            WHERE id = %s;
            """,
            (name, description, tags, uploader, str(embedding), content, app_id),
        )
    else:
        cur.execute(
            """
            UPDATE apps
            SET name        = %s,
                description = %s,
                tags        = %s,
                uploader    = %s,
                embedding   = %s,
                uploaded_at = NOW()
            WHERE id = %s;
            """,
            (name, description, tags, uploader, str(embedding), app_id),
        )
    conn.commit()
    cur.close(); conn.close()


def api_delete(app_id: int | str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM apps WHERE id = %s;", (app_id,))
    conn.commit()
    cur.close(); conn.close()


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
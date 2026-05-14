import sys
from db import get_conn

def add_app_with_tags(name, content, tags):
    conn = get_conn()
    cur = conn.cursor()
	
    embedding = get_embedding(content)

    # 1. create app
    cur.execute("""
        INSERT INTO apps (name, content)
        VALUES (%s, %s)
        RETURNING id;
    """, (name, content, embedding))

    app_id = cur.fetchone()[0]

    # 2. attach tags
    for tag in tags:
        cur.execute("SELECT id FROM tags WHERE name = %s", (tag,))
        row = cur.fetchone()

        if row:
            tag_id = row[0]
            cur.execute("""
                INSERT INTO app_tags (app_id, tag_id)
                VALUES (%s, %s)
            """, (app_id, tag_id))

    conn.commit()
    cur.close()
    conn.close()

    print("Created app with tags:", app_id)

if __name__ == "__main__":
    cmd = sys.argv[1]

    if cmd == "add-app":
        name = sys.argv[2]
        content = sys.argv[3]
        add_app(name, content)

    elif cmd == "add-app-tags":
        name = sys.argv[2]
        content = sys.argv[3]
        tags = sys.argv[4:]
        add_app_with_tags(name, content, tags)

def search(tag_name):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        WITH RECURSIVE tag_tree AS (
            SELECT id
            FROM tags
            WHERE name = %s

            UNION ALL

            SELECT t.id
            FROM tags t
            JOIN tag_tree tt ON t.parent_id = tt.id
        )
        SELECT DISTINCT a.id, a.name, a.content
        FROM apps a
        JOIN app_tags at ON a.id = at.app_id
        WHERE at.tag_id IN (SELECT id FROM tag_tree);
    """, (tag_name,))

    rows = cur.fetchall()

    for r in rows:
        print(r)

    cur.close()
    conn.close()

def search(query):
    conn = get_conn()
    cur = conn.cursor()

    query_vec = get_embedding(query)

    cur.execute("""
        WITH RECURSIVE tag_tree AS (
            SELECT id
            FROM tags
            WHERE name = %s

            UNION ALL

            SELECT t.id
            FROM tags t
            JOIN tag_tree tt ON t.parent_id = tt.id
        )
        SELECT DISTINCT a.name, a.content
        FROM apps a
        JOIN app_tags at ON a.id = at.app_id
        WHERE at.tag_id IN (SELECT id FROM tag_tree)
        ORDER BY a.embedding <-> %s
        LIMIT 10;
    """, (query, query_vec))

    rows = cur.fetchall()

    for r in rows:
        print(r)

    cur.close()
    conn.close()
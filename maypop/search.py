def search(query):
    conn = get_conn()
    cur = conn.cursor()

    vec = get_embedding(query)

    cur.execute("""
        SELECT id, name
        FROM apps
        ORDER BY embedding <-> %s
        LIMIT 10;
    """, (vec,))

    for row in cur.fetchall():
        print(f"{row[0]} | {row[1]}")

    cur.close()
    conn.close()
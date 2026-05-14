from maypop.db import get_conn

def pull(app_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, content
        FROM apps
        WHERE id = %s;
    """, (app_id,))

    row = cur.fetchone()

    if not row:
        print("Not found on server")
    else:
        print("ID:", row[0])
        print("Name:", row[1])
        print("Content:", row[2])

    cur.close()
    conn.close()
from maypop.db import get_conn


def push(name, content):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO apps (name, content)
        VALUES (%s, %s)
        RETURNING id;
        """,
        (name, content)
    )

    app_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    print(f"Pushed app '{name}' with id {app_id}")
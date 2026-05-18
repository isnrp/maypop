# maypop/pull.py
import pathlib
from maypop.db import get_conn


def pull(app_id: str, dest: str = "."):
    """
    Pull an app by id and save its content as index.html inside `dest/`.

    Examples
    --------
    maypop pull 3          → saves to ./3/index.html
    maypop pull 3 ./myapp  → saves to ./myapp/index.html
    """
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
        print("Not found on server.")
        return

    app_id_val, name, content = row

    # decide output folder
    out_dir = pathlib.Path(dest) if dest != "." else pathlib.Path(f"./{app_id_val}")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / "index.html"
    out_file.write_text(content, encoding="utf-8")

    print(f"Pulled '{name}' (id {app_id_val}) → {out_file}")
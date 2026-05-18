# cli.py
import sys

from maypop.push import push
from maypop.search import search
from maypop.pull import pull


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage:")
        print("  maypop push <name> <path>        # path to index.html or a folder")
        print("  maypop search <query>")
        print("  maypop pull <id> [dest_folder]")
        return

    cmd = args[0]

    # -------------------
    # PUSH
    # -------------------
    if cmd == "push":
        if len(args) < 3:
            print("Usage: maypop push <name> <path> [uploader] [tag1,tag2,...]")
            print("  <path> can be a folder containing index.html, or the file itself.")
            return

        name     = args[1]
        path     = args[2]
        uploader = args[3] if len(args) >= 4 else ""
        tags     = args[4].split(",") if len(args) >= 5 else []
        push(name, path, tags=tags, uploader=uploader)

    # -------------------
    # SEARCH
    # -------------------
    elif cmd == "search":
        if len(args) < 2:
            print("Usage: maypop search <query>")
            return

        query = " ".join(args[1:])
        search(query)

    # -------------------
    # PULL
    # -------------------
    elif cmd == "pull":
        if len(args) < 2:
            print("Usage: maypop pull <id> [dest_folder]")
            return

        app_id = args[1]
        dest   = args[2] if len(args) >= 3 else "."
        pull(app_id, dest)

    else:
        print(f"Unknown command: {cmd}")
        print("Use: push | search | pull")
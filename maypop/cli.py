import sys

from maypop.push import push
from maypop.search import search
from maypop.pull import pull


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage:")
        print("  maypop push <name> <content>")
        print("  maypop search <query>")
        print("  maypop pull <id>")
        return

    cmd = args[0]

    # -------------------
    # PUSH
    # -------------------
    if cmd == "push":
        if len(args) < 3:
            print("Usage: maypop push <name> <content>")
            return

        name = args[1]
        content = " ".join(args[2:])  # allows spaces in content
        push(name, content)

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
            print("Usage: maypop pull <id>")
            return

        pull(args[1])

    else:
        print(f"Unknown command: {cmd}")
        print("Use: push | search | pull")
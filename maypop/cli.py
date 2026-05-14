import sys
from maypop.push import push
from maypop.pull import pull
from maypop.search import search

def main():
    cmd = sys.argv[1]

    if cmd == "push":
        push(sys.argv[2:])

    elif cmd == "pull":
        pull(sys.argv[2:])

    elif cmd == "search":
        search(sys.argv[2])

if __name__ == "__main__":
    main()
from argparse import ArgumentParser
from pathlib import Path
from livereload import Server
from subprocess import run

parser = ArgumentParser()
parser.add_argument('paths', type=Path, nargs='+')
parser.add_argument('--cmd', required=True)
parser.add_argument('--root', type=Path)
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', default=5500)
args = parser.parse_args()

def callback():
    run(args.cmd, shell=True)

server = Server()
for path in args.paths:
    watcher = server.watch(str(path), callback)
server.serve(host=args.host, port=args.port, root=args.root)


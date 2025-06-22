# Copyright 2025 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Modcast v1.0 - Test it there

Simple client that recieves mods from host.
Used by me to test faster on my tablet.
Host: run from commandline or use your own host
Client: install as plugin and press the button in the newly added dev console tab
"""

HOST = '1.1.1.1'
PORT = 1111

if __name__ == '__main__':
    from http.server import SimpleHTTPRequestHandler
    from socketserver import TCPServer
    from sys import exit

    Hdlr = SimpleHTTPRequestHandler

    with TCPServer((HOST, PORT), Hdlr) as httpd:
        print(f"Modcast server v1.0\nRunning on (http://{HOST}:{PORT}/)")
        httpd.serve_forever()

    exit()

from os.path import basename, getsize, getmtime, join, exists
from urllib.request import urlretrieve
from os import makedirs, remove
from datetime import datetime
from typing import override

from babase import Plugin, app, PluginSpec
from _babase import env
from babase._general import getclass
from babase._devconsole import (
    DevConsoleTabEntry as ENT,
    DevConsoleTab as TAB
)

FILE = "power.py"

class Modcast(TAB):
    def load(s):
        dl_url = f"http://{HOST}:{PORT}/{FILE}"

        install_fn = FILE
        install_path_base = env()['python_directory_user']
        install_fp = join(install_path_base, install_fn)
        b = exists(install_fp)

        makedirs(install_path_base, exist_ok=True)

        tmp_fp, _ = urlretrieve(dl_url)
        with open(tmp_fp, 'r') as src_f:
            mod_content = src_f.read()
        with open(install_fp, 'w+') as dest_f:
            dest_f.write(mod_content)
        remove(tmp_fp)
    @override
    def refresh(s):
        x = -s.width / 2

        btn_base_width = (s.width - x) / 2
        btn_width = btn_base_width * (4/3)
        btn_height = s.height / 3

        s.button(
            f"Load {FILE} from server",
            pos=(x, 0),
            size=(btn_width, btn_height),
            corner_radius=0,
            style='blue',
            call=s.load
        )

# brobord collide grass
# ba_meta require api 9
# ba_meta export plugin
class byBordd(Plugin):
    def __init__(s):
        I = app.devconsole
        E = ENT('Modcast',Modcast)
        I.tabs.append(E)
        I._tab_instances['Modcast'] = E.factory()

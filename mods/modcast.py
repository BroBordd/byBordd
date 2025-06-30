# Copyright 2025 - Solely by BrotherBoard - Feel free to utilize/modify this for personal use
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
FILE = "polish.py" # This 'FILE' is local to the client and will be overridden by host's setting.

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
import ast

from babase import Plugin, app, PluginSpec
from _babase import env
from babase._general import getclass
from babase._devconsole import (
    DevConsoleTabEntry as ENT,
    DevConsoleTab as TAB
)

class Modcast(TAB):
    def _get_host_file_variable(s, var_name):
        modcast_url = f"http://{HOST}:{PORT}/modcast.py"
        temp_modcast_fp = None
        try:
            temp_modcast_fp, _ = urlretrieve(modcast_url)
            with open(temp_modcast_fp, 'r') as f:
                content = f.read()

            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == var_name:
                            if isinstance(node.value, ast.Constant): # For Python 3.8+; ast.Str for older
                                return node.value.value
                            elif isinstance(node.value, ast.Str): # For older Python versions
                                return node.value.s
            return None
        except Exception:
            return None
        finally:
            if temp_modcast_fp and exists(temp_modcast_fp):
                remove(temp_modcast_fp)

    def load(s):
        mod_to_download = s._get_host_file_variable('FILE')
        if not mod_to_download:
            mod_to_download = "default_mod.py" # Fallback if FILE not found or error

        dl_url = f"http://{HOST}:{PORT}/{mod_to_download}"

        install_fn = mod_to_download
        install_path_base = env()['python_directory_user']
        install_fp = join(install_path_base, install_fn)

        makedirs(install_path_base, exist_ok=True)

        tmp_fp, _ = urlretrieve(dl_url)
        with open(tmp_fp, 'r') as src_f:
            mod_content = src_f.read()
        with open(install_fp, 'w+') as dest_f:
            dest_f.write(mod_content)
        remove(tmp_fp)

    @override
    def refresh(s):
        current_mod_name = s._get_host_file_variable('FILE')
        if not current_mod_name:
            current_mod_name = "..." # Show pending if cannot retrieve

        x = -s.width / 2

        btn_base_width = (s.width - x) / 2
        btn_width = btn_base_width * (4/3)
        btn_height = s.height / 3

        s.button(
            f"Load {current_mod_name} from server",
            pos=(x, 0),
            size=(btn_width, btn_height),
            corner_radius=0,
            style='blue',
            call=s.load
        )

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s):
        I = app.devconsole
        E = ENT('Modcast',Modcast)
        I.tabs.append(E)
        I._tab_instances['Modcast'] = E.factory()

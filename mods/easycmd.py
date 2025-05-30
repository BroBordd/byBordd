import babase
import bauiv1 as bui
import bauiv1lib.party
from bauiv1lib.popup import PopupMenuWindow
import random
import bascenev1 as bs
from bascenev1 import get_game_roster
import json
import os

class CMDPW(bauiv1lib.party.PartyWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ids = [0]
        self._usrs = []
        self._dir = babase.env()["python_directory_user"]
        self._save = self._dir+"/Configs/QuickCMD.txt"
        if not os.path.exists(self._save):
            with open(self._save, 'w') as file:
                file.write("kick\nban\n")
        with open(self._save, "r") as file:
            self._cmds = file.read().strip().split("\n")
        with open(self._save, "r") as file:
            if not file.read(1): self._cmds = []
        self._cmds.insert(0, "*Select CMD")
        self._cmds.append("*Manage CMDS")
        self._auto = os.path.exists(self._dir+"/Configs/QuickCMD.ON")
        self._opts = ["*Manage CMDS", "Add", "Add (No USER) -", "Remove", "Auto Send (ON)" if self._auto else "Auto Send (OFF)"]
        self._mode = 0
        self._fine = None # this prevents highend conflicts
        self._cmd_btn = bui.buttonwidget(
            parent=self._root_widget,
            size=(70, 35),
            label='CMD',
            scale=0.8,
            button_type='square',
            position=(self._width - 425, self._height - 45),
            on_activate_call=self._safe
        )

    def _update_stuffs(self):
        self._ids = [0]
        roster = get_game_roster()
        self._usrs = ['*Select USER']
        for n in range(len(roster)):
            self._ids.append(roster[n]['client_id'])
            try:
                self._usrs.append(str(roster[n]['players'][0]['name_full']))
            except IndexError:
                self._usrs.append(str(json.loads(roster[n]['spec_string'])['n']))
        self._usrs.append("*none")

    def _safe(self):
        self._update_stuffs()
        self._pop(0)

    def _pop(self, i):
        self._mode = i
        arr = self._cmds
        arr[0] = "*Select CMD"
        if i == 1: arr = self._usrs
        elif i == 2: arr = self._opts
        elif i == 3: arr[0] = "*Remove CMD"
        self._fine = PopupMenuWindow(position=self._cmd_btn.get_screen_space_center(),
                                choices=arr,
                                choices_disabled=[arr[0]],
                                current_choice=arr[-1],
                                delegate=self)

    def _push(self, text):
        bui.textwidget(edit=self._text_field, text=text)

    def popup_menu_selected_choice(self, p: PopupMenuWindow,
                                   c: str) -> None:
        if p != self._fine:
            super().popup_menu_selected_choice(p, c)
            return # phew that's not my business

        if c.startswith("Auto"):
            if self._auto:
                os.remove(self._dir+"/Configs/QuickCMD.ON")
                self._opts[4] = "Auto Send (OFF)"
            else:
                self._opts[4] = "Auto Send (ON)"
                with open(self._dir+"/Configs/QuickCMD.ON", "w") as file:
                    file.write("1")
            self._auto = not self._auto
            return

        if c == self._usrs[-1]:
            if self._auto and self._mode == 1:
                bs.chatmessage(bui.textwidget(query=self._text_field))
                self._push('')
            return

        elif c == self._cmds[-1]:
            self._pop(2)
            return

        co = c
        if c.endswith(" -"): c = c[:-2]

        t = bui.textwidget(query=self._text_field)
        self._push(f"/{c} " if self._mode == 0 else t+str(self._ids[self._usrs.index(c)]) if self._mode == 1 else t)

        if self._mode == 0 and not co.endswith(" -"):
            self._pop(1)

        if self._mode == 2:
            if not t and c.startswith("Add"):
                bs.screenmessage("type command in chat first (don't send)")
            elif t and c.startswith("Add"):
                if t.startswith("/"): t = t[1:]
                with open(self._save, "a") as file:
                    if c == "Add":
                        file.write("\n"+t.split()[0])
                        self._cmds.insert(-1, t.split()[0])
                        bs.screenmessage(f"added command {t.split()[0]}")
                    else:
                        file.write("\n"+t+" -")
                        self._cmds.insert(-1, t+" -")
                        bs.screenmessage(f"added command {t} - (Won't ask for USER)")
            else:
                self._pop(3)

        if self._mode == 3:
            self._cmds.remove(co)
            with open(self._save, "r") as file:
                lines = file.read().strip().split("\n")
                lines = [line for line in lines if line != co]
                with open(self._save, "w") as file: file.write("\n".join(lines) if co != " " else "")
                bs.screenmessage(f"removed command {c}")

        if (self._auto and co.endswith(" -")) or (self._auto and self._mode != 1):
            bs.chatmessage(bui.textwidget(query=self._text_field))
            self._push('')
            return

# ba_meta require api 8
# ba_meta export plugin
class byBordd(babase.Plugin):
    def __init__(self):
        bauiv1lib.party.PartyWindow = CMDPW

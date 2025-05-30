import babase
import bauiv1 as bui
import bauiv1lib.party
import re
import bascenev1 as bs

class PWSlashN(bauiv1lib.party.PartyWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _send_chat_message(self) -> None:
        s = bui.textwidget(query=self._text_field)
        msgs = re.findall(r'.{1,50}(?=\s|$)', s)
        if len(msgs) > 1:
            bui.textwidget(edit=self._text_field, text='')
            for msg in msgs: bs.chatmessage(msg)
        else: super()._send_chat_message()

# ba_meta require api 8
# ba_meta export plugin
class byBordd(babase.Plugin):
    def __init__(self):
        bauiv1lib.party.PartyWindow = PWSlashN

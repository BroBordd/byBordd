# BitBox - Bored me brings bits to the game
# Copyright 2025 - Solely by BroBordd
# Bug? Feedback? Telegram >> @GalaxyA14user

from babase import Plugin
from bauiv1 import textwidget as tw

class PixText:
    """Renders monospaced pixelated text.

    Uses a 5x9 pixel font for retro UIs. Characters use individual pixel widgets.

    Attributes:
        CHAR_SPACING (float): Horizontal character spacing.
        LINE_SPACING (float): Vertical line spacing.

    Internal Data:
        _KEYS (callable): Lambda returning font characters.
        _DATA (callable): Lambda returning hex pixel data.
    """
    CHAR_SPACING = 1.5
    LINE_SPACING = 1.2

    _KEYS = lambda: (
        'ABCDEFGHIJKLMNOP'
        'QRSTUVWXYZabcdef'
        'ghijklmnopqrstuv'
        'wxyz ,!"#$%&()*+'
        '-./0123456789:;<'
        '=>?@[]^_`{}|~\\\''
    )
    _DATA = lambda: (
        '74631FC62|F463E8C7C|74610845C|F46318C7C|FC21E843E|FC21E842|746109C5E|8C63F8C62|'
        'F9084213E|F08421498|8C65C9462|84210843E|8EF75AC62|8E6B59C62|746318C5C|F4631F42|'
        '746318D5C41|F463E9462|7C20E087C|F90842108|8C6318C5C|8C6315288|8D6B5AA94|8C5445462|'
        '8C62A2108|F8444443E|001C17C5E|842D98C5C|001D1845C|085F18CDA|001D1FC1E|191E4213E|'
        '001F18CDA17|843D18C62|20384213E|081E10862E|84252E4A2|E1084213E|002BFAD6A|002D98C62|'
        '001D18C5C|002D98C7D08|001F18CDA108|0036C423C|001F0707C|013E42106|002318CDA|002315288|'
        '00235AA94|002317462|0023152884C|003E2223E||000000011|210840108|52A8|52BEAFA94|'
        '011F4717C4|D688845AC|6420F9498|110842104|208421088|A228|00084F908|000007|000000108|'
        '08444221|001D3AE5C|00384213E|001D1323E|001D10B8317|0004654BE21|003F087821F|'
        '3221E8C5C|003E1111084|7462E8C5C|001D18BC226|000840108|0008401088|000444104|'
        '0001F07C|000820888|744260108|746FBFC1E|31084210C|30842108C|228|00000003E|83|'
        '110882104|208411088|210842108|001151|420821042|1088'
    )

    def __init__(
        s,
        parent,
        text,
        position,
        color=(1,1,1),
        res='\u25A0',
        scale=1,
        spacing=0
    ) -> None:
        """Initializes a PixText instance.

        Args:
            parent: Parent object for pixel widgets.
            text (str): Initial string (supports '\\n').
            position (tuple): (x, y) base coordinates.
            color (tuple, optional): Overall pixel color (RGB). Default: white.
            res (str, optional): Character for each pixel. Default: '\u25A0'.
            scale (float, optional): Global text scale. Default: 1.
            spacing (int, optional): Internal pixel spacing. Default: 0.
        """
        s.parent = parent
        s.text = text
        s.position = position
        s.color = color
        s.res = res
        s.scale = scale
        s.spacing = spacing
        s.pixels = []
        s._highlight_map = {} # Stores pixel index to highlight color

        s._char_data_map = dict(zip(list(PixText._KEYS()), PixText._DATA().split('|')))

        s.scan()

    def dehex(s, st) -> list:
        """Converts hex string to binary pixel list (5x9 grid).

        Args:
            st (str): Hex pixel data.

        Returns:
            list: 45 integers (0 or 1) for pixel states.
        """
        st = st.ljust(12, '0')
        try:
            b = bin(int(st, 16))[2:].zfill(48)[:45]
        except ValueError as e:
            print(f"Warning: PixText.dehex received invalid hex data '{st}'. Error: {e}")
            return [0] * (5 * 9)
        return [int(bit) for bit in b]

    def scan(s) -> None:
        """Renders the current text.

        Nukes old pixels, then spawns new ones using character data and global 'tw'.
        Handles newlines, scaling, and spacing.
        """
        s.nuke()
        s._highlight_map = {} # Clear highlight map on full re-scan

        sx,sy = s.position
        ps = 1 + s.spacing
        xo = yo = 0

        for ch in s.text:
            if ch == '\n':
                xo = 0
                yo -= (9 * ps + s.LINE_SPACING) * s.scale
                continue

            cd = s._char_data_map.get(ch, s._char_data_map[' '])
            fp = s.dehex(cd)
            for cy in range(9):
                for cx in range(5):
                    if fp[cy * 5 + cx] == 1:
                        x = sx + (xo + cx * ps) * s.scale
                        y = sy + (yo + (9 - 1 - cy) * ps) * s.scale
                        p = tw(
                            parent=s.parent,
                            position=(x,y),
                            color=s.color,
                            scale=0.1,
                            text=s.res,
                            shadow=0.0,
                            flatness=1.0
                        )
                        s.pixels.append(p)
            xo += (5 * ps + s.CHAR_SPACING) * s.scale

    def set_text(s, new_text) -> None:
        """Updates displayed text.

        If 'new_text' differs, nukes old pixels and renders new ones.

        Args:
            new_text (str): The new string.
        """
        if s.text != new_text:
            s.text = new_text
            s.scan()

    def highlight(s, highlights) -> None:
        """Applies highlight colors to specific words or phrases within the text.

        This method updates the colors of existing pixels by calling 'tw' on them.

        Args:
            highlights (dict): A dictionary where keys are the text strings to highlight
                                and values are their corresponding RGB color tuples.
                                Example: {"HELLO": (1, 0, 0), "WORLD": (0, 0, 1)}
        """
        # Reset any previous highlights by setting all pixels to the base color
        for p in s.pixels:
            if hasattr(p, 'color'): # Ensure it has a color attribute before trying to update
                tw(p, color=s.color) # Use tw to update existing pixel color
        s._highlight_map = {}

        # Iterate through the text to find matches and apply highlights
        current_pixel_offset = 0
        for char_index, ch in enumerate(s.text):
            if ch == '\n':
                continue

            char_pixel_count = sum(s.dehex(s._char_data_map.get(ch, s._char_data_map[' '])))

            found_highlight = False
            for highlight_text, highlight_color in highlights.items():
                if highlight_text in s.text[char_index:]:
                    start_of_match_in_substring = s.text[char_index:].find(highlight_text)
                    if start_of_match_in_substring == 0:
                        # Calculate the start pixel index for the highlight
                        highlight_start_pixel = 0
                        for i in range(char_index):
                            if s.text[i] != '\n':
                                highlight_start_pixel += sum(s.dehex(s._char_data_map.get(s.text[i], s._char_data_map[' '])))

                        # Calculate the total pixels for the highlight_text
                        highlight_pixels_length = 0
                        for h_char in highlight_text:
                            highlight_pixels_length += sum(s.dehex(s._char_data_map.get(h_char, s._char_data_map[' '])))

                        # Apply color to the pixels in the range using the tw update mechanism
                        for i in range(highlight_start_pixel, highlight_start_pixel + highlight_pixels_length):
                            if i < len(s.pixels):
                                tw(s.pixels[i], color=highlight_color) # Use tw to update existing pixel color
                                s._highlight_map[i] = highlight_color
                        found_highlight = True
                        break # Only apply the first matching highlight for a substring

            current_pixel_offset += char_pixel_count


    def nuke(s) -> None:
        """Nukes the entire PixText widget."""
        [p.delete() for p in s.pixels]
        s.pixels.clear()
        s._highlight_map = {}

# brobord collide grass
# ba_meta require api 9
# ba_meta export plugin
class byBordd(Plugin):
    has_settings_ui = lambda s: True
    show_settings_ui = lambda s, src: s.demo(src)
    """Our demo"""
    def demo(s,src):
        from bauiv1 import (
            containerwidget as cw,
            gettexture as gt,
            imagewidget as iw
        )
        w = cw(
            size=(330,100),
            transition='in_scale',
            scale=4.0,
            background=False,
            scale_origin_stack_offset=getattr(src,'get_screen_space_center',lambda:(0,0))()
        )
        cw(w,on_outside_click_call=lambda:cw(w,transition='out_scale'))

        iw(
            parent=w,
            texture=gt('black'),
            position=(15,30),
            size=(300,50)
        )

        # Demo Text for PixText
        demo_text = "Spaz died again. Nah uh...\nBro picked up all shields in da map,\nKronk was exploded while Zoe watched.\nFull gear blud and Taobao still scored zero"

        # Highlight map for the demo text
        highlight_map = {
            "Spaz": (0.0, 0.9, 0.9),     # Cyan
            "Nah": (1.0, 0.0, 0.0),      # Red
            "shields": (1.0, 0.0, 1.0),  # Magenta Pink
            "map": (1.0, 0.5, 0.0),      # Orange
            "Kronk": (0.0, 1.0, 0.0),    # Green
            "exploded": (1.0, 1.0, 0.0), # Yellow
            "Zoe": (1.0, 0.2, 0.4),      # Pink (close to magenta)
            "Taobao": (1.0, 1.0, 0.6)    # Light Yellow
        }
        # The instance
        m = PixText(
            parent=w,
            position=(0,50),
            color=(1,1,1),
            text=demo_text
        )
        m.highlight(highlight_map)

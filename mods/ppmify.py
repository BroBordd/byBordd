# Copyright 2025 - Solely by BrotherBoard
# Feedback is appreciated - Telegram >> @GalaxyA14user

"""
PPMify v1.0 - Bring your images to the scene

PPMify is now inside BSM library. So this plugin
is deprecated.
"""

from bascenev1 import newnode, getactivity, Activity
from babase import Plugin, pushcall
from threading import Thread
from math import floor
from time import time

class Image:
    __doc__ = """
        The main Image class for displaying a PPM image in the scene.

        It reads the PPM file and creates text nodes for each pixel in a
        separate thread to avoid blocking the game's main thread. Node creation
        is scheduled back on the main thread within the correct activity context.

        Inline usage:
            >>> from ppmify import Image
            >>> img = Image(
            ...     path='image.ppm',
            ...     resolution=(50, 50),
            ...     position=(2, 0.4, -1)
            ... )
            >>> # To remove the image later:
            >>> # img.delete()

        Arguments:
            - path: str
                Path to the PPM P6 image file. Make sure BombSquad has permissions.
            - resolution: tuple[int, int] = (50, 50)
                The target resolution (width, height) for the displayed image.
                The original image will be scaled to fit this resolution, potentially
                stretching if the aspect ratio mismatches.
            - pixel_spacing: float = 0.14
                The distance between the centers of adjacent pixel nodes. This
                effectively controls the overall size of the displayed image.
                Defaults to 0.14 (matches the original code's default 'scale').
            - position: tuple[float, float, float] = (0, 0, 0)
                The world coordinates for the bottom-left corner of the image grid.
            - pixel_node_scale: float = 0.01
                The scale multiplier for individual text nodes (pixels).
                Defaults to 0.01 (matches the original code's default 'pixel_scale').
                The visible size of the text node depends on this scale and the
                'pixel_spacing'.
            - compression: int = 0
                Color compression ratio (0-100). Higher values reduce the number
                of unique colors used, potentially grouping more pixels together.
                Default is 0 (no compression). Values above 98 can result in
                very few colors.
            - display_char: str = '\u25A0'
                The character used for each pixel node. Defaults to a filled square.

        PPM (Portable Pixmap) is a simple image format often used for raw pixel data.
        A P6 PPM file is expected (binary RGB).

        Converting your image file to ppm P6:
            - Using ImageMagick (recommended):
                `magick input_image.png -compress none output_image.ppm`
                (Using `-compress none` ensures a P6 uncompressed format)
            - Online converters may work, but verify they produce P6 format.
    """

    def __init__(
        s,
        path: str,
        resolution: tuple[int, int] = (50, 50),
        pixel_spacing: float = 0.14,
        position: tuple[float, float, float] = (0, 0, 0),
        pixel_node_scale: float = 0.01,
        compression: int = 0,
        display_char: str = '\u25A0'
    ) -> None:
        s.path = path
        s.res = resolution
        s.pspac = pixel_spacing
        s.pos = position
        s.pnsca = pixel_node_scale
        s.cmp = compression
        s.dspc = display_char

        s.pixels: list[Pixel] = []
        s.calculating = False
        s.deleted = False
        s.calc_thread: Thread | None = None
        s.error: str | None = None

        # Kang context
        try:
            s.activity: Activity | None = getactivity()
            if s.activity is None:
                 print("PPMify Warning: Image created outside an active activity. Node creation may fail.")
        except Exception as e:
             print(f"PPMify Error getting activity context: {e}")
             s.activity = None

        s.start_calc()

    def start_calc(s) -> None:
        if s.calculating:
            print("PPMify Warning: Calculation already in progress.")
            return
        if s.activity is None or s.activity.expired:
             print("PPMify Error: Cannot start calculation. No valid activity context captured.")
             s.error = "No valid activity context."
             return

        s.calculating = True
        s.error = None
        s.calc_thread = Thread(target=s.perform_calc)
        s.calc_thread.daemon = True
        s.calc_thread.start()

    def perform_calc(s) -> None:
        """Reads and processes the PPM file data in a separate thread."""
        start_time = time()
        print(f"PPMify: Starting calculation for {s.path}...")

        try:
            tw, th = s.res
            px, py, pz = s.pos
            comp = max(0, min(100, s.cmp))
            color_levels = max(1, 256 - floor(comp * 2.55))

            try:
                with open(s.path, 'rb') as fp:
                    magic = fp.readline().strip()
                    if magic != b'P6':
                        raise ValueError(f"Not a valid PPM P6 file. Magic is {magic}")

                    ow, oh, max_v = None, None, None
                    while ow is None or oh is None or max_v is None:
                        line = fp.readline().strip()
                        if not line or len(line) > 100:
                             raise ValueError("Incomplete or malformed PPM header.")
                        if line.startswith(b'#'): continue

                        parts = line.split()
                        if ow is None and len(parts) >= 2:
                            try:
                                ow, oh = int(parts[0].decode('ascii')), int(parts[1].decode('ascii'))
                                if len(parts) >= 3:
                                    max_v = int(parts[2].decode('ascii'))
                            except ValueError:
                                raise ValueError("Invalid dimensions or max color value.")
                        elif max_v is None and len(parts) >= 1:
                             try:
                                 max_v = int(parts[0].decode('ascii'))
                             except ValueError:
                                 raise ValueError("Invalid max color value.")

                    if ow is None or oh is None or max_v is None:
                         raise ValueError("Could not read dimensions or max color value.")
                    if ow <= 0 or oh <= 0:
                         raise ValueError(f"Invalid dimensions: {ow}x{oh}")
                    if max_v <= 0 or max_v > 255:
                         print(f"PPMify Warning: Max color value is {max_v}, expected 255. Normalizing.")

                    exp_size = ow * oh * 3
                    raw = fp.read(exp_size)
                    if len(raw) != exp_size:
                        raise ValueError(f"Incomplete pixel data. Expected {exp_size}, got {len(raw)}.")

            except FileNotFoundError:
                raise FileNotFoundError(f"Image file not found at {s.path}")
            except ValueError as e:
                 raise ValueError(f"Error reading PPM header: {e}")
            except Exception as e:
                raise IOError(f"Error reading {s.path}: {e}")

            res_pix: dict[tuple[int, int, int], list[tuple[float, float, float]]] = {}
            xsf = ow / tw
            ysf = oh / th

            for ty in range(th):
                for tx in range(tw):
                    ox = min(ow - 1, floor(tx * xsf))
                    oy_raw = floor(ty * ysf)
                    oy = min(oh - 1, max(0, oh - 1 - oy_raw))

                    pix_idx = (oy * ow + ox) * 3
                    r_b, g_b, b_b = raw[pix_idx], raw[pix_idx + 1], raw[pix_idx + 2]

                    r_n = r_b / max_v if max_v > 0 else 0.0
                    g_n = g_b / max_v if max_v > 0 else 0.0
                    b_n = b_b / max_v if max_v > 0 else 0.0

                    rl = min(color_levels - 1, max(0, floor(r_n * color_levels)))
                    gl = min(color_levels - 1, max(0, floor(g_n * color_levels)))
                    bl = min(color_levels - 1, max(0, floor(b_n * color_levels)))

                    color_key = (rl, gl, bl)

                    world_pos = (px + tx * s.pspac,
                                 py + ty * s.pspac,
                                 pz)

                    if color_key not in res_pix: res_pix[color_key] = []
                    res_pix[color_key].append(world_pos)

            final_data: list[tuple[tuple[float, float, float], tuple[float, float, float]]] = []
            div = color_levels - 1 if color_levels > 1 else 1

            for color_key, positions in res_pix.items():
                rl, gl, bl = color_key
                rep_color = (rl / div, gl / div, bl / div)
                for pos in positions:
                     final_data.append((rep_color, pos))

            elapsed = time() - start_time
            print(f"PPMify: Calculation finished in {elapsed:.2f}s. Found {len(res_pix)} colors.")

            # Schedule pixles prolly
            pushcall(lambda: s.on_calc_complete(final_data), from_other_thread=True)

        except (FileNotFoundError, ValueError, IOError) as e:
            print(f"PPMify Error during calculation: {e}")
            s.error = str(e)
            pushcall(lambda: s.on_calc_complete(None, s.error), from_other_thread=True)
        except Exception as e:
            print(f"PPMify Unexpected error during calculation: {e}")
            import traceback
            traceback.print_exc()
            s.error = f"Unexpected error: {e}"
            pushcall(lambda: s.on_calc_complete(None, s.error), from_other_thread=True)

    def on_calc_complete(
        s,
        pixel_data: list[tuple[tuple[float, float, float], tuple[float, float, float]]] | None,
        error_message: str | None = None
    ) -> None:
        """Callback on main thread after calculation."""
        s.calculating = False

        if s.deleted:
            print("PPMify: Image deleted during calculation, skipping node creation.")
            return

        if error_message:
            s.error = error_message
            print(f"PPMify Error creating image: {error_message}")
            return

        if pixel_data is None:
             print(f"PPMify Error: Calculation finished without data or error.")
             s.error = "Calculation finished without data."
             return

        act = s.activity
        if act is None or not act or act.expired:
            print(f"PPMify Error: Cannot create nodes. Activity context gone or invalid.")
            s.error = "Activity context expired before node creation."
            return

        # Get in context and spam pixels
        try:
            with act.context:
                print(f"PPMify: Creating {len(pixel_data)} pixel nodes...")
                s.pixels = []
                for color, pos in pixel_data:
                     clamped_color = (max(0.0, min(1.0, color[0])),
                                      max(0.0, min(1.0, color[1])),
                                      max(0.0, min(1.0, color[2])))

                     z = Pixel(
                        pos=pos,
                        color=clamped_color,
                        scale=s.pnsca,
                        dsp=s.dspc
                     )
                     if z.node:
                         s.pixels.append(z)

                print(f"PPMify: Successfully created {len(s.pixels)} nodes.")

        except Exception as e:
             print(f"PPMify Error during node creation: {e}")
             import traceback
             traceback.print_exc()
             s.error = f"Error creating nodes: {e}"
             s.delete()

    def delete(s) -> None:
        """Deletes all pixel nodes."""
        s.deleted = True

        if s.pixels:
            print(f"PPMify: Deleting {len(s.pixels)} nodes.")
            try:
                for pix in s.pixels:
                    if pix and pix.node and pix.node.exists():
                        pix.delete()
                s.pixels = []
            except Exception as e:
                 print(f"PPMify Error during node deletion: {e}")
                 import traceback
                 traceback.print_exc()
        else:
             print(f"PPMify: Delete called. No nodes to delete yet or creation failed.")

class Pixel:
    __doc__ = """
        Represents a single pixel (text node) in the BombSquad scene.
    """
    def __init__(
        s,
        pos: tuple[float, float, float],
        color: tuple[float, float, float],
        scale: float,
        dsp: str
    ) -> None:
        s.node = None
        try:
            s.node = newnode(
                'text',
                delegate=s,
                attrs={
                    'text': dsp,
                    'position': pos,
                    'in_world': True,
                    'color': color,
                    'shadow': 0.0,
                    'flatness': 1.0,
                    'scale': scale
                }
            )
        except Exception as e:
            print(f"PPMify Error: Could not create pixel node at {pos}: {e}")
            # traceback.print_exc()

    def delete(s) -> None:
        """Deletes the associated scene node."""
        if s.node and s.node.exists():
            try:
                s.node.delete()
            except Exception as e:
                 print(f"PPMify Error during pixel node deletion: {e}")
                 # traceback.print_exc()
            s.node = None

# ba_meta require api 9
# ba_meta export plugin
class byBordd(Plugin): pass

# Copyright 2025 - Solely by BrotherBoard
# Feedback is appreciated - Telegram >> @GalaxyA14user

"""
BSM v2.0 - The BombSquadMedia Library

Provides functionality to display static images (PPM format) and play video
sequences (PPM frames with a stamps.json timing file) within the BombSquad
scene using a grid of text nodes as pixels.

Supports concurrent loading of media data and offers playback controls
for video media, including speed, looping, and rotation of the source media.

Classes:
    Pixel: Represents a single text node used as a pixel.
    Image: Handles concurrent loading of a single PPM image with optional resizing and rotation.
    Video: Handles concurrent loading and playback of a video sequence
           from a folder containing PPM frames and a stamps.json file, with
           optional resizing, rotation, speed control, and looping.
    Screen: Manages a grid of Pixel nodes and loads/displays Image or Video media.
            Provides methods to stop playback, clear, fill, and set the opacity of the screen.
            Displays a simple colored "BSM" placeholder on creation.
"""

from os import makedirs
from os.path import join, isabs, exists
from json import load, JSONDecodeError
from math import floor
from bascenev1 import (
    timer as tick,
    newnode,
    Call,
    getactivity,
    Activity
)
from babase import (
    Plugin,
    env,
    pushcall
)
from threading import Thread
from time import time
from traceback import print_exc

ROOT = lambda: join(env()['python_directory_user'], 'BSM')

try:
    makedirs(ROOT(), exist_ok=True)
except Exception as e:
    print(f"BSM Error: Failed to create root directory {ROOT()}: {e}")

class Pixel:
    __doc__ = """
        Represents a single pixel (text node) in the BombSquad scene.

        Each Pixel instance corresponds to a single text node used to
        display a colored character, forming part of the overall image
        or video frame on a Screen.

        Attributes:
            node: The bascenev1.Node of type 'text' representing the pixel.
                  None if node creation failed.
    """
    def __init__(
        s,
        pos: tuple[float, float, float],
        color: tuple[float, float, float],
        scale: float,
        dsp: str
    ) -> None:
        """
        Initializes a Pixel instance and creates its text node.

        Args:
            pos: The (x, y, z) position of the pixel node in world coordinates.
            color: The initial (r, g, b) color tuple for the pixel node.
            scale: The scale of the pixel node.
            dsp: The character string to display for the pixel (e.g., '\u25A0').
        """
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
            print(f"BSMPixel Error: Could not create node at {pos}: {e}")

    def set(s,c) -> None:
        """
        Sets the color of the pixel node.

        Args:
            c: The (r, g, b) color tuple to set.
        """
        if s.node and s.node.exists():
            s.node.color = c

    def delete(s) -> None:
        """
        Deletes the pixel node from the scene.
        """
        if s.node and s.node.exists():
            try:
                s.node.delete()
            except Exception as e:
                 print(f"BSMPixel Error during node deletion: {e}")
            s.node = None

class Image:
    __doc__ = """
        Handles concurrent loading of a single PPM image file.

        The Image class is used to load static images onto a Screen.
        It specifically requires PPM (Portable Pixmap) files in P6 binary format.
        The image file should be placed within the ROOT() directory or a subfolder
        thereof, and the 'path' argument should be relative to ROOT().

        To prepare a standard image file (like JPG, PNG) for use with Image:
        1.  Convert your image to PPM (P6 binary format).
            Tools like ImageMagick (magick) or FFmpeg can do this.
            Example using ImageMagick:
            ~$ magick input.png -type TrueColor -strip -colorspace sRGB <BSM_ROOT>/my_image.ppm
            Replace <BSM_ROOT> with the actual path to your BombSquad user directory's BSM folder.
        2.  Place the resulting .ppm file in your BombSquad user directory's BSM folder
            or a subfolder within it.

        Loading Examples:
            - If my_image.ppm is directly in the BSM folder
            >>> img = Image(path='my_image.ppm', resolution=(100, 50))

            - If another_image.ppm is in BSM/images/
            >>> img2 = Image(path='images/another_image.ppm', resolution=(100, 50), rotate=90)

        The image data is loaded and processed in a separate thread to
        avoid blocking the main BombSquad thread. A callback can be
        registered to be notified when processing is complete.

        Attributes:
            path: The path to the PPM file (relative to ROOT()).
            res: The target resolution (width, height) for resizing, or None.
            rotate_angle: The rotation angle (0, 90, 180, 270) applied to the source data.
            data: The processed pixel data (list of color tuples) once complete.
                  None if processing failed or not yet complete.
            processing_complete: True if processing has finished (successfully or with error).
            error: An error message string if processing failed, otherwise None.
            on_data_ready_callback: A function to call when processing is complete.
    """
    def __init__(
        s,
        path: str,
        resolution: tuple[int,int] = None,
        rotate: int = 0
    ) -> None:
        """
        Initializes an Image instance and starts background processing.

        Args:
            path: The path to the PPM file (relative to ROOT()).
            resolution: An optional tuple (width, height) to resize the image to.
                        If None, the original PPM resolution is used.
            rotate: The rotation angle for the image data (0, 90, 180, 270) clockwise.
                    Defaults to 0.
        """
        s.path = path
        s.res = resolution
        s.rotate_angle = rotate
        s.data = None
        s.processing_complete = False
        s.error = None
        s.on_data_ready_callback = None

        s.start_processing()

    def start_processing(s) -> None:
        """Initiates background thread for image processing."""
        act = getactivity()
        if act is None or act.expired:
             print("BSMImage Warning: No active activity when starting processing.")

        thread = Thread(target=s._perform_calc)
        thread.daemon = True
        thread.start()

    def _perform_calc(s) -> None:
        """Internal method run in a separate thread to call the calc function."""
        try:
            pa = calc(s.path, s.res, s.rotate_angle)
            pushcall(lambda: s._on_calc_complete(pa), from_other_thread=True)
        except Exception as e:
            error_msg = f"Error processing image {s.path} with rotation {s.rotate_angle}: {e}"
            print(f"BSMImage Error: {error_msg}")
            pushcall(lambda: s._on_calc_complete(None, error_msg), from_other_thread=True)

    def _on_calc_complete(s, pa, err = None) -> None:
        """Callback executed in the main thread when background processing finishes."""
        s.data = pa
        s.error = err
        s.processing_complete = True

        if s.on_data_ready_callback:
            act = getactivity()
            if act and not act.expired:
                try:
                    with act.context:
                        s.on_data_ready_callback(s)
                except Exception as e:
                    print(f"BSMImage Error in callback: {e}")
                    print_exc()
            else:
                 print("BSMImage Warning: No valid activity context for callback.")


    def set_on_data_ready_callback(s, callback) -> None:
        """
        Sets a callback function to be called when the image data is ready.

        Args:
            callback: A function that takes the Image instance as its argument.
                      Called in the main BombSquad thread within an activity context.
        """
        s.on_data_ready_callback = callback
        if s.processing_complete:
             act = getactivity()
             if act and not act.expired:
                 try:
                    with act.context:
                        s.on_data_ready_callback(s)
                 except Exception as e:
                    print(f"BSMImage Error in callback: {e}")
                    print_exc()
             else:
                 print("BSMImage Warning: No valid activity context for immediate callback.")

class Video:
    __doc__ = """
        Handles concurrent loading and playback of a video sequence.

        The Video class loads a sequence of PPM frames from a specified folder
        located inside the ROOT() directory. This folder must contain:
        1.  PPM frame files (e.g., frame_0000.ppm, frame_0001.ppm, ...).
        2.  A 'stamps.json' file mapping cumulative timestamps (in seconds)
            to the corresponding frame filenames.

        The 'stamps.json' file should be a JSON object where keys are string
        representations of cumulative timestamps (e.g., "0.0", "0.04", "0.08")
        and values are the corresponding frame filenames (e.g., "frame_0000.ppm").
        Timestamps should be sorted in ascending order.

        To prepare a standard video file (like GIF, MP4) for use with Video:
        1.  Convert your video into a sequence of PPM frames.
            Tools like ImageMagick (magick) or FFmpeg can do this.
            Example using ImageMagick for a GIF:
            ~$ magick input.gif -type TrueColor -strip -colorspace sRGB <BSM_ROOT>/my_video_folder/frame_%04d.ppm
            Example using FFmpeg for MP4:
            ~$ ffmpeg -i input.mp4 -pix_fmt rgb24 <BSM_ROOT>/my_video_folder/frame_%04d.ppm
            Replace <BSM_ROOT> with the actual path to your BombSquad user directory's BSM folder.
        2.  Generate a 'stamps.json' file containing the cumulative timestamp for each frame.
            This file is a JSON object where keys are timestamp strings and values are
            the corresponding frame filenames. Timestamps should be in seconds.
            Example structure: {"0.0": "frame_0000.ppm", "0.04": "frame_0001.ppm", ...}
            You might need a custom script or tool to generate this file based on your
            video's frame rate or original frame delays. For GIFs, ImageMagick's identify
            can provide frame delays, which can then be processed (e.g., with awk)
            to calculate cumulative timestamps.
        3.  Place the resulting .ppm files and the stamps.json file into a
            subfolder within your BombSquad user directory's BSM folder.

        Example File Structure:
            <BombSquad User Directory>/BSM/my_video/stamps.json
            <BombSquad User Directory>/BSM/my_video/frame_0000.ppm
            <BombSquad User Directory>/BSM/my_video/frame_0001.ppm
            ...

        Loading Example:
            # If your video files are in <User Dir>/BSM/my_video/
            video = Video(folder_name='my_video', resolution=(80, 40), rotate=180)
            my_screen.load(video, speed=1.0, loop=True)

        Loading and processing of individual frames happen concurrently
        in background threads. Playback is managed by a timer in the
        main BombSquad thread.

        Attributes:
            folder_name: The name of the folder (relative to ROOT()) containing video files.
            res: The target resolution (width, height) for resizing frames, or None.
            rotate_angle: The rotation angle (0, 90, 180, 270) applied to each frame data.
            data: A dictionary {timestamp: pixel_array} storing loaded frame data.
            timestamp_map: A dictionary {timestamp: filename} read from stamps.json.
            frames_to_process: Total number of frames to load.
            processed_frames: Number of frames successfully processed so far.
            error: An error message string if loading/processing failed, otherwise None.
            processing_complete: True if all frames have finished processing.
            on_data_ready_callback: A function to call when all frame data is loaded.
            video_play_timer: A boolean/None indicator for active playback.
            current_video_frame_index: The index of the currently displayed frame in the sorted timestamps.
            video_playback_speed: The multiplier for playback speed (1.0 is normal).
            video_loop: True if the video should loop when it reaches the end.
    """
    def __init__(
        s,
        folder_name: str,
        resolution: tuple[int, int] = None,
        rotate: int = 0
    ) -> None:
        """
        Initializes a Video instance and starts background loading of frames.

        Args:
            folder_name: The name of the folder located inside ROOT()
                         This folder must contain 'stamps.json' and the frame files.
            resolution: An optional tuple (width, height) to resize each frame to.
                        If None, the original PPM resolution is used.
            rotate: The rotation angle for each frame's data (0, 90, 180, 270) clockwise.
                    Defaults to 0.
        """
        s.folder_name = folder_name
        s.res = resolution
        s.rotate_angle = rotate
        s.data = {}
        s.timestamp_map: dict[float | int, str] = {}
        s.frames_to_process = 0
        s.processed_frames = 0
        s.error = None
        s.processing_complete = False
        s.on_data_ready_callback = None

        s.start_processing()

    def start_processing(s) -> None:
        """Initiates background process to read timestamps and load frames."""
        act = getactivity()
        if act is None or act.expired:
             print("BSMVideo Warning: No active activity when starting processing.")

        timestamp_map = s._read_timestamp_map_from_folder()
        if timestamp_map is None:
            s.error = f"Failed to read timestamps from folder '{s.folder_name}'"
            s.processing_complete = True
            print(f"BSMVideo Error: {s.error}")
            s._on_processing_complete()
            return

        s.timestamp_map = timestamp_map
        s.frames_to_process = len(s.timestamp_map)

        if s.frames_to_process == 0:
            print("BSMVideo: No frames found in stamps.json, complete.")
            s.processing_complete = True
            s._on_processing_complete()
            return

        print(f"BSMVideo: Start processing {s.frames_to_process} frames from folder '{s.folder_name}'.")
        s.processed_frames = 0
        s.error = None
        s.processing_complete = False

        for timestamp, filename in s.timestamp_map.items():
            thread = Thread(target=s._process_frame, args=(timestamp, filename, s.res, s.rotate_angle))
            thread.daemon = True
            thread.start()

    def _read_timestamp_map_from_folder(s) -> dict[float | int, str] | None:
        """Reads and returns the timestamp map from stamps.json in the folder."""
        folder_full_path = join(ROOT(), s.folder_name)
        json_path = join(folder_full_path, 'stamps.json')
        try:
            if not exists(json_path):
                 print(f"BSMVideo Error: stamps.json not found in folder '{s.folder_name}'.")
                 return None

            with open(json_path, 'r') as f:
                timestamp_map = load(f)
                converted_map = {}
                for key, value in timestamp_map.items():
                     try:
                         if '.' in key:
                             converted_key = float(key)
                         else:
                             converted_key = int(key)
                     except ValueError:
                         converted_key = key
                     converted_map[converted_key] = value
                return converted_map

        except FileNotFoundError:
            print(f"BSMVideo Error: stamps.json not found at '{json_path}'.")
            return None
        except JSONDecodeError:
            print(f"BSMVideo Error: Could not decode '{json_path}'. Is it valid JSON?")
            return None
        except Exception as e:
            print(f"BSMVideo Error reading '{json_path}': {e}")
            return None

    def _process_frame(s, timestamp, filename, res, rotate_angle) -> None:
        """Internal method run in a separate thread to load and process a single frame."""
        frame_relative_path = join(s.folder_name, filename)
        try:
            pa = calc(frame_relative_path, res, rotate_angle)
            pushcall(lambda: s._on_frame_processed(timestamp, pa), from_other_thread=True)
        except Exception as e:
            error_msg = f"Error frame '{frame_relative_path}' at {timestamp} with rotation {rotate_angle}: {e}"
            print(f"BSMVideo Error: {error_msg}")
            pushcall(lambda: s._on_frame_processed(timestamp, None, error_msg), from_other_thread=True)

    def _on_frame_processed(
        s,
        t,
        pa,
        err = None
    ) -> None:
        """Callback executed in the main thread when a single frame processing finishes."""
        s.processed_frames += 1

        if err:
            if s.error is None:
                s.error = err
            print(f"BSMVideo: Frame {t} failed: {err}")

        if pa is not None:
            s.data[t] = pa

        if s.processed_frames >= s.frames_to_process:
            s.processing_complete = True
            print(f"BSMVideo: All {s.frames_to_process} frames processed.")
            s._on_processing_complete()

    def _on_processing_complete(s) -> None:
        """Callback executed in the main thread when all video frames are processed."""
        if s.error:
            print(f"BSMVideo: Video processing finished with errors: {s.error}")
        else:
            print("BSMVideo: Video processing finished successfully.")

        if s.on_data_ready_callback:
            act = getactivity()
            if act and not act.expired:
                try:
                    with act.context:
                        s.on_data_ready_callback(s)
                except Exception as e:
                    print(f"BSMVideo Error in callback: {e}")
                    print_exc()
            else:
                 print("BSMVideo Warning: No valid activity context for callback.")


    def set_on_data_ready_callback(s, callback) -> None:
        """
        Sets a callback function to be called when all video frame data is ready.

        Args:
            callback: A function that takes the Video instance as its argument.
                      Called in the main BombSquad thread within an activity context.
        """
        s.on_data_ready_callback = callback
        if s.processing_complete:
             act = getactivity()
             if act and not act.expired:
                 try:
                    with act.context:
                        s.on_data_ready_callback(s)
                 except Exception as e:
                    print(f"BSMVideo Error in callback: {e}")
                    print_exc()
             else:
                 print("BSMVideo Warning: No valid activity context for immediate callback.")


    def delete(s) -> None:
        """Cleans up the Video instance."""
        print("BSMVideo: Delete called.")
        s.timestamp_map = {}
        s.data = {}
        s.on_data_ready_callback = None


class Screen:
    __doc__ = """
        Manages a grid of Pixel nodes and displays Image or Video media on them.

        The Screen class creates and positions the grid of text nodes that
        act as pixels. It handles loading media onto this grid and managing
        video playback, including speed and looping. Provides methods to
        stop playback, clear, fill, and set the opacity of the screen.
        Displays a simple colored "BSM" placeholder on creation if the
        resolution is sufficient.

        Attributes:
            pos: The (x, y, z) position of the bottom-left corner of the screen grid.
            res: The resolution (width, height) of the screen grid (number of pixels).
            scale: The scale of individual pixel nodes.
            spacing_val: The spacing between pixel nodes ('auto' or a float value).
            char: The character used for pixel nodes.
            pixels: A list of Pixel instances forming the screen grid.
            media: The currently loaded Image or Video instance.
            video_data: The pixel data for video frames (from the loaded Video instance).
            video_timestamps: Sorted list of timestamps for video frames.
            video_play_timer: A boolean/None indicator for active playback.
            current_video_frame_index: The index of the currently displayed frame in the sorted timestamps.
            video_playback_speed: The current playback speed multiplier.
            video_loop: True if the video should loop when it reaches the end.
    """
    def __init__(
        s,
        position: tuple[float, float, float] = (-2,1,1),
        resolution: tuple[int, int] = (100,50),
        scale: float = 0.01,
        spacing: float | str = 'auto',
        char: str = '\u25A0',
        media: Image | Video = None
    ) -> None:
        """
        Initializes a Screen instance and creates its pixel grid.

        Args:
            position: The (x, y, z) position of the bottom-left corner of the screen.
                      Defaults to (-2, 1, 1).
            resolution: The resolution (width, height) of the screen grid.
                        Defaults to (100, 50).
            scale: The scale of individual pixel nodes. Defaults to 0.01.
            spacing: The spacing between pixel nodes. 'auto' calculates spacing
                     based on scale, otherwise a float value can be provided.
                     Defaults to 'auto'.
            char: The character used for pixel nodes. Defaults to a solid block '\u25A0'.
            media: An optional Image or Video instance to load immediately upon creation.
                   Defaults to None.
        """
        s.pos = position
        s.res = resolution
        s.scale = scale
        s.spacing_val = spacing
        s.char = char
        s.media = None
        s.video_data = None
        s.video_timestamps = None
        s.video_play_timer = None
        s.current_video_frame_index = 0
        s.video_playback_speed = 1.0
        s.video_loop = False

        px,py,pz = position
        rx,ry = resolution
        sc = scale
        sp = s.spacing_val
        if sp == 'auto': sp = sc * 13.5

        s.pixels = []
        act = getactivity()
        if act and not act.expired:
             try:
                with act.context:
                    for i in range(ry):
                        for j in range(rx):
                            p_pos = (px + j * sp, py + i * sp, pz)
                            p = Pixel(
                                pos=p_pos,
                                color=(0,0,0),
                                scale=sc,
                                dsp=char
                            )
                            if p.node:
                                s.pixels.append(p)
                            else:
                                print(f"BSMScreen Warning: Failed to create pixel node at {p_pos}")

                    s.bsm()

             except Exception as e:
                 print(f"BSMScreen Error creating pixel nodes or drawing placeholder: {e}")
                 print_exc()
                 s.delete()
        else:
             print("BSMScreen Warning: No active activity when creating screen. Pixel nodes not created.")

        print (f"BSMScreen: New Screen at {position} with resolution {resolution}")
        if media: s.load(media)

    def bsm(o) -> None:
        if o.res[0] < 11 or o.res[1] < 3: return
        w,h=o.res;lw,lh,ls=3,3,1;tw,th=(lw*3)+(ls*2),lh;sx,sy=(w-tw)//2,(h-th)//2;p=o.pixels
        C=[(1.,0,0),(0,1.,0),(0,0,1.)]
        L=[[0,3,4,5,6,7,8],[1,2,4,6,7],[0,1,2,3,4,5,6,8]]
        lo=[0,lw+ls,(lw+ls)*2]
        for li in range(3):
            for ri in L[li]:
                so=(lh-1-(ri//lw))*w+(ri%lw)
                si=(sy*w)+sx+lo[li]+so
                if 0<=si<len(p)and p[si]:p[si].set(C[li])

    def load(s, media: Image | Video, speed: float = 1.0, loop: bool = False) -> None:
        """
        Loads an Image or Video onto the screen.

        If a Video is loaded, playback starts automatically.
        This will replace the "BSM" placeholder.

        Args:
            media: The Image or Video instance to load.
            speed: Playback speed multiplier for videos (1.0 is normal).
                   Defaults to 1.0. Must be > 0.
            loop: Whether the video should loop when it finishes. Defaults to False.
        """
        s.media = media
        s.video_data = None
        s.video_timestamps = None
        s._stop_video_playback()

        s.video_playback_speed = max(0.01, speed)
        s.video_loop = loop

        s.clear()

        if media.processing_complete:
            s._load_data_to_pixels(media)
        else:
            print(f"BSMScreen: Media data not ready, waiting for callback.")
            media.set_on_data_ready_callback(s._on_media_data_ready)

    def _on_media_data_ready(s, media: Image | Video) -> None:
        """Callback executed when the loaded media's data is ready."""
        if media.error:
            print(f"BSMScreen: Media loading failed with error: {media.error}")
            s.fill((1.0, 0.0, 0.0))
            print(f"BSMScreen: Displaying red error screen due to media loading failure.")
            return

        if s.media is not media:
            print("BSMScreen Warning: Received callback for media that is no longer loaded.")
            return

        print(f"BSMScreen: Media data ready, loading onto screen.")
        s._load_data_to_pixels(media)

    def _load_data_to_pixels(s, media: Image | Video) -> None:
        """Loads the processed media data onto the pixel grid."""
        act = getactivity()
        if act is None or act.expired:
            print("BSMScreen Error: Cannot load data. Activity context gone or invalid.")
            return

        try:
            with act.context:
                if isinstance(media, Image):
                    if media.data and len(media.data) == len(s.pixels):
                        for i, color in enumerate(media.data):
                            s.pixels[i].set(color)
                    elif media.data is None:
                         print("BSMScreen Error: Image data is None.")
                         s.fill((1.0, 0.0, 0.0))
                    else:
                        print(f"BSMScreen Error: Image data size ({len(media.data)}) mismatch with pixel count ({len(s.pixels)}).")
                        s.fill((1.0, 0.0, 0.0))

                elif isinstance(media, Video):
                    s.video_data = media.data
                    if s.video_data:
                        s.video_timestamps = sorted(s.video_data.keys())
                        s.current_video_frame_index = 0
                        s._start_video_playback()
                    else:
                        print("BSMScreen Error: Video data is empty.")
                        s.fill((1.0, 0.0, 0.0))

                else:
                    print(f"BSMScreen Error: Cannot load unknown media type {type(media)}")
                    s.fill((1.0, 0.0, 0.0))

        except Exception as e:
            print(f"BSMScreen Error loading data: {e}")
            print_exc()
            s.fill((1.0, 0.0, 0.0))

    def stop(s) -> None:
        """
        Stops any currently playing video on the screen.
        """
        print("BSMScreen: Stop playback called.")
        s.video_play_timer = None

    def clear(s) -> None:
        """
        Clears the screen by setting all pixels to black.
        """
        print("BSMScreen: Clear called.")
        s.stop()
        s.fill((0.0, 0.0, 0.0))
        s.bsm()

    def fill(s, color: tuple[float, float, float]) -> None:
        """
        Fills the entire screen with a single color.

        Args:
            color: The (r, g, b) color tuple to fill the screen with (0.0 to 1.0).
        """
        print(f"BSMScreen: Filling screen with color {color}.")
        act = getactivity()
        if act and not act.expired:
            try:
                with act.context:
                    for pix in s.pixels:
                        if pix: pix.set(color)
            except Exception as e:
                print(f"BSMScreen Error filling screen: {e}")
                print_exc()
        else:
            print("BSMScreen Warning: Cannot fill screen. Activity context gone or invalid.")

    def set_opacity(s, value: float) -> None:
        """
        Sets the opacity of all pixels on the screen.

        Args:
            value: The opacity value (0.0 for fully transparent, 1.0 for fully opaque).
        """
        print(f"BSMScreen: Setting opacity to {value}.")
        act = getactivity()
        if act and not act.expired:
            try:
                with act.context:
                    for pix in s.pixels:
                        if pix and pix.node:
                            pix.node.opacity = max(0.0, min(1.0, value)) # Clamp value between 0.0 and 1.0
            except Exception as e:
                print(f"BSMScreen Error setting opacity: {e}")
                print_exc()
        else:
            print("BSMScreen Warning: Cannot set opacity. Activity context gone or invalid.")

    def _start_video_playback(s) -> None:
        """Starts the video playback timer."""
        s.video_play_timer = True
        s._play_next_video_frame()

    def _stop_video_playback(s) -> None:
        """Stops the video playback by setting the timer indicator to None."""
        s.video_play_timer = None

    def _play_next_video_frame(s) -> None:
        """Displays the next video frame and schedules the subsequent one."""
        if s.video_play_timer is None or not s.video_timestamps or not s.pixels:
             if s.video_play_timer is not None:
                 print("BSMScreen Warning: Playback called with no data or pixels or timer stopped.")
             s._stop_video_playback()
             return

        if s.current_video_frame_index < len(s.video_timestamps):
            ts = s.video_timestamps[s.current_video_frame_index]
            frame_data = s.video_data.get(ts)

            if frame_data and len(frame_data) == len(s.pixels):
                act = getactivity()
                if act and not act.expired:
                     try:
                         with act.context:
                            for i, color in enumerate(frame_data):
                                s.pixels[i].set(color)
                     except Exception as e:
                         print(f"BSMScreen Error updating pixels for frame {ts}: {e}")
                         print_exc()
                         s._stop_video_playback()
                         return
                else:
                    print(f"BSMScreen Error: Activity expired during video playback.")
                    s._stop_video_playback()
                    return

                s.current_video_frame_index += 1

                if s.current_video_frame_index < len(s.video_timestamps):
                    next_ts = s.video_timestamps[s.current_video_frame_index]
                    delay = next_ts - ts
                    if delay < 0:
                         print(f"BSMScreen Warning: Negative video frame delay ({delay}), using 0.")
                         delay = 0

                    actual_delay = delay / s.video_playback_speed
                    if actual_delay < 0: actual_delay = 0

                    tick(actual_delay, Call(s._play_next_video_frame))
                else:
                    print("BSMScreen: Video playback complete.")
                    if s.video_loop:
                        print("BSMScreen: Looping video.")
                        s.current_video_frame_index = 0
                        s._start_video_playback()
                    else:
                        s._stop_video_playback()

            else:
                print(f"BSMScreen Error: Frame data for timestamp {ts} invalid or size mismatch.")
                s._stop_video_playback()
        else:
             print("BSMScreen Warning: _play_next_video_frame called with invalid index.")
             s._stop_video_playback()


    def delete(s) -> None:
        """Cleans up the Screen instance and its pixel nodes."""
        print("BSMScreen: Delete called.")
        s._stop_video_playback()
        if s.pixels:
            for pix in s.pixels:
                if pix: pix.delete()
            s.pixels.clear()
        s.media = None
        s.video_data = None
        s.video_timestamps = None
        s.video_play_timer = None


def calc(p, t_res = None, rotate_angle: int = 0):
    """
    Loads and processes a PPM image file, handling resizing and rotation.

    Reads a PPM (Portable Pixmap, P6 binary format) file from the specified
    path (relative to ROOT()), extracts pixel data, and optionally resizes
    and rotates it to a target resolution using nearest-neighbor sampling.

    Args:
        p: The path to the PPM file (relative to ROOT()).
        t_res: An optional tuple (target_width, target_height) for resizing.
               If None, the original image resolution is used.
        rotate_angle: The rotation angle in degrees (0, 90, 180, 270) clockwise.
                      Defaults to 0.

    Returns:
        A list of (r, g, b) color tuples representing the pixel data for the
        target resolution after rotation. Returns None if loading or processing failed.
        The list is ordered row by row, from bottom-left to top-right, matching
        the Screen's pixel layout.
    """
    p_full = join(ROOT(), p)
    ow, oh = 0, 0

    try:
        with open(p_full, 'rb') as f:
            magic = f.readline().strip()
            if magic != b'P6':
                print(f"BSMCalc Error: Bad magic {magic}")
                return None

            mv = None
            while ow == 0 or oh == 0 or mv is None:
                line = f.readline().strip()
                if not line or len(line) > 100:
                     print("BSMCalc Error: Bad header.")
                     return None
                if line.startswith(b'#'): continue

                parts = line.split()
                if ow == 0 and len(parts) >= 2:
                    try:
                        ow, oh = int(parts[0].decode('ascii')), int(parts[1].decode('ascii'))
                        if len(parts) >= 3:
                            mv = int(parts[2].decode('ascii'))
                    except ValueError:
                        print("BSMCalc Error: Bad dims/max.")
                        return None
                elif mv is None and len(parts) >= 1:
                     try:
                         mv = int(parts[0].decode('ascii'))
                     except ValueError:
                         print("BSMCalc Error: Bad max val.")
                         return None

            if ow <= 0 or oh <= 0 or mv is None:
                 print(f"BSMCalc Error: No dims/max {ow}x{oh} {mv}.")
                 return None

            if mv <= 0 or mv > 255:
                 print(f"BSMCalc Warning: Max val {mv}, expected 255. Normalizing.")

            exp_size = ow * oh * 3
            r = f.read(exp_size)
            if len(r) != exp_size:
                print(f"BSMCalc Error: Bad data size. Exp {exp_size}, got {len(r)}.")
                return None

    except FileNotFoundError:
        print(f"BSMCalc Error: File not found {p_full}")
        return None
    except Exception as e:
        print(f"BSMCalc Error reading {p_full}: {e}")
        return None

    if t_res is None:
        tw, th = ow, oh
    else:
        tw, th = t_res
        if tw <= 0 or th <= 0:
            print(f"BSMCalc Error: Bad target res {t_res}")
            return None

    pa = [None] * (tw * th)

    valid_angles = [0, 90, 180, 270]
    if rotate_angle not in valid_angles:
        print(f"BSMCalc Warning: Unsupported rotation angle {rotate_angle}. Using 0 degrees.")
        rotate_angle = 0

    for ty in range(th):
        for tx in range(tw):
            ox, oy = 0, 0

            if rotate_angle == 0:
                ox = floor(tx * (ow / tw))
                oy_raw = floor(ty * (oh / th))
                oy = oh - 1 - oy_raw

            elif rotate_angle == 90:
                ox = floor(ty * (ow / th))
                oy_raw = floor(tx * (oh / tw))
                oy = oh - 1 - oy_raw

            elif rotate_angle == 180:
                ox = ow - 1 - floor(tx * (ow / tw))
                oy_raw = floor(ty * (oh / th))
                oy = oh - 1 - (oh - 1 - oy_raw)

            elif rotate_angle == 270:
                ox = ow - 1 - floor(ty * (ow / th))
                oy_raw = floor(tx * (oh / tw))
                oy = oh - 1 - oy_raw

            ox = max(0, min(ow - 1, ox))
            oy = max(0, min(oh - 1, oy))

            pix_idx = (oy * ow + ox) * 3
            if pix_idx + 2 >= len(r) or pix_idx < 0:
                 print(f"BSMCalc Error: Calculated pixel index out of bounds: {pix_idx}. ow={ow}, oh={oh}, ox={ox}, oy={oy}, len(r)={len(r)}. Target (tx,ty)={(tx,ty)}, Rotate={rotate_angle}.")
                 pa[ty * tw + tx] = (0, 0, 0)
                 continue

            r_b, g_b, b_b = r[pix_idx], r[pix_idx + 1], r[pix_idx + 2]

            r_n = r_b / mv if mv > 0 else 0.0
            g_n = g_b / mv if mv > 0 else 0.0
            b_n = b_b / mv if mv > 0 else 0.0

            arr_idx = ty * tw + tx

            pa[arr_idx] = (r_n, g_n, b_n)

    return pa

# brobord collide grass
# ba_meta require api 9
# ba_meta export plugin
class byBordd(Plugin): pass


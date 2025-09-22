# Copyright 2025 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @BroBordd

"""
Kang v1.0 - Simple roster grabber

I made this to understand how stuff work.
Will be used by Finder to collect users, soon.
"""

from babase import (
    app,
    Plugin,
    app_instance_uuid as U
)
from socket import (
    socket,
    AF_INET,
    SOCK_DGRAM
)
from json import dumps, loads
from threading import Thread
from time import sleep, time
from random import randint

spec = {"s":"{\"n\":\"Kanger\",\"a\":\"\",\"sn\":\"\"}","d":"69"*20}
auth = {'b':app.env.engine_build_number,'tk':'','ph':''}
rost = None

def kang(i,p):
    Thread(target=lambda:_kang((i,p))).start()

def _kang(a):
    sock = socket(AF_INET,SOCK_DGRAM)
    sock.settimeout(3)
    me = f'{(71+randint(0,150)):02x}'

    p = lambda h,e=b'': (
        (z:=q(h.replace(' ',''))+e),
        sock.sendto(z,a)
    )
    g = lambda b: sock.recvfrom(b)[0]
    j = lambda h: dumps(h).encode('utf-8')
    q = bytes.fromhex

    p(f'18 21 00 {me}',U().encode()) # 1
    ok = f'{g(3)[1]:02x}' # 2
    sr = g(1024) # 3

    p(f'24 {ok} 10 21 00',j(spec)) # 4
    p(f'24 {ok} 11 f0 ff f0 ff 00 12',j(auth)) # 5
    p(f'24 {ok} 11 f1 ff f0 ff 00 15',j({})) # 6
    p(f'24 {ok} 11 f2 ff f0 ff 00 03') # 7
    ko = g(1024) # 8
    kk = g(9) # 9

    # --- Start: Definitive Roster Grabbing Logic ---

    # Message type IDs from source code/captures
    SERVER_RELIABLE_MESSAGE = 0x25
    BA_SCENEPACKET_MESSAGE = 0x11
    BA_MESSAGE_MULTIPART = 0x0d
    BA_MESSAGE_MULTIPART_END = 0x0e
    BA_MESSAGE_PARTY_ROSTER = 0x09

    # State variables
    roster_parts = bytearray()
    collecting_roster = False # Use a more specific state name
    global rost
    rost = None

    print("Listening for roster...")
    start_time = time()

    try:
        # A short but reasonable timeout to wait for the roster
        while time() - start_time < 5.0:
            packet = g(1024)

            # Basic validation for the packet structure
            if not packet or len(packet) < 9:
                continue

            # Check for the correct reliable message wrapper from the server
            if packet[0] == SERVER_RELIABLE_MESSAGE and packet[2] == BA_SCENEPACKET_MESSAGE:
                payload_type = packet[8]
                payload_data = packet[9:]

                # Case 1: A simple, non-split roster message
                if payload_type == BA_MESSAGE_PARTY_ROSTER:
                    print(" ✓ Roster received in a single packet.")
                    # If we were collecting parts, that was an error. Reset.
                    collecting_roster = False
                    roster_parts.clear()
                    # Decode the payload directly
                    json_string = payload_data.rstrip(b'\x00').decode('utf-8')
                    rost = loads(json_string)
                    break # Success

                # Case 2: A multi-part message chunk
                elif payload_type == BA_MESSAGE_MULTIPART:
                    # Check if this is the START of a roster multipart message
                    if payload_data and payload_data[0] == BA_MESSAGE_PARTY_ROSTER:
                        print(" multipart message detected. Collecting parts...")
                        collecting_roster = True
                        roster_parts.clear() # Ensure we start with a clean buffer
                        roster_parts.extend(payload_data[1:]) # Add first chunk, skipping the roster ID
                    # Otherwise, if we are already collecting, this is a middle part
                    elif collecting_roster:
                        roster_parts.extend(payload_data)
                    # If neither, it's a multipart for something else. Ignore it.

                # Case 3: The end of a multi-part message
                elif payload_type == BA_MESSAGE_MULTIPART_END:
                    # Only process this if we were actively collecting roster parts
                    if collecting_roster:
                        print(" ✓ Final part received. Reassembling...")
                        roster_parts.extend(payload_data)

                        # Now that we have all parts, decode the complete JSON
                        json_string = roster_parts.rstrip(b'\x00').decode('utf-8')
                        rost = loads(json_string)
                        # Reset state and exit loop on success
                        collecting_roster = False
                        break

    except Exception as e:
        print(f"Error while processing packets: {e}")
        # Reset state on any error to be safe for next attempt
        roster_parts.clear()
        collecting_roster = False

    p(f'20 {ok}') # -1
    sock.close()
    return rost

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s):
        """
        >>> from kang import kang
        >>> rost = kang('192.168.111.1',43269)
        """
        # DEBUG
        # __import__('bascenev1').connect_to_party = lambda address,port,print_progress=0:kang(address,port)

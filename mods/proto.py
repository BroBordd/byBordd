# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only

import socket
import struct
import babase as ba
import bauiv1 as bui
import bascenev1 as bs
import json
import uuid
import threading
import time
import random
import re
from traceback import format_exc
from enum import IntEnum

class ApplicationConfiguration:
    ACTIVE_THEME = 0
    AUTOSTART_ENABLED = False
    ANTIKICK_ENABLED = True
    USER_INTERFACE_DEBUG = False
    CLIENT_VERSION = "1.0"
    REVISION_COUNTER = 3

class DarkVisualTheme:
    MAIN_BACKGROUND = (0, 0, 0)
    TINT_COLOR = (0.1, 0.1, 0.1)
    TEXT_COLOR = (0.8, 0.8, 0.8)
    ERROR_COLOR = (1, 0, 0)
    SUCCESS_COLOR = (0, 1, 0)
    INFORMATION_COLOR = (1, 1, 0)
    SHADOW_COLOR = (0, 0, 0)
    DEFAULT_OPACITY = 0.7

class LightVisualTheme:
    MAIN_BACKGROUND = (1, 1, 1)
    TINT_COLOR = (0.7, 0.7, 0.7)
    TEXT_COLOR = (0.2, 0.2, 0.2)
    ERROR_COLOR = (1, 0.3, 0.3)
    SUCCESS_COLOR = (0.3, 1, 0.3)
    INFORMATION_COLOR = (1, 1, 0.3)
    SHADOW_COLOR = (0.2, 0.2, 0.2)
    DEFAULT_OPACITY = 0.7

class DrawingConstants:
    VERTICAL_LINE = '\u2502'
    HORIZONTAL_LINE = '\u2500'
    PIPE_CORNER = '\u251C'
    BOTTOM_CORNER = '\u2514'

ACTIVE_THEME_CLASS = [LightVisualTheme, DarkVisualTheme][ApplicationConfiguration.ACTIVE_THEME]

class LogSeverity(IntEnum):
    OUTGOING_PACKET = 0
    INCOMING_PACKET = 1
    BASIC_MESSAGE = 2
    ERROR_MESSAGE = 3
    SUCCESS_MESSAGE = 4
    INFORMATION_MESSAGE = 5

class PacketType(IntEnum):
    REMOTE_PING = 0
    REMOTE_PONG = 1
    REMOTE_ID_REQUEST = 2
    REMOTE_ID_RESPONSE = 3
    REMOTE_DISCONNECT = 4
    REMOTE_STATE = 5
    REMOTE_STATE_ACK = 6
    REMOTE_DISCONNECT_ACK = 7
    REMOTE_GAME_QUERY = 8
    REMOTE_GAME_RESPONSE = 9
    REMOTE_STATE2 = 10
    SIMPLE_PING = 11
    SIMPLE_PONG = 12
    JSON_PING = 13
    JSON_PONG = 14
    POKE = 21
    HOST_QUERY = 22
    HOST_QUERY_RESPONSE = 23
    CLIENT_REQUEST = 24
    CLIENT_ACCEPT = 25
    CLIENT_DENY = 26
    CLIENT_DENY_VERSION_MISMATCH = 27
    CLIENT_DENY_ALREADY_IN_PARTY = 28
    CLIENT_DENY_PARTY_FULL = 29
    DISCONNECT_FROM_CLIENT_REQUEST = 32
    DISCONNECT_FROM_CLIENT_ACK = 33
    DISCONNECT_FROM_HOST_REQUEST = 34
    DISCONNECT_FROM_HOST_ACK = 35
    CLIENT_GAMEPACKET_COMPRESSED = 36
    HOST_GAMEPACKET_COMPRESSED = 37

class ScenePacketType(IntEnum):
    HANDSHAKE = 15
    HANDSHAKE_RESPONSE = 16
    MESSAGE = 17
    MESSAGE_UNRELIABLE = 18
    DISCONNECT = 19
    KEEPALIVE = 20

class MessageType(IntEnum):
    SESSION_RESET = 0
    SESSION_COMMANDS = 1
    SESSION_DYNAMICS_CORRECTION = 2
    NULL_MESSAGE = 3
    REQUEST_REMOTE_PLAYER = 4
    ATTACH_REMOTE_PLAYER = 5
    DETACH_REMOTE_PLAYER = 6
    REMOTE_PLAYER_INPUT_COMMANDS = 7
    REMOVE_REMOTE_PLAYER = 8
    PARTY_ROSTER = 9
    CHAT = 10
    PARTY_MEMBER_JOINED = 11
    PARTY_MEMBER_LEFT = 12
    MULTIPART = 13
    MULTIPART_END = 14
    CLIENT_PLAYER_PROFILES = 15
    ATTACH_REMOTE_PLAYER_2 = 16
    HOST_INFO = 17
    CLIENT_INFO = 18
    KICK_VOTE = 19
    JMESSAGE = 20
    CLIENT_PLAYER_PROFILES_JSON = 21

class SessionCommandType(IntEnum):
    BASE_TIME_STEP = 0
    STEP_SCENE_GRAPH = 1
    ADD_SCENE_GRAPH = 2
    REMOVE_SCENE_GRAPH = 3
    ADD_NODE = 4
    NODE_ON_CREATE = 5
    SET_FOREGROUND_SCENE = 6
    REMOVE_NODE = 7
    SET_NODE_ATTR_FLOAT = 21
    SET_NODE_ATTR_INT32 = 22
    SET_NODE_ATTR_BOOL = 23
    SET_NODE_ATTR_FLOATS = 24
    SET_NODE_ATTR_INT32S = 25
    SET_NODE_ATTR_STRING = 26

class ProtocolConstants(IntEnum):
    PROTOCOL_VERSION_LOW = 33
    PROTOCOL_VERSION_HIGH = 0
    ACK_EXTRA = 0
    DUMMY_MN_LOW = 240
    DUMMY_MN_HIGH = 255
    DUMMY_ACK_LOW = 240
    DUMMY_ACK_HIGH = 255

class HuffmanNode:
    def __init__(self) -> None:
        self.left_child_index = -1
        self.right_child_index = -1
        self.parent_index = 0
        self.bit_count = 0
        self.bit_value = 0
        self.frequency = 0

class HuffmanCodec:
    def __init__(self) -> None:
        frequencies = [
            101342, 9667, 3497, 1072, 0, 3793, 0, 0, 2815, 5235,
            *([0]*3), 3570, *([0]*3), 1383, *([0]*3), 2970, 0, 0, 2857,
            *([0]*8), 1199, *([0]*29), 1494, 1974, *([0]*12), 1351,
            *([0]*113), 1475, *([0]*64)
        ]
        self.nodes = [HuffmanNode() for _ in range(511)]
        for index in range(256):
            self.nodes[index].frequency = frequencies[index]

        current_index = 256
        while current_index < 511:
            search_index = 0
            while self.nodes[search_index].parent_index != 0:
                search_index += 1
            min1_index = search_index
            search_index += 1

            while self.nodes[search_index].parent_index != 0:
                search_index += 1
            min2_index = search_index
            search_index += 1

            while search_index < current_index:
                if self.nodes[search_index].parent_index == 0:
                    if self.nodes[min1_index].frequency > self.nodes[min2_index].frequency:
                        if self.nodes[search_index].frequency < self.nodes[min1_index].frequency:
                            min1_index = search_index
                    else:
                        if self.nodes[search_index].frequency < self.nodes[min2_index].frequency:
                            min2_index = search_index
                search_index += 1

            self.nodes[current_index].frequency = self.nodes[min1_index].frequency + self.nodes[min2_index].frequency
            self.nodes[min1_index].parent_index = current_index - 255
            self.nodes[min2_index].parent_index = current_index - 255
            self.nodes[current_index].right_child_index = min1_index
            self.nodes[current_index].left_child_index = min2_index
            current_index += 1

        for index in range(256):
            self.nodes[index].bit_value = 0
            self.nodes[index].bit_count = 0
            traversal_index = index
            while self.nodes[traversal_index].parent_index != 0:
                parent_index = self.nodes[traversal_index].parent_index + 255
                bit_addition = 1 if self.nodes[parent_index].right_child_index == traversal_index else 0
                self.nodes[index].bit_value = (self.nodes[index].bit_value << 1) | bit_addition
                self.nodes[index].bit_count += 1
                traversal_index = parent_index

            if self.nodes[index].bit_count >= 8:
                self.nodes[index].bit_count = 8
                self.nodes[index].bit_value = index << 1
            else:
                self.nodes[index].bit_value = (self.nodes[index].bit_value << 1) | 1
            self.nodes[index].bit_count += 1

    def WriteBitstream(self, output_buffer: list[int], position: int, bit_value: int, bit_count: int) -> int:
        bit_index = 0
        while bit_index < bit_count:
            byte_index = position // 8
            bit_offset = position % 8
            while len(output_buffer) <= byte_index:
                output_buffer.append(0)
            if (bit_value >> bit_index) & 1:
                output_buffer[byte_index] |= (1 << bit_offset)
            position += 1
            bit_index += 1
        return position

    def CompressPayload(self, input_data: bytes) -> bytes:
        if not input_data:
            return bytes()
        if input_data[0] & 0x80:
            raise ValueError("First byte high bit is restricted.")

        total_bits_required = sum(self.nodes[byte_val].bit_count for byte_val in input_data)
        remainder_bits = total_bits_required % 8
        if ((total_bits_required + 7) // 8 + 1) >= len(input_data):
            return input_data

        output_buffer = [0]
        current_position = 8
        for byte_val in input_data:
            current_position = self.WriteBitstream(output_buffer, current_position, self.nodes[byte_val].bit_value, self.nodes[byte_val].bit_count)

        output_buffer[0] = ((8 - remainder_bits % 8) if remainder_bits else 0) | 0x80
        return bytes(output_buffer)

    def DecompressPayload(self, input_data: bytes) -> bytes:
        if not input_data:
            raise ValueError("Empty data payload.")

        remainder_bits = input_data[0] & 0x0F
        is_compressed = (input_data[0] >> 7) & 1
        if not is_compressed:
            return input_data

        total_bits_available = (len(input_data) - 1) * 8
        if remainder_bits > total_bits_available:
            raise ValueError("Invalid remainder count.")

        total_bits_available -= remainder_bits
        output_buffer = []
        bit_position = 0
        byte_offset = 1

        while bit_position < total_bits_available:
            current_bit = (input_data[byte_offset + bit_position // 8] >> (bit_position % 8)) & 1
            bit_position += 1

            if current_bit:
                node_index = 510
                resolved_byte_value = 0
                while True:
                    current_bit = (input_data[byte_offset + bit_position // 8] >> (bit_position % 8)) & 1
                    if current_bit == 0:
                        if self.nodes[node_index].left_child_index == -1:
                            resolved_byte_value = node_index
                            break
                        else:
                            node_index = self.nodes[node_index].left_child_index
                            bit_position += 1
                    else:
                        if self.nodes[node_index].right_child_index == -1:
                            resolved_byte_value = node_index
                            break
                        else:
                            node_index = self.nodes[node_index].right_child_index
                            bit_position += 1

                    if self.nodes[node_index].left_child_index == -1 and self.nodes[node_index].right_child_index == -1:
                        resolved_byte_value = node_index
                        break

                    if bit_position > total_bits_available:
                        raise ValueError("Buffer overflow during decompression.")
                output_buffer.append(resolved_byte_value & 0xFF)
            else:
                byte_index = byte_offset + bit_position // 8
                bit_offset_local = bit_position % 8
                if bit_offset_local != 0:
                    resolved_byte_value = (input_data[byte_index] >> bit_offset_local) | (input_data[byte_index + 1] << (8 - bit_offset_local))
                else:
                    resolved_byte_value = input_data[byte_index]
                output_buffer.append(resolved_byte_value & 0xFF)
                bit_position += 8
                if bit_position > total_bits_available:
                    raise ValueError("Buffer overflow during byte read.")

        return bytes(output_buffer)

def GenerateStringTransitionFrames(old_text: str, new_text: str) -> list[str]:
    frames = [old_text]
    common_prefix_length = 0
    for old_char, new_char in zip(old_text, new_text):
        if old_char == new_char:
            common_prefix_length += 1
        else:
            break

    current_string_state = list(old_text)
    while len(current_string_state) > common_prefix_length:
        current_string_state.pop()
        frames.append("".join(current_string_state))

    for index in range(common_prefix_length, len(new_text)):
        current_string_state.append(new_text[index])
        frames.append("".join(current_string_state))

    return frames

def PlayUserInterfaceSound(sound_name: str, stop_delay: float = 0.0) -> None:
    sound_object = bui.getsound(sound_name)
    if sound_object:
        sound_object.play()
        if stop_delay > 0.0:
            bui.apptimer(stop_delay, sound_object.stop)

def DisplayScreenMessage(message: str) -> None:
    bui.screenmessage(message, color=ACTIVE_THEME_CLASS.TEXT_COLOR)

def SerializeJsonToBytes(data_dict: dict) -> bytes:
    return json.dumps(data_dict).encode('utf-8')

class NetworkClientState:
    def __init__(self) -> None:
        self.server_address = ""
        self.server_port = 0
        self.spec_name = "Proto"
        self.spec_short_name = ""
        self.spec_account = ""
        self.spec_device = ""
        self.auth_b = ""
        self.auth_token = ""
        self.auth_hash = ""
        self.custom_buffer = ""
        self.custom_buffer2 = ""
        self.packet_delay = 0.0

        self.is_connected = False
        self.is_busy = False
        self.client_id = ""
        self.host_id = ""
        self.last_spec_payload = b""
        self.last_auth_payload = b""
        self.keepalive_sequence = 0x20
        self.multipart_buffer = b""
        self.node_registry = {}
        self.current_game_name = "Unknown"
        self.current_game_desc = "Unknown"
        self.game_info_ready = 0
        self.seq_out = 0

GlobalNetworkState = NetworkClientState()
GlobalLogRecords = []

class ProtoNetworkManager:
    def __init__(self) -> None:
        self.ui_controller = None
        self.udp_socket = None
        self.worker_thread = None
        self.huffman_codec = HuffmanCodec()
        self.keepalive_timer = None
        self.disconnect_callback = None
        self.is_listening = False

    def AttachUI(self, ui_controller) -> None:
        self.ui_controller = ui_controller

    def DetachUI(self) -> None:
        self.ui_controller = None

    def LogEvent(self, payload, severity: LogSeverity) -> None:
        GlobalLogRecords.append((severity, payload))
        def _update_ui():
            if self.ui_controller and getattr(self.ui_controller, 'IsUserInterfaceValid', lambda: False)():
                self.ui_controller.RenderLogRecord(payload, severity)
        if ba.in_logic_thread():
            _update_ui()
        else:
            ba.pushcall(_update_ui, from_other_thread=True)

    def RefreshUIState(self) -> None:
        def _update_ui():
            if self.ui_controller and getattr(self.ui_controller, 'IsUserInterfaceValid', lambda: False)():
                self.ui_controller.UpdateInterfaceState()
        if ba.in_logic_thread():
            _update_ui()
        else:
            ba.pushcall(_update_ui, from_other_thread=True)

    def EstablishConnectionAsync(self) -> None:
        if GlobalNetworkState.is_busy:
            DisplayScreenMessage("Connection operation in progress, please wait.")
            PlayUserInterfaceSound('block')
            return

        if self.udp_socket is not None:
            self.LogEvent("Terminating active connection.", LogSeverity.BASIC_MESSAGE)
            PlayUserInterfaceSound('deek')
            self.CleanupNetworkResources()
            self.RefreshUIState()
            self.LogEvent("Connection terminated.", LogSeverity.SUCCESS_MESSAGE)
            return

        if self.ui_controller and getattr(self.ui_controller, 'IsUserInterfaceValid', lambda: False)():
            self.ui_controller.GatherInterfaceData()

        if not GlobalNetworkState.server_address:
            DisplayScreenMessage("Server address is required.")
            PlayUserInterfaceSound('block')
            return

        try:
            int(GlobalNetworkState.server_port)
        except ValueError:
            DisplayScreenMessage("Server port must be an integer.")
            PlayUserInterfaceSound('block')
            return

        GlobalNetworkState.last_spec_payload = self.BuildSpecificationPayload()
        GlobalNetworkState.is_busy = True

        self.worker_thread = threading.Thread(target=self.ExecuteConnectionHandshake, daemon=True)
        self.worker_thread.start()
        PlayUserInterfaceSound('dingSmall')
        self.LogEvent("Starting handshake sequence.", LogSeverity.BASIC_MESSAGE)

    def BuildSpecificationPayload(self) -> bytes:
        spec_dict = {
            's': json.dumps({
                'n': GlobalNetworkState.spec_name,
                'a': GlobalNetworkState.spec_account,
                'sn': GlobalNetworkState.spec_short_name
            }, separators=(',', ':')),
            'd': GlobalNetworkState.spec_device
        }
        return json.dumps(spec_dict, separators=(',', ':')).encode('utf-8')

    def ExecuteConnectionHandshake(self) -> None:
        try:
            self.PerformSocketOperations()
        except Exception as caught_exception:
            self.LogEvent([str(caught_exception), format_exc()], LogSeverity.ERROR_MESSAGE)
            ba.pushcall(self.CleanupNetworkResources, from_other_thread=True)
            ba.pushcall(lambda: PlayUserInterfaceSound('dingSmall'), from_other_thread=True)
        else:
            ba.pushcall(lambda: PlayUserInterfaceSound('dingSmallHigh'), from_other_thread=True)
        finally:
            GlobalNetworkState.is_busy = False

    def PerformSocketOperations(self) -> None:
        server_ip_type = bui.get_ip_address_type(GlobalNetworkState.server_address)
        self.udp_socket = socket.socket(server_ip_type, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(0.5)

        target_tuple = (GlobalNetworkState.server_address, int(GlobalNetworkState.server_port))

        def DispatchData(data_bytes: bytes) -> None:
            self.udp_socket.sendto(data_bytes, target_tuple)
            self.LogEvent(data_bytes, LogSeverity.OUTGOING_PACKET)

        def AwaitResponse(buffer_size: int) -> bytes:
            received_bytes = self.udp_socket.recvfrom(buffer_size)[0]
            self.LogEvent(received_bytes, LogSeverity.INCOMING_PACKET)
            return received_bytes

        self.LogEvent("Initializing socket.", LogSeverity.BASIC_MESSAGE)

        generated_request_id = f"{(71 + random.randint(0, 150)):02x}"
        GlobalNetworkState.client_id = generated_request_id
        session_uuid_bytes = str(uuid.uuid4()).encode()

        def SendClientRequest() -> None:
            request_packet = (
                PacketType.CLIENT_REQUEST.to_bytes(1, 'little') +
                ProtocolConstants.PROTOCOL_VERSION_LOW.to_bytes(1, 'little') +
                ProtocolConstants.PROTOCOL_VERSION_HIGH.to_bytes(1, 'little') +
                bytes.fromhex(generated_request_id) +
                session_uuid_bytes
            )
            DispatchData(request_packet)

        SendClientRequest()
        timeout_deadline = time.time() + 10.0
        last_transmit_time = time.time()
        assigned_host_id = None

        while assigned_host_id is None:
            if time.time() > timeout_deadline:
                raise TimeoutError("Handshake sequence timed out.")
            if time.time() - last_transmit_time > 0.5:
                SendClientRequest()
                last_transmit_time = time.time()

            try:
                incoming_handshake = AwaitResponse(1024)
            except (socket.timeout, TimeoutError):
                continue

            if incoming_handshake.startswith(PacketType.CLIENT_ACCEPT.to_bytes(1, 'little')):
                if len(incoming_handshake) != 3:
                    continue
                if incoming_handshake[2] != int(generated_request_id, 16):
                    continue
                assigned_host_id = f"{incoming_handshake[1]:02x}"
            elif incoming_handshake.startswith(PacketType.CLIENT_DENY_PARTY_FULL.to_bytes(1, 'little')):
                raise PermissionError("Server party capacity reached.")
            elif incoming_handshake.startswith(PacketType.CLIENT_DENY_ALREADY_IN_PARTY.to_bytes(1, 'little')):
                raise PermissionError("Client identification collision.")
            elif incoming_handshake.startswith(PacketType.CLIENT_DENY_VERSION_MISMATCH.to_bytes(1, 'little')):
                raise PermissionError("Protocol version incompatibility.")
            elif incoming_handshake.startswith(PacketType.CLIENT_DENY.to_bytes(1, 'little')):
                raise PermissionError("Server explicitly denied connection.")

        self.udp_socket.settimeout(5.0)
        GlobalNetworkState.host_id = assigned_host_id
        self.LogEvent(f"Handshake validated. {generated_request_id} -> {assigned_host_id}", LogSeverity.SUCCESS_MESSAGE)

        host_spec = ""
        host_salt = ""
        v2a_req = None

        while True:
            packet = AwaitResponse(1024)
            if packet[0] == PacketType.HOST_GAMEPACKET_COMPRESSED:
                payload = self.huffman_codec.DecompressPayload(packet[2:])
                if payload and payload[0] == ScenePacketType.HANDSHAKE:
                    try:
                        json_start = payload.find(b'{')
                        if json_start != -1:
                            handshake_json = json.loads(payload[json_start:].decode('utf-8', errors='ignore').rstrip('\x00'))
                            host_spec = handshake_json.get("s", "")
                            host_salt = handshake_json.get("l", "")
                            v2a_req = handshake_json.get("v2a", None)
                            self.LogEvent([f"Server Handshake Parsed", f"V2 Required: {v2a_req is not None}\nSalt: {host_salt}"], LogSeverity.INFORMATION_MESSAGE)
                            break
                    except Exception as e:
                        self.LogEvent(f"Failed to parse server handshake: {e}", LogSeverity.ERROR_MESSAGE)
                        break

        handshake_response = (
            PacketType.CLIENT_GAMEPACKET_COMPRESSED.to_bytes(1, 'little') +
            bytes.fromhex(assigned_host_id) +
            ScenePacketType.HANDSHAKE_RESPONSE.to_bytes(1, 'little') +
            ProtocolConstants.PROTOCOL_VERSION_LOW.to_bytes(1, 'little') +
            ProtocolConstants.PROTOCOL_VERSION_HIGH.to_bytes(1, 'little') +
            GlobalNetworkState.last_spec_payload
        )
        DispatchData(handshake_response)

        peer_hash = GlobalNetworkState.auth_hash
        if not peer_hash or peer_hash == "<AUTO>":
            try:
                import _babase
                peer_hash = _babase.calc_v1_peer_hash(host_spec + host_salt)
            except Exception:
                peer_hash = "fallback_hash"

        auth_b_val = int(GlobalNetworkState.auth_b) if GlobalNetworkState.auth_b.isdigit() else 14248
        auth_dict = {
            'b': auth_b_val,
            'tk': GlobalNetworkState.auth_token,
            'ph': peer_hash
        }

        def DispatchReliableMessage(msg_type_byte: bytes, payload_bytes: bytes) -> None:
            msg = (
                PacketType.CLIENT_GAMEPACKET_COMPRESSED.to_bytes(1, 'little') +
                bytes.fromhex(assigned_host_id) +
                ScenePacketType.MESSAGE.to_bytes(1, 'little') +
                GlobalNetworkState.seq_out.to_bytes(2, 'little') +
                b'\x00\x00\x00' +
                msg_type_byte +
                payload_bytes
            )
            GlobalNetworkState.seq_out += 1
            DispatchData(msg)

        DispatchReliableMessage(MessageType.CLIENT_INFO.to_bytes(1, 'little'), SerializeJsonToBytes(auth_dict))

        DispatchReliableMessage(MessageType.CLIENT_PLAYER_PROFILES_JSON.to_bytes(1, 'little'), SerializeJsonToBytes({}))

        DispatchReliableMessage(MessageType.NULL_MESSAGE.to_bytes(1, 'little'), b"")

        validation_response = AwaitResponse(1024)
        if len(validation_response) > 2 and validation_response[2] == ScenePacketType.DISCONNECT.value:
            raise ConnectionAbortedError("Server terminated connection immediately post-handshake.")

        AwaitResponse(9)

        ba.pushcall(self.InitializeSessionServices, from_other_thread=True)
        self.LogEvent("Network session established successfully.", LogSeverity.SUCCESS_MESSAGE)
        GlobalNetworkState.is_connected = True
        self.RefreshUIState()

    def InitializeSessionServices(self) -> None:
        self.keepalive_timer = bui.AppTimer(0.1, self.TransmitKeepaliveSignal, repeat=True)
        self.is_listening = True
        threading.Thread(target=self.IncomingTrafficListener, daemon=True).start()

    def TransmitKeepaliveSignal(self) -> None:
        if not GlobalNetworkState.is_connected or not self.udp_socket:
            return

        try:
            valid_port = int(GlobalNetworkState.server_port)
        except ValueError:
            return

        GlobalNetworkState.keepalive_sequence = (GlobalNetworkState.keepalive_sequence + 32) & 0xFFFFFF
        keepalive_packet = (
            PacketType.CLIENT_GAMEPACKET_COMPRESSED.to_bytes(1, 'little') +
            bytes.fromhex(GlobalNetworkState.host_id) +
            ScenePacketType.KEEPALIVE.to_bytes(1, 'little') +
            GlobalNetworkState.keepalive_sequence.to_bytes(3, 'little')
        )

        target_tuple = (GlobalNetworkState.server_address, valid_port)
        try:
            self.udp_socket.sendto(keepalive_packet, target_tuple)
        except OSError:
            pass

    def CleanupNetworkResources(self) -> None:
        if self.keepalive_timer:
            self.keepalive_timer = None
        self.is_listening = False

        if self.udp_socket:
            if GlobalNetworkState.host_id:
                disconnect_packet = (
                    PacketType.DISCONNECT_FROM_CLIENT_REQUEST.to_bytes(1, 'little') +
                    bytes.fromhex(GlobalNetworkState.host_id)
                )
                try:
                    self.udp_socket.sendto(disconnect_packet, (GlobalNetworkState.server_address, int(GlobalNetworkState.server_port)))
                except OSError:
                    pass
            self.udp_socket.close()
            self.udp_socket = None

        if self.worker_thread and self.worker_thread.is_alive() and threading.current_thread() != self.worker_thread:
            self.worker_thread.join(timeout=1.0)

        GlobalNetworkState.is_connected = False
        GlobalNetworkState.host_id = ""
        GlobalNetworkState.client_id = ""
        GlobalNetworkState.keepalive_sequence = 0x20
        GlobalNetworkState.node_registry.clear()
        GlobalNetworkState.multipart_buffer = b""
        GlobalNetworkState.seq_out = 0

    def IncomingTrafficListener(self) -> None:
        while self.is_listening and self.udp_socket:
            try:
                incoming_bytes = self.udp_socket.recvfrom(2048)[0]
                self.ProcessIncomingPacket(incoming_bytes)
            except OSError:
                break
            except Exception as processing_error:
                self.LogEvent([str(processing_error), format_exc()], LogSeverity.ERROR_MESSAGE)

    def ProcessIncomingPacket(self, raw_bytes: bytes) -> None:
        if len(raw_bytes) == 0:
            return

        packet_type_id = raw_bytes[0]
        if packet_type_id != PacketType.HOST_GAMEPACKET_COMPRESSED:
            self.LogEvent(raw_bytes, LogSeverity.INCOMING_PACKET)
            return

        if len(raw_bytes) < 2:
            return

        compressed_payload = raw_bytes[2:]
        try:
            decompressed_scenepacket = self.huffman_codec.DecompressPayload(compressed_payload)
        except ValueError:
            return

        if len(decompressed_scenepacket) == 0:
            return

        scenepacket_type_id = decompressed_scenepacket[0]
        if scenepacket_type_id == ScenePacketType.KEEPALIVE:
            return

        if scenepacket_type_id != ScenePacketType.MESSAGE:
            return

        message_payload = decompressed_scenepacket[6:]
        if len(message_payload) == 0:
            return

        self.RouteMessagePayload(message_payload)

    def RouteMessagePayload(self, message_payload: bytes) -> None:
        message_type_id = message_payload[0]
        message_body = message_payload[1:]

        if message_type_id == MessageType.SESSION_COMMANDS:
            self.ProcessSessionCommands(message_payload)
        elif message_type_id == MessageType.MULTIPART:
            GlobalNetworkState.multipart_buffer += message_body
        elif message_type_id == MessageType.MULTIPART_END:
            reconstructed_message = GlobalNetworkState.multipart_buffer + message_body
            GlobalNetworkState.multipart_buffer = b""
            self.RouteMessagePayload(reconstructed_message)
        elif message_type_id == MessageType.CHAT:
            self.ProcessChatMessage(message_body)
        elif message_type_id == MessageType.PARTY_ROSTER:
            self.ProcessPartyRoster(message_body)
        elif message_type_id == MessageType.JMESSAGE:
            self.ProcessJMessage(message_body)

    def ProcessSessionCommands(self, full_message_payload: bytes) -> None:
        canonicalized_commands = self.CanonicalizeSessionCommands(full_message_payload)
        for command_record in canonicalized_commands:
            command_identifier = command_record["cmd"]
            command_data_body = command_record["body"]

            if command_identifier == SessionCommandType.ADD_NODE:
                if len(command_data_body) >= 12:
                    scene_index, node_type_index, node_id_val = struct.unpack_from('<iii', command_data_body)
                    GlobalNetworkState.node_registry[node_id_val] = {"type": node_type_index, "attrs": {}}

            elif command_identifier == SessionCommandType.SET_NODE_ATTR_STRING:
                if len(command_data_body) >= 12:
                    node_id_val, attribute_index = struct.unpack_from('<ii', command_data_body, 0)
                    string_length = struct.unpack_from('<I', command_data_body, 8)[0]
                    if len(command_data_body) >= 12 + string_length:
                        decoded_string = command_data_body[12:12 + string_length].decode('utf-8', errors='replace').strip('\x00')
                        if node_id_val in GlobalNetworkState.node_registry:
                            GlobalNetworkState.node_registry[node_id_val]["attrs"][attribute_index] = decoded_string
                        if '"gameNames"' in decoded_string or '"gameDescriptions"' in decoded_string:
                            ba.pushcall(lambda text=decoded_string: self.ProcessGameInfoString(text), from_other_thread=True)

    def ProcessGameInfoString(self, decoded_string: str) -> None:
        try:
            parsed = json.loads(decoded_string)
            text_array = parsed.get("t", [])

            if len(text_array) >= 2:
                if text_array[0] == "gameNames":
                    GlobalNetworkState.current_game_name = text_array[1]
                    GlobalNetworkState.game_info_ready |= 1

                elif text_array[0] == "gameDescriptions":
                    formatted_desc = text_array[1]
                    for sub in parsed.get("s", []):
                        if len(sub) == 2:
                            formatted_desc = formatted_desc.replace(sub[0], sub[1])

                    GlobalNetworkState.current_game_desc = formatted_desc
                    GlobalNetworkState.game_info_ready |= 2

                if GlobalNetworkState.game_info_ready == 3:
                    log_summary = "ROUND INFO"
                    log_detail = f"{GlobalNetworkState.current_game_name}\n{GlobalNetworkState.current_game_desc}"
                    self.LogEvent([log_summary, log_detail], LogSeverity.INFORMATION_MESSAGE)

                    GlobalNetworkState.game_info_ready = 0

        except Exception as e:
            print(f"Proto JSON Parse Error: {e} | String: {decoded_string!r}")

    def CanonicalizeSessionCommands(self, raw_message: bytes) -> list[dict]:
        command_list = []
        byte_cursor = 1
        payload_length = len(raw_message)

        while byte_cursor < payload_length:
            if byte_cursor + 2 > payload_length:
                break
            command_length = struct.unpack_from('<H', raw_message, byte_cursor)[0]
            byte_cursor += 2

            if byte_cursor + command_length > payload_length:
                break

            command_bytes = raw_message[byte_cursor:byte_cursor + command_length]
            byte_cursor += command_length

            if len(command_bytes) == 0:
                continue

            raw_command_byte = command_bytes[0]
            try:
                resolved_command_enum = SessionCommandType(raw_command_byte)
            except ValueError:
                resolved_command_enum = raw_command_byte

            command_list.append({
                "cmd": resolved_command_enum,
                "body": command_bytes[1:]
            })

        return command_list

    def ProcessChatMessage(self, chat_body: bytes) -> None:
        if len(chat_body) == 0:
            return
        spec_size = chat_body[0]
        if len(chat_body) <= 1 + spec_size:
            return

        spec_data_json = chat_body[1:1 + spec_size].decode('utf-8', errors='replace')
        chat_text = chat_body[1 + spec_size:].decode('utf-8', errors='replace')

        try:
            parsed_spec = json.loads(spec_data_json)
        except json.JSONDecodeError:
            parsed_spec = {"n": "Unknown"}

        sender_name = parsed_spec.get('n', 'Unknown')
        log_summary = f"{sender_name}: {chat_text}"
        log_detail = f"CHAT MESSAGE\nSPEC={parsed_spec}\nCONTENT='{chat_text}'"
        self.LogEvent([log_summary, log_detail], LogSeverity.INFORMATION_MESSAGE)

        if ApplicationConfiguration.ANTIKICK_ENABLED:
            if parsed_spec.get('n') == '<HOST>' and f"A kick vote has been started for {GlobalNetworkState.spec_name}." in chat_text:
                self.LogEvent(["ANTIKICK", "Re-establishing connection to evade kick."], LogSeverity.SUCCESS_MESSAGE)
                ba.pushcall(self.EstablishConnectionAsync, from_other_thread=True)

    def ProcessPartyRoster(self, roster_body: bytes) -> None:
        if len(roster_body) == 0:
            return

        roster_json_bytes = roster_body[:-1]
        try:
            roster_list = json.loads(roster_json_bytes.decode('utf-8', errors='replace'))
        except json.JSONDecodeError:
            return

        display_lines = ['PARTY ROSTER STATE']
        for index, client_entry in enumerate(roster_list):
            is_final_client = (index == len(roster_list) - 1)
            prefix_char = DrawingConstants.BOTTOM_CORNER if is_final_client else DrawingConstants.PIPE_CORNER
            client_id_val = client_entry.get('i', '?')
            display_lines.append(f"{prefix_char}{DrawingConstants.HORIZONTAL_LINE} CLIENT ID {client_id_val}:")

            indent_spacing = "    " if is_final_client else f"{DrawingConstants.VERTICAL_LINE}   "
            client_spec_raw = client_entry.get('spec', '{}')

            try:
                parsed_spec = json.loads(client_spec_raw)
            except json.JSONDecodeError:
                parsed_spec = {}

            branches = []
            spec_display_items = [f"{key}={val!r}" for key, val in parsed_spec.items()]
            branches.append(("SPECIFICATION:", spec_display_items))

            players_list = client_entry.get('p', [])
            if players_list:
                for player_entry in players_list:
                    player_items = [f"n={player_entry.get('n', '')!r}", f"nf={player_entry.get('nf', '')!r}"]
                    branches.append((f"PLAYER ID {player_entry.get('i', '?')}:", player_items))
            else:
                branches.append(("STATUS: Spectating/No Players", []))

            for branch_idx, (header_text, item_lines) in enumerate(branches):
                is_final_branch = (branch_idx == len(branches) - 1)
                branch_prefix = DrawingConstants.BOTTOM_CORNER if is_final_branch else DrawingConstants.PIPE_CORNER
                display_lines.append(f"{indent_spacing}{branch_prefix}{DrawingConstants.HORIZONTAL_LINE} {header_text}")

                if item_lines:
                    item_indent = indent_spacing + ("    " if is_final_branch else f"{DrawingConstants.VERTICAL_LINE}   ")
                    for item_idx, item_text in enumerate(item_lines):
                        is_final_item = (item_idx == len(item_lines) - 1)
                        item_prefix = DrawingConstants.BOTTOM_CORNER if is_final_item else DrawingConstants.PIPE_CORNER
                        display_lines.append(f"{item_indent}{item_prefix}{DrawingConstants.HORIZONTAL_LINE} {item_text}")

        self.LogEvent(["ROSTER UPDATE", '\n'.join(display_lines)], LogSeverity.INFORMATION_MESSAGE)

    def ProcessJMessage(self, jmessage_body: bytes) -> None:
        if len(jmessage_body) == 0:
            return
        try:
            json_text = jmessage_body.decode('utf-8', errors='replace').rstrip('\x00')
            parsed_msg = json.loads(json_text)
        except json.JSONDecodeError:
            return

        if parsed_msg.get("t") == 0:
            message_content = parsed_msg.get("m", "<empty>")
            r = parsed_msg.get("r", 1.0)
            g = parsed_msg.get("g", 1.0)
            b = parsed_msg.get("b", 1.0)
            log_summary = f"SCREEN MSG: {message_content}"
            log_detail = f"TOAST MESSAGE (Modern Path)\nTEXT: {message_content}\nCOLOR: RGB({r}, {g}, {b})"
            self.LogEvent([log_summary, log_detail], LogSeverity.INFORMATION_MESSAGE)

            if ApplicationConfiguration.ANTIKICK_ENABLED:
                if f"A kick vote has been started for {GlobalNetworkState.spec_name}" in message_content:
                    self.LogEvent(["ANTIKICK", "Re-establishing connection to evade kick."], LogSeverity.SUCCESS_MESSAGE)
                    ba.pushcall(self.EstablishConnectionAsync, from_other_thread=True)

GlobalNetworkManager = ProtoNetworkManager()

class ProtoUserInterfaceController:
    def __init__(self) -> None:
        self.input_widgets = {}
        self.hint_widgets = []
        self.text_cache = {}
        self.animation_tasks = {}
        self.active_log_widgets = []
        self.log_vertical_offset = 0
        self.network_manager = GlobalNetworkManager
        self.network_manager.AttachUI(self)
        self.BuildMainWindow()
        self.state_monitor_timer = bui.AppTimer(0.01, self.MonitorInterfaceState, repeat=True)

        config_dict = bui.app.config.get('proto_saved_state', {})
        if config_dict:
            for attr_name, attr_value in config_dict.items():
                if attr_name in self.input_widgets:
                    bui.textwidget(edit=self.input_widgets[attr_name], text=str(attr_value))

        self.SyncInterfaceWithGlobalState()
        self.UpdateInterfaceState()

    def SyncInterfaceWithGlobalState(self) -> None:
        mapping = {
            'server_address': GlobalNetworkState.server_address,
            'server_port': GlobalNetworkState.server_port,
            'spec_name': GlobalNetworkState.spec_name,
            'spec_short_name': GlobalNetworkState.spec_short_name,
            'spec_account': GlobalNetworkState.spec_account,
            'spec_device': GlobalNetworkState.spec_device,
            'auth_b': GlobalNetworkState.auth_b,
            'auth_token': GlobalNetworkState.auth_token,
            'auth_hash': GlobalNetworkState.auth_hash,
            'custom_buffer': GlobalNetworkState.custom_buffer,
            'custom_buffer2': GlobalNetworkState.custom_buffer2,
            'packet_delay': GlobalNetworkState.packet_delay
        }

        for widget_key, val in mapping.items():
            if val and widget_key in self.input_widgets:
                bui.textwidget(edit=self.input_widgets[widget_key], text=str(val))

    def BuildMainWindow(self) -> None:
        PlayUserInterfaceSound('powerup01', 0.15)
        self.window_width = 1010
        self.window_height = 500

        self.root_container = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=(self.window_width, self.window_height),
            background=False,
            transition='in_left'
        )

        bui.imagewidget(
            parent=self.root_container,
            position=(-self.window_width * 0.1, -self.window_height * 0.1),
            size=(self.window_width * 1.2, self.window_height * 1.2),
            texture=bui.gettexture('softRect'),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            color=ACTIVE_THEME_CLASS.SHADOW_COLOR
        )

        bui.imagewidget(
            parent=self.root_container,
            position=(-1, -1),
            size=(self.window_width, self.window_height),
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.MAIN_BACKGROUND,
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        )

        self.CreateHeaderSection()
        self.CreateNetworkInputSection()
        self.CreatePayloadInjectionSection()
        self.CreateLogViewerSection()

    def CreateHeaderSection(self) -> None:
        header_x = 90
        header_y = self.window_height - 70
        header_width = 340
        header_height = 50

        bui.imagewidget(
            parent=self.root_container,
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            position=(header_x, header_y - 2),
            size=(header_width, header_height + 4),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        )

        self.title_text = bui.textwidget(
            parent=self.root_container,
            h_align='center',
            v_align='center',
            maxwidth=header_width - 60,
            position=(header_x + header_width / 2.4, header_y + header_height / 4 - 2),
            color=ACTIVE_THEME_CLASS.TEXT_COLOR,
            text=f"Proto v{ApplicationConfiguration.CLIENT_VERSION} - Ready."
        )

        bui.containerwidget(edit=self.root_container, cancel_button=bui.buttonwidget(
            parent=self.root_container,
            position=(20, header_y),
            size=(50, 50),
            label=bui.charstr(bui.SpecialChar.BACK),
            text_scale=0.8,
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            on_activate_call=self.CloseUserInterface,
            enable_sound=False,
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        ))

    def CreateNetworkInputSection(self) -> None:
        input_y = self.window_height - 140
        field_height = 50

        bui.buttonwidget(
            parent=self.root_container,
            position=(20, input_y),
            size=(50, 50),
            label=bui.charstr(bui.SpecialChar.DPAD_CENTER_BUTTON),
            text_scale=0.8,
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            on_activate_call=self.RetrieveHostConnectionInfo,
            enable_sound=False,
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        )

        port_width = 100
        addr_width = 450 - port_width - 130

        self.input_widgets['server_address'] = self.BuildInputField((96, input_y - 4), (addr_width, field_height + 8), "Server Address")
        self.input_widgets['server_port'] = self.BuildInputField((110 + addr_width, input_y - 4), (port_width, field_height + 8), "Port")

        self.DrawHorizontalSeparator(input_y - 20, 410)

        input_y -= 90
        spec_width = (450 - 80) / 3

        self.input_widgets['spec_name'] = self.BuildInputField((20, input_y - 4), (spec_width, field_height + 8), "Spec n")
        self.input_widgets['spec_short_name'] = self.BuildInputField((40 + spec_width, input_y - 4), (spec_width, field_height + 8), "Spec sn")
        self.input_widgets['spec_account'] = self.BuildInputField((60 + 2 * spec_width, input_y - 4), (spec_width, field_height + 8), "Spec a")

        input_y -= 70
        device_width = 450 - 116

        bui.buttonwidget(
            parent=self.root_container,
            position=(20, input_y),
            size=(50, 50),
            label=bui.charstr(bui.SpecialChar.PLAY_BUTTON),
            text_scale=0.8,
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            on_activate_call=self.EvaluateDeviceSpec,
            enable_sound=False,
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        )

        self.input_widgets['spec_device'] = self.BuildInputField((98, input_y - 4), (device_width, field_height + 8), "Spec d")

        self.DrawHorizontalSeparator(input_y - 20, 410)

        input_y -= 90

        self.input_widgets['auth_b'] = self.BuildInputField((20, input_y - 4), (spec_width, field_height + 8), "Auth b")
        self.input_widgets['auth_token'] = self.BuildInputField((40 + spec_width, input_y - 4), (spec_width, field_height + 8), "Auth tk")
        self.input_widgets['auth_hash'] = self.BuildInputField((60 + 2 * spec_width, input_y - 4), (spec_width, field_height + 8), "Auth ph")

        self.DrawHorizontalSeparator(input_y - 20, 410)

        input_y -= 90
        action_width = (450 - 110) / 3

        self.more_button = bui.buttonwidget(
            parent=self.root_container,
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            enable_sound=False,
            size=(action_width, 50),
            position=(23, input_y),
            label='More',
            on_activate_call=self.OpenMoreMenu
        )

        self.memory_button = bui.buttonwidget(
            parent=self.root_container,
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            enable_sound=False,
            size=(action_width, 50),
            position=(53 + action_width, input_y),
            label='Presets',
            on_activate_call=self.OpenPresetManager
        )

        self.connection_toggle_button = bui.buttonwidget(
            parent=self.root_container,
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            enable_sound=False,
            size=(action_width, 50),
            position=(83 + 2 * action_width, input_y),
            label='Establish',
            on_activate_call=self.network_manager.EstablishConnectionAsync
        )

        self.DrawVerticalSeparator(450, 18, self.window_height - 36)

    def CreatePayloadInjectionSection(self) -> None:
        injection_area_x = 470
        injection_area_width = 320 - 40
        base_scroll_y = self.window_height / 2 + 20
        total_scroll_height = self.window_height / 2 - 40
        split_height = (total_scroll_height - 20) / 2
        top_scroll_y = base_scroll_y + split_height + 20
        scroll_widget = bui.scrollwidget(
            parent=self.root_container,
            border_opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            position=(injection_area_x, top_scroll_y),
            size=(injection_area_width, split_height)
        )

        inner_container = bui.containerwidget(
            parent=scroll_widget,
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            background=False
        )

        list_index = 0
        for enum_class in [PacketType, ScenePacketType, MessageType]:
            for enum_item in enum_class:
                bui.textwidget(
                    parent=inner_container,
                    size=(injection_area_width, 30),
                    text=enum_item.name,
                    maxwidth=injection_area_width - 20,
                    v_align='center',
                    color=ACTIVE_THEME_CLASS.TEXT_COLOR,
                    position=(0, 30 * list_index),
                    selectable=True,
                    glow_type='uniform',
                    click_activate=True,
                    on_activate_call=ba.CallPartial(self.AppendEnumToBuffer, enum_item)
                )
                list_index += 1

        bui.containerwidget(edit=inner_container, size=(injection_area_width, list_index * 30))

        self.DrawHorizontalSeparator(base_scroll_y + split_height + 8, injection_area_width, injection_area_x)

        template_scroll_widget = bui.scrollwidget(
            parent=self.root_container,
            border_opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            position=(injection_area_x, base_scroll_y),
            size=(injection_area_width, split_height)
        )
        template_container = bui.containerwidget(
            parent=template_scroll_widget,
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            background=False
        )
        template_items = ["Sample Ping", "Chat Message"]
        for i, t_name in enumerate(template_items):
            bui.textwidget(
                parent=template_container,
                size=(injection_area_width, 30),
                text=t_name,
                maxwidth=injection_area_width - 20,
                v_align='center',
                color=ACTIVE_THEME_CLASS.TEXT_COLOR,
                position=(0, 30 * i),
                selectable=True,
                glow_type='uniform',
                click_activate=True,
                on_activate_call=ba.CallPartial(self.InsertTemplate, t_name)
            )
        bui.containerwidget(edit=template_container, size=(injection_area_width, len(template_items) * 30))

        self.DrawHorizontalSeparator(self.window_height / 2, injection_area_width, injection_area_x)

        input_y = self.window_height / 2 - 50 - 20

        self.input_widgets['custom_buffer'] = self.BuildInputField((injection_area_x + 4, input_y + 2), (injection_area_width, 50), "Hex Header")
        input_y -= 55
        self.input_widgets['custom_buffer2'] = self.BuildInputField((injection_area_x + 4, input_y + 2), (injection_area_width, 50), "Tailing Text")
        input_y -= 53
        self.input_widgets['packet_delay'] = self.BuildInputField((injection_area_x + 4, input_y - 1), (injection_area_width, 50), "Delay (sec)")

        input_y -= 50
        bui.buttonwidget(
            parent=self.root_container,
            label='Send Packet',
            position=(injection_area_x + 10, input_y - 2),
            size=(injection_area_width - 18, 50 - 14),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            on_activate_call=self.TransmitCustomPayload,
            enable_sound=False,
            texture=bui.gettexture('white')
        )

        self.DrawVerticalSeparator(450 + 320, 18, self.window_height - 36)

    def CreateLogViewerSection(self) -> None:
        self.log_area_x = 790
        self.log_area_width = 240 - 40
        self.log_area_height = self.window_height - 90

        self.log_scroll_widget = bui.scrollwidget(
            parent=self.root_container,
            border_opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            position=(self.log_area_x, 70),
            size=(self.log_area_width, self.log_area_height),
            color=ACTIVE_THEME_CLASS.TINT_COLOR
        )

        self.log_container_widget = bui.containerwidget(
            parent=self.log_scroll_widget,
            background=False
        )

        bui.buttonwidget(
            parent=self.root_container,
            texture=bui.gettexture('white'),
            enable_sound=False,
            on_activate_call=self.ClearLogDisplay,
            label='Clear Logs',
            position=(self.log_area_x + 8, 20),
            size=(self.log_area_width - 14, 50 - 14),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR
        )

        self.no_log_indicator = bui.textwidget(
            parent=self.root_container,
            position=(self.log_area_x + self.log_area_width / 2 - 25, self.window_height - self.log_area_height / 2 - 30),
            color=(*ACTIVE_THEME_CLASS.TINT_COLOR, ACTIVE_THEME_CLASS.DEFAULT_OPACITY),
            text='No events.',
            h_align='center',
            v_align='center'
        )

        for record in GlobalLogRecords:
            self.RenderLogRecord(record[1], record[0])

    def BuildInputField(self, position: tuple, size: tuple, placeholder: str):
        text_input = bui.textwidget(
            parent=self.root_container,
            position=position,
            size=size,
            editable=True,
            max_height=size[1],
            v_align='center',
            glow_type='uniform',
            color=ACTIVE_THEME_CLASS.TEXT_COLOR,
            allow_clear_button=False,
            text=""
        )
        hint_widget = bui.textwidget(
            parent=self.root_container,
            position=position,
            size=size,
            v_align='center',
            color=(*ACTIVE_THEME_CLASS.TEXT_COLOR, ACTIVE_THEME_CLASS.DEFAULT_OPACITY),
            text=placeholder
        )
        self.hint_widgets.append(hint_widget)
        return text_input

    def DrawHorizontalSeparator(self, position_y: float, width: float, position_x: float = 20) -> None:
        bui.imagewidget(
            parent=self.root_container,
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            size=(width, 4),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            position=(position_x, position_y)
        )

    def DrawVerticalSeparator(self, position_x: float, position_y: float, height: float) -> None:
        bui.imagewidget(
            parent=self.root_container,
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            size=(4, height),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            position=(position_x, position_y)
        )

    def IsUserInterfaceValid(self) -> bool:
        return self.root_container.exists() and not self.root_container.transitioning_out

    def MonitorInterfaceState(self) -> None:
        if not self.IsUserInterfaceValid():
            self.state_monitor_timer = None
            return

        for (attr_key, widget_ref), hint_widget in zip(self.input_widgets.items(), self.hint_widgets):
            current_text = bui.textwidget(query=widget_ref)

            if self.text_cache.get(attr_key) != current_text:
                self.text_cache[attr_key] = current_text

                opacity = 0 if current_text else ACTIVE_THEME_CLASS.DEFAULT_OPACITY
                bui.textwidget(edit=hint_widget, color=(*ACTIVE_THEME_CLASS.TEXT_COLOR, opacity))

    def UpdateInterfaceState(self) -> None:
        if not self.IsUserInterfaceValid():
            return

        connection_status_text = f"Proto v{ApplicationConfiguration.CLIENT_VERSION} - "
        if GlobalNetworkState.is_connected:
            connection_status_text += f"Online ({GlobalNetworkState.client_id} -> {GlobalNetworkState.host_id})"
            self.ExecuteTransitionAnimation(self.title_text, bui.textwidget(query=self.title_text), connection_status_text, bui.textwidget, 'text')
            self.ExecuteTransitionAnimation(self.connection_toggle_button, 'Establish', 'Terminate', bui.buttonwidget, 'label')
        else:
            connection_status_text += "Ready."
            self.ExecuteTransitionAnimation(self.title_text, bui.textwidget(query=self.title_text), connection_status_text, bui.textwidget, 'text')
            self.ExecuteTransitionAnimation(self.connection_toggle_button, 'Terminate', 'Establish', bui.buttonwidget, 'label')

    def ExecuteTransitionAnimation(self, target_widget, current_value, final_value, widget_func, target_property) -> None:
        frames = GenerateStringTransitionFrames(current_value, final_value)
        animation_id = str(target_widget)

        def AnimationTick(frame_index: int):
            if not target_widget.exists():
                self.animation_tasks.pop(animation_id, None)
                return
            widget_func(edit=target_widget, **{target_property: frames[frame_index]})
            if frame_index + 1 < len(frames):
                self.animation_tasks[animation_id] = bui.AppTimer(0.02, ba.CallPartial(AnimationTick, frame_index + 1))
            else:
                self.animation_tasks.pop(animation_id, None)

        self.animation_tasks[animation_id] = bui.AppTimer(0.02, ba.CallPartial(AnimationTick, 0))

    def GatherInterfaceData(self) -> None:
        GlobalNetworkState.server_address = bui.textwidget(query=self.input_widgets['server_address']).strip()
        GlobalNetworkState.server_port = bui.textwidget(query=self.input_widgets['server_port']).strip()
        GlobalNetworkState.spec_name = bui.textwidget(query=self.input_widgets['spec_name']).strip()
        GlobalNetworkState.spec_short_name = bui.textwidget(query=self.input_widgets['spec_short_name']).strip()
        GlobalNetworkState.spec_account = bui.textwidget(query=self.input_widgets['spec_account']).strip()
        GlobalNetworkState.spec_device = bui.textwidget(query=self.input_widgets['spec_device']).strip()
        GlobalNetworkState.auth_b = bui.textwidget(query=self.input_widgets['auth_b']).strip()
        GlobalNetworkState.auth_token = bui.textwidget(query=self.input_widgets['auth_token']).strip()
        GlobalNetworkState.auth_hash = bui.textwidget(query=self.input_widgets['auth_hash']).strip()
        GlobalNetworkState.custom_buffer = bui.textwidget(query=self.input_widgets['custom_buffer']).strip()
        GlobalNetworkState.custom_buffer2 = bui.textwidget(query=self.input_widgets['custom_buffer2']).strip()
        GlobalNetworkState.packet_delay = bui.textwidget(query=self.input_widgets['packet_delay']).strip()

    def RetrieveHostConnectionInfo(self) -> None:
        connection_info = bs.get_connection_to_host_info_2()
        if connection_info is None:
            DisplayScreenMessage("No active server connection found.")
            PlayUserInterfaceSound('block')
            return
        bui.textwidget(edit=self.input_widgets['server_address'], text=connection_info.address)
        bui.textwidget(edit=self.input_widgets['server_port'], text=str(connection_info.port))
        PlayUserInterfaceSound('gunCocking')

    def EvaluateDeviceSpec(self) -> None:
        raw_code = bui.textwidget(query=self.input_widgets['spec_device'])
        if not raw_code:
            DisplayScreenMessage("Enter a valid expression.")
            PlayUserInterfaceSound('block')
            return
        try:
            evaluated_result = str(eval(raw_code))
            bui.textwidget(edit=self.input_widgets['spec_device'], text=evaluated_result)
            PlayUserInterfaceSound('gunCocking')
        except Exception as eval_error:
            DisplayScreenMessage(str(eval_error))
            PlayUserInterfaceSound('block')

    def PersistInputState(self) -> None:
        current_save_dict = bui.app.config.get('proto_presets', {})
        preset_name = f'Preset {len(current_save_dict) + 1}'
        state_buffer = {}
        for attr_name, widget_ref in self.input_widgets.items():
            widget_text = bui.textwidget(query=widget_ref)
            if widget_text:
                state_buffer[attr_name] = widget_text

        if not state_buffer:
            DisplayScreenMessage("All fields empty, nothing to save.")
            PlayUserInterfaceSound('block')
            return

        current_save_dict[preset_name] = state_buffer
        bui.app.config['proto_presets'] = current_save_dict
        bui.app.config.commit()

        bui.app.config['proto_saved_state'] = state_buffer
        bui.app.config.commit()

        DisplayScreenMessage(f"State saved as {preset_name}.")
        PlayUserInterfaceSound('gunCocking')

    def AppendEnumToBuffer(self, enum_item: IntEnum) -> None:
        current_hex = bui.textwidget(query=self.input_widgets['custom_buffer'])
        appended_hex = current_hex + enum_item.to_bytes(1, 'little').hex()
        bui.textwidget(edit=self.input_widgets['custom_buffer'], text=appended_hex)
        PlayUserInterfaceSound('deek')

    def InsertTemplate(self, template_name: str) -> None:
        if template_name == "Sample Ping":
            # 0b = PacketType.SIMPLE_PING (11)
            bui.textwidget(edit=self.input_widgets['custom_buffer'], text="0b")
            bui.textwidget(edit=self.input_widgets['custom_buffer2'], text="")
        elif template_name == "Chat Message":
            # 24 = CLIENT_GAMEPACKET_COMPRESSED (36)
            # <HOST_ID> = dynamic macro replaced at send-time
            # 11 = SCENEPACKET_MESSAGE (17) (Top bit 0 acts as Huffman placebo)
            # f0 ff f0 ff 00 = Dummy MN (2 bytes) + Dummy ACKs (3 bytes)
            # 0a = MESSAGE_CHAT (10)
            # 0d = spec_length (13 bytes)
            # 7b226e223a2250726f746f227d = spec bytes: {"n":"Proto"}
            packet_hex = "24 <HOST_ID> 11 f0 ff f0 ff 00 0a 0d 7b 22 6e 22 3a 22 50 72 6f 74 6f 22 7d"
            bui.textwidget(edit=self.input_widgets['custom_buffer'], text=packet_hex)
            bui.textwidget(edit=self.input_widgets['custom_buffer2'], text="Hi")
        PlayUserInterfaceSound('gunCocking')

    def TransmitCustomPayload(self) -> None:
        if not GlobalNetworkState.is_connected or self.network_manager.udp_socket is None:
            DisplayScreenMessage("Connection must be established to send packets.")
            PlayUserInterfaceSound('block')
            return

        try:
            transmission_delay = float(bui.textwidget(query=self.input_widgets['packet_delay']))
        except ValueError:
            transmission_delay = 0.0

        hex_data_raw = bui.textwidget(query=self.input_widgets['custom_buffer']).strip()
        tailing_data_raw = bui.textwidget(query=self.input_widgets['custom_buffer2'])

        if "<HOST_ID>" in hex_data_raw:
            if not GlobalNetworkState.host_id:
                DisplayScreenMessage("Host ID not established yet.")
                PlayUserInterfaceSound('block')
                return
            hex_data_raw = hex_data_raw.replace("<HOST_ID>", GlobalNetworkState.host_id)
        hex_data_raw = hex_data_raw.replace(" ", "")

        try:
            processed_hex_bytes = bytes.fromhex(hex_data_raw)
            processed_tailing_bytes = tailing_data_raw.encode('utf-8')
            final_transmission_bytes = processed_hex_bytes + processed_tailing_bytes
        except ValueError as hex_error:
            self.network_manager.LogEvent([str(hex_error), format_exc()], LogSeverity.ERROR_MESSAGE)
            PlayUserInterfaceSound('block')
            return

        target_tuple = (GlobalNetworkState.server_address, int(GlobalNetworkState.server_port))

        def DispatchSocketCall():
            if self.network_manager.udp_socket:
                self.network_manager.udp_socket.sendto(final_transmission_bytes, target_tuple)
                self.network_manager.LogEvent(final_transmission_bytes, LogSeverity.OUTGOING_PACKET)

        if transmission_delay > 0.0:
            bui.apptimer(transmission_delay, DispatchSocketCall)
        else:
            DispatchSocketCall()
        PlayUserInterfaceSound('deek')

    def AppendLogRecord(self, data_payload, severity_level: LogSeverity) -> None:
        GlobalLogRecords.append((severity_level, data_payload))
        if not self.IsUserInterfaceValid():
            return
        self.RenderLogRecord(data_payload, severity_level)

    def RenderLogRecord(self, data_payload, severity_level: LogSeverity) -> None:
        if self.no_log_indicator and self.no_log_indicator.exists():
            self.no_log_indicator.delete()
            self.no_log_indicator = None

        if severity_level in [LogSeverity.OUTGOING_PACKET, LogSeverity.INCOMING_PACKET]:
            display_text = data_payload.hex(' ')
        elif severity_level in [LogSeverity.ERROR_MESSAGE, LogSeverity.INFORMATION_MESSAGE]:
            display_text = data_payload[0]
        else:
            display_text = str(data_payload)

        bg_colors = [
            ACTIVE_THEME_CLASS.TEXT_COLOR, ACTIVE_THEME_CLASS.MAIN_BACKGROUND,
            ACTIVE_THEME_CLASS.TINT_COLOR, ACTIVE_THEME_CLASS.ERROR_COLOR,
            ACTIVE_THEME_CLASS.SUCCESS_COLOR, ACTIVE_THEME_CLASS.INFORMATION_COLOR
        ]
        text_colors = [ACTIVE_THEME_CLASS.MAIN_BACKGROUND] * 2 + [ACTIVE_THEME_CLASS.TEXT_COLOR] * 4

        bui.imagewidget(
            parent=self.log_container_widget,
            texture=bui.gettexture('white'),
            color=bg_colors[severity_level.value],
            size=(self.log_area_width - 15, 30),
            position=(-5, self.log_vertical_offset * 30),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        )

        truncated_text = display_text[:30] + bui.charstr(bui.SpecialChar.RIGHT_ARROW) if len(display_text) >= 30 else display_text

        log_entry_widget = bui.textwidget(
            parent=self.log_container_widget,
            position=(0, self.log_vertical_offset * 30),
            text=truncated_text,
            color=(*text_colors[severity_level.value], ACTIVE_THEME_CLASS.DEFAULT_OPACITY),
            size=(self.log_area_width, 30),
            selectable=True,
            click_activate=True,
            glow_type='uniform',
            v_align='center',
            maxwidth=self.log_area_width - 20
        )

        bui.textwidget(edit=log_entry_widget, on_activate_call=ba.CallPartial(self.OpenLogDetails, data_payload, severity_level, log_entry_widget))
        bui.containerwidget(edit=self.log_container_widget, size=(self.log_area_width, max(self.log_vertical_offset * 30 + 30, self.log_area_height - 15)), visible_child=log_entry_widget)
        self.log_vertical_offset += 1

    def ClearLogDisplay(self) -> None:
        PlayUserInterfaceSound('deek')
        GlobalLogRecords.clear()
        self.log_vertical_offset = 0
        for child in self.log_container_widget.get_children():
            child.delete()
        bui.containerwidget(edit=self.log_container_widget, size=(self.log_area_width, 0))

    def OpenLogDetails(self, data_payload, severity_level: LogSeverity, source_widget) -> None:
        PlayUserInterfaceSound('powerup01', 0.15)

        is_binary = severity_level in [LogSeverity.OUTGOING_PACKET, LogSeverity.INCOMING_PACKET]
        is_sequence = severity_level in [LogSeverity.ERROR_MESSAGE, LogSeverity.INFORMATION_MESSAGE]

        primary_text = data_payload
        secondary_text = ""

        if is_binary:
            try:
                secondary_text = '\n'.join((3*' ').join((3*' ').join(chr(byte_val) if 32 <= byte_val < 127 else '.' for byte_val in data_payload[i:i+8]) for i in range(j, min(j+16, len(data_payload)), 8)) for j in range(0, len(data_payload), 16))
            except Exception:
                pass
            primary_text = '\n'.join((' ').join(data_payload[i:i+8].hex(' ') for i in range(j, min(j+16, len(data_payload)), 8)) for j in range(0, len(data_payload), 16))
        elif is_sequence:
            primary_text = data_payload[0]
            secondary_text = data_payload[1]

        dialog_width = 650
        dialog_height = 400 if (is_binary or is_sequence) else 200
        origin_x, origin_y = source_widget.get_screen_space_center()

        def CloseDetailsDialog(with_sound=True):
            if with_sound:
                PlayUserInterfaceSound('laser')
            bui.containerwidget(edit=details_root, transition='out_scale')

        details_root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=(dialog_width, dialog_height),
            background=False,
            transition='in_scale',
            scale_origin_stack_offset=(origin_x, origin_y),
            on_outside_click_call=CloseDetailsDialog
        )

        bui.imagewidget(
            parent=details_root,
            position=(-dialog_width * 0.1, -dialog_height * 0.1),
            size=(dialog_width * 1.2, dialog_height * 1.2),
            texture=bui.gettexture('softRect'),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            color=ACTIVE_THEME_CLASS.SHADOW_COLOR
        )

        bui.imagewidget(
            parent=details_root,
            position=(-1, -1),
            size=(dialog_width, dialog_height),
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.MAIN_BACKGROUND,
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        )

        bui.buttonwidget(
            parent=details_root,
            size=(dialog_width, dialog_height),
            enable_sound=False,
            texture=bui.gettexture('empty'),
            opacity=0,
            selectable=False,
            label=''
        )

        bg_colors = [
            ACTIVE_THEME_CLASS.TEXT_COLOR, ACTIVE_THEME_CLASS.MAIN_BACKGROUND,
            ACTIVE_THEME_CLASS.TINT_COLOR, ACTIVE_THEME_CLASS.ERROR_COLOR,
            ACTIVE_THEME_CLASS.SUCCESS_COLOR, ACTIVE_THEME_CLASS.INFORMATION_COLOR
        ]
        text_colors = [ACTIVE_THEME_CLASS.MAIN_BACKGROUND] * 2 + [ACTIVE_THEME_CLASS.TEXT_COLOR] * 4

        scroll_width = dialog_width - 40
        scroll_height = 160

        scroll_widget_1 = bui.scrollwidget(
            border_opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            parent=details_root,
            position=(20, 20),
            size=(scroll_width, scroll_height),
            color=ACTIVE_THEME_CLASS.TINT_COLOR
        )

        text_height = bui.get_string_height(primary_text, suppress_warning=True)
        text_height = max(text_height, scroll_height - 15)

        container_1 = bui.containerwidget(
            parent=scroll_widget_1,
            background=False,
            size=(scroll_width, text_height)
        )

        bui.imagewidget(
            parent=container_1,
            size=(scroll_width - 17, text_height),
            color=bg_colors[severity_level.value],
            texture=bui.gettexture('white'),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        )

        bui.textwidget(
            parent=container_1,
            text=primary_text,
            color=(*text_colors[severity_level.value], ACTIVE_THEME_CLASS.DEFAULT_OPACITY),
            position=(5, 0),
            selectable=True,
            size=(scroll_width, text_height),
            maxwidth=scroll_width - 30,
            click_activate=True,
            glow_type='uniform',
            on_activate_call=ba.CallPartial(bui.clipboard_set_text, data_payload.hex() if is_binary else primary_text)
        )

        if not (is_binary or is_sequence):
            return

        bui.imagewidget(
            parent=details_root,
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            size=(dialog_width - 40, 4),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            position=(20, 20 + scroll_height + 20)
        )

        scroll_widget_2 = bui.scrollwidget(
            border_opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            parent=details_root,
            position=(20, 40 + scroll_height),
            size=(scroll_width, scroll_height),
            color=ACTIVE_THEME_CLASS.TINT_COLOR
        )

        text_width = bui.get_string_width(secondary_text, suppress_warning=True)
        text_height = bui.get_string_height(secondary_text, suppress_warning=True)
        max_width = scroll_width - 30

        if text_width > max_width:
            scale_factor = max_width / text_width
            actual_height = text_height * scale_factor
        else:
            actual_height = text_height

        actual_height = max(actual_height, scroll_height - 15)

        container_2 = bui.containerwidget(
            parent=scroll_widget_2,
            background=False,
            size=(scroll_width, actual_height)
        )

        bui.imagewidget(
            parent=container_2,
            size=(scroll_width - 15, actual_height),
            color=bg_colors[severity_level.value],
            texture=bui.gettexture('white'),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        )

        def PrepareClipboardText():
            if is_binary:
                return data_payload.decode('utf-8', errors='replace').translate(str.maketrans({c: '.' for c in range(0x10000) if not chr(c).isprintable()}))
            return secondary_text

        bui.textwidget(
            parent=container_2,
            text=secondary_text,
            color=(*text_colors[severity_level.value], ACTIVE_THEME_CLASS.DEFAULT_OPACITY),
            position=(5, 0),
            selectable=True,
            maxwidth=max_width,
            click_activate=True,
            size=(scroll_width, actual_height),
            glow_type='uniform',
            on_activate_call=ba.CallPartial(bui.clipboard_set_text, PrepareClipboardText())
        )

    def AutoFillV1Auth(self) -> None:
        import babase as ba
        import random

        try:
            build_num = str(bui.app.env.engine_build_number)
        except Exception:
            build_num = "14248"

        try:
            import baplus
            acc_name = baplus.get_v1_account_display_string(False)
            if not acc_name:
                acc_name = "Proto"
        except Exception:
            acc_name = "Proto"

        device_id = ''.join(random.choices('0123456789abcdef', k=40))

        bui.textwidget(edit=self.input_widgets['spec_name'], text=acc_name)
        bui.textwidget(edit=self.input_widgets['spec_short_name'], text=acc_name)
        bui.textwidget(edit=self.input_widgets['auth_b'], text=build_num)
        bui.textwidget(edit=self.input_widgets['spec_device'], text=device_id)
        bui.textwidget(edit=self.input_widgets['auth_hash'], text="<AUTO>")

        bui.textwidget(edit=self.input_widgets['auth_token'], text="")

        DisplayScreenMessage("Auto-Filled V1 Client Data")
        PlayUserInterfaceSound('gunCocking')

    def OpenMoreMenu(self) -> None:
        PlayUserInterfaceSound('powerup01', 0.15)

        button_height = 36
        margin_x = 10
        margin_y = 15
        spacing_y = 10

        dialog_width = 160

        dialog_height = (margin_y * 2) + (button_height * 2) + spacing_y

        origin_x, origin_y = self.more_button.get_screen_space_center()

        def CloseMoreMenuDialog(with_sound=True):
            if with_sound:
                PlayUserInterfaceSound('laser')
            bui.containerwidget(edit=more_root, transition='out_scale')

        more_root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=(dialog_width, dialog_height),
            scale=1.3,
            background=False,
            transition='in_scale',
            scale_origin_stack_offset=(origin_x, origin_y),
            stack_offset=(origin_x, origin_y / 1.8),
            on_outside_click_call=CloseMoreMenuDialog
        )

        bui.imagewidget(
            parent=more_root,
            position=(-dialog_width * 0.1, -dialog_height * 0.1),
            size=(dialog_width * 1.2, dialog_height * 1.2),
            texture=bui.gettexture('softRect'),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            color=ACTIVE_THEME_CLASS.SHADOW_COLOR
        )

        bui.imagewidget(
            parent=more_root,
            position=(-1, -1),
            size=(dialog_width, dialog_height),
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.MAIN_BACKGROUND,
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        )

        bui.buttonwidget(
            parent=more_root,
            position=(margin_x, margin_y),
            size=(dialog_width - (margin_x * 2), button_height),
            label="Save Preset",
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            texture=bui.gettexture('white'),
            on_activate_call=lambda: [self.PersistInputState(), CloseMoreMenuDialog(False)],
            enable_sound=False
        )

        bui.buttonwidget(
            parent=more_root,
            position=(margin_x, margin_y + button_height + spacing_y),
            size=(dialog_width - (margin_x * 2), button_height),
            label="Auto-Fill V1",
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            texture=bui.gettexture('white'),
            on_activate_call=lambda: [self.AutoFillV1Auth(), CloseMoreMenuDialog(False)],
            enable_sound=False
        )

    def OpenPresetManager(self) -> None:
        PlayUserInterfaceSound('powerup01', 0.15)
        dialog_width = 160
        dialog_height = 240
        origin_x, origin_y = self.memory_button.get_screen_space_center()

        def ClosePresetDialog(with_sound=True):
            if with_sound:
                PlayUserInterfaceSound('laser')
            bui.containerwidget(edit=preset_root, transition='out_scale')

        preset_root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=(dialog_width, dialog_height),
            scale=1.3,
            background=False,
            transition='in_scale',
            scale_origin_stack_offset=(origin_x, origin_y),
            stack_offset=(origin_x, origin_y / 1.8),
            on_outside_click_call=ClosePresetDialog
        )

        bui.imagewidget(
            parent=preset_root,
            position=(-dialog_width * 0.1, -dialog_height * 0.1),
            size=(dialog_width * 1.2, dialog_height * 1.2),
            texture=bui.gettexture('softRect'),
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            color=ACTIVE_THEME_CLASS.SHADOW_COLOR
        )

        bui.imagewidget(
            parent=preset_root,
            position=(-1, -1),
            size=(dialog_width, dialog_height),
            texture=bui.gettexture('white'),
            color=ACTIVE_THEME_CLASS.MAIN_BACKGROUND,
            opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY
        )

        bui.buttonwidget(
            parent=preset_root,
            size=(dialog_width, dialog_height),
            enable_sound=False,
            texture=bui.gettexture('empty'),
            opacity=0,
            selectable=False,
            label=''
        )

        scroll_width = dialog_width - 20
        scroll_height = dialog_height - 60

        scroll_widget = bui.scrollwidget(
            border_opacity=ACTIVE_THEME_CLASS.DEFAULT_OPACITY,
            parent=preset_root,
            size=(scroll_width, scroll_height),
            position=(10, 50),
            color=ACTIVE_THEME_CLASS.TINT_COLOR
        )

        preset_dict = bui.app.config.get('proto_presets', {})
        inner_container = bui.containerwidget(
            parent=scroll_widget,
            background=False,
            size=(scroll_width, 0)
        )

        selection_state = {"active_widget": None}

        def SelectPresetItem(widget_ref):
            if selection_state["active_widget"]:
                bui.textwidget(edit=selection_state["active_widget"], color=ACTIVE_THEME_CLASS.TEXT_COLOR)
            selection_state["active_widget"] = widget_ref
            bui.textwidget(edit=widget_ref, color=ACTIVE_THEME_CLASS.MAIN_BACKGROUND)

        def PopulatePresetList():
            total_height = max(len(preset_dict) * 30, scroll_height - 15)
            for child in inner_container.get_children():
                child.delete()
            for index, preset_key in enumerate(preset_dict):
                preset_widget = bui.textwidget(
                    parent=inner_container,
                    position=(0, total_height - 30 - 30 * index),
                    text=preset_key,
                    maxwidth=scroll_width,
                    selectable=True,
                    click_activate=True,
                    color=ACTIVE_THEME_CLASS.TEXT_COLOR,
                    glow_type='uniform',
                    size=(scroll_width, 30)
                )
                bui.textwidget(edit=preset_widget, on_activate_call=ba.CallPartial(SelectPresetItem, preset_widget))
            bui.containerwidget(edit=inner_container, size=(scroll_width, total_height))

        PopulatePresetList()

        def DeleteSelectedPreset():
            active_widget = selection_state["active_widget"]
            if not active_widget:
                DisplayScreenMessage("Select a preset first.")
                PlayUserInterfaceSound('block')
                return
            preset_key = bui.textwidget(query=active_widget)
            preset_dict.pop(preset_key, None)
            bui.app.config['proto_presets'] = preset_dict
            bui.app.config.commit()
            DisplayScreenMessage(f"Deleted {preset_key}.")
            PlayUserInterfaceSound('laser')
            PopulatePresetList()

        button_width = dialog_width / 2 - 20

        bui.buttonwidget(
            parent=preset_root,
            position=(10, 10),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            texture=bui.gettexture('white'),
            size=(button_width, 30),
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_CROSS_BUTTON) + ' ',
            enable_sound=False,
            on_activate_call=DeleteSelectedPreset
        )

        def LoadSelectedPreset():
            active_widget = selection_state["active_widget"]
            if not active_widget:
                DisplayScreenMessage("Select a preset first.")
                PlayUserInterfaceSound('block')
                return
            preset_key = bui.textwidget(query=active_widget)
            loaded_data = preset_dict[preset_key]

            for attr_name, attr_value in loaded_data.items():
                if attr_name in self.input_widgets:
                    bui.textwidget(edit=self.input_widgets[attr_name], text=str(attr_value))

            bui.app.config['proto_saved_state'] = loaded_data
            bui.app.config.commit()

            DisplayScreenMessage(f"Loaded {preset_key}.")
            PlayUserInterfaceSound('gunCocking')
            ClosePresetDialog(False)

        bui.buttonwidget(
            parent=preset_root,
            position=(button_width + 25, 10),
            color=ACTIVE_THEME_CLASS.TINT_COLOR,
            textcolor=ACTIVE_THEME_CLASS.TEXT_COLOR,
            texture=bui.gettexture('white'),
            size=(button_width, 30),
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_CIRCLE_BUTTON) + ' ',
            enable_sound=False,
            on_activate_call=LoadSelectedPreset
        )

    def CloseUserInterface(self) -> None:
        self.GatherInterfaceData()
        bui.containerwidget(edit=self.root_container, transition='out_left')
        PlayUserInterfaceSound('laser')
        if self.state_monitor_timer:
            self.state_monitor_timer = None
        self.network_manager.DetachUI()

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(ba.Plugin):
    def has_settings_ui(self) -> bool:
        return True

    def show_settings_ui(self, source_widget=None) -> None:
        ProtoUserInterfaceController()

    def __init__(self) -> None:
        import _babase

        original_terminal_adder = getattr(_babase, 'dev_console_add_python_terminal')

        def WrappedTerminalAdder(*args, **kwargs):
            try:
                return original_terminal_adder(*args, **kwargs)
            except RuntimeError:
                pass

        setattr(_babase, 'dev_console_add_python_terminal', WrappedTerminalAdder)

        def ConsoleCommandInterceptor(input_text: str):
            if input_text.lower() == 'proto()':
                _babase.set_dev_console_input_text('')
                ProtoUserInterfaceController()

        from babase._ui import DevConsoleStringEditAdapter
        original_apply = getattr(DevConsoleStringEditAdapter, '_do_apply')

        def HookedApply(instance, input_text):
            original_apply(instance, input_text)
            ConsoleCommandInterceptor(input_text)

        setattr(DevConsoleStringEditAdapter, '_do_apply', HookedApply)

        print(f"Proto v{ApplicationConfiguration.CLIENT_VERSION} ({ApplicationConfiguration.REVISION_COUNTER}) - Type Proto() in dev console or access via settings UI.")

        if ApplicationConfiguration.AUTOSTART_ENABLED:
            bui.apptimer(1.0, ProtoUserInterfaceController)

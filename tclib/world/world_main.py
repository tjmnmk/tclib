# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""

import copy
from Crypto.Hash import SHA
from Crypto.Random import random as c_random

from tclib.shared.common import *
from connect import *
from player import *
from world_prototype import *
from callback import *
from tclib.shared.modules import monotonic_time

from tclib.world.world_guild import *
from tclib.world.world_channel import *
from tclib.world.world_chat import *
from tclib.world.world_misc import *
from tclib.world.world_prototype import *
from tclib.shared.opcodes_translate import *

RECV_LOOP_SLEEP = 0.2
WAIT_FUNC_SLEEP = 0.2
WAIT_FUNC_DEFAULT_TIMEOUT = 60
NAME_QUERY_TIMEOUT = 20

class NothingToReturn(object):
    def __init__(self):
        raise NotImplementedError

class World(threading.Thread,
            WorldChannel,
            WorldChat,
            WorldGuild,
            WorldMisc,
            WorldPrototype):
    """
    Attributes
    ----------
    callback : Callback
        See Callback class
    """
    
    def __init__(self, host, port, acc_name, S_hash, ver, realm_id):
        """
        Parameters
        ----------
        host : str
        port : int
        acc_name : str
        S_hash : str
        ver : WoWVersions
        realm_id : int
        """
        
        threading.Thread.__init__(self)
        WorldChannel.__init__(self)
        WorldChat.__init__(self)
        WorldGuild.__init__(self)
        WorldMisc.__init__(self)
        
        self._acc_name = acc_name
        self._S_hash = S_hash
        self._ver = ver
        self._realm_id = realm_id
                
        self.callback = Callback()
        self._ping_counter = 0
        self._my_players = []
        self._my_player = None
        self._client_start_time = monotonic_time.monotonic_time()
        self._server_seed = ""
        self._player_cache = PlayerCache()
        
        self._char_enum_done = False
        self._login_verify_world_done = False
        
        self._die = False
        self._err = None
        
        self._world_connect = WorldConnect(self, host, port, acc_name, S_hash, ver)
        
    def run(self):
        self.callback.start()
        self._world_connect.start()
        
        try:
            self._worker()
        except StreamBrokenError as e:
            logging.getLogger("tclib").exception(e)
            self._err = e
        except Exception as e:
            logging.getLogger("tclib").exception(e)
            self._err = StreamBrokenError(e)
            raise
        finally:
            self._world_connect.die()
            self.callback.die()
            self._world_connect.join()
            self.callback.join()
        
    def disconnect(self):
        """
        Disconnect
        """
        
        self._die = True
        self.join()
        
    def _worker(self):
        self._world_connect.err()
        
        while 1:
            if self._die:
                return
            self._world_connect.err()           
            cmd, buff = self._world_connect.recv_msg()
            if cmd == None:
                time.sleep(RECV_LOOP_SLEEP)
                continue
            if self._ver >= EXPANSION_CATA:
                try:
                    cmd = opcode_translate_cata_wotlk(cmd)
                except OPCODENotImplementedError:
                    continue

            handler, required_flags = WORLD_HANDLERS.get(cmd, (None, None))
            if handler:
                ret = handler(self, cmd, buff)
                if ret != None:
                    try:
                        self.callback.call(cmd, *ret)
                    except TypeError:
                        self.callback.call(cmd, ret)
                
    def _send(self, cmd, buff = bytebuff(), correct_cmd = True):
        """
        Forward packet to WorldConnect.
        
        Parameters
        ----------
        cmd : int
        buff : bytebuff
        correct_cmd : bool
        """
        
        if self._ver >= EXPANSION_CATA and correct_cmd:
            cmd = opcode_translate_wotlk_cata(cmd)
        self._world_connect.send_msg(cmd, buff)
                
    def _handle_auth_challange(self, cmd, buff):
        """
        Very first message! Called from WorldConnect.
        
        SMSG_AUTH_CHALLENGE
        
        Returns
        ----------
        self._server_seed : str
            some crypto shit
        seed1 : str
            some crypto shit
        seed2 : str
            some crypto shit
        """
        
        if self._ver == EXPANSION_PANDA:
            buff.skip(2)
            buff.skip(8 * 4)
            buff.skip(1)
            self._server_seed = buff.get("4s")
        if self._ver == EXPANSION_CATA:
            seed1 = buff.get("16s")
            seed2 = buff.get("16s")
            self._server_seed = buff.get("4s")
            buff.skip(1)
        elif self._ver == EXPANSION_WOTLK:
            buff.skip(4)
            self._server_seed = buff.get("4s")
            seed1 = buff.get("16s")
            seed2 = buff.get("16s")
        else:
            self._server_seed = buff.get("4s")
            seed1 = None
            seed2 = None
        
        self._send_auth_session()
        
        return self._server_seed, seed1, seed2
                
    def _send_auth_session(self):
        """
        CMSG_AUTH_SESSION
        """
        buff = bytebuff()
        client_seed = int_to_bytes(c_random.getrandbits(4*8), 4, "little")
        K = SHA.new(self._acc_name + "\0" * 4 + client_seed + self._server_seed + self._S_hash).digest()
        
        if self._ver == EXPANSION_PANDA:
            buff.add_zeros(4)
            buff.add("s", K[14])
            buff.add("s", K[8])
            buff.add_zeros(4)
            buff.add("s", K[10])
            buff.add("s", K[19])
            buff.add("s", K[16])
            buff.add("s", K[13])
            buff.add("s", K[4])
            buff.add_zeros(1)
            buff.add("s", K[9])
            buff.add("s", K[0])
            buff.add("4s", client_seed)
            buff.add("s", K[5])
            buff.add("s", K[2])
            buff.add("H", self._ver.get_build())
            buff.add("s", K[12])
            buff.add_zeros(4)
            buff.add("s", K[12])
            
    recvPacket >> digest[10];
    recvPacket >> digest[19];
    recvPacket >> digest[16];
    recvPacket >> digest[13];
    recvPacket >> digest[4];
    recvPacket.read_skip<uint8>();
    recvPacket >> digest[9];
    recvPacket >> digest[0];
    recvPacket >> clientSeed;
    recvPacket >> digest[5];
    recvPacket >> digest[2];
    recvPacket >> clientBuild;
    recvPacket >> digest[12];
    recvPacket.read_skip<uint32>();
    recvPacket >> digest[18];
    recvPacket >> digest[17];
    recvPacket >> digest[11];
    recvPacket.read_skip<uint64>();
    recvPacket >> digest[7];
    recvPacket >> digest[1];
    recvPacket >> digest[3];
    recvPacket.read_skip<uint8>();
    recvPacket >> digest[6];
    recvPacket.read_skip<uint32>();
    recvPacket >> digest[15];
        elif self._ver == EXPANSION_CATA:
            buff.add_zeros(9)
            buff.add("s", K[10])
            buff.add("s", K[18])
            buff.add("s", K[12])
            buff.add("s", K[5])
            buff.add_zeros(8)
            buff.add("s", K[15])
            buff.add("s", K[9])
            buff.add("s", K[19])
            buff.add("s", K[4])
            buff.add("s", K[7])
            buff.add("s", K[16])
            buff.add("s", K[3])
            buff.add("H", self._ver.get_build())
            buff.add("s", K[8])
            buff.add("I", self._realm_id)
            buff.add_zeros(1)
            buff.add("s", K[17])
            buff.add("s", K[6])
            buff.add("s", K[0])
            buff.add("s", K[1])
            buff.add("s", K[11])
            buff.add("4s", client_seed)
            buff.add("s", K[2])
            buff.add_zeros(4)
            buff.add("s", K[14])
            buff.add("s", K[13])
            buff.add_zeros(4)
            buff.add_bit(0)
            buff.add("12t", len(self._acc_name))
            buff.fill_byte()
            buff.add("k", self._acc_name)
        elif self._ver == EXPANSION_WOTLK:
            buff.add("I", self._ver.get_build())
            buff.add_zeros(4)
            buff.add("S", self._acc_name)
            buff.add_zeros(4)
            buff.add("4s", client_seed)
            buff.add_zeros(8)
            buff.add("I", self._realm_id)
            buff.add_zeros(8)
            buff.add("20s", K)
            buff.add_zeros(4)
        else:
            buff.add("I", self._ver.get_build())
            buff.add("I", self._realm_id)
            buff.add("S", self._acc_name)
            buff.add("4s", client_seed)
            buff.add("20s", K)
        
        self._send(CMSG_AUTH_SESSION, buff)

    def _send_name_query(self, guid):
        """
        CMSG_NAME_QUERY
        """
        
        buff = bytebuff()
        buff.add("Q", guid)
        self._send(CMSG_NAME_QUERY, buff)
        
    def _handle_name_query_response(self, cmd, buff):
        """
        SMSG_NAME_QUERY_RESPONSE
        
        Called from WorldConnect. Do not rename!
        Contain player info.
               
        Parameters
        ----------
        buff : bytebuff
        
        Returns
        ----------
        player : Player
        """
        
        buff._position = 0
        if self._ver >= EXPANSION_WOTLK:
            guid = buff.get("G")
            unknown = buff.get("B")
        else:
            guid = buff.get("Q")
            unknown = 0
        if unknown:
            player = UnknownPlayer()
            player.guid = guid
        else:
            player = Player()
            player.guid = guid
            player.name = buff.get("S")
            player.realm = buff.get("S")
            if self._ver >= EXPANSION_WOTLK:
                player.race = buff.get("B")
                player.gender = buff.get("B")
                player.game_class = buff.get("B")
            else:
                player.race = buff.get("I")
                player.gender = buff.get("I")
                player.game_class = buff.get("I")
            if self._ver >= EXPANSION_TBC:
                player.declined = buff.get("B")
        
        self._player_cache.add(player)
        self.callback.call(SMSG_NAME_QUERY_RESPONSE, player) # little hack, because called from WorldConnect return is not enough.
        
    def cache_player(self, guid):
        """
        Just alias for _send_name_query
        """
        
        self._send_name_query(guid)
        
    def get_player(self, guid, timeout = NAME_QUERY_TIMEOUT, default = "UnknownPlayer()"):
        """
        Get player info for player with given guid.
        
        Parameters
        ----------
        guid : int
        timeout : int
        default : object
        
        Returns
        ----------
        player: Player
        """
        
        player = self._player_cache.get_by_guid(guid)
        if player:
            return player
        
        self._send_name_query(guid)
        num_of_loops = timeout / RECV_LOOP_SLEEP + 1
        for i in xrange(int(num_of_loops)):
            time.sleep(RECV_LOOP_SLEEP)
            player = self._player_cache.get_by_guid(guid)
            if player:
                return player
        if default == "UnknownPlayer()":
            return UnknownPlayer()
        return default
        
    def get_player_name(self, guid, timeout = NAME_QUERY_TIMEOUT, default = "UnknownPlayer()"):
        """
        Get player name for player with given guid.
        
        Parameters
        ----------
        guid : int
        timeout : int
        default : object
        
        Returns
        ----------
        name: str
        """
        
        return self.get_player(guid, timeout = NAME_QUERY_TIMEOUT, default = "UnknownPlayer()").name

    def _handle_auth_response(self, cmd, buff):
        """
        SMSG_AUTH_RESPONSE
        
        .. todo:: implement queue len, etc.
        
        Returns
        ----------
        err : int
            AUTH_OK
            AUTH_FAILED
            AUTH_REJECT
            AUTH_BAD_SERVER_PROOF
            AUTH_UNAVAILABLE
            AUTH_SYSTEM_ERROR
            AUTH_BILLING_ERROR
            AUTH_BILLING_EXPIRED
            AUTH_VERSION_MISMATCH
            AUTH_UNKNOWN_ACCOUNT
            AUTH_INCORRECT_PASSWORD
            AUTH_SESSION_EXPIRED
            AUTH_SERVER_SHUTTING_DOWN
            AUTH_ALREADY_LOGGING_IN
            AUTH_LOGIN_SERVER_NOT_FOUND
            AUTH_WAIT_QUEUE
            AUTH_BANNED
            AUTH_ALREADY_ONLINE
            AUTH_NO_TIME
            AUTH_DB_BUSY
            AUTH_SUSPENDED
            AUTH_PARENTAL_CONTROL
            AUTH_LOCKED_ENFORCED
        """
        #err = buff.get("B")
        
        #if err == AUTH_OK:
        self._send_char_enum()
        #return err
        
    def _send_char_enum(self):
        """
        CMSG_CHAR_ENUM
        """

        self._send(CMSG_CHAR_ENUM)
        
    def _handle_char_enum(self, cmd, buff):
        """
        SMSG_CHAR_ENUM
        
        Contain list of yours character and some info about them.
        
        Returns
        ----------
        players : list of Players
        """
        
        def read_byte_if_needed(byte, need, buff):
            if byte in need:
                return (buff.get("B") ^ 1) << (byte * 8)
            return 0
        
        if self._ver >= EXPANSION_CATA:
            buff.skip(3)
            try:
                num_of_chars = buff.get("17t")
            except IndexError: #hotfix, rewrite
                self._my_players = []
                self._char_enum_done = True
                return []
        else:
            num_of_chars = buff.get("B")
        players = []
        if self._ver >= EXPANSION_CATA:
            player_packet_flags = []
            for i in range(num_of_chars):
                guid_to_read = []
                guild_guid_to_read = []
                name_len = 0
                if buff.get_bit(): guid_to_read.append(3)
                if buff.get_bit(): guild_guid_to_read.append(1)
                if buff.get_bit(): guild_guid_to_read.append(7)
                if buff.get_bit(): guild_guid_to_read.append(2)
                name_len = buff.get("7t")
                if buff.get_bit(): guid_to_read.append(4)
                if buff.get_bit(): guid_to_read.append(7)
                if buff.get_bit(): guild_guid_to_read.append(3)
                if buff.get_bit(): guid_to_read.append(5)
                if buff.get_bit(): guild_guid_to_read.append(6)
                if buff.get_bit(): guid_to_read.append(1)
                if buff.get_bit(): guild_guid_to_read.append(5)
                if buff.get_bit(): guild_guid_to_read.append(4)
                buff.skip_bits(1)
                if buff.get_bit(): guid_to_read.append(0)
                if buff.get_bit(): guid_to_read.append(2)
                if buff.get_bit(): guid_to_read.append(6)
                if buff.get_bit(): guild_guid_to_read.append(0)
                player_packet_flags.append((guid_to_read, guild_guid_to_read, name_len))
            buff.left_bits()
            
            for guid_to_read, guild_guid_to_read, name_len in player_packet_flags:
                player = Player()
                guid = 0
                guild_guid = 0
                player.game_class = buff.get("B")
                buff.skip((4 + 4 + 1) * 23)
                player.pet_familyid = buff.get("I")
                guild_guid |= read_byte_if_needed(2, guild_guid_to_read, buff)
                unk = buff.get("B")
                player.hair_style = buff.get("B")
                guild_guid |= read_byte_if_needed(3, guild_guid_to_read, buff)
                player.pet_id = buff.get("I")
                player.flags = buff.get("I")
                player.hair_color = buff.get("B")
                guid |= read_byte_if_needed(4, guid_to_read, buff)
                player.map_id = buff.get("I")
                guild_guid |= read_byte_if_needed(5, guild_guid_to_read, buff)
                player.z = buff.get("f")
                guild_guid |= read_byte_if_needed(6, guild_guid_to_read, buff)
                player.pet_level = buff.get("I")
                guid |= read_byte_if_needed(3, guid_to_read, buff)
                player.y = buff.get("f")
                unk2 = buff.get("I")
                player.hair_facial = buff.get("B")
                guid |= read_byte_if_needed(7, guid_to_read, buff)
                player.gender = buff.get("B")
                player.name = buff.get_raw(name_len)
                player.face = buff.get("B")
                guid |= read_byte_if_needed(0, guid_to_read, buff)
                guid |= read_byte_if_needed(2, guid_to_read, buff)
                guild_guid |= read_byte_if_needed(1, guild_guid_to_read, buff)
                guild_guid |= read_byte_if_needed(7, guild_guid_to_read, buff)
                player.x = buff.get("f")
                player.skin = buff.get("B")
                player.race = buff.get("B")
                player.level = buff.get("B")
                guid |= read_byte_if_needed(6, guid_to_read, buff)
                guild_guid |= read_byte_if_needed(4, guild_guid_to_read, buff)
                guild_guid |= read_byte_if_needed(0, guild_guid_to_read, buff)
                guid |= read_byte_if_needed(5, guid_to_read, buff)
                guid |= read_byte_if_needed(1, guid_to_read, buff)
                player.zone_id = buff.get("I")
                player.guid = guid
                
                self._player_cache.add(player)
                players.append(player)
        else:
            for i in range(num_of_chars):
                player = Player()
                player.guid =              buff.get("Q")
                player.name =              buff.get("S")
                player.race =              buff.get("B")
                player.game_class =        buff.get("B")
                player.gender =            buff.get("B")
                player.skin =              buff.get("B")
                player.face =              buff.get("B")
                player.hair_style =        buff.get("B")
                player.hair_color =        buff.get("B")
                player.hair_facial =       buff.get("B")
                player.level =             buff.get("B")
                player.zone_id =           buff.get("I")
                player.map_id =            buff.get("I")
                player.x =                 buff.get("f")
                player.y =                 buff.get("f")
                player.z =                 buff.get("f")
                player.guild_id =          buff.get("I")
                player.flags =             buff.get("I")
                if self._ver >= EXPANSION_WOTLK:
                    player.unk =               buff.get("I")
                player.unk2 =              buff.get("B")
                player.pet_id =            buff.get("I")
                player.pet_level =         buff.get("I")
                player.pet_familyid =      buff.get("I")
                if self._ver == EXPANSION_WOTLK:
                    buff.skip(207)
                elif self._ver == EXPANSION_TBC:
                    buff.skip(180)
                if self._ver == EXPANSION_VANILLA:
                    buff.skip(100)
            
                self._player_cache.add(player)
                players.append(player)
        
        self._my_players = players
        self._char_enum_done = True
        return players
    
    def get_my_player(self):
        """
        Returns
        ----------
        player : Player
        """
        
        assert(self._my_player != None)
        return self._my_player
            
    def _send_player_login(self, guid):
        """
        CMSG_PLAYER_LOGIN
        
        Parameters
        ----------
        guid : int
        """
        
        buff = bytebuff()
        if self._ver >= EXPANSION_CATA:
            guid_packed = struct.pack("<Q", guid)
            for i in (2, 3, 0, 6, 4, 5, 1, 7):
                if ord(guid_packed[i]):
                    buff.add_bit(1)
                else:
                    buff.add_bit(0)
            
            for i in (2, 7, 0, 3, 5, 6, 1, 4):
                if ord(guid_packed[i]):
                    buff.add("B", ord(guid_packed[i]) ^ 1)   
        else:
            buff.add("Q", guid)
        self._send(CMSG_PLAYER_LOGIN, buff)
        
    def _handle_login_verify_world(self, cmd, buff):
        """
        SMSG_LOGIN_VERIFY_WORLD
        
        Contain list of yours character and some info about them.
        
        Returns
        ----------
        map : int
        position_x : float
        position_y : float
        position_z : float
        position_o : float
            orientation
        """
        
        map = buff.get("I")
        position_x = buff.get("f")
        position_y = buff.get("f")
        position_z = buff.get("f")
        position_o = buff.get("f")
        
        self._login_verify_world_done = True
        return map, position_x, position_y, position_z, position_o
        
    def _send_ping(self):
        """
        CMSG_PING
        
        .. todo:: Implement latency
        """
        
        buff = bytebuff()
        latency = 0
        buff.add("I", latency)
        buff.add("I", self._ping_counter)
        self._send(CMSG_PING, buff)
        
    def _handle_pong(self, cmd, buff):
        """
        SMSG_PONG
        
        .. todo:: Implement latency
        
        Returns
        ----------
        ping_counter : int
        latency      : int
            Not implemented
        """
        
        ping_counter = buff.get("I")
        latency = 0
        return ping_counter, latency

    def _handle_time_sync_req(self, cmd, buff):
        """
        SMSG_TIME_SYNC_REQ
        
        Returns
        ----------
        time_sync_counter : int
        """
        
        time_sync_counter = buff.get("I")
        self._send_time_sync_response(time_sync_counter)
        return time_sync_counter
    
    def _send_time_sync_response(self, time_sync_counter):
        """
        CMSG_TIME_SYNC_RESP
        """
        
        buff = bytebuff()
        tick = (monotonic_time.monotonic_time() - self._client_start_time) * 1000
        buff.add("I", time_sync_counter)
        buff.add("I", tick)
        self._send(CMSG_TIME_SYNC_RESP, buff)
        
    def login(self, player):
        """
        Login.
        
        Parameters
        ----------
        player : Player or str
        
        Raises
        ------
        BadPlayer
        """
        
        if isinstance(player, str):
            player, player_name = Player(), player
            player.name = player_name
        
        for player_c in self._my_players:
            if player_c.name == player.name:
                self._my_player = player_c
                self._send_player_login(player_c.guid)
                return
        raise BadPlayer(player)
    
    def wait_get_my_players(self, timeout = WAIT_FUNC_DEFAULT_TIMEOUT):
        """
        _handle_char_enum; SMSG_CHAR_ENUM
        
        Returns
        ----------
        _my_players : dict of Players
        
        Raises
        ------
        TimeoutError
        StreamBrokenError
        """
        
        start_time = monotonic_time.monotonic_time()
        while 1:
            self.err()
            if self._char_enum_done:
                _my_players_copy = []
                for player in self._my_players:
                    _my_players_copy.append(copy.deepcopy(player))
                return _my_players_copy
            if start_time + timeout < monotonic_time.monotonic_time():
                break
            time.sleep(WAIT_FUNC_SLEEP)
        raise TimeoutError()
    
    def wait_when_login_complete(self, timeout = WAIT_FUNC_DEFAULT_TIMEOUT):
        """
        _handle_login_verify_world; SMSG_LOGIN_VERIFY_WORLD
        
        Raises
        ------
        TimeoutError
        StreamBrokenError
        """
        
        start_time = monotonic_time.monotonic_time()
        while 1:
            self.err()
            if self._login_verify_world_done:
                break
            if start_time + timeout < monotonic_time.monotonic_time():
                break
            time.sleep(WAIT_FUNC_SLEEP)
    
    def err(self):
        """
        Raises
        ------
        StreamBrokenError
        """

        if self._err:
            raise self._err

# CMD : (HANDLER, REQUIRED_FLAGS)        
WORLD_HANDLERS = {
SMSG_CHAR_ENUM               : (World._handle_char_enum,            0),
SMSG_PONG                    : (World._handle_pong,                 0),
SMSG_AUTH_RESPONSE           : (World._handle_auth_response,        0),
SMSG_NAME_QUERY_RESPONSE     : (World._handle_name_query_response,  0),
SMSG_AUTH_CHALLENGE          : (World._handle_auth_challange,       0),
SMSG_TIME_SYNC_REQ           : (World._handle_time_sync_req,        0),
SMSG_MESSAGECHAT             : (WorldChat._handle_message_chat,     0),
SMSG_GM_MESSAGECHAT          : (WorldChat._handle_message_chat,     0),
CMSG_WHO                     : (WorldMisc._handle_who,              0),
SMSG_PLAYED_TIME             : (WorldMisc._handle_played_time,      0),
SMSG_CHANNEL_NOTIFY          : (WorldChannel._handle_notify_packet, 0),
SMSG_GUILD_EVENT             : (WorldGuild._handle_guild_event,     0),
SMSG_GUILD_QUERY_RESPONSE    : (WorldGuild._handle_guild_query,     0),
SMSG_LOGIN_VERIFY_WORLD      : (World._handle_login_verify_world,   0),
SMSG_WHO                     : (WorldMisc._handle_who,              0),
SMSG_CHANNEL_LIST            : (WorldChannel._handle_channel_list,  0),
}
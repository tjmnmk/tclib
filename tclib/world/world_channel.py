# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""

import itertools

from tclib.shared.common import *
from tclib.shared.bytebuff import *
from tclib.world.world_prototype import *
from tclib.world.player import *
from tclib.shared.modules import monotonic_time

class WorldChannel(WorldPrototype):
    def __init__(self):
        self._channel_list = []
        self._channel_list_lock = threading.RLock()
        
    def _register_channel(self, name):
        name = name.lower()
        if self.get_channel_by_name(name):
            return False
        
        with self._channel_list_lock:
            ids = []
            for channel in self._channel_list:
                ids.append(channel.id)
            for i in itertools.count(1):
                if i not in ids:
                    channel = Channel(name, i, self)
                    self._channel_list.append(channel)
                    return channel
                    
    def _unregister_channel(self, name):
        name = name.lower()
        channel = self.get_channel_by_name(name)
        if not channel:
            return False
        
        with self._channel_list_lock:
            self._channel_list.remove(channel)
        return True
    
    def send_channel_list(self, name = None):
        """
        CMSG_CHANNEL_LIST (CMSG_CHANNEL_DISPLAY_LIST)
        
        Parameters
        ----------
        name : str
            channel name; if None send for all joined channels
        """
        
        if name == None:
            for channel in self.get_all_channels():
                assert(channel.name != None)
                self.send_channel_list(channel.name)
            return
        
        assert(self._ver < EXPANSION_CATA or len(name) < 2**8)
        buff = bytebuff()
        name = name.lower()
        
        if self._ver >= EXPANSION_CATA:
            buff.add("<B", len(name))
            buff.add_raw(name)
        else:
            buff.add("S", name)
        
        self._send(CMSG_CHANNEL_LIST, buff)
        
    def _handle_channel_list(self, cmd, buff, timeout = 20):
        """
        SMSG_CHANNEL_LIST
        
        Returns
        ----------
        channel : Channel
        players: list of Player
        """
        
        buff.skip(1)
        channel_name = buff.get("S").lower()
        channel = self.get_channel_by_name(channel_name)
        buff.skip(1)
        list_size = buff.get("I")
        
        player_guid_list = []
        for i in range(list_size):
            player_guid_list.append(buff.get("Q"))
            buff.skip(1)
            
        players = []
        for guid in player_guid_list:
            self.cache_player(guid)
        time_now = monotonic_time.monotonic_time()
        for guid in player_guid_list:
            if time_now + timeout < monotonic_time.monotonic_time():
                return channel, players
            players.append(self.get_player(guid, timeout = 1))
            
        return channel, players
        
    def get_all_channels(self):
        """
        Returns
        ----------
        list of channels
            list of all joined channels
        """
        
        with self._channel_list_lock:
            return list(self._channel_list) #copy list
    
    def get_channel_by_name(self, name):
        """
        Parameters
        ----------
        name : str
            channel name
        
        Returns
        ----------
        channel : Channel or None
            Return none if channel not found.
        """
        
        name = name.lower()
        with self._channel_list_lock:
            for channel in self._channel_list:
                if name.lower() == channel.name.lower():
                    return channel
        return None
        
    def send_join_channel(self, name, password = ""):
        """
        CMSG_JOIN_CHANNEL
        
        Parameters
        ----------
        name : str
        password : str
        """

        name = name.lower()
        
        buff = bytebuff()
        if self._ver >= EXPANSION_CATA:
            buff.add("I", 0)
            buff.add_bit(0) # unknown
            buff.add_bit(0) # unknown
            buff.add("8t", len(name))
            buff.add("8t", len(password))
            buff.fill_byte()
            buff.add("k", name)
            buff.add("k", password)
        elif self._ver >= EXPANSION_TBC:
            buff.add_zeros(6)
            buff.add("S", name.lower())
            buff.add("S", password)
        else:
            buff.add("S", name.lower())
            buff.add("S", password)
        
        self._send(CMSG_JOIN_CHANNEL, buff)
        
    def send_leave_channel(self, name):
        """
        CMSG_LEAVE_CHANNEL
        
        Parameters
        ----------
        name : str
        """
        
        name = name.lower()
        
        buff = bytebuff()
        if self._ver >= EXPANSION_CATA:
            buff.add("I", 0) # unknown
            buff.add("8t", len(name))
            buff.add("k", name)
        else:
            buff.add_zeros(4)
            buff.add("S", name)
        
        self._send(CMSG_LEAVE_CHANNEL, buff)

    def _handle_notify_packet(self, cmd, buff):
        """
        SMSG_CHANNEL_NOTIFY
        
        Returns
        ----------
        channel: Channel
        channel_ret : tuple
            See Channel._handle_notify
        """
        
        notify_type = buff.get("B")
        channel_name = buff.get("S").lower()
        if not channel_name:
            raise StreamBrokenError("SMSG_CHANNEL_NOTIFY; Missing channel name")
        buff.cut()
        channel = self.get_channel_by_name(channel_name)
        if not channel:
            channel = self._register_channel(channel_name)
        channel_ret = channel._handle_notify(notify_type, buff)
        if channel._destroy or not channel.joined:
            self._unregister_channel(channel_name)
            
        return channel, channel_ret
        
class Channel(object):
    """
    Attributes
    ----------
    name : str
    id : int
    ch_flags : int
        Channel flags.
    my_flags : int
        My flags.
    self.joined : bool
    """
    
    def __init__(self, channel_name, channel_id, world):
        """
        Parameters
        ----------
        channel_name : str
        channel_id : int
        world : World
        """
        self.name = channel_name
        self.id = channel_id
        self.ch_flags = CHANNEL_FLAG_NONE
        self.my_flags = MEMBER_FLAG_NONE
        self.joined = False
        self._destroy = False
        self._world = world
        
    def __hash__(self):
        """
        .. todo:: rewrite, slow
        """
        
        return hash("%d\0%s\0%d" % (self.id, self.name, hash(self._world)))
    
    def __eq__(self, cls):
        return isinstance(cls, self.__class__) \
               and self.id == cls.id \
               and self.name == cls.name \
               and self.world == cls.world
    
    def __ne__(self, cls):
        return not self.__eq__(cls)
    
    def __str__(self):
        return self.name
        
    def _handle_notify(self, notify_type, buff):
        """
        Implemented:
        CHAT_JOINED_NOTICE => $player joined channel.
        CHAT_LEFT_NOTICE => $player left channel.
        CHAT_PASSWORD_CHANGED_NOTICE => [$channel] Password changed by $player.
        CHAT_OWNER_CHANGED_NOTICE => [$channel] Owner changed to $player.
        CHAT_ANNOUNCEMENTS_ON_NOTICE => [$channel] Channel announcements enabled by $player.
        CHAT_ANNOUNCEMENTS_OFF_NOTICE => [$channel] Channel announcements disabled by $player.
        CHAT_PLAYER_ALREADY_MEMBER_NOTICE => [$channel] Player $player is already on the channel.
        CHAT_INVITE_NOTICE => $player has invited you to join the channel $channel.
        CHAT_NOT_IN_LFG_NOTICE => [$channel] You must be queued in looking for group before joining this channel.
        CHAT_VOICE_ON_NOTICE => [$channel] Channel voice enabled by $player.
        CHAT_VOICE_OFF_NOTICE => [$channel] Channel voice disabled by $player.
        CHAT_YOU_JOINED_NOTICE => Joined Channel: [$channel]
        CHAT_YOU_LEFT_NOTICE => Left Channel: [$channel]
        CHAT_WRONG_PASSWORD_NOTICE => Wrong password for $channel.
        CHAT_NOT_MEMBER_NOTICE => Not on channel $channel.
        CHAT_NOT_MODERATOR_NOTICE => Not a moderator of $channel.
        CHAT_NOT_OWNER_NOTICE => [$channel] You are not the channel owner.
        CHAT_MUTED_NOTICE => [$channel] You do not have permission to speak.
        CHAT_BANNED_NOTICE => [$channel] You are banned from that channel.
        CHAT_INVITE_WRONG_FACTION_NOTICE => Target is in the wrong alliance for $player.
        CHAT_WRONG_FACTION_NOTICE => Wrong alliance for $player.
        CHAT_INVALID_NAME_NOTICE => Invalid channel name.
        CHAT_NOT_MODERATED_NOTICE => $channel is not moderated
        CHAT_THROTTLED_NOTICE => [$channel] The number of messages that can be sent to this channel is limited, please wait to send another message.
        CHAT_NOT_IN_AREA_NOTICE => [$channel] You are not in the correct area for this channel.
        CHAT_PLAYER_NOT_FOUND_NOTICE => [$channel] Player $player was not found.
        CHAT_CHANNEL_OWNER_NOTICE => [$channel] Channel owner is $player.
        CHAT_PLAYER_NOT_BANNED_NOTICE => [$channel] Player $player is not banned.
        CHAT_PLAYER_INVITED_NOTICE => [$channel] You invited $player to join the channel
        CHAT_PLAYER_INVITE_BANNED_NOTICE => [$channel] $player has been banned.
        CHAT_MODE_CHANGE_NOTICE => $None
        CHAT_PLAYER_KICKED_NOTICE => [$channel] Player $player kicked by $player.
        CHAT_PLAYER_BANNED_NOTICE => [$channel] Player $player banned by $player.
        CHAT_PLAYER_UNBANNED_NOTICE => [$channel] Player %s unbanned by %s.
        
        Not implemented:
        CHAT_MODERATION_ON_NOTICE => [$channel] Channel moderation enabled by $player.
        CHAT_MODERATION_OFF_NOTICE => [$channel] Channel moderation disabled by $player.
        
        Returns
        ----------
        notify_type : int
        channel : Channel
            channel.name
            channel.id
            channel.ch_flags
            channel.my_flags
        data : dict
            CHAT_JOINED_NOTICE,
            CHAT_LEFT_NOTICE, 
            CHAT_PASSWORD_CHANGED_NOTICE, 
            CHAT_OWNER_CHANGED_NOTICE, 
            CHAT_ANNOUNCEMENTS_ON_NOTICE, 
            CHAT_ANNOUNCEMENTS_OFF_NOTICE, 
            CHAT_PLAYER_ALREADY_MEMBER_NOTICE, 
            CHAT_INVITE_NOTICE, 
            CHAT_NOT_IN_LFG_NOTICE, 
            CHAT_VOICE_ON_NOTICE, 
            CHAT_VOICE_OFF_NOTICE =>
            { 
            "player" : player 
            }
            CHAT_YOU_JOINED_NOTICE =>
            { "ch_flags" : int,
              "server_channel_id" : int
            }
            CHAT_YOU_LEFT_NOTICE =>
            {
            "ch_flags" : int 
            }
            CHAT_WRONG_PASSWORD_NOTICE, 
            CHAT_NOT_MEMBER_NOTICE, 
            CHAT_NOT_MODERATOR_NOTICE, 
            CHAT_NOT_OWNER_NOTICE, 
            CHAT_MUTED_NOTICE, 
            CHAT_BANNED_NOTICE, 
            CHAT_INVITE_WRONG_FACTION_NOTICE, 
            CHAT_WRONG_FACTION_NOTICE, 
            CHAT_INVALID_NAME_NOTICE, 
            CHAT_NOT_MODERATED_NOTICE, 
            CHAT_THROTTLED_NOTICE, 
            CHAT_NOT_IN_AREA_NOTICE =>
            {
            }
            CHAT_PLAYER_NOT_FOUND_NOTICE, 
            CHAT_CHANNEL_OWNER_NOTICE, 
            CHAT_PLAYER_NOT_BANNED_NOTICE, 
            CHAT_PLAYER_INVITED_NOTICE, 
            CHAT_PLAYER_INVITE_BANNED_NOTICE =>
            { "player" : player }
            CHAT_MODE_CHANGE_NOTICE =>
            { "my_flags" : my_flags }
            CHAT_PLAYER_KICKED_NOTICE, 
            CHAT_PLAYER_BANNED_NOTICE, 
            CHAT_PLAYER_UNBANNED_NOTICE =>
            { 
            "player" : player,
            "moderator" : player
            }
        """
        
        if notify_type in (CHAT_JOINED_NOTICE,
                           CHAT_LEFT_NOTICE, 
                           CHAT_PASSWORD_CHANGED_NOTICE, 
                           CHAT_OWNER_CHANGED_NOTICE, 
                           CHAT_ANNOUNCEMENTS_ON_NOTICE, 
                           CHAT_ANNOUNCEMENTS_OFF_NOTICE, 
                           CHAT_PLAYER_ALREADY_MEMBER_NOTICE, 
                           CHAT_INVITE_NOTICE, 
                           CHAT_NOT_IN_LFG_NOTICE, 
                           CHAT_VOICE_ON_NOTICE, 
                           CHAT_VOICE_OFF_NOTICE):
            player = Player()
            player_guid = buff.get("Q")
            player = self._world.get_player(player_guid)
            return notify_type, {
                                "player"      : player,
                                }
            
        if notify_type == CHAT_YOU_JOINED_NOTICE:
            self.joined = True
            self.ch_flags = buff.get("B")
            server_channel_id = buff.get("I")
            return notify_type, { 
                                "ch_flags" : self.ch_flags,
                                "server_channel_id" : server_channel_id,
                                }
            
        if notify_type == CHAT_YOU_LEFT_NOTICE:
            self.joined = False
            self._destroy = True
            server_channel_id = buff.get("I")
            unk = buff.get("B")
            return notify_type, { 
                                "ch_flags" : self.ch_flags 
                                }
        
        if notify_type in (CHAT_WRONG_PASSWORD_NOTICE, 
                           CHAT_NOT_MEMBER_NOTICE, 
                           CHAT_NOT_MODERATOR_NOTICE, 
                           CHAT_NOT_OWNER_NOTICE, 
                           CHAT_MUTED_NOTICE, 
                           CHAT_BANNED_NOTICE, 
                           CHAT_INVITE_WRONG_FACTION_NOTICE, 
                           CHAT_WRONG_FACTION_NOTICE, 
                           CHAT_INVALID_NAME_NOTICE, 
                           CHAT_NOT_MODERATED_NOTICE, 
                           CHAT_THROTTLED_NOTICE, 
                           CHAT_NOT_IN_AREA_NOTICE):
            return notify_type, {}
        
        if notify_type in (CHAT_PLAYER_NOT_FOUND_NOTICE, 
                           CHAT_CHANNEL_OWNER_NOTICE, 
                           CHAT_PLAYER_NOT_BANNED_NOTICE, 
                           CHAT_PLAYER_INVITED_NOTICE, 
                           CHAT_PLAYER_INVITE_BANNED_NOTICE):
            player = Player()
            player.name = buff.get("S")
            return notify_type, { 
                                "player"      : player,
                                }
        
        if notify_type == CHAT_MODE_CHANGE_NOTICE:
            player = Player()
            player_guid = buff.get("Q")
            old_flags = buff.get("B")
            self.my_flags = buff.get("B")
            player = self._world.get_player(player_guid)
            return notify_type, {
                                "player"      : player,
                                "old_flags"   : old_flags,
                                "new_flags"   : self.my_flags,
                                }
        
        if notify_type in (CHAT_PLAYER_KICKED_NOTICE, 
                           CHAT_PLAYER_BANNED_NOTICE, 
                           CHAT_PLAYER_UNBANNED_NOTICE):
            player_guid = buff.get("Q")
            player = self._world.get_player(player_guid)
            moderator_guid = buff.get("Q")
            moderator = self._world.get_player(moderator_guid)
            return notify_type, { 
                                "player" : player,
                                "moderator" : moderator
                                }

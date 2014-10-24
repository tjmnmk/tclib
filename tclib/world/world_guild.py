# -*- coding: utf-8 -*-

from tclib.shared.bytebuff import *
from tclib.world.world_prototype import *

class WorldGuild(WorldPrototype):
    def __init__(self):
        WorldPrototype.__init__(self)
        
    def _handle_guild_event(self, cmd, buff):
        """
        SMSG_GUILD_EVENT
        
        Implemented: GE_SIGNED_ON, GE_SIGNED_OFF, GE_MOTD
        
        GE_SIGNED_ON: [$Player] has come online.
        GE_SIGNED_OFF: [$Player] has come offline.
        GE_MOTD: Guild Message of the Day: $msg
        
        Returns
        ----------
        event : int
        data : dict
            GE_SIGNED_ON, GE_SIGNED_OFF =>
            { "name"  : str,
              "guid"  : int
              }
            GE_MOTD =>
            {
            "motd"  : str
            }
        """
        
        event = buff.get("B")
        count = buff.get("B")
        if event in (GE_SIGNED_ON, GE_SIGNED_OFF):
            if count != 1:
                raise StreamBrokenError()
            
            name = buff.get("S")
            guid = buff.get("Q")
            return event,  { "name"  : name,
                             "guid"  : guid
                           }
                
        if event == GE_MOTD:
            if count != 1:
                raise StreamBrokenError()
            motd = buff.get("S")
            return event, { "motd"  : motd }
        
        
    def send_guild_query(self, guild_id = None):
        """
        CMSG_GUILD_QUERY
        
        Parameters
        ----------
        guild_id : int
        """
        
        if guild_id == None:
            guild_id = self._my_player.guild_id
        
        buff = bytebuff()
        buff.add("I", guild_id)
        self._connection.send(CMSG_GUILD_QUERY, buff)
        
    def _handle_guild_query(self, cmd, buff):
        """
        SMSG_GUILD_QUERY_RESPONSE
        
        Returns
        ----------
        guild_id     : int
        player_guild : bool
        guild_name   : str
        rank_names   : list of str
        """
        
        buff = bytebuff()
        guild_id = buff.get("I")
        guild_name = buff.get("S")
        player_guild = False
        if guild_id == self._my_player.guild_id:
            player_guild = True
        
        rank_names = []
        guild_ranks_max_count = 10
        for i in range(guild_ranks_max_count):
            rank_name = buff.get("S")
            if not rank_name:
                break
            
            rank_names.append()
            
        return guild_id, player_guild, guild_name, rank_names
            
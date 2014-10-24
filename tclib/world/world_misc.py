# -*- coding: utf-8 -*-

from tclib.shared.common import *
from tclib.shared.bytebuff import *
from tclib.world.world_prototype import *
from tclib.world.player import *

class WorldMisc(WorldPrototype):   
    def send_who(self, minlevel = 0, maxlevel = 100, racemask = 0xFFFFFFFF, classmask = 0xFFFFFFFF, player_name = "", guild_name = "", user_strings = None, zones = None):
        """
        CMSG_WHO
    
        Parameters
        ----------
        minlevel : int
        maxlevel : int
        racemask : int
        classmask : int
        player_name : str
        guild_name : str
        user_strings : list of strs
        zones : list of ints
        """

        if user_strings == None:
            user_strings = ()
        if zones == None:
            zones = ()
            
        assert(len(user_strings) <= 4)
        assert(len(zones) <= 10)
        
        buff = bytebuff()
        buff.add("I", minlevel)
        buff.add("I", maxlevel)
        buff.add("S", player_name)
        buff.add("S", guild_name)
        buff.add("I", racemask)
        buff.add("I", classmask)
        buff.add("I", len(zones))
        for i in zones:
            buff.add("I", i)
        buff.add("I", len(user_strings))
        for string in user_strings:
            buff.add("S", string)
            
        self._send(CMSG_WHO, buff)
        
    def _handle_who(self, cmd, buff):
        """
        SMSG_WHO
        
        [Player]: Level 0 Orc Shaman <Guild> - Oggrimar
        1 player total
        
        Parameters
        ----------
        buff : bytebuff
        
        Returns
        ----------
        players : list of player
        """

        display_count = buff.get("I")
        match_count = buff.get("I")
        
        players = []
        for i in range(display_count):
            p = Player()
            p.name = buff.get("S")
            p.guild_name = buff.get("S")
            p.level = buff.get("I")
            p.game_class = buff.get("I")
            p.race = buff.get("I")
            p.gender = buff.get("B")
            p.zone_id = buff.get("I")
            players.append(p)
            
        return players

    def send_contact_list(self):
        """
        CMSG_CONTACT_LIST
        """
        
        buff = bytebuff()
        buff.add("I", 1) #unknown, always 1
        self._connection.send(CMSG_CONTACT_LIST, buff)
        
    def send_add_ignore(self, player_name):
        """
        CMSG_ADD_IGNORE
        
        Parameters
        ----------
        player_name : str
        """
        
        buff = bytebuff()
        buff.add("S", player_name)
        self._connection.send(CMSG_ADD_IGNORE, buff)
        
    def send_played_time(self, show = True):
        """
        CMSG_PLAYED_TIME
        
        Parameters
        ----------
        show : bool
        """
        
        buff = bytebuff()
        buff.add("B", int(show))
        self._connection.send(CMSG_PLAYED_TIME, buff)
        
    def _handle_played_time(self, cmd, buff):
        """
        SMSG_PLAYED_TIME
        
        Total time played: 0 days, 0 hour, 0 minutes, 0 seconds
        Time played this leve: 0 days, 0 hour, 0 minutes, 0 seconds
        
        Returns
        ----------
        played_total : int
            seconds; 
        played_level : int
            seconds; 
        show : bool
        """
        
        played_total = buff.get("I")
        played_level = buff.get("I")
        show = bool(buff.get("B"))
        
        return played_total, played_level, show
    
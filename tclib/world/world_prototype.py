# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""


from tclib.shared.common import *
from tclib.shared.const import *


class UnknownPlayer_SMP(object):
    pass


class WorldPrototype(object):  
    def __init__(self):
        self._my_player = NotImplementedVar
        self._ver = NotImplementedVar
        
    def _send(self, cmd, buff, correct_opcode = True):
        raise NotImplementedError()
    
    def get_player(self, guid, timeout = 20, default = UnknownPlayer_SMP):
        raise NotImplementedError()
    
    def get_player_name(self, guid, timeout = 20, default = UnknownPlayer_SMP):
        raise NotImplementedError()
    
    def cache_player(self, guid):
        raise NotImplementedError()

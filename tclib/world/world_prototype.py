# -*- coding: utf-8 -*-

from tclib.shared.common import *
from tclib.shared.const import *


class WorldPrototype(object):  
    def __init__(self):
        self._my_player = NotImplementedVar
        self._ver = NotImplementedVar
        
    def _send(self, cmd, buff, correct_opcode = True):
        raise NotImplementedError()
    
    def get_player(self, guid, timeout = 20, default = "UnknownPlayer()"):
        raise NotImplementedError()
    
    def get_player_name(self, guid, timeout = 20, default = "UnknownPlayer()"):
        raise NotImplementedError()
    
    def cache_player(self, guid):
        raise NotImplementedError()
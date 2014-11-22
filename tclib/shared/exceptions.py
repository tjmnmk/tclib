# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""

class LogonChallangeError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)
        
class LogonProofError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class OPCODENotImplementedError(Exception):
    pass

class StreamBrokenError(Exception):
    pass

class CryptoError(Exception):
    pass

class BadPlayer(Exception):
    pass

class TimeoutError(Exception):
    pass

class WoWVersionsError(Exception):
    pass
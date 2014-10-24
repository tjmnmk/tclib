# -*- coding: utf-8 -*-

class LogonChallangeError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value
        
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
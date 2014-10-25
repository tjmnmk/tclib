# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""

import binascii
import threading

from Crypto.Hash import SHA, HMAC
from Crypto.Cipher import ARC4
from tclib.shared.common import *

class CryptoPrototype(object):
    def __init__(self, S_hash):
        """
        Parameters
        ----------
        S_hash : str
            Provided by Realm.
        ver : WoWVersions
        """
        
        self._decrypt_lock = threading.RLock()
        self._encrypt_lock = threading.RLock()
        
    def decrypt(self):
        """
        Decrypt data
        
        Parameters
        ----------
        data : str
            encrypted data
        
        Returns
        -------
        data : str
            decrypted data
        """
        
        raise NotImplementedError()
        
    def encrypt(self, data):
        """
        Encrypt data
        
        Parameters
        ----------
        data : str
            decrypted data
        
        Returns
        -------
        data : str
            encrypted data
        """
        
        raise NotImplementedError()
        
class Crypto_WOTLK(CryptoPrototype):
    def __init__(self, S_hash):
        """
        Parameters
        ----------
        S_hash : str
            Provided by Realm.
        ver : WoWVersions
        """
        CryptoPrototype.__init__(self, S_hash)

        def compute_hmac(key):
            hash_i = HMAC.new(key, digestmod = SHA)
            hash_i.update(S_hash)
            return hash_i.digest()
            
        encrypt_hmac = compute_hmac(self._ENCRYPTION_KEY)
        decrypt_hmac = compute_hmac(self._DECRYPTION_KEY)
        
        self._encrypt_i = ARC4.new(encrypt_hmac)
        self._decrypt_i = ARC4.new(decrypt_hmac)
        
        zeros = "\0" * 1024
        self.decrypt(zeros)
        self.encrypt(zeros)
        
    def decrypt(self, data):
        """
        Decrypt data
        
        Parameters
        ----------
        data : str
            encrypted data by arc4
        
        Returns
        -------
        data : str
            decrypted data
        """
        
        with self._decrypt_lock:
            data = self._decrypt_i.decrypt(data)
        return data
    
    def encrypt(self, data):
        """
        Encrypt data
        
        Parameters
        ----------
        data : str
            decrypted data
        
        Returns
        -------
        data : str
            encrypted data by arc4
        """
        
        with self._encrypt_lock:
            data = self._encrypt_i.encrypt(data)
        return data
    
    _DECRYPTION_KEY = "\xCC\x98\xAE\x04\xE8\x97\xEA\xCA\x12\xDD\xC0\x93\x42\x91\x53\x57"
    _ENCRYPTION_KEY = "\xC2\xB3\x72\x3C\xC6\xAE\xD9\xB5\x34\x3C\x53\xEE\x2F\x43\x67\xCE"
    
    
class Crypto_VANILLA(CryptoPrototype):
    def __init__(self, S_hash):
        CryptoPrototype.__init__(self, S_hash)
        
        self._key = S_hash
        self._lock = threading.RLock()
        
        self._send_i = 0
        self._send_j = 0
        self._recv_i = 0
        self._recv_j = 0
        
    def decrypt(self, data):
        decrypted_data = ""
        with self._lock:
            for ch in data:
                self._recv_i %= len(self._key)
                x = (ord(ch) - self._recv_j) ^ ord(self._key[self._recv_i])
                x %= 256
                self._recv_i += 1
                self._recv_j = ord(ch)
                decrypted_data += chr(x)
        return decrypted_data
    
    def encrypt(self, data):
        encrypted_data = ""
        with self._lock:
            for ch in data:
                self._send_i %= len(self._key)
                x = (ord(ch) ^ ord(self._key[self._send_i])) + self._send_j
                x %= 256
                self._send_i += 1
                encrypted_data += chr(x)
                self._send_j = x
        return encrypted_data
    
    
class Crypto_TBC(Crypto_VANILLA, CryptoPrototype):
    def __init__(self, S_hash):
        CryptoPrototype.__init__(self, S_hash)
        Crypto_VANILLA.__init__(self, S_hash)
        
        hash_i = HMAC.new(self._RECV_SEED, digestmod = SHA)
        hash_i.update(S_hash)
        self._key = hash_i.digest()
    
    _RECV_SEED = "\x38\xA7\x83\x15\xF8\x92\x25\x30\x71\x98\x67\xB1\x8C\x04\xE2\xAA"
    
    
class Crypto_WOTLKTest(unittest.TestCase):
    def test_encrypt(self):
        ci = Crypto_WOTLK(self.S_hash)
        ci.encrypt("init")
        encrypted_data = ci.encrypt("test")
        encrypted_data_e = "\x2b\x01\x16\x93"
        self.assertEqual(encrypted_data, encrypted_data_e)
        
    def test_decrypt(self):
        ci = Crypto_WOTLK(self.S_hash)
        ci.decrypt("\x44\x55\x66")
        decrypted_data = ci.decrypt("\x11\x55\x77\x11")
        decrypted_data_e = "\x16\xe6\x82\x02"
        self.assertEqual(decrypted_data, decrypted_data_e)

    S_hash = "\x0a\xed\x8e\xb3\x4f\x8d\xe0\x1f\x2d\xdf\x4f\xba\x1b\x6a\x8c\xd8\xe9\xb6\xd0\x40\x2a\xd7\x9c\x3e\xb5\x74\x01\xf8\xba\x46\x26\x6e\xb3\x44\xc4\xe1\xce\xb7\xa5\xf0"
    
if __name__ == '__main__':
    unittest.main()

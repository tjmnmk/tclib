# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""


from Crypto.Hash import SHA
from Crypto.Random import random as c_random
from tclib.shared.common import *
import logging
import binascii


def srp6a(acc_name, acc_password, B_byte, g, N_byte, s_byte):
    """
    TrinityCore modified version
    
    .. a_link: https://en.wikipedia.org/wiki/Secure_Remote_Password_protocol
    
    Parameters
    ----------
    acc_name : str
    acc_password : str
    B_byte : str
    g : int
    N_byte : str
    s_byte : str
    
    Returns
    ----------
    M1_byte : str
    M2_byte : str
    A_byte : str
    crc_hash : str
    S_hash_byte : str
    
    Raises
    ------
    CryptoError
    """
    
    
    B = bytes_to_int(B_byte, "little")
    N = bytes_to_int(N_byte, "little")
    g_byte = int_to_bytes(g, 1, "little")
    
    logging.getLogger("tclib").info("SRP6A - SERVER:")
    logging.getLogger("tclib").info("B: %d", B)
    logging.getLogger("tclib").info("N: %d", N)
    logging.getLogger("tclib").info("g: %d", g)
    logging.getLogger("tclib").info("s: 0x%s", binascii.hexlify(s_byte))
    logging.getLogger("tclib").info("CLIENT:")
           
    if not B % N:
        raise CryptoError("SRP6A B % N != 0")
        
    k = 3
    
    auth = acc_name.upper() + ":" + acc_password.upper()
    authx_byte = SHA.new(auth).digest()
    
    a = c_random.getrandbits(19*8)
    logging.getLogger("tclib").info("a: %d", a)
    x_byte = SHA.new(s_byte + authx_byte).digest()
    x = bytes_to_int(x_byte, "little")
    v = pow(g, x, N)
    A = pow(g, a, N)
    A_byte = int_to_bytes(A, 32, "little")
    u_byte = SHA.new(A_byte + B_byte).digest()
    u = bytes_to_int(u_byte, "little")
    
    S = pow( (B - k * v), (a + u * x), N )
    S_byte = int_to_bytes(S, 32, "little")
    
    logging.getLogger("tclib").info("S: %d", S)
    
    S1 = ""
    S2 = ""
    for i in range(16):
        S1 += S_byte[i * 2]
        S2 += S_byte[i * 2 + 1]
        
    S1_hash_byte = SHA.new(S1).digest()
    S2_hash_byte = SHA.new(S2).digest()
    
    S_hash_byte = ""
    for i in range(20):
        S_hash_byte += S1_hash_byte[i]
        S_hash_byte += S2_hash_byte[i]
        
    logging.getLogger("tclib").info("S_hash: 0x%s", binascii.hexlify(S_hash_byte))
   
    acc_hash_byte = SHA.new(acc_name).digest()
    N_hash_byte = SHA.new(N_byte).digest()
    N_hash = bytes_to_int(N_hash_byte, "little")
    g_hash_byte = SHA.new(g_byte).digest()
    g_hash = bytes_to_int(g_hash_byte, "little")
    Ng_hash = N_hash ^ g_hash
    Ng_hash_byte = int_to_bytes(Ng_hash, 20, "little")
    
    logging.getLogger("tclib").info("Ng_hash: %d", Ng_hash)
    
    M1_byte = SHA.new(Ng_hash_byte + acc_hash_byte + s_byte + A_byte + B_byte + S_hash_byte).digest()
    M2_byte = SHA.new(A_byte + M1_byte + S_hash_byte).digest()
    
    logging.getLogger("tclib").info("M1: 0x%s", binascii.hexlify(M1_byte))
    logging.getLogger("tclib").info("M2: 0x%s", binascii.hexlify(M2_byte))
    
    crc_hash = "\0" * 20
    
    return M1_byte, M2_byte, A_byte, crc_hash, S_hash_byte


class Srp6aTest(unittest.TestCase):
    def setUp(self):
        c_random.getrandbits = self.fake_random
    
    @staticmethod
    def fake_random(size):
        """
        Chosen by fair dice roll. Guaranted to be random.
        """
        
        return 949989894894889489
    
    def test_srp6a(self):
        acc_name = "test"
        acc_password = "test2"
        B = "\x76\x37\x4b\xa9\xab\x39\x68\x03\x67\x80\xf9\x63\x76\x69\xd5\xef\x95\xcd\x7e\xe9\x51\x91\x53\x62\xbf\xca\xe7\xca\x08\x41\x6b\x2f"
        g = 7
        N = "\xb7\x9b\x3e\x2a\x87\x82\x3c\xab\x8f\x5e\xbf\xbf\x8e\xb1\x01\x08\x53\x50\x06\x29\x8b\x5b\xad\xbd\x5b\x53\xe1\x89\x5e\x64\x4b\x89"
        s = "\x05\xd8\x4b\x08\xef\xbc\x97\x6b\xa8\xae\xd7\xf9\x01\xcf\xaf\x34\x58\x06\xd9\xa8\x2c\xbc\x00\xfb\x12\xd9\x42\x1b\xdf\x40\xdb\xf1"
        M1, M2, A, crc_hash, S_hash = srp6a(acc_name, acc_password, B, g, N, s)
            
        M1_e = "\x0a\x2c\x18\x4d\x39\xd9\x5f\x89\x46\xed\x24\xd9\x74\x50\x63\xe1\x45\xce\xa4\x40"
        M2_e = "\x5a\xf2\x2d\x58\x4e\xf6\xbf\x85\x9b\x09\xf6\xc0\x23\x2f\x4d\xca\x35\x7a\x74\xa5"
        A_e = "\xf5\x3a\xec\x65\x00\xce\xa7\x90\x6a\xb1\xc8\xd7\x84\xa2\x01\x1c\x30\x0f\x3f\x26\x63\x80\xfb\x6f\xd7\xb9\xd6\x66\x4a\x29\x49\x89"
        crc_hash_e = "\0" * 20
        S_hash_e = "\x0a\xed\x8e\xb3\x4f\x8d\xe0\x1f\x2d\xdf\x4f\xba\x1b\x6a\x8c\xd8\xe9\xb6\xd0\x40\x2a\xd7\x9c\x3e\xb5\x74\x01\xf8\xba\x46\x26\x6e\xb3\x44\xc4\xe1\xce\xb7\xa5\xf0"

        self.assertEqual(M1, M1_e)
        self.assertEqual(M2, M2_e)
        self.assertEqual(A, A_e)
        self.assertEqual(crc_hash, crc_hash_e)
        self.assertEqual(S_hash, S_hash_e)


if __name__ == '__main__':
    unittest.main()
    
# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""


import struct, socket, errno
import os

from tclib.shared.bytebuff import bytebuff
from tclib.shared.common import *
from srp6a import *


NETWORK_SLEEP = 0.1


class Realm(threading.Thread):
    def __init__(self, acc_name, acc_password, host, port, ver):
        """
        Parameters
        ----------
        acc_name : str
        acc_password : str
        host : str
        port : int
        ver : WoWVersions
        """
        
        threading.Thread.__init__(self)
        
        self.realm_list_done = False
        self.logon_challange_done = False
        self.logon_proof_done = False
        self._realms = {}
        
        self._acc_name = acc_name[:255]
        self._acc_password = acc_password
        self._ver = ver
        self._host = host
        self._port = port
        
        self._connection = None
        self._die = False
        self._err = None
        
        self._M1 = ""
        self._M2 = ""
        self._A = ""
        self._crc_hash = ""
        self._S_hash = ""
        
        self._handlers = { CMD_LOGON_CHALLANGE :        self._handle_logon_challange,
                           CMD_LOGON_PROOF :            self._handle_logon_proof,
                           CMD_REALM_LIST :             self._handle_realm_list,
                           }
        
    def run(self):
        try:
            self._connect()
            self._send_logon_challange()
            while not self.realm_list_done:
                cmd = ord(self._recv("B"))
                logging.getLogger("tclib").debug("REALM: recv cmd: %s", hex(cmd))
                self._handlers[cmd]()
                time.sleep(NETWORK_SLEEP)
        except (StreamBrokenError, LogonProofError, LogonChallangeError, CryptoError) as e:
            logging.getLogger("tclib").exception(e)
            self._err = e
        except struct.error as e:
            logging.getLogger("tclib").exception(e)
            self._err = StreamBrokenError()
        except socket.error as e:
            logging.getLogger("tclib").exception(e)
            if not self._die:
                self._err = StreamBrokenError(e)
        except Exception as e:
            logging.getLogger("tclib").exception(e)
            raise
            
    def _connect(self):
        self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connection.connect((self._host, self._port))
        
    def _send(self, data):
        self._connection.sendall(data)
        
    def _recv(self, size_or_fmt):
        size = size_or_fmt
        if isinstance(size_or_fmt, str):
            size = bytebuff.calcsize(size_or_fmt)
            
        data = self._connection.recv(size, socket.MSG_WAITALL)
        if len(data) != size:
            raise StreamBrokenError()
        return data
    
    def _send_command(self, cmd, data):
        logging.getLogger("tclib").debug("REALM: sending cmd: %s", hex(cmd))
        self._send(struct.pack("<B", cmd) + data)
        
    def done(self):
        return not self.is_alive()
    
    def get_S_hash(self):
        """
        Returns
        ----------
        S_hash : str
        """
        
        assert(not self.is_alive())
        return self._S_hash
    
    def get_realms(self):
        """
        Returns
        ----------
        realms : dict
        """
        
        assert(not self.is_alive())
        return self._realms
        
    def die(self):
        """
        Kills that thread (just close sockets)
        """

        self._die = True
        self._connection.close()
        
    def err(self):
        """
        Raises
        ------
        StreamBrokenError
        LogonProofError
        LogonChallangeError
        CryptoError
        """

        if self._err:
            raise self._err
        
    def _send_logon_challange(self):
        """
        CMD_LOGON_CHALLANGE
        
        uint8_t            cmd
        uint8_t            err
        uint16_t           size
        uint8_t            gamename[4]
        uint8_t            version1
        uint8_t            version2
        uint8_t            version3
        uint16_t           build
        uint8_t            platform[4] // NUL TERMINATED
        uint8_t            os[4]       // NUL TERMINATED
        uint8_t            country[4]
        uint32_t           timezone_bias
        uint32_t           ip
        uint8_t            I_len
        uint8_t            I[]
        """
        
        buff = bytebuff()
        
        err = 0x8 # 8 == OK
        gamename = reverse_string("WoW")
        platform = reverse_string("x86")
        os = reverse_string("OSX") # warden is disabled on osx
        country = reverse_string("enUS")
        timezone_bias = 60
        ip = 127 + 1 * (256 ** 3)         #127.0.0.1
        acc_len = len(self._acc_name)
        size = bytebuff.calcsize("<4s3BH4s4s4s2IB") + acc_len
        version1, version2, version3, version4 = self._ver.get_versionlist()
        build = self._ver.get_build()
        
        buff.add("B", err)
        buff.add("H", size)
        buff.add("S", gamename)
        buff.add("3B", version1, version2, version3)
        buff.add("H", build)
        buff.add("S", platform)
        buff.add("S", os)
        buff.add("4s", country)
        buff.add("I", timezone_bias)
        buff.add("I", ip)
        buff.add("B", acc_len)
        buff.add("k", self._acc_name)
        
        self._send_command(CMD_LOGON_CHALLANGE, buff.data)
        
    def _handle_logon_challange(self):
        """
        CMD_LOGON_CHALLANGE
            
        uint8_t             cmd;
        uint8_t             err;
        uint8_t             unk;
        uint8_t             B[32];
        uint8_t             g_len;
        uint8_t             g;
        uint8_t             N_len;
        uint8_t             N[32];
        uint8_t             s[32];
        uint8_t             unk2[16];
        uint8_t             security_flag;
        uint8_t             unk3[];
        """
            
        if self.logon_challange_done:
            raise StreamBrokenError()
            
        buff = bytebuff()
        buff.data = self._recv("2B")
        
        unk = buff.get("B")
        err = buff.get("B")
        if err != WOW_SUCCESS:
            raise LogonChallangeError(err)

        fmt = "32s3B32s32s16sB"
        buff = bytebuff(self._recv(fmt))
        B, g_len, g, N_len, N, s, unk2, security_flag = buff.get(fmt)
        self._M1, self._M2, self._A, self._crc_hash, self._S_hash = \
        srp6a(self._acc_name, self._acc_password, B, g, N, s)
        
        if security_flag & 0x01:
            self._recv(20)
        if security_flag & 0x02:
            self._recv(12)
        if security_flag & 0x04:
            self._recv(1)
        
        self.logon_challange_done = True
        self._send_logon_proof()
        
    def _send_logon_proof(self):
        """
        CMD_LOGON_PROOF
    
        uint8_t            cmd
        uint8_t            A[32]
        uint8_t            M1[20]
        uint8_t            crc_hash[20]
        uint8_t            number_of_keys
        uint8_t            unk
        """
            
        buff = bytebuff()
        
        buff.add("32s", self._A)
        buff.add("20s", self._M1)
        buff.add("20s", self._crc_hash)
        buff.add_zeros("2B")
        
        self._send_command(CMD_LOGON_PROOF, buff.data)
        
    def _handle_logon_proof(self):            
        """
        CMD_LOGON_PROOF
        
        uint8_t         cmd
        uint8_t         err
        uint8_t         M2[20]
        uint32_t        account_flags
        uint32_t        survey_id     // TBC+
        uint16_t        unk           // TBC+ 
        """
            
        if not self.logon_challange_done or self.logon_proof_done:
            raise StreamBrokenError()
            
        buff = bytebuff()
        buff.data = self._recv("B")
        err = buff.get("B")
        
        if err != WOW_SUCCESS:
            raise LogonProofError(err)
            
        if self._ver >= EXPANSION_TBC:
            buff = bytebuff(self._recv("20s2IH"))
        else:
            buff = bytebuff(self._recv("20sI"))
        M2 = buff.get("20s")
        if M2 != self._M2:
            raise StreamBrokenError()
            
        self.logon_proof_done = True
        self._send_realm_list()
        
    def _send_realm_list(self):
        """ CMD_REALM_LIST
        
            uint8_t            cmd
            uint32_t           unk """
            
        buff = bytebuff()
        buff.add("I", 0)
        
        self._send_command(CMD_REALM_LIST, buff.data)
        
    def _handle_realm_list(self):           
        """ 
        CMD_REALM_LIST
            
        header:
        uint8_t             cmd
        uint16_t            size
        uint32_t            unk
        uint16_t            number_of_realms
        
        realm:
        uint8_t             realmtype
        uint8_t             online
        uint8_t             color
        uint8_t             name[]
        uint8_t             address[]
        uint32_t            population
        uint8_t             number_of_chars
        uint8_t             timezone
        uint8_t             unk 
        """
            
        if not self.logon_proof_done or self.realm_list_done:
            raise StreamBrokenError()
        
        buff = bytebuff(self._recv("H")) 
        size = buff.get("H")
        if size < 6:
            raise StreamBrokenError()
        
        buff = bytebuff(self._recv(size))
        
        buff.skip(4)
        if self._ver >= EXPANSION_TBC:
            number_of_realms = buff.get("H")
        else:
            number_of_realms = buff.get("B")
            
        realms = {}
        realm_id = 1
        for i in range(number_of_realms):
            if self._ver >= EXPANSION_TBC:
                realmtype = buff.get("B")
                locked = bool(buff.get("B") & REALM_FLAG_OFFLINE)
            else:
                realmtype = buff.get("I")
                locked = False
            color = buff.get("B")
            name = buff.get("S")
            if not name:
                raise StreamBrokenError()
                
            address = buff.get("S")
            host = ""
            port = ""
            try:
                host = address.split(":")[0]
                port = int(address.split(":")[1])
            except (KeyError, ValueError):
                raise StreamBrokenError()
                
            population = buff.get("I")
            number_of_char = buff.get("B")
            timezone = buff.get("B")
            
            self._realms[name] = ( {"realmtype" :      realmtype, 
                                   "locked" :          locked,
                                   "color" :           color,
                                   "name" :            name,
                                   "host" :            host,
                                   "port" :            port,
                                   "population" :      population,
                                   "number_of_char" :  number_of_char,
                                   "timezone" :        timezone,
                                   "id" :              realm_id, } )
            
            buff.skip("B")
            realm_id += 1
            
        logging.getLogger("tclib").info("Realms: %s", self._realms)
        self.realm_list_done = True


" PRESUNOUT !!!!!!!!!!!!!!!!!!!!!!!! "
class RealmTest(unittest.TestCase):
    def setUp(self):
        from tclib.shared.wow_versions import WoWVersions
        self.acc_name = "###"
        self.acc_password = "###"
        self.host = "###"
        self.port = 3724
        self.ver = WoWVersions(version = "4.3.4")
    
    def test_all(self):
        ri = Realm(self.acc_name, self.acc_password, self.host, self.port, self.ver)
        ri.start()
        ri.join()
        ri.err()


if __name__ == '__main__':
    unittest.main()
    

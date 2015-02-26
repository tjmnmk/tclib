# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""

import zlib
import logging
import errno

from tclib.shared.bytebuff import *
from tclib.shared.opcodes_translate import *
from crypto import *

NETWORK_LOOP_SLEEP = 0.2      

class WorldConnect(threading.Thread):
    def __init__(self, world, host, port, acc_name, S_hash, ver):
        """
        Parameters
        ----------
        world : World
        host : str
        port : int
        acc_name : str
        S_hash : str
        ver : WoWVersions
        """
        
        threading.Thread.__init__(self)
        
        self._acc_name = acc_name
        self._ver = ver
        self._host = host
        self._port = port
        self._world = world
        
        if self._ver >= EXPANSION_PANDA:
            self._crypto = CryptoPANDA(S_hash)
        elif self._ver == EXPANSION_CATA:
            self._crypto = CryptoCATA(S_hash)
        elif self._ver == EXPANSION_WOTLK:
            self._crypto = CryptoWOTLK(S_hash)
        elif self._ver == EXPANSION_TBC:
            self._crypto = CryptoTBC(S_hash)
        else:
            self._crypto = CryptoVANILLA(S_hash)
        self._recv_buff = "" # _recv_to_buff; _recv_command
        self._decrypted_header = () # size; cmd, _recv_command
        self._zlib_stream = zlib.decompressobj()
        
        self._send_queue = Queue.Queue()
        self._recv_queue = Queue.Queue()
        
        self._die = False
        self._err = None
        
        self._connection = None
        
    def _connect(self):
        logging.getLogger("tclib").debug("WORLD: connecting, host: %s, port: %d", self._host, self._port)
        self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connection.connect((self._host, self._port))
        self._connection.setblocking(1)
        logging.getLogger("tclib").debug("WORLD: connected")
            
    def _send_command(self, cmd, buff, encrypt = True):
        data = buff.data
        assert(len(data) < 2**16-7)
        logging.getLogger("tclib").debug("WORLD: sending cmd: %s; data: %s", hex(cmd), buff)
        
        headerbuff = bytebuff()
        headerbuff.add(">H", len(data) + 4)
        headerbuff.add("H", cmd)
        headerbuff.add_zeros(2)
        
        header = headerbuff.data
        if encrypt:
            header = self._crypto.encrypt(header)
        self._send(header + data)
        
    def _send(self, data):
        self._connection.sendall(data)
        
    def _recvall(self, size):
        data = ""
        for i in range(int(60 / NETWORK_LOOP_SLEEP) + 1):
            time.sleep(NETWORK_LOOP_SLEEP)
            data += self._connection.recv(size - len(data))
            if len(data) == size:
                return data
        raise StreamBrokenError("Timeout.")
        
    def _recv_to_buff(self):
        bufsize = 4096
        data = ""
        try:
            while 1:
                data += self._connection.recv(bufsize)
                if len(data) % bufsize or len(data) == 0:
                    break
        except socket.error as e:
            if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN): # errno.EWOULDBLOCK == busy; sending data
                raise
                
        self._recv_buff += data
        return len(data)
    
    def die(self):
        """
        Kills that thread (just close sockets)
        """
        
        self._die = True
        self._connection.close()
        
    def run(self):
        try:
            self._worker()
        except StreamBrokenError as e:
            logging.getLogger("tclib").exception(e)
            self._err = e
        except socket.error as e:
            if not self._die:
                logging.getLogger("tclib").exception(e)
                self._err = StreamBrokenError(e)
        except OSError as e:
            if e == errno.EBADF and not self._die:
                logging.getLogger("tclib").exception(e)
                self._err = StreamBrokenError(e)
        except struct.error as e:
            logging.getLogger("tclib").exception(e)
            self._err = StreamBrokenError(e)
        except Exception as e:
            logging.getLogger("tclib").exception(e)
            self._err = StreamBrokenError(e)
            raise
        
    def _worker(self):
        self._connect()
        # SMSG_AUTH_CHALLENGE
        if self._ver >= EXPANSION_CATA: #rewrite
            self._connection.recv(50, socket.MSG_WAITALL)
            self._send("\x00\x2fWORLD OF WARCRAFT CONNECTION - CLIENT TO SERVER")
            buff = bytebuff(self._connection.recv(41, socket.MSG_WAITALL))
        else:
            buff = bytebuff(self._connection.recv(44, socket.MSG_WAITALL))
        size = buff.get(">H") # wotlk - 42, cata - 39; tbc - 6
        cmd = buff.get("H")
        if self._ver >= EXPANSION_CATA:
            cmd = opcode_translate_cata_wotlk(cmd)
        if cmd != SMSG_AUTH_CHALLENGE:
            raise StreamBrokenError()
        buff.cut()
        self._world._handle_auth_challange(cmd, buff)
        # CMSG_AUTH_SESSION
        cmd, buff = self._send_queue.get()
        self._send_command(cmd, buff, False)
        
        self._connection.setblocking(0)
        while 1:
            time.sleep(NETWORK_LOOP_SLEEP)
            while 1:
                cmd, buff = self._recv_command()
                if cmd == None:
                    break
                elif cmd == SMSG_NAME_QUERY_RESPONSE or cmd == CATA_SMSG_NAME_QUERY_RESPONSE: # little hack, world threat is now probably blocked
                    self._world._handle_name_query_response(cmd, buff)
                self._recv_queue.put((cmd, buff))
            while 1:
                try:
                    cmd, buff = self._send_queue.get_nowait()
                    self._send_command(cmd, buff)
                except Queue.Empty:
                    break
                
    def _recv_command(self, decrypt = True):
        """
        .. todo:: rewrite
        """
        
        recv_size = self._recv_to_buff()
        if len(self._recv_buff) < 5 and not self._decrypted_header: # all packets are terminated by 0x00
            return None, None
        
        if not self._decrypted_header: # decrypt header
            if decrypt:
                first4 = self._crypto.decrypt(self._recv_buff[:4])
            else:
                first4 = self._recv_buff[:4]
            headerbuff = bytebuff(first4)
            self._recv_buff = self._recv_buff[4:]
            size_1 = headerbuff.get(">B")
            if size_1 & 0x80 and self._ver >= EXPANSION_WOTLK: #big packet
                if decrypt:
                    headerbuff += self._crypto.decrypt(self._recv_buff[:1])
                else:
                    headerbuff += self._recv_buff[:1]
                self._recv_buff = self._recv_buff[1:]
                size_2 = headerbuff.get(">H")
                size = ((size_1 ^ 0x80) << 16) + size_2 - 2
            else: # little packet
                size_2 = headerbuff.get(">B")
                size = (size_1 << 8) + size_2 - 2
            cmd = headerbuff.get("H")
            self._decrypted_header = (size, cmd)
        
        if self._decrypted_header:
            size = self._decrypted_header[0]
            cmd = self._decrypted_header[1]
            if len(self._recv_buff) < size:
                return None, None
            data = self._recv_buff[:size]
            self._recv_buff = self._recv_buff[size:]
            if self._ver >= EXPANSION_CATA and cmd & COMPRESSED_OPCODE_MASK:
                cmd ^= COMPRESSED_OPCODE_MASK
                data = self._zlib_stream.decompress(data[4:])
                buff = bytebuff(data)
            else:
                buff = bytebuff(data)
            self._decrypted_header = ()
            logging.getLogger("tclib").debug("WORLD: recv cmd: %s; data: %s", hex(cmd), buff)
            return cmd, buff
        
        return None, None
            
    def send_msg(self, cmd, buff):
        """
        Parameters
        ----------
        cmd : int
        buff : bytebuff
        """
        
        self._send_queue.put((cmd, buff))
        
    def recv_msg(self):
        """
        Returns
        -------
        cmd : int
            Return None if nothing to return.
        buff : bytebuff
            Return None if nothing to return.
        """
        
        cmd, buff = None, None
        try:
            cmd, buff = self._recv_queue.get_nowait()
        except Queue.Empty:
            pass
        return cmd, buff
    
    def err(self):
        """
        Raises
        ------
        StreamBrokenError
        """

        if self._err:
            raise self._err
        
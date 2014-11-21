# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""

import re
import struct
import binascii
import unittest


class bytebuff(object):
    def __init__(self, data = "", position = 0, bit_position = 0, default_order = "<"):
        """
        Parameters
        ----------
        data : str
        position: int
        default_order : str
        """

        self.data = data # TODO: use something muttable
        self.default_order = default_order
        
        self._position = position
        self._bit_position_w = 0
        self._bit_position_r = bit_position
        
    def __add__(self, buff):
        """
        Join bytebuff or string, left position unchanged.

        Parameters
        ----------
        buff : str, bytebuff
        """
        
        if isinstance(buff, bytebuff):
            self.data += buff.data
            return self
        
        if isinstance(buff, str):
            self.data += buff
            return self
        
        raise TypeError("cannot concatenate %s and %s objects" % (self.__name__, buff.__name__))
    
    def copy(self):
        buff = bytebuff()
        buff.data = self.data
        buff.default_order = self.default_order
        buff._position = self._position
        buff._bit_position_w = self._bit_position_w
        buff._bit_position_r = self._bit_position_r
        return buff

    def __str__(self):
        """
        Returns
        -------
        str
            hex(buff)
        """

        return "0x" + binascii.hexlify(self.data)
   
    def __len__(self):
        return len(self.data)
    
    def cut(self):
        """
        Remove already read data
        """
        
        self.data = self.data[self._position:]
        self._position = 0
        
        self._bit_position_w_old = self._bit_position_w
        self._bit_position_w = 0
        for i in range(self._bit_position_r):
            self.add_bit(0)
            self._bit_position_w += 1
        self._bit_position_w = self._bit_position_w_old
        assert(self._bit_position_r == self._bit_position_w)
        
    def add(self, fmt, *args):
        """
        .. todo:: Rewrite
        
        Parameters
        ----------
        fmt : str
              S for null terminated string
              k for string
              t for bits from int (buff.add("8t", 254)) etc., always big endian, careless on fmt and default_order
        *args : items specified in given format
        
        Raises
        ------
        struct.error
        """

        fmt = self._fmt_order_add(fmt)
        
        order = fmt[0]
        fmt_items = re.findall('[0-9]*.', fmt[1:])
        
        for fmt_item in fmt_items:
            c_type = fmt_item[-1]
            count = 1
            if len(fmt_item) > 1:
                count = int(fmt_item[:-1])
                              
            if c_type in ("S", "k"): # NULL-TERMINATED STRING
                assert(self._bit_position_w == 0)
                for i in range(count):
                    assert(isinstance(args[0], str) or isinstance(args[0], bytes))
                    self.data += args[0]
                    if c_type == "S":
                        self.data += "\0"
                    args = args[1:]
                    
            elif c_type == "t": # bit
                num = args[0]
                assert(count >= num.bit_length())
                for i in range(count - 1, -1, -1): #(count -1) => 0
                    self.add_bit((num >> i) % 2)
                args = args[1:]
                    
            else: #struct pakcage
                assert(self._bit_position_w == 0)
                self.data += struct.pack(order + fmt_item, *(args[:count]))
                args = args[count:]
                
    def get_raw(self, length):
        return self.get("%ds" % length)
    
    def add_raw(self, data):
        self.add("%ds" % len(data), data)
    
    def fill_byte(self):
        if self._bit_position_w == 0:
            return
        self._position += 1
        self._bit_position_w = 0
    
    def add_bit(self, value):
        """
        .. todo:: rewrite
        """
        
        value = int(value)
        assert(value == 0 or value == 1)
        if self._bit_position_w == 0:
            self.data += "\0"
        cur_byte_val = ord(self.data[-1])
        cur_byte_val |= value << (7 - self._bit_position_w)
        self.data = self.data[:-1] + chr(cur_byte_val)
        self._bit_position_w += 1
        if int(self._bit_position_w / 8): #self._bit_position_w >> 3
            self._bit_position_w = 0
        
    def get_bit(self):
        """
        .. todo:: rewrite
        """
        
        byte = ord(self.data[self._position])
        value = (byte >> (7 - self._bit_position_r)) % 2
        self._bit_position_r += 1
        if int(self._bit_position_r / 8): #self._bit_position_r >> 3
            self._bit_position_r = 0
            self._position += 1
        return value
        
    def skip_bits(self, num):
        for i in range(num):
            self.skip_bit()

    def skip_bit(self):
        self.get_bit()
        
    def left_bits(self):
        if self._bit_position_r == 0:
            return
        self._bit_position_r = 0
        self._position += 1
        
    def add_bytes(self, bytes):
        """
        Parameters
        ----------
        bytes : str
        """
        
        assert(self._bit_position_w == 0)
        self.data += str(bytes)
        
    def add_zeros(self, size_or_fmt):
        """
        Parameters
        ----------
        size_or_fmt : int or str
        """
        
        assert(self._bit_position_w == 0)
        size = self._get_size_fmt(size_or_fmt)
        self.add(str(size) + "s", size * "\0")
        
    def skip(self, size_or_fmt):
        """
        Parameters
        ----------
        size_or_fmt : int or str
        """
        
        assert(self._bit_position_w == 0)
        size = self._get_size_fmt(size_or_fmt)
        self._position += size
    
    def get(self, fmt):
        """
        .. todo:: Rewrite, treat exceptions
        
        Parameters
        ----------
        fmt : str
              S for null terminated string, G for packed guid, ${x}t for bits (return int) 
        
        Raises
        ------
        struct.error
        
        Returns
        -------
        list
            values specified in given format
        """

        if self._position == len(self.data):
            raise struct.error()
        
        def fmt_item_count(fmt_item):
            count = 1
            if len(fmt_item) > 1:
                count = int(fmt_item[:-1])
                
            return count
        
        fmt = self._fmt_order_add(fmt)
        order = fmt[0]
        
        fmt_items = re.findall('[0-9]*.', fmt[1:])
        items = []
        for fmt_item in fmt_items:
            if fmt_item[-1] == "t": #bits
                count = fmt_item_count(fmt_item)
                value = 0
                for i in range(count - 1, -1, -1):
                    value |= self.get_bit() << i
                items.append(value)
            
            elif fmt_item[-1] == "S": # NULL TERMINATED STRING
                assert(self._bit_position_w == 0)
                count = fmt_item_count(fmt_item)
                for i in range(count):
                    string = self.data[self._position:].split("\0")[0]
                    
                    if len(string) >= len(self.data[self._position:]):
                        raise struct.error()
                    
                    items.append(string)
                    self._position += len(string) + 1
            
            elif fmt_item[-1] == "G": # PACKED GUID
                assert(self._bit_position_w == 0)
                count = fmt_item_count(fmt_item)
                for i in range(count):
                    mark = ord(self.data[self._position])
                    self._position += 1
                    guid = 0
                    
                    for i in range(8):
                        if mark & (1 << i):
                            guid += ord(self.data[self._position]) << (8 * i)
                            self._position += 1
                            
                            if self._position > len(self.data):
                                raise struct.error()
                            
                    items.append(guid)
                  
            else: # STRUCT.PACKAGE
                assert(self._bit_position_r == 0)
                fmt_item_end = self.calcsize(fmt_item) + self._position
                unpacked = struct.unpack(order + fmt_item, self.data[self._position:fmt_item_end])
                self._position += self.calcsize(fmt_item)
                items.extend(unpacked)
                    
        if len(items) == 1:
            return items[0]
        
        return list(items)
    
    def get_bytes(self, size_or_fmt):
        """
        Parameters
        ----------
        size_or_fmt : int or str
        
        Returns
        -------
        bytes : str
        """
        
        assert(self._bit_position_w == 0)
        size = self._get_size_fmt(size_or_fmt)
        return self.get("%ds" % size)
    
    def _get_size_fmt(self, size_or_fmt):
        """
        Calc size from argument or return argument if that is instance of int.
        
        Parameters
        ----------
        size_or_fmt : int or str
            Size of fmt for struct.calcsize
        
        Returns
        -------
        size : int
        """
        
        assert(isinstance(size_or_fmt, str) or isinstance(size_or_fmt, int))
        
        size = 0
        if isinstance(size_or_fmt, str):
            assert(not "S" in size_or_fmt and not "G" in size_or_fmt)
            size = self.calcsize(size_or_fmt)
        else:
            size = size_or_fmt
        return size
            
    def _fmt_order_add(self, fmt):
        """
        Return default_order + fmt if order is not specified in given fmt.
        
        Parameters
        ----------
        fmt : str
            format string
        
        Returns
        -------
        fmt : str
            format string
        """
        
        if self._is_order(fmt[0]):
            return fmt
        else:
            return self.default_order + fmt
        
    def _is_order(self, char):
        """
        Return true if argument is order character.
        
        Parameters
        ----------
        char : str
        
        Returns
        -------
        size : bool
        """
        
        assert(len(char) == 1)
        if char in ("@=<>!"):
            return True
        return False
        
    def clear(self):
        """
        Clear all data, set position to 0.
        """
        
        self.data = ""
        self._position = 0
        self._bit_position_w = 0
        self._bit_position_r = 0
        
    def set_default_order(self, default_order):
        """
        Set default order
        
        Parameters
        ----------
        default_order : str
        """
        
        self.default_order = default_order
    
    calcsize = struct.calcsize
    

class bytebuffTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_adders(self):
        """
        Test: add (except t), add_bytes, add_zeros, clear
        """

        def add(ord):
            if ord == bytebuff_default_order:
                ord = ""
            buff.add(ord + "2B2S1I", 1, 200, "A", "B", 1000000)
            buff.add_zeros("B")
            buff.add_zeros(1)
            buff.add_bytes("\xFF")
            
        bytebuff_default_order = ">"
        buff = bytebuff(default_order = bytebuff_default_order)
            
        bytes_big = "\x01\xc8\x41\x00\x42\x00\x40\x42\x0f\x00\x00\x00\xFF"
        bytes_little = "\x01\xc8\x41\x00\x42\x00\x00\x0f\x42\x40\x00\x00\xFF"
        add("<")
        self.assertEqual(bytes_big, buff.data)
        buff.clear()
        add(">")
        self.assertEqual(bytes_little, buff.data)
        
    def test_getters(self):
        """ 
        Test: get (except t), set_default_order, skip, clear, get_bytes
        """

        bytes_big = "\x01\xc8\x41\x00\x42\x00\x40\x42\x0f\x00\x01\x01\xFF\x66\x77"
        bytes_little = "\x01\xc8\x41\x00\x42\x00\x00\x0f\x42\x40\xFF\x01\xFF\x66\x77"
        buff = bytebuff(bytes_big)
        buff.set_default_order("<")
        data = buff.get("2B2S1I")
        self.assertEqual(data, [1, 200, 'A', 'B', 1000000])
        buff.skip(1)
        self.assertEqual(buff.get("G"), 255)
        self.assertEqual(buff.get_bytes("2B"), "\x66\x77")
        
        buff = bytebuff(bytes_little)
        buff.set_default_order(">")
        data = buff.get("2B2S1I")
        self.assertEqual(data, [1, 200, 'A', 'B', 1000000])
        buff.skip(1)
        self.assertEqual(buff.get("G"), 255)
        self.assertEqual(buff.get_bytes("2B"), "\x66\x77")
        
    def test_bits(self):
        """
        Test: get (only t), add (only t), add_bit
        """
        
        buff = bytebuff()
        for i in range(9):
            buff.add_bit(1)
        buff.add("4t", 10)
        self.assertEqual(str(buff), "0xffd0")
        x = buff.get("9t")
        y = buff.get("4t")
        self.assertEqual(x, 511)
        self.assertEqual(y, 10)
        
        
if __name__ == '__main__':
    unittest.main()
        
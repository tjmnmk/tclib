# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""


import array
import unittest
import string
import time
import threading
import socket
import Queue
import threading
import logging
import errno

from tclib.shared.exceptions import *
from tclib.shared.const import *


def bytes_to_int(bytes_r, order):
    """
    Convert bytes to int.
    
    .. todo:: Optimize
    
    Parameters
    ----------
    bytes_r : str
    order : "little" or "big"
        endianity
        
    Returns
    -------
    int
    """
    
    assert(order in ("little", "big"))
    
    if order == "little":
        bytes_r = reverse_string(bytes_r)
    
    return int(bytes_r.encode('hex'), 16)


def int_to_bytes(num, length, order):
    """
    Convert int to bytes.
    
    .. todo:: Optimize
    
    Parameters
    ----------
    num : int
    length : str
        len of returned bytes
    order : "little" or "big"
        endianity
        
    Returns
    -------
    str
    """
    
    assert(order in ("little", "big"))
    assert((1 << 8*length) >= num )
    
    bytes_r = ""
    for i in range(1, length + 1):
        bytes_r = chr(num % 256) + bytes_r
        num = num >> 8

    if order == "little":
        bytes_r = reverse_string(bytes_r)
        
    return bytes_r


def reverse_string(x):
    """
    Reverse string; "abcd" => "dcba".
    
    Parameters
    ----------
    x : str
        
    Returns
    -------
    str
    """
    
    return x[::-1]


def reverse_dict(dictionary):
    """
    Swap keys and values.
    Very slow.
    
    Parameters
    ----------
    dictionary : dict
        
    Returns
    -------
    dict
    """
    
    return dict(zip(dictionary.values(),dictionary.keys()))


def is_printable(str_r):
    """ 
    Return true if string is printable
    
    Parameters
    ----------
    str_r : str
    
    Returns
    -------
    bool
    """

    return all(c in string.printable for c in str_r)


@property
def NotImplementedVar(self):
    """
    NotImplementedError for class variables.
    
    > class A(object):
    >    x = NotImplementedVar 
    >   
    > A().x
    >
    > NotImplementedError:
    """

    raise NotImplementedError


def int_bitswap(value, length_in_bits):
    """ 
    Swap bits in int
    
    Parameters
    ----------
    value : int
    length_in_bits : int
    
    Returns
    -------
    int
    """
    
    return int(bin(value)[2:].zfill(length_in_bits)[::-1], 2)


def int_get_bit(value, pos):
    """
    Get bit on postion pos from value
    
    Parameters
    ----------
    value : int
    pos : int
    
    Returns
    -------
    bit : int
        0 or 1
    """
    
    assert(pos <= value.bit_length)
    bit = (value >> pos) % 2
    return bit


def int_numof_1_bit(value):
    return bin(value)[2:].count("1")


class CommonTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_reverse_dict(self):
        dictionary = { 1 : "A", 2 : "B" }
        dictionary_r = { "A" : 1, "B" : 2 }
        self.assertEqual(reverse_dict(dictionary), dictionary_r)
        
    def test_reverse_string(self):
        line = "ABCD"
        line_r = "DCBA"
        self.assertEqual(reverse_string(line), line_r)
    
    def test_int_to_bytes(self):
        num = 1000000
        bytes_big = "\x00\x0f\x42\x40"
        bytes_little = "\x40\x42\x0f\x00"
        self.assertEqual(int_to_bytes(num, 4, "big"), bytes_big)
        self.assertEqual(int_to_bytes(num, 4, "little"), bytes_little)
        
    def test_bytes_to_int(self):
        num = 1000000
        bytes_big = "\x00\x0f\x42\x40"
        bytes_little = "\x40\x42\x0f\x00"
        self.assertEqual(bytes_to_int(bytes_big, "big"), num)
        self.assertEqual(bytes_to_int(bytes_little, "little"), num)
        
    def test_is_printable(self):
        non_printable = "\x00\x0f\x42\x40"
        printable = "HELLO WORLD"
        self.assertFalse(is_printable(non_printable))
        self.assertTrue(is_printable(printable))
        
    def test_NotImplementedVar(self):
        class test(object):
            var = NotImplementedVar
        with self.assertRaises(NotImplementedError):
            print test().var
        
    def test_int_bitswap(self):
        self.assertEqual(int_bitswap(6543, 16), 61848)
        
if __name__ == '__main__':
    unittest.main()
    
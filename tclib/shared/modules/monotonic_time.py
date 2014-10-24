# -*- coding: utf-8 -*-

__all__ = [
  'timespec', 'get_monotonic_time_impl', 'monotonic_time'
]

import ctypes
import os
import sys
import errno
import time

class timespec(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_long),
        ('tv_nsec', ctypes.c_long)
    ]
    def to_seconds_double(self):
        return self.tv_sec + self.tv_nsec * 1e-9

def monotonic_time(impl=None):
    if impl is None:
        impl = get_monotonic_time_impl()
    return impl().to_seconds_double()

def get_monotonic_time_impl():
    if sys.platform.startswith("linux"):
        return lambda: monotonic_time_unix(1, impl=get_monotonic_time_impl_unix())
    elif sys.platform.startswith("freebsd"):
        return lambda: monotonic_time_unix(4, impl=get_monotonic_time_impl_unix())
    #elif sys.platform.startswith("darwin"):
    #    return lambda: monotonic_time_darwin(impl=get_monotonic_time_impl_darwin())
    elif sys.platform.startswith("win32"):
        return monotonic_time_win32(impl=get_monotonic_time_impl_win32())
    else:
        return lambda: monotonic_time_fallback(impl=get_monotonic_time_fallback())

def get_monotonic_time_impl_darwin():
    """
    .. todo:: opravit to nejak atd.
    """
    
    return ctypes.CDLL('libmonotonic_time.dylib', use_errno=True).darwin_clock_gettime_MONOTONIC
def monotonic_time_darwin(impl=None):
    if impl is None:
        impl = get_monotonic_time_impl_darwin()
    t = timespec()
    if impl(ctypes.pointer(t)) != 0:
        errno_ = ctypes.get_errno()
        raise OSError(errno_, os.strerrno(errno_))
    return t

def get_monotonic_time_impl_unix():
    fxn = ctypes.CDLL('librt.so.1', use_errno=True).clock_gettime
    fxn.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]
    return fxn
def monotonic_time_unix(clock, impl=None):
    if impl is None:
        impl = get_monotonic_time_impl_unix()
    t = timespec()
    if impl(clock, ctypes.pointer(t)) != 0:
        errno_ = ctypes.get_errno()
        raise OSError(errno_, os.strerror(errno_))
    return t

def get_monotonic_time_impl_win32():
    return getattr(ctypes.windll.kernel32, 'GetTickCount64', ctypes.windll.kernel32.GetTickCount)
def monotonic_time_win32(impl=None):
    if impl is None:
        impl = get_monotonic_time_impl_win32()
    ms = impl()
    t = timespec()
    t.tv_sec = ms / 1000
    t.tv_nsec = (ms - (t.tv_sec * 1000)) * 1e6
    return t

def get_monotonic_time_fallback():
    return time.time
def monotonic_time_fallback(impl=None):
    if impl is None:
        impl = get_monotonic_time_impl_win32()
    sec = impl()
    t = timespec()
    t.tv_sec = int(sec)
    t.tv_nsec = int((sec - t.tv_sec) * 1e9)   
    return t 

if __name__ == "__main__":
    print monotonic_time()

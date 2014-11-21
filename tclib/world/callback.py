# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""

from tclib.shared.common import *

CALLBACK_QUEUE_TIMEOUT = 0.1

class Callback(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
        self._callbacks = {}
        self._callback_queue = Queue.Queue()
        self._die = False
        self._err = Queue.Queue()
        
    def run(self):
        while 1:
            try:
                cmd, args = self._callback_queue.get(True, CALLBACK_QUEUE_TIMEOUT)
            except Queue.Empty:
                if self._die:
                    return
                continue
            if not cmd in self._callbacks:
                continue
            
            func, parrent = self._callbacks[cmd]
            try:
                if parrent == None:
                    if args != None:
                        func(cmd, *args)
                    else:
                        func(cmd)
                else:
                    if args != None:
                        func(parrent, cmd, *args)
                    else:
                        func(parrent, cmd)
            except Exception as e:
                logging.getLogger("tclib").exception(e)
                self._err.put((e, cmd, func, parrent))
            
    def die(self):
        self._die = True
    
    def register(self, cmd, func, parrent = None):
        """
        Parameters
        ----------
        cmd : int
            command (opcode)
        func : function
            callback function
        parrent : parrent class
            default None
        """
        
        if cmd in self._callbacks:
            raise KeyError("Duplicite cmd")
        self._callbacks[cmd] = (func, parrent)
        
    def call(self, cmd, *args):
        self._callback_queue.put((cmd, args))
    
    def err(self):
        """
        Returns
        ----------
        Exception
            From callback function
        cmd : int
            command (opcode)
        callback_func : function
        parrent : class
            Parrent class
        """
        
        return self._err.get()
    
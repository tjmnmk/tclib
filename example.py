# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""

import tclib
import time

acc_name = "acc"
acc_password = "pass"
host = "255.255.255.0"
port = 3724
ver = tclib.WoWVersions(version = "4.3.4")

def handle_message_chat(cmd, msg_type, data):
    print "msg_type :", msg_type
    print "lang :", data["lang"], tclib.const.LANG_NAME[data["lang"]]
    print "player: ", data["source"].name
    print "msg: ", data["msg"]

r = tclib.Realm(acc_name, acc_password, host, port, ver)
r.start()
r.join(60)
print r.get_realms()
S_hash = r.get_S_hash()

w = tclib.World(host, 8085, acc_name, S_hash, ver, 1)
w.start()
print str(w.wait_get_my_players()[0])
w.login(w.wait_get_my_players()[0])
w.callback.register(tclib.const.SMSG_MESSAGECHAT, handle_message_chat)
w.callback.register(tclib.const.SMSG_GM_MESSAGECHAT, handle_message_chat)

while 1:
    time.sleep(10)

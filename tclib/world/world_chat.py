# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""

from tclib.world.world_prototype import *
from tclib.shared.common import *
from tclib.shared.bytebuff import *
from tclib.shared.const import *

class WorldChat(WorldPrototype):
    def send_message_chat(self, msg_type, msg, to = ""):
        """
        CMSG_MESSAGECHAT
        
        Send chat message.
        
        Parameters
        ----------
        msg_type : int
            Implemented: CHAT_MSG_WHISPER,
                         CHAT_MSG_CHANNEL,
                         CHAT_MSG_SAY,
                         CHAT_MSG_PARTY,
                         CHAT_MSG_RAID,
                         CHAT_MSG_GUILD,
                         CHAT_MSG_OFFICER,
                         CHAT_MSG_YELL,
                         CHAT_MSG_WHISPER,
                         CHAT_MSG_CHANNEL
        msg : str
        to : str
            Required if msg_type is CHAT_MSG_WHISPER or CHAT_MSG_CHANNEL
            
        Raises
        ----------
        NotImplementedError
            If msg_type is not implemented.
        """
        
        if msg_type == CHAT_MSG_WHISPER and self._ver < EXPANSION_CATA:
            lang = LANG_GLOBAL
        else:
            lang = self._my_player.default_lang
        buff = bytebuff()
        if msg_type in (CHAT_MSG_WHISPER, CHAT_MSG_CHANNEL):
            assert(to)
            if self._ver >= EXPANSION_CATA:
                buff.add("I", lang)
                buff.add("10t", len(to))
                buff.add("9t", len(msg))
                buff.fill_byte()
                if msg_type == CHAT_MSG_WHISPER:
                    buff.add_raw(to)
                    buff.add_raw(msg)
                if msg_type == CHAT_MSG_CHANNEL:
                    buff.add_raw(msg)
                    buff.add_raw(to)
                cmd = msg_type_translate_wotlk_cata(msg_type)
                self._send(cmd, buff, False)
            else:
                buff.add("I", msg_type)
                buff.add("I", lang)
                buff.add("S", to)
                buff.add("S", msg)
                self._send(CMSG_MESSAGECHAT, buff)
            return

        if msg_type in (CHAT_MSG_SAY,
                        CHAT_MSG_PARTY,
                        CHAT_MSG_RAID,
                        CHAT_MSG_GUILD,
                        CHAT_MSG_OFFICER,
                        CHAT_MSG_YELL):
            if self._ver >= EXPANSION_CATA:
                buff.add("I", lang)
                buff.add("9t", len(msg))
                buff.fill_byte()
                buff.add_raw(msg)
                cmd = msg_type_translate_wotlk_cata(msg_type)
                self._send(cmd, buff, False)
            else:
                buff.add("I", msg_type)
                buff.add("I", lang)
                buff.add("S", msg)
                self._send(CMSG_MESSAGECHAT, buff)
            return
        
        raise NotImplementedError()
    
    def _handle_message_chat(self, cmd, buff):
        """
        SMSG_MESSAGECHAT, SMSG_GM_MESSAGECHAT
        
        CHAT_MSG_SAY: [$Player] says: $blabla
        CHAT_MSG_PARTY: [Party][$Player]: $blabla
        CHAT_MSG_RAID: [Raid][$Player]: $blabla
        CHAT_MSG_GUILD: [Guild][$Player]: $blabla
        CHAT_MSG_OFFICER: [Officer][$Player]: $blabla
        CHAT_MSG_YELL: [$Player] yells: $blabla
        CHAT_MSG_WHISPER: [$Player] whispers: $blabla
        CHAT_MSG_WHISPER_INFORM: To [%Player]: $blabla
        CHAT_MSG_RAID_LEADER: [Raid Leader][$Player]: $blabla
        CHAT_MSG_RAID_WARNING: [Raid Warning][$Player]: $blabla
        CHAT_MSG_CHANNEL: [$0. $Channel][$Player]: $blabla
        CHAT_MSG_SYSTEM: $blabla #?
        CHAT_MSG_ACHIEVEMENT: [$Player] has earned the achievement [$AchiName]!
        CHAT_MSG_GUILD_ACHIEVEMENT: [$Player] has earned the achievement [$AchiName]!
        CHAT_MSG_IGNORED: The player $Player is ignoring you. #?
        
        Returns
        ----------
        msg_type : int
            Implemented:
                CHAT_MSG_SAY, 
                CHAT_MSG_PARTY,
                CHAT_MSG_RAID,
                CHAT_MSG_GUILD,
                CHAT_MSG_OFFICER,
                CHAT_MSG_YELL,
                CHAT_MSG_WHISPER,
                CHAT_MSG_WHISPER_INFORM,
                CHAT_MSG_RAID_LEADER,
                CHAT_MSG_RAID_WARNING,
                CHAT_MSG_CHANNEL,
                CHAT_MSG_SYSTEM,
                CHAT_MSG_ACHIEVEMENT,
                CHAT_MSG_GUILD_ACHIEVEMENT,
                CHAT_MSG_IGNORED,
        data : dict
            CHAT_MSG_SAY, 
            CHAT_MSG_PARTY,
            CHAT_MSG_RAID,
            CHAT_MSG_GUILD,
            CHAT_MSG_OFFICER,
            CHAT_MSG_YELL,
            CHAT_MSG_WHISPER,
            CHAT_MSG_WHISPER_INFORM,
            CHAT_MSG_RAID_LEADER,
            CHAT_MSG_RAID_WARNING => 
            { "lang"        : lang,
              "source"      : source,
              "msg"         : msg,
              "chat_tag"    : chat_tag,
            }
            CHAT_MSG_CHANNEL =>
            { "lang"        : lang,
              "source"      : source,
              "msg"         : msg,
              "chat_tag"    : chat_tag,
            }
            CHAT_MSG_SYSTEM =>
            { "lang"        : lang,
              "msg_len"     : msg_len,
              "msg"         : msg,
              "chat_tag"    : chat_tag,
            }
            CHAT_MSG_ACHIEVEMENT, CHAT_MSG_GUILD_ACHIEVEMENT =>
            { "lang"        : lang,
              "achi_id"     : achi_id,
            }
            CHAT_MSG_IGNORED =>
            { "lang"        : lang,
              "source"      : source,
            }
        """
        
        msg_type = buff.get("B")
        lang = buff.get("I")
        
        if lang == LANG_ADDON:
            return
        
        if self._ver == EXPANSION_VANILLA:
            buff.skip(8 + 4)
        
        if msg_type in (CHAT_MSG_SAY, 
                        CHAT_MSG_PARTY,
                        CHAT_MSG_RAID,
                        CHAT_MSG_GUILD,
                        CHAT_MSG_OFFICER,
                        CHAT_MSG_YELL,
                        CHAT_MSG_WHISPER,
                        CHAT_MSG_WHISPER_INFORM,
                        CHAT_MSG_RAID_LEADER,
                        CHAT_MSG_RAID_WARNING):
            source_guid = buff.get("Q")
            source = self.get_player(source_guid)
            source_name = source.name
            buff.skip(4)
            if cmd in (SMSG_GM_MESSAGECHAT, CATA_SMSG_GM_MESSAGECHAT):
                gm_sender_name_len = buff.get("I")
                gm_sender_name = buff.get("S")
            if self._ver >= EXPANSION_TBC:
                buff.skip(8)
            msg_len = buff.get("I")
            msg = buff.get("S")
            chat_tag = buff.get("B")
            
            if lang not in self._my_player.supported_langs:
                msg_encoded = msg.encode("rot13")
            else:
                msg_encoded = msg
            
            return msg_type, { "lang"         : lang,
                               "source"       : source,
                               "msg"          : msg_encoded,
                               "msg_original" : msg,
                               "chat_tag"     : chat_tag,
                               }
            
        if msg_type == CHAT_MSG_CHANNEL:
            source_guid = buff.get("Q")
            source = self.get_player(source_guid)
            source_name = source.name
            buff.skip(4)
            if cmd in (SMSG_GM_MESSAGECHAT, CATA_SMSG_GM_MESSAGECHAT):
                gm_sender_name_len = buff.get("I")
                gm_sender_name = buff.get("S")
            channel = buff.get("S")
            if self._ver >= EXPANSION_TBC:
                buff.skip(8)
            msg_len = buff.get("I")
            msg = buff.get("S")
            chat_tag = buff.get("B")
            
            if lang not in self._my_player.supported_langs:
                msg_encoded = msg.encode("rot13")
            else:
                msg_encoded = msg
            
            return msg_type, { "lang"         :  lang,
                               "source"       :  source,
                               "channel"      :  channel,
                               "msg"          :  msg_encoded,
                               "msg_original" :  msg,
                               "chat_tag"     :  chat_tag,
                               }
            
        if msg_type == CHAT_MSG_SYSTEM:
            buff.skip(20)
            if cmd in (SMSG_GM_MESSAGECHAT, CATA_SMSG_GM_MESSAGECHAT):
                gm_sender_name_len = buff.get("I")
                gm_sender_name = buff.get("S")
            msg_len = buff.get("I")
            msg = buff.get("S")
            chat_tag = buff.get("B")
            
            return msg_type, { "lang"         : lang,
                               "msg_len"      : msg_len,
                               "msg"          : msg,
                               "msg_original" : msg,
                               "chat_tag"     : chat_tag,
                               }
            
        if msg_type in (CHAT_MSG_ACHIEVEMENT, CHAT_MSG_GUILD_ACHIEVEMENT) and self._ver >= EXPANSION_WOTLK:
            source_guid = buff.get("Q")
            source = self.get_player(source_guid)
            buff.skip(16)
            buff.skip("S") #zjistit co to posila
            buff.skip(1)
            achi_id = buff.get("I")
            
            return msg_type, { "lang"        : lang,
                               "source"      : source,
                               "achi_id"     : achi_id,
                               }
            
        if msg_type == CHAT_MSG_IGNORED:
            source_guid = buff.get("Q")
            source = self.get_player(source_guid)
            source_name = source.name
            
            return msg_type, { "lang"        : lang,
                               "source"      : source,
                               }
        
            
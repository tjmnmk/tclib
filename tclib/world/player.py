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


class Player(object):
    guid = None
    name = None
    _race = None
    game_class = None
    gender = None
    skin = None
    face = None
    hair_style = None
    hair_color = None
    hair_facial = None
    level = None
    zone_id = None
    map_id = None
    x = None
    y = None
    z = None
    guild_id = None
    flags = None
    pet_id = None
    pet_level = None
    pet_family = None
    guild_name = None
    default_lang = None
    realm = None
    declined = None
    supported_langs = ()
    
    @property
    def race(self):
        return self._race
    
    @race.setter
    def race(self, value):
        self._race = value
        
        if value in RACE_HORDE:
            self.default_lang = LANG_ORCISH
        elif value in RACE_ALLIANCE:
            self.default_lang = LANG_COMMON
        else:
            self.default_lang = None
            
        if self.default_lang != None:
            self.supported_langs = (RACE_TO_LANG[value], LANG_GLOBAL, self.default_lang)
            
    def __str__(self):
        return str(dict(self.__iter__()))
            
    def __iter__(self):
        for key in self._iter_list:
            yield (key, self.__dict__.get(key))
            
    def __eq__(self, other_player):
        if not isinstance(other_player, Player):
            raise NotImplemented()
        return bool(self.guid == other_player.guid)
    
    def __copy__(self):
        new = type(self)()
        new.__dict__.update(self.__dict__)
        return new
    
    def __deepcopy__(self, memo):
        return self.__copy__()

    _iter_list = ("guid", 
                 "name", 
                 "_race", 
                 "game_class", 
                 "gender", 
                 "skin", 
                 "face", 
                 "hair_style",
                 "hair_color",
                 "hair_facial",
                 "level",
                 "zone_id",
                 "map_id",
                 "x",
                 "y",
                 "z",
                 "guild_id",
                 "flags",
                 "pet_id",
                 "pet_level",
                 "pet_family",
                 "guild_name",
                 "default_lang",
                 "realm",
                 "declined"
                 )
    
    
class UnknownPlayer(Player):
    def __init__(self):
        Player.__init__(self)
        self.guid =              -1
        self.name =              "unknown"
        self.race =              0
        self.game_class =        0
        self.gender =            0
        self.skin =              0
        self.face =              0
        self.hair_style =        0
        self.hair_color =        0
        self.hair_facial =       0
        self.level =             1
        self.zone_id =           0
        self.map_id =            0
        self.x =                 0.0
        self.y =                 0.0
        self.z =                 0.0
        self.guild_id =          0
        self.flags =             0
        self.unk =               0
        self.unk2 =              0
        self.pet_id =            0
        self.pet_level =         1
        self.pet_familyid =      0
    
    
class PlayerCache(dict):
    def __init__(self):
        dict.__init__(self)
    
    def add(self, player):
        self.__setitem__(player.guid, player)
        
    def get_by_guid(self, guid, default = None):
        return self.get(guid, default)
    
    def get_by_name(self, name, default = None):
        """
        Very slow.
        
        Parameters
        ----------
        name : str
        """
        
        for k, v in self.items():
            if v.name == name:
                return v
        return default
    
    
class RealmTest(unittest.TestCase):
    def test_all(self):
        cache = PlayerCache()
        player_a, player_b = Player(), Player()
        player_a.name, player_b.name = "aaa", "bbb"
        player_a.guid, player_b.guid = 123, 456
        cache.add(player_a)
        cache.add(player_b)
        self.assertEqual(cache.get_by_guid(123), player_a)
        self.assertEqual(cache.get_by_guid(456), player_b)
        self.assertEqual(cache.get_by_name("aaa"), player_a)
        self.assertEqual(cache.get_by_name("bbb"), player_b)
        self.assertEqual(cache.get_by_guid(4568889, "test"), "test")
        self.assertEqual(cache.get_by_guid(4568889), None)
        self.assertEqual(cache.get_by_name("xxx", "test"), "test")
        self.assertEqual(cache.get_by_name("xxx"), None)


if __name__ == '__main__':
    unittest.main()

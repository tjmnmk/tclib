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
from tclib.shared.exceptions import *
import unittest


class WoWVersions(object):
    def __init__(self, build = None, version = None, expansion = None):
        self._version = None
        if build:
            self.set_by_build(build)
        if version:
            version_tmp = self._version
            self.set_by_versionstring(version)
            if version_tmp and version_tmp != self._version:
                raise WoWVersionsError("Version conflict")
        if expansion:
            version_tmp = self._version
            self.set_by_expansion(expansion)
            if version_tmp and version_tmp != self._version:
                raise WoWVersionsError("Version conflict")
            
    def _check_set(self):
        if not self._version:
            raise WoWVersionsError("Bad Version")
    
    def set_by_build(self, build):
        """
        Parameters
        ----------
        build : int
        
        Raises
        ------
        WoWVersionsError
        """
        
        for i in self.versions:
            if i[0] == build:
                self._version = i
                break
            
        self._check_set()
        
    def set_by_versionstring(self, version):
        """
        Parameters
        ----------
        version : str
        
        Raises
        ------
        WoWVersionsError
        """
        
        for i in self.versions:
            x = "%d.%d.%d%s" % i[1:]
            if x == version:
                self._version = i
                break
        
        self._check_set()
    
    def set_by_expansion(self, expansion):
        """
        Parameters
        ----------
        expansion : int or "VANILLA", "TBC", "WOTLK", "CATA"
        
        Raises
        ------
        WoWVersionsError
        """

        expansion = self.expansions_r.get(expansion, expansion)
        
        for i in self.versions:
            if expansion == i[1]:
                if self._version and self._version[0] > i[1]:
                    continue
                self._version = i
        
        self._check_set()
                
    def get_build(self):
        """
        Returns
        ----------
        int
            build
        
        Raises
        ------
        WoWVersionsError
        """

        self._check_set()
        return self._version[0]
    
    def get_versionstring(self):
        """
        Returns
        ----------
        str
            Human readable version string (3.3.5a)
        
        Raises
        ------
        WoWVersionsError
        """
        
        self._check_set()
        return "%d.%d.%d%s" % self._version[1:]
    
    def get_versionlist(self):
        """
        Returns
        ----------
        list
            3.3.5a => (3,3,5,"a")
        
        Raises
        ------
        WoWVersionsError
        """

        self._check_set()
        return self._version[1:]
    
    def get_expansion(self):
        """
        Returns
        ----------
        int
            Num. of expansion 1 => VANILLA; 2 => TBC ...
        
        Raises
        ------
        WoWVersionsError
        """

        self._check_set()
        return self._version[1]
    
    def get_expansionstring(self):
        """
        Returns
        ----------
        str
            Human readable expansion string. (VANILLA, TBC, WOTLK, CATA)
        
        Raises
        ------
        WoWVersionsError
        """
        
        self._check_set()
        return self.expansions[self.get_expansion()]
    
    def __cmp__(self, value):
        if isinstance(value, int) or isinstance(value, long):
            return cmp(self.get_expansion(), value)
                
        if isinstance(value, str):
            value = WoWVersions(version=value)
        if isinstance(value, WoWVersions):
            return cmp(self.get_build(), value.get_build())
        
        raise TypeError()

    __str__ = get_versionstring
    
    versions = ( (18291, 5, 4, 8, '')
                 (17898, 5, 4, 7, ''),
                 (17688, 5, 4, 2, 'hotfix1'),
                 (17658, 5, 4, 2, ''),
                 (17538, 5, 4, 1, ''),
                 (17399, 5, 4, 0, 'hotfix2'),
                 (17371, 5, 4, 0, 'hotfix1'),
                 (17359, 5, 4, 0, ''),
                 (17128, 5, 3, 0, 'a'),
                 (17116, 5, 3, 0, 'hotfix4'),
                 (17055, 5, 3, 0, 'hotfix3'),
                 (16992, 5, 3, 0, 'hotfix2'),
                 (16983, 5, 3, 0, 'hotfix1'),
                 (16977, 5, 3, 0, ''),
                 (16826, 5, 2, 0, 'j'),
                 (16769, 5, 2, 0, 'i'),
                 (16760, 5, 2, 0, 'h'),
                 (16733, 5, 2, 0, 'g'),
                 (16716, 5, 2, 0, 'f'),
                 (16709, 5, 2, 0, 'e'),
                 (16701, 5, 2, 0, 'd'),
                 (16685, 5, 2, 0, 'c'),
                 (16683, 5, 2, 0, 'b'),
                 (16669, 5, 2, 0, 'a'),
                 (16650, 5, 2, 0, ''),
                 (16357, 5, 1, 0, 'A'),
                 (16309, 5, 1, 0, ''),
                 (16135, 5, 0, 5, 'b'),
                 (16057, 5, 0, 5, ''),
                 (16016, 5, 0, 4, ''),
                 (15595, 4, 3, 4, ''),
                 (14545, 4, 2, 2, ''),
                 (13623, 4, 0, 6, 'a'),
                 (12340, 3, 3, 5, 'a'),
                 (11723, 3, 3, 3, 'a'),
                 (11403, 3, 3, 2, ''),
                 (11159, 3, 3, 0, 'a'),
                 (10505, 3, 2, 2, 'a'),
                 (9947,  3, 1, 3, ''),
                 (8606,  2, 4, 3, ''),
                 (6141,  1, 12, 3, ''),
                 (6005,  1, 12, 2, ''),
                 (5875,  1, 12, 1, ''),
                 )
    
    expansions = { EXPANSION_CATA    : "CATA",
                   EXPANSION_WOTLK   : "WOTLK",
                   EXPANSION_TBC     : "TBC",
                   EXPANSION_VANILLA : "VANILLA"
                   }
    
    expansions_r = reverse_dict(expansions)
    
    
class WoWVersionsTest(unittest.TestCase):
    def setUp(self):
        self._build = 12340
        self._version = "3.3.5a"
        self._expansion = 3
        self._expansionstring = "WOTLK"

    def check(self, ver):
        self.assertEqual(ver.get_expansionstring(), self._expansionstring)
        self.assertEqual(ver.get_expansion(), self._expansion)
        self.assertEqual(ver.get_versionstring(), self._version)
        self.assertEqual(ver.get_build(), self._build)
        self.assertEqual(str(ver), self._version)
        
    def test_init(self):
        ver = WoWVersions(build = self._build, version = self._version, expansion = self._expansion)
        self.check(ver)
        
    def test_init2(self):
        ver = WoWVersions(build = self._build, expansion = self._expansion)
        self.check(ver)
        
    def test_set_by_build(self):
        ver = WoWVersions()
        ver.set_by_build(self._build)
        self.check(ver)

    def test_set_by_expansion(self):
        ver = WoWVersions()
        ver.set_by_expansion(self._expansion)
        self.check(ver)

    def test_set_by_versionstring(self):
        ver = WoWVersions()
        ver.set_by_versionstring(self._version)
        self.check(ver)


if __name__ == '__main__':
    unittest.main()

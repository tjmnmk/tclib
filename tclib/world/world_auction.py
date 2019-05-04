# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""


from tclib.shared.bytebuff import *
from tclib.world.world_prototype import *
from tclib.shared.const import *


class WorldAuction(WorldPrototype):
    def __init__(self):
        WorldPrototype.__init__(self)
        self._auctioneer_guid = None
        self._auction_ready = False

    def send_auction_hello(self, auctioneer_guid):
        """
        MSG_AUCTION_HELLO

        Send auction hello.

        Parameters
        ----------
        auctioneer_guid : int
        """

        if self._ver != EXPANSION_WOTLK:
            raise NotImplementedError # TODO: implement

        buff = bytebuff()
        buff.add("Q", auctioneer_guid)
        self._send(MSG_AUCTION_HELLO, buff)

    def _handle_auction_hello(self, cmd, buff):
        """
        MSG_AUCTION_HELLO

        Returns
        ----------
        auctioneer_guid : int
        house_id : int
        enabled : bool
        """

        if self._ver != EXPANSION_WOTLK:
            return # TODO: implement

        auctioneer_guid = buff.get("Q")
        house_id = buff.get("I")
        enabled = bool(buff.get("B"))
        if enabled:
            self._auctioneer_guid = auctioneer_guid
            self._auction_ready = True
        return auctioneer_guid, house_id, enabled

    def send_auction_list_items(self,
                                listfrom,
                                searchedname = AUCTION_SEARCHEDNAME_ALL,
                                levelmin = AUCTION_LEVELMIN_ALL,
                                levelmax = AUCTION_LEVELMAX_ALL,
                                auction_slot_id = AUCTION_FILTERS_ALL,
                                auction_main_category = AUCTION_FILTERS_ALL,
                                auction_sub_category = AUCTION_FILTERS_ALL,
                                quality = AUCTION_FILTERS_ALL,
                                only_usable = False,
                                get_all = False):
        """
        CMSG_AUCTION_LIST_ITEMS

        Send auction list items.

        listfrom : int
            Page number
        searchedname : string
            AUCTION_SEARCHEDNAME_ALL for all
        levelmin : int
            AUCTION_LEVELMIN_ALL for all
        levelmax : int
            AUCTION_LEVELMAX_ALL for all
        auction_slot_id : int
            AUCTION_FILTERS_ALL for all
        auction_main_category : int
            AUCTION_FILTERS_ALL for all
        auction_sub_category : int
            AUCTION_FILTERS_ALL for all
        quality : int
            AUCTION_FILTERS_ALL for all
        only_usable : bool
        get_all : bool
        """

        if self._ver != EXPANSION_WOTLK:
            raise NotImplementedError # TODO: implement
        if not self._auction_ready:
            raise SendAuctionHelloFirst

        buff = bytebuff()
        buff.add("Q", self._auctioneer_guid)
        buff.add("I", listfrom)
        buff.add("S", searchedname)
        buff.add("B", levelmin)
        buff.add("B", levelmax)
        buff.add("I", auction_slot_id)
        buff.add("I", auction_main_category)
        buff.add("I", auction_sub_category)
        buff.add("I", quality)
        buff.add("B", int(only_usable))
        buff.add("B", int(get_all))
        buff.add("B", 0) # unknown
        self._send(CMSG_AUCTION_LIST_ITEMS, buff)

    def _handle_auction_list_items(self, cmd, buff):
        """
        SMSG_AUCTION_LIST_RESULT

        Returns
        ----------
        items : list of items
        total_count : int
        search_delay_ms : int
        """

        if self._ver != EXPANSION_WOTLK:
            return # TODO: implement

        count = buff.get("I")

        items = []
        for i in range(count):
            item = {}
            item["id"] = buff.get("I")
            item["entry"] = buff.get("I")
            enchs = []
            for ench_slot in range(6):
                ench = {}
                ench["slot"] = ench_slot
                ench["id"] = buff.get("I")
                ench["duration"] = buff.get("I")
                ench["charges"] = buff.get("I")
                enchs.append(ench)
            item["enchs"] = enchs
            item["random_property_id"] = buff.get("i")
            item["suffix_factor"] = buff.get("I")
            item["count"] = buff.get("I")
            item["spell_charges"] = buff.get("I")
            buff.skip("I") #unknown
            item["owner"] = buff.get("Q")
            item["startbid"] = buff.get("I")
            item["minimal_outbid"] = buff.get("I")
            item["buyout"] = buff.get("I")
            item["timeleft"] = buff.get("I")
            item["bidder"] = buff.get("Q")
            item["bid"] = buff.get("I")
            items.append(item)
        total_count = buff.get("I")
        search_delay_ms = buff.get("I")
        return items, total_count, search_delay_ms

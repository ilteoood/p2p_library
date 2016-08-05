__author__ = 'iLTeoooD'

'''

DEVICE AND INFORMATION MANAGER

'''

import dbus


class DeviceMapper():
    def __init__(self, bus, wpas):
        self.__dict = {}
        self.__bus = bus
        self.__wpas = wpas

    def formatMacAddr(self, hw_addr):
        if len(hw_addr) > 12:
            hw_addr = hw_addr.split("/")[-1]
        return hw_addr[:2] + ":" + hw_addr[2:4] + ":" + hw_addr[4:6] + ":" + hw_addr[6:8] + ":" + hw_addr[
                                                                                                  8:10] + ":" + hw_addr[
                                                                                                                10:12]

    def addPeer(self, hw_addr):
        hw_addr_parsed = self.formatMacAddr(hw_addr)
        if hw_addr_parsed not in self.__dict.keys():
            iface_obj = self.__bus.get_object(self.__wpas, hw_addr)
            name = iface_obj.Get("fi.w1.wpa_supplicant1.Peer", "DeviceName", dbus_interface=dbus.PROPERTIES_IFACE)
            self.__dict[hw_addr_parsed] = name
            print "Device %s found: %s" % (hw_addr_parsed, name,)

    def fillDict(self, peers):
        for peer in peers:
            self.addPeer(peer)

    def rmPeer(self, hw_addr):
        hw_addr_parsed = self.formatMacAddr(hw_addr)
        name = ""
        if hw_addr_parsed in self.__dict.keys():
            name = self.__dict[hw_addr_parsed]
            del self.__dict[hw_addr_parsed]
        print "Device %s lost: %s" % (hw_addr_parsed, name,)

    def getMac(self, name):
        for item in self.__dict.items():
            if item[1] == name:
                return item[0]
        return ""

    def getName(self, mac):
        return self.__dict[self.formatMacAddr(mac)]

    def printDict(self):
        msg = ""
        for key in self.__dict.keys():
            msg += "- " + key + " -> " + self.__dict[key] + "\n"
        print(msg)

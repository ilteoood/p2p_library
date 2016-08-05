__author__ = 'iLTeoooD'

'''

Event handler for DBUS

'''

import gobject
import threading
import os
import time
import socket
from dbus.mainloop.glib import DBusGMainLoop

from device_mapper import *


class P2PLibrary(threading.Thread):
    def __init__(self, iface_name):
        self.__interface_name = iface_name
        self.__wpas_dbus_interface = "fi.w1.wpa_supplicant1"
        self.__p2pdict = dbus.Dictionary({'Timeout': int(0)})

        threading.Thread.__init__(self)
        self.daemon = True

        __wpas_dbus_opath = "/" + self.__wpas_dbus_interface.replace(".", "/")
        __wpas_dbus_interfaces_interface = self.__wpas_dbus_interface + ".Interface"
        self.__wpas_dbus_interfaces_p2pdevice = __wpas_dbus_interfaces_interface + ".P2PDevice"
        self.__wpas_dbus_interface_group = self.__wpas_dbus_interface + ".Group"

        DBusGMainLoop(set_as_default=True)
        self.__bus = dbus.SystemBus()
        self.__dev_map = DeviceMapper(self.__bus, self.__wpas_dbus_interface)
        __wpas_object = self.__bus.get_object(self.__wpas_dbus_interface, __wpas_dbus_opath)
        __wpas = dbus.Interface(__wpas_object, self.__wpas_dbus_interface)

        try:
            self.__path = __wpas.GetInterface(self.__interface_name)
        except dbus.DBusException:
            error = 'Error:\n  Interface ' + self.__interface_name + ' was not found'
            print error
            os._exit(0)

        __interface_object = self.__bus.get_object(self.__wpas_dbus_interface, self.__path)

        try:
            p2p_interface_prop = __interface_object.GetAll(self.__wpas_dbus_interfaces_p2pdevice,
                                                           dbus_interface=dbus.PROPERTIES_IFACE)
        except dbus.exceptions.DBusException:
            print "Abort: can't start discovery, your Wi-Fi card doesn't support the Wi-Fi Direct technology."
            os._exit(-1)
        p2p_interface_prop["P2PDeviceConfig"].update({"DeviceName": socket.gethostname()})
        __interface_object.Set(self.__wpas_dbus_interfaces_p2pdevice, "P2PDeviceConfig",
                               p2p_interface_prop["P2PDeviceConfig"], dbus_interface=dbus.PROPERTIES_IFACE)

        self.__main_p2p_interface = dbus.Interface(__interface_object, self.__wpas_dbus_interfaces_p2pdevice)
        self.__p2p_interface = self.__main_p2p_interface

        self.__set_handler()

        self.__p2p_interface.Find(self.__p2pdict)

        self.__dev_map.fillDict(p2p_interface_prop["Peers"])

    def connect(self, who, go_intent, join):
        try:
            self.__main_p2p_interface.Connect(
                {"wps_method": "pbc",
                 "join": dbus.Boolean(join),
                 "go_intent": dbus.Int32(go_intent),
                 "peer": dbus.ObjectPath(self.__path + '/Peers/' + self.__dev_map.getMac(who).replace(":", ""))})
        except dbus.exceptions.DBusException:
            print "Unable to connect"
        except ValueError:
            print "Device not found"

    def disconnect(self):
        try:
            self.__p2p_interface.Disconnect()
            self.__restart_find()
        except dbus.exceptions.DBusException:
            print "Unable to disconnect"

    def flush(self):
        self.__p2p_interface.Flush()
        self.__restart_find()

    def devices(self):
        self.__dev_map.printDict()

    def invite(self, who):
        try:
            self.__p2p_interface.Invite(
                {"peer": dbus.ObjectPath(self.__path + '/Peers/' + self.__dev_map.getMac(who).replace(":", ""))})
        except dbus.exceptions.DBusException:
            print "Unable to invite"
        except ValueError:
            print "Device not found"

    def __device_found(self, obj):
        self.__dev_map.addPeer(obj)

    def __device_lost(self, path):
        self.__dev_map.rmPeer(path)

    def __p2p_state_changed(self, msg):
        print "p2pStateChange"
        print msg

    def __invitation_result(self, dict):
        msg = "fail"
        if dict["status"] > 0:
            msg = "success"
        print "Status of the invitation: " + msg

    def __invitation_received(self, dict):
        print "Invitation to join a group received"

    def __group_started(self, dict):
        print "Group started with the role " + dict["role"]

    def __wps_failed(self, msg):
        print "WPSFailure"
        print msg

    def __group_finished(self, dict):
        print "Group closed, your role was: " + dict["role"]
        self.__p2p_interface = self.__main_p2p_interface

    def __go_negotiation_success(self, dict):
        print "Group owner negotiation success as: %s" % (dict["role_go"],)

    def __go_negotiation_failure(self, dict):
        print "Negotiation with %s failed.\nStatus: %s" % (
            self.__dev_map.formatMacAddr(dict["peer_object"]), dict["status"])

    def __go_negotiation_request(self, obj, psw="", go_intent=""):
        print "Connection request from %s: %s" % (self.__dev_map.formatMacAddr(obj), self.__dev_map.getName(obj),)

    def __provision_discovery_failure(self, obj, status):
        print obj
        print status

    def __group_formation_failure(self, reason):
        if reason == "":
            reason = "unknown"
        print "Group formation failed with reason: " + reason
        self.__restart_find()

    def __find_stopped(self):
        self.__restart_find()

    def __restart_find(self):
        time.sleep(3)
        print "Restarting find..."
        self.__main_p2p_interface.Find(self.__p2pdict)

    def __peer_joined(self, obj):
        print "Peer %s: %s connected" % (self.__dev_map.formatMacAddr(obj), self.__dev_map.getName(obj))

    def __peer_disconnected(self, obj):
        print "Peer %s: %s disconnected" % (self.__dev_map.formatMacAddr(obj), self.__dev_map.getName(obj))

    def __iface_add(self, iface_path, propr):
        print "Group assigned to the interface %s" % (propr["Ifname"])
        self.__p2p_interface = dbus.Interface(self.__bus.get_object(self.__wpas_dbus_interface, iface_path),
                                              self.__wpas_dbus_interfaces_p2pdevice)

    def __set_handler(self):
        events = {
            "DeviceFound": (self.__device_found, self.__wpas_dbus_interfaces_p2pdevice),
            "DeviceLost": (self.__device_lost, self.__wpas_dbus_interfaces_p2pdevice),
            "GONegotiationRequest": (self.__go_negotiation_request, self.__wpas_dbus_interfaces_p2pdevice),
            "GONegotiationSuccess": (self.__go_negotiation_success, self.__wpas_dbus_interfaces_p2pdevice),
            "GONegotiationFailure": (self.__go_negotiation_failure, self.__wpas_dbus_interfaces_p2pdevice),
            "GroupStarted": (self.__group_started, self.__wpas_dbus_interfaces_p2pdevice),
            "GroupFormationFailure": (self.__group_formation_failure, self.__wpas_dbus_interfaces_p2pdevice),
            "GroupFinished": (self.__group_finished, self.__wpas_dbus_interfaces_p2pdevice),
            "FindStopped": (self.__find_stopped, self.__wpas_dbus_interfaces_p2pdevice),
            "PeerJoined": (self.__peer_joined, self.__wpas_dbus_interface_group),
            "PeerDisconnected": (self.__peer_disconnected, self.__wpas_dbus_interface_group),
            "P2PStateChanged": (self.__p2p_state_changed, self.__wpas_dbus_interfaces_p2pdevice),
            "InvitationReceived": (self.__invitation_received, self.__wpas_dbus_interfaces_p2pdevice),
            "InvitationResult": (self.__invitation_result, self.__wpas_dbus_interfaces_p2pdevice),
            "WpsFailed": (self.__wps_failed, self.__wpas_dbus_interfaces_p2pdevice),
            "ProvisionDiscoveryFailure": (self.__provision_discovery_failure, self.__wpas_dbus_interfaces_p2pdevice),
            "InterfaceAdded": (self.__iface_add, self.__wpas_dbus_interface)
        }
        for event in events:
            self.__bus.add_signal_receiver(events[event][0], dbus_interface=events[event][1], signal_name=event)

    def run(self):
        gobject.MainLoop().get_context().iteration(True)
        gobject.threads_init()
        gobject.MainLoop().run()

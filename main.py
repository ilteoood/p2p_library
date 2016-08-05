__author__ = 'iLTeoooD'

from p2p_library import *
import sys
import os
import argparse


def main(parser):
    temp_cmd = ""
    p2p = P2PLibrary(parser.interface)
    p2p.start()
    while True:
        cmd = raw_input("$> ")
        if cmd != "!!":
            if cmd != "":
                temp_cmd = cmd
        else:
            cmd = temp_cmd
        if cmd == "ls":
            p2p.devices()
        elif cmd.startswith("connect") or cmd.startswith("join"):
            cmd_split = cmd.split(" ")
            if len(cmd_split) == 2:
                join = cmd_split[0] == "join"
                if parser.server:
                    p2p.connect(cmd_split[1], 15, join)
                else:
                    p2p.connect(cmd_split[1], 7, join)
        elif cmd == "disconnect":
            p2p.disconnect()
        elif cmd == "flush":
            p2p.flush()
        elif cmd.startswith("invite"):
            cmd_split = cmd.split(" ")
            if len(cmd_split) == 2:
                p2p.invite(cmd_split[1])
        elif cmd == "exit":
            exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="p2p_library")
    parser.add_argument("-i", "--interface", action="store", help="Name of the interface", required=True)
    parser.add_argument("-o", "--go", action="store_true", dest="server", help="Use the interface as GO")
    parser.add_argument("-c", "--client", action="store_false", dest="server", help="Use the interface as client")
    parser = parser.parse_args()
    if os.getuid() != 0:
        print "Permission denied: try as SuperUser"
    else:
        main(parser)

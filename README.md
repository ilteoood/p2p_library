With p2p_library you can easily create a Wi-Fi Direct network!

You can find an example of use of this library inside the main.py file; it requires these parameters:

- -i or --interface, used to specify the network interface card. Mandatory.
- -o or --go, used to create the group with the Group Owner role. Optional.
- -c or --client, used to create the group with the Client role. Optional, is the default choice.

To work, this software needs: wpa_supplicant, D-BUS, GObject and Python (obviously).

The main.py implements these commands:

- !!: repeat the last command
- ls: print the list of the nearby devices
- connect <device_name>: send an invitation
- disconnect: remove the device from the group
- flush: clean the interface cache
- invite <device_name>: send an invitation for an already formed group
- join <device_name>: join the group that use <device_name> as go

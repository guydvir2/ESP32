import network

wlan = network.WLAN(network.STA_IF)  # start service
wlan.active(True)  # turn on
# wlan.scan() # Scan for available access points
wlan.connect("HomeNetwork_2.4G", "guyd5161")  # Connect to an AP
wlan.ifconfig(("192.168.2.201", "255.255.255.0", "192.168.2.1", "192.168.2.1"))  # static IP

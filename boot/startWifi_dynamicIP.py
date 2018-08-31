import network

wlan = network.WLAN(network.STA_IF)  # start service
wlan.active(True)  # turn on
wlan.connect("HomeNetwork_2.4G", "guyd5161")  # Connect to an AP

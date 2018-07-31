import network

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.scan()                             # Scan for available access points
sta_if.connect("HomeNetwork_2.4G", "guyd5161") # Connect to an AP

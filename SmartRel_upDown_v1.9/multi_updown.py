# from wifi_tools import *
# import utime
# import os

import machine
import jReader
from ubinascii import hexlify
import SmartRel
import _thread


def rel_0():
    # ################### Program Starts Here ####################
    rev = '1.9'
    config_file = 'config.json'
    saved_data = jReader.JSONconfig(config_file)
    con_data = saved_data.data_from_file
    client_id = hexlify(machine.unique_id())
    # ############################################################
    SmartRelay = SmartRel.UpDownRelaySwitcher(pin_in1=con_data["pin_in1"], pin_in2=con_data["pin_in2"],
                                              pin_out1=con_data["pin_out1"],
                                              pin_out2=con_data["pin_out2"], server=con_data["server"],
                                              client_id=client_id, listen_topics=con_data["listen_topics"],
                                              msg_topic=con_data["out_topic"], static_ip=con_data["static_ip"],
                                              user=con_data["user"],
                                              device_topic=con_data["client_topic"], password=con_data["password"],
                                              rev=rev,
                                              state_topic=con_data["state_topic"], avail_topic=con_data["avail_topic"])


def rel_1():
    # ################### Program Starts Here ####################
    rev = '1.9'
    config_file = 'config.json1'
    saved_data = jReader.JSONconfig(config_file)
    con_data = saved_data.data_from_file
    client_id = hexlify(machine.unique_id())
    # ############################################################
    SmartRelay1 = SmartRel.UpDownRelaySwitcher(pin_in1=con_data["pin_in1"], pin_in2=con_data["pin_in2"],
                                               pin_out1=con_data["pin_out1"],
                                               pin_out2=con_data["pin_out2"], server=con_data["server"],
                                               client_id=client_id, listen_topics=con_data["listen_topics"],
                                               msg_topic=con_data["out_topic"], static_ip=con_data["static_ip"],
                                               user=con_data["user"],
                                               device_topic=con_data["client_topic"], password=con_data["password"],
                                               rev=rev,
                                               state_topic=con_data["state_topic"], avail_topic=con_data["avail_topic"])


if __name__ == "__main__":
    _thread.start_new_thread(rel_0, ())
    _thread.start_new_thread(rel_1, ())

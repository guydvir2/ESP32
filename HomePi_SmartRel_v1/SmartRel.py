from wifi_tools import *
import utime
import machine
import jReader
import os


class ErrorLog:
    def __init__(self, log_filename=None, time_stamp=1, screen_output=1):

        self.time_stamp_in_log = time_stamp
        self.valid_logfile = False
        self.output2screen = screen_output

        if log_filename is None:
            self.err_log = os.getcwd() + 'HPi_err.log'
        else:
            self.err_log = log_filename

        self.check_logfile_valid()

    def check_logfile_valid(self):
        # verify existance of log file
        if self.err_log in os.listdir():
            self.valid_logfile = True
        # create new file
        else:
            open(self.err_log, 'a').close()

            if self.err_log in os.listdir():
                self.valid_logfile = True

            if self.valid_logfile is True:
                msg = '>>Log file %s was created successfully' % self.err_log
            else:
                msg = '>>Log file %s failed to create' % self.err_log

            self.append_log(msg, time_stamp=1)

    def append_log(self, log_entry='', time_stamp=None):
        # permanent time_stamp
        if time_stamp is None:
            if self.time_stamp_in_log == 1:
                self.msg = '%s %s' % (self.time_stamp(), log_entry)
            else:
                self.msg = '%s' % log_entry
        # ADHOC time_stamp - over-rides permanent one
        elif time_stamp is 1:
            self.msg = '%s %s' % (self.time_stamp(), log_entry)
        elif time_stamp is 0:
            self.msg = '%s' % log_entry

        if self.valid_logfile is True:
            myfile = open(self.err_log, 'a')
            myfile.write(self.msg + '\n')
            myfile.close()
        else:
            print('Log err')

        if self.output2screen == 1:
            print(self.msg)


class DualRelaySwitcher(MQTTCommander, ErrorLog):
    def __init__(self, pin_in1=4, pin_in2=5, pin_out1=14, pin_out2=12,
                 server=None, client_id=None, topic1=None, topic2=None,
                 static_ip=''):

        # Pin definitions
        self.pin_up = machine.Pin(pin_out1, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)
        self.pin_down = machine.Pin(pin_out2, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)
        self.pin_button_up = machine.Pin(pin_in1, machine.Pin.IN, machine.Pin.PULL_UP)
        self.pin_button_down = machine.Pin(pin_in2, machine.Pin.IN, machine.Pin.PULL_UP)

        self.t_SW = 0.1
        self.PBit()

        ErrorLog.__init__(self, log_filename='error.log')
        self.append_log("Boot")  # ,%s, %s" % (server, topic1))

        # Class can be activated without MQTTcommander
        if server is not None and client_id is not None and topic1 is not None:
            MQTTCommander.__init__(self, server, client_id, topic1, topic2, static_ip)
        utime.sleep(2)

    #     CODE DOES NOT CONTINUE FROM DOWN HERE (LOOP IS IN MQTTCommader)


    # Define Relay states as Up, Down and Off
    def switch_up(self):
        self.pin_down.value(1)
        utime.sleep(self.t_SW)
        self.pin_up.value(0)

    def switch_down(self):
        self.pin_up.value(1)
        utime.sleep(self.t_SW)
        self.pin_down.value(0)

    def switch_off(self):
        self.pin_down.value(1)
        utime.sleep(self.t_SW)
        self.pin_up.value(1)

    #

    # Define hardware state retrieval
    def but_down_state(self):
        if self.pin_button_down.value() == 0:  # pressed
            return 1
        elif self.pin_button_down.value() == 1:  # released
            return 0

    def but_up_state(self):
        if self.pin_button_up.value() == 0:  # pressed
            return 1
        elif self.pin_button_up.value() == 1:  # released
            return 0

    def rel_up_state(self):
        if self.pin_up.value() == 1:  # open
            return 0
        elif self.pin_up.value() == 0:  # closed
            return 1

    def rel_down_state(self):
        if self.pin_down.value() == 1:  # open
            return 0
        elif self.pin_down.value() == 0:  # closed
            return 1

    #

    # Define Physical button operation
    def button_switch(self):
        # switch_up.
        if self.but_up_state() == 1 and self.rel_up_state() == 0:
            self.switch_up()
            try:
                self.pub("Button Switch: [UP]")
            except NameError:
                print("UP")
                self.append_log("fail to publish to broker")
        # switch down
        elif self.but_down_state() == 1 and self.rel_down_state() == 0:
            self.switch_down()
            try:
                self.pub("Button Switch: [DOWN]")
            except NameError:
                print("DOWN")
                self.append_log("fail to publish to broker")

        # switch off
        elif self.but_down_state() == 0 and self.but_down_state() == 0:
            self.switch_off()
            try:
                self.pub("Button Switch: [OFF]")
            except NameError:
                print("OFF")
                self.append_log("fail to publish to broker")

    def PBit(self):
        print("PowerOnBit started")
        self.switch_down()
        utime.sleep(self.t_SW * 4)
        self.switch_up()
        utime.sleep(self.t_SW * 4)
        self.switch_off()


config_file = jReader.JSONconfig('config.json')
con_data = config_file.data_from_file

SmartRelay = DualRelaySwitcher(pin_in1=con_data["pin_in1"], pin_in2=con_data["pin_in2"], pin_out1=con_data["pin_out1"],
                               pin_out2=con_data["pin_out2"], server=con_data["server"],
                               client_id=con_data["client_ID"], topic1=con_data["listen_topics"],
                               topic2=con_data["out_topic"],
                               static_ip=con_data["static_ip"])

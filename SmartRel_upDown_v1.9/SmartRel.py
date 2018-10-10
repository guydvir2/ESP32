from wifi_tools import *
import utime
import machine
import os
import jReader
import ubinascii


class ErrorLog:
    # log saved on ESP as a file
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

        # if os.stat(self.err_log)[6] > 1000:
        #     self.pub("error_log file exceeds its allowed size")
        # if os.stat(self.err_log)[6] > 5000:
        #     self.pub("error_log file deleted")
        #     os.remove(self.err_log)


class UpDownRelaySwitcher(MQTTCommander, ErrorLog):
    def __init__(self, pin_in1=4, pin_in2=5, pin_out1=14, pin_out2=12,
                 server=None, client_id=None, listen_topics=None, msg_topic=None, device_topic=None,
                 static_ip=None, user=None, password=None, rev=None, state_topic=None, avail_topic=None):

        # Pin definitions
        self.pin_up = machine.Pin(pin_out1, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)
        self.pin_down = machine.Pin(pin_out2, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)
        self.pin_button_up = machine.Pin(pin_in1, machine.Pin.IN, machine.Pin.PULL_UP)
        self.pin_button_down = machine.Pin(pin_in2, machine.Pin.IN, machine.Pin.PULL_UP)

        self.t_SW = 0.1
        self.PBit()

        ErrorLog.__init__(self, log_filename='error.log')

        # Class can be activated without MQTTcommander
        if server is not None and client_id is not None and device_topic is not None:
            MQTTCommander.__init__(self, server=server, client_id=client_id, device_topic=device_topic,
                                   msg_topic=msg_topic, state_topic=state_topic, avail_topic=avail_topic,
                                   listen_topics=listen_topics, static_ip=static_ip, user=user, password=password)
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
    def switch_by_button(self):
        # switch_up.
        if self.but_up_state() == 1 and self.rel_up_state() == 0:
            self.switch_up()
            try:
                self.pub("Button: [UP]")
            except NameError:
                print("UP")
                self.append_log("fail to publish to broker")
        # switch down
        elif self.but_down_state() == 1 and self.rel_down_state() == 0:
            self.switch_down()
            try:
                self.pub("Button: [DOWN]")
            except NameError:
                print("DOWN")
                self.append_log("fail to publish to broker")

        # switch off
        elif self.but_down_state() == 0 and self.but_down_state() == 0:
            self.switch_off()
            try:
                self.pub("Button: [OFF]")
            except NameError:
                print("OFF")
                self.append_log("fail to publish to broker")

    def hw_query(self):
        return [self.but_up_state(), self.but_down_state()]

    def mqtt_commands(self, msg, topic):
        msgs = ['reset', 'up', 'down', 'status', 'off', 'info']
        output1 = "Topic:[%s], Message: " % (topic.decode("UTF-8").strip())

        if msg.lower() == msgs[1]:
            self.switch_up()
            self.pub(output1 + "Remote CMD: [UP]")
            self.mqtt_client.publish(self.state_topic, "up", retain=True)
        elif msg.lower() == msgs[2]:
            self.switch_down()
            self.pub(output1 + "Remote CMD: [DOWN]")
            self.mqtt_client.publish(self.state_topic, "down", retain=True)
        elif msg.lower() == msgs[3]:
            self.pub(output1 + "Status CMD: [%s,%s,%s,%s]" % (
                self.but_up_state(), self.rel_up_state(), self.but_down_state(), self.rel_down_state()))
        elif msg.lower() == msgs[4]:
            self.switch_off()
            self.pub(output1 + "Remote CMD: [OFF]")
            self.mqtt_client.publish(self.state_topic, "off", retain=True)
        elif msg.lower() == msgs[5]:
            p = '%d-%d-%d %d:%d:%d' % (
                self.boot_time[0], self.boot_time[1], self.boot_time[2], self.boot_time[3], self.boot_time[4],
                self.boot_time[5])
            self.pub('Boot time: [%s], ip: [%s]' % (p, self.sta_if.ifconfig()[0]))

    def PBit(self):
        print("PowerOnBit started")
        self.switch_down()
        utime.sleep(self.t_SW * 4)
        self.switch_up()
        utime.sleep(self.t_SW * 4)
        self.switch_off()


if __name__ == "__main__":
    # ################### Program Starts Here ####################
    rev = '1.9'
    config_file = 'config.json'
    saved_data = jReader.JSONconfig('config.json')
    con_data = saved_data.data_from_file
    client_id = ubinascii.hexlify(machine.unique_id())
    # ############################################################
    SmartRelay = UpDownRelaySwitcher(pin_in1=con_data["pin_in1"], pin_in2=con_data["pin_in2"],
                                     pin_out1=con_data["pin_out1"],
                                     pin_out2=con_data["pin_out2"], server=con_data["server"],
                                     client_id=client_id, listen_topics=con_data["listen_topics"],
                                     msg_topic=con_data["out_topic"], static_ip=con_data["static_ip"],
                                     user=con_data["user"],
                                     device_topic=con_data["client_topic"], password=con_data["password"], rev=rev,
                                     state_topic=con_data["state_topic"], avail_topic=con_data["avail_topic"])

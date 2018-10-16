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

    def xport_logfile(self):
        # return os.listdir()
        if self.err_log in os.listdir() is True:
            with open(self.err_log, 'r') as f:
                return f.readlines()
        else:
            print('file', self.err_log, ' not found')
            return 0


class MultiRelaySwitcher(ErrorLog, MQTTCommander):
    def __init__(self, input_pins, output_pins, server=None, client_id=None, listen_topics=None, msg_topic=None,
                 device_topic=None, static_ip=None, user=None, password=None, rev=None, state_topic=None,
                 avail_topic=None):

        self.switching_delay = 0.1
        self.rev = rev
        self.boot_time = utime.localtime()
        self.system_states = {"on": 1, "off": 0, "up": [1, 0], "down": [0, 1], "stop": [0, 0]}

        self.input_hw, self.output_hw = [], []

        # Init GPIO setup ###
        if type(input_pins[0]) is list:
            state_topic_temp = []
            for i, switch in enumerate(input_pins):
                state_topic_temp.append(state_topic + '_%d' % i)
                self.output_hw.append([])
                self.input_hw.append([])

                for m, pin in enumerate(switch):
                    self.input_hw[i].append(machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP))
                    self.output_hw[i].append(
                        machine.Signal(machine.Pin(output_pins[i][m], machine.Pin.OUT, machine.Pin.PULL_UP, value=1),
                                       invert=True))
        else:
            state_topic_temp = state_topic
            for i, pin in enumerate(output_pins):
                self.input_hw.append(machine.Pin(input_pins[i], machine.Pin.IN, machine.Pin.PULL_UP))
                self.output_hw.append(
                    machine.Signal(machine.Pin(pin, machine.Pin.OUT, machine.Pin.PULL_UP, value=1),
                                   invert=True))
        # ####
        ErrorLog.__init__(self, log_filename='error.log')
        self.PBit()

        # if server is not None and client_id is not None and device_topic is not None:
        MQTTCommander.__init__(self, server=server, client_id=client_id, device_topic=device_topic,
                               msg_topic=msg_topic, state_topic=state_topic_temp, avail_topic=avail_topic,
                               listen_topics=listen_topics, static_ip=static_ip, user=user,
                               password=password)
        utime.sleep(1)

    # Manual Switching ####
    def switch_by_button(self):
        # detect INPUT change to trigger output change
        for i, but_state in enumerate(self.get_buttons_state()):
            if but_state != self.last_buttons_state[i]:
                self.switch_state(sw=i, state=but_state)
                utime.sleep(self.switching_delay)
                output1 = "Button CMD: Switch [#%d,%s]" % (i, str(but_state))
                self.pub(output1)

    # ###

    # Remote Switching ####
    def switch_state(self, sw, state):
        if state in list(self.system_states.keys()):
            state = self.system_states[state]
            # print(state)
        elif state in list(self.system_states.values()):
            pass
        else:
            print("bad_value")

        # case of UP/Down Switch
        if type(self.input_hw[sw]) is list and type(self.output_hw[sw]) is list and self.get_rel_state(sw=sw) != state:
            if state in list(self.system_states.values()):
                self.set_sw_off(sw=sw)
                utime.sleep(self.switching_delay)
                if state != [0, 0]:
                    for i, pin in enumerate(self.output_hw[sw]):
                        pin.value(state[i])
                        utime.sleep(self.switching_delay)
                    try:
                        self.mqtt_client.publish(self.state_topic[sw], "%d,%s" % (sw, self.get_key(value=state)),
                                                 retain=True)
                    except AttributeError:
                        print("Fail to publish1")

        # case of on/off switch
        elif type(self.input_hw[sw]) is not list and type(self.output_hw[sw]) is not list and self.get_rel_state(
                sw=sw) != state:
            self.output_hw[sw].value(state)
            try:
                self.mqtt_client.publish(self.state_topic, "%d,%s" % (sw, self.get_key(value=state)), retain=True)

            except AttributeError:
                print("Fail to publish3")

    def set_sw_off(self, sw):
        if type(self.output_hw[sw]) is list:
            # case of UP/DOWN switch
            [pin.off() for pin in self.output_hw[sw]]
        else:
            # case of ON/OFF switch
            [pin.off() for pin in self.output_hw]

        #   fail to publish MQTT at boot time (mostly)
        try:
            if type(self.output_hw[sw]) is list:
                self.mqtt_client.publish(self.state_topic[sw], "%d,%s" % (sw, "stop"), retain=True)
            else:
                self.mqtt_client.publish(self.state_topic, "%d,%s" % (sw, "off"), retain=True)
        except AttributeError:
            print("Fail to publish4")

    def get_rel_state(self, sw):
        if type(self.output_hw[sw]) is list:
            return [pin.value() for pin in self.output_hw[sw]]
        else:
            return [pin.value() for pin in self.output_hw]
        # try:
        #     return [pin.value() for pin in self.output_hw[sw]]
        # except TypeError:
        #     return [pin.value() for pin in self.output_hw]

    def get_buttons_state(self):
        temp = []
        conv_list = [1, 0]

        for i, switch in enumerate(self.input_hw):
            # case of UP/Down switch
            if type(switch) is list:
                temp.append([])
                for m, pin in enumerate(switch):
                    temp[i].append(conv_list[pin.value()])
            # case of ON/OFF switch
            else:
                temp.append(conv_list[switch.value()])
        return temp

    def get_key(self, value):
        a = list(self.system_states.keys())[list(self.system_states.values()).index(value)]
        return a

    def mqtt_commands(self, topic, msg):
        if msg.lower() == "status":
            output1 = "Topic:[%s], Status: Switches %s, Relays %s" % (
                topic.decode("UTF-8").strip(), str(self.get_buttons_state()),
                str([self.get_rel_state(sw=i) for i in range(len(self.output_hw) - 1)]))
            self.pub(output1)
        elif msg.lower() == "info":
            t = self.time_stamp(time_tup=self.boot_time)
            output1 = "Topic:[%s], Status_2: boot %s, rev [%s]" % (
                topic.decode("UTF-8").strip(), t, self.rev)
            self.pub(output1)
        else:
            try:
                sw, state = int(msg.split(',')[0].strip()), msg.split(',')[1].strip()
                if sw <= len(self.output_hw) - 1:
                    self.switch_state(sw=sw, state=state)
                    output1 = "Topic:[%s], Remote CMD: Switch [#%d,%s]" % (
                        topic.decode("UTF-8").strip(), sw, state.upper())
                    self.pub(output1)

            except ValueError:
                self.pub("Bad command")

    def PBit(self):
        print("PowerOnBit started")
        for i, switch in enumerate(self.output_hw):
            if type(switch) is list:
                # print(i,"up")
                self.switch_state(sw=i, state="up")
                utime.sleep(self.switching_delay * 8)
                # print(i, "down")
                self.switch_state(sw=i, state="down")
                utime.sleep(self.switching_delay * 8)
                # print(i, "stop")
                self.switch_state(sw=i, state="stop")
                utime.sleep(self.switching_delay * 8)
            else:
                self.switch_state(sw=i, state="on")
                utime.sleep(self.switching_delay * 8)
                self.switch_state(sw=i, state="off")
                utime.sleep(self.switching_delay * 8)


# ################### Program Starts Here ####################
rev = '2.0'
config_file = 'config.json'
saved_data = jReader.JSONconfig('config.json')
con_data = saved_data.data_from_file
client_id = ubinascii.hexlify(machine.unique_id())
# ############################################################

SmartRelay = MultiRelaySwitcher(input_pins=con_data["input_pins"], output_pins=con_data["output_pins"],
                                server=con_data["server"],
                                client_id=client_id, listen_topics=con_data["listen_topics"],
                                msg_topic=con_data["out_topic"], static_ip=con_data["static_ip"], user=con_data["user"],
                                device_topic=con_data["client_topic"], password=con_data["password"], rev=rev,
                                state_topic=con_data["state_topic"], avail_topic=con_data["avail_topic"])

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

        self.t_SW = 0.1
        self.input_hw = []
        self.output_hw = []
        for i, pin in enumerate(input_pins):
            self.input_hw.append(machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP))
            self.output_hw.append(machine.Pin(output_pins[i], machine.Pin.OUT, machine.Pin.PULL_UP, value=1))

        ErrorLog.__init__(self, log_filename='error.log')
        self.PBit()

        # Class can be activated without MQTTcommander
        if server is not None and client_id is not None and device_topic is not None:
            MQTTCommander.__init__(self, server=server, client_id=client_id, device_topic=device_topic,
                                   msg_topic=msg_topic, state_topic=state_topic, avail_topic=avail_topic,
                                   listen_topics=listen_topics, static_ip=static_ip, user=user, password=password)
        utime.sleep(1)

    def switch_by_button(self):
        for i, device in enumerate(self.output_hw):
            device.value(self.input_hw[i].value())

    def hw_query(self):
        return [device.value() for device in self.input_hw]

    def mqtt_commands(self, topic, msg):
        output1 = "Topic:[%s], Message: " % (topic.decode("UTF-8").strip())
        func_int, num_int = -1, -1

        if 'on' in msg.lower() or 'off' in msg.lower():
            func, num = msg.split(',')[0].strip(), msg.split(',')[1].strip()
            if func is 'on':
                func_int = 0
            elif func is "off":
                func_int = 1

            if 0 <= int(num) <= len(self.output_hw) - 1:
                num_int = int(num)

                self.output_hw[num_int].value(func_int)
                self.pub(output1 + "[Remote]: Switch [%s][%s]" % (num, func))
                self.mqtt_client.publish(self.state_topic,
                                         "%s" % str([[1, 0][device.value()] for device in self.output_hw]),
                                         retain=True)
        #
        # elif msg.lower().strip() is "status":
        #     self.pub(output1 + "[Remote]: Switches %s Buttons %s" % (
        #         str([device.value() for device in self.output_hw]),
        #         str([device.value() for device in self.input_hw])))
        #
        # elif msg.lower().strip() == "info":
        #     p = '%d-%d-%d %d:%d:%d' % (
        #         self.boot_time[0], self.boot_time[1], self.boot_time[2], self.boot_time[3], self.boot_time[4],
        #         self.boot_time[5])
        #     self.pub('Boot time: [%s], ip: [%s]' % (p, self.sta_if.ifconfig()[0]))

        elif msg.lower().strip() is "err_log":
            log_list = self.xport_logfile()
            self.pub(output1 + str(log_list))

        else:
            self.pub(output1 + " invalid command")

    def PBit(self):
        print("PowerOnBit started")
        for device in self.output_hw:
            device.value(0)
            utime.sleep(self.t_SW * 4)
            device.value(1)
            utime.sleep(self.t_SW * 4)


# ################### Program Starts Here ####################
rev = '1.0'
config_file = 'config.froom'
saved_data = jReader.JSONconfig('config.froom')
con_data = saved_data.data_from_file
client_id = ubinascii.hexlify(machine.unique_id())
# ############################################################

SmartRelay = MultiRelaySwitcher(input_pins=con_data["input_pins"], output_pins=con_data["output_pins"],
                                server=con_data["server"],
                                client_id=client_id, listen_topics=con_data["listen_topics"],
                                msg_topic=con_data["out_topic"], static_ip=con_data["static_ip"], user=con_data["user"],
                                device_topic=con_data["client_topic"], password=con_data["password"], rev=rev,
                                state_topic=con_data["state_topic"], avail_topic=con_data["avail_topic"])

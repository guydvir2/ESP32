from wifi_tools import MQTTCommander
from utime import sleep, localtime
from machine import Pin, Signal, unique_id
import jReader
from errlog import ErrorLog
from ubinascii import hexlify


class MultiRelaySwitcher(MQTTCommander, ErrorLog):
    def __init__(self, server=None, client_id=None, listen_topics=None, msg_topic=None, sw_amount=None, sw_type=None,
                 device_topic=None, static_ip=None, user=None, password=None, rev=None, state_topic=None,
                 avail_topic=None, port_type=None):

        self.switching_delay = 0.1
        self.rev = rev
        self.boot_time = localtime()
        self.system_states = {"on": 1, "off": 0, "up": [1, 0], "down": [0, 1], "stop": [0, 0]}

        self.input_hw, self.output_hw = [], []
        state_topic_temp = []
        input_pins, output_pins = self.pins_selection(port_type=port_type, amount=sw_amount, sw_type=sw_type)

        # Init GPIO setup ###
        for i, switch in enumerate(input_pins):
            if type(switch) is list:
                state_topic_temp.append(state_topic + '_%d' % i)
                self.output_hw.append([])
                self.input_hw.append([])
                for m, pin in enumerate(switch):
                    self.input_hw[i].append(Pin(pin, Pin.IN, Pin.PULL_UP))
                    self.output_hw[i].append(Signal(Pin(output_pins[i][m], Pin.OUT, Pin.PULL_UP, value=1),
                                                    invert=True))
            else:
                state_topic_temp = state_topic
                self.input_hw.append(Pin(switch, Pin.IN, Pin.PULL_UP))
                self.output_hw.append(Signal(Pin(switch, Pin.OUT, Pin.PULL_UP, value=1), invert=True))
        #
        self.PBit()

        ErrorLog.__init__(self, log_filename='error.log')
        print("System parameters: port type: %s, "
              "switch type: %s, switches amount: %d, MQTT: broker:%s, listen: %s device:%s" % (
                  port_type, sw_type, sw_amount, server, str(listen_topics), str(device_topic)))
        MQTTCommander.__init__(self, server=server, client_id=client_id, device_topic=device_topic,
                               msg_topic=msg_topic, state_topic=state_topic_temp, avail_topic=avail_topic,
                               listen_topics=listen_topics, static_ip=static_ip, user=user,
                               password=password)

    @staticmethod
    def pins_selection(port_type="esp8266", amount=1, sw_type='sw'):
        if port_type == "esp32":
            # currently only 1 pair available for esp8266
            in_vector = [0, 2]  # , 14, 12]
            out_vector = [5, 4]  # , 13, 15]
        elif port_type == "esp8266":
            in_vector = [22, 19, 23, 18]
            out_vector = [5, 17, 16, 4]

        if sw_type is "sw" and amount <= len(in_vector):
            return in_vector[:amount], out_vector[: amount]

        elif sw_type is "tog" and amount <= len(in_vector) / 2:
            return [[in_vector[2 * i], in_vector[2 * i + 1]] for i in range(amount)], \
                   [[out_vector[2 * i], out_vector[2 * i + 1]] for i in range(amount)]

    # Manual Switching ####
    def switch_by_button(self):
        # detect INPUT change to trigger output change
        for i, but_state in enumerate(self.get_buttons_state()):
            if but_state != self.last_buttons_state[i]:
                self.switch_state(sw=i, state=but_state)
                sleep(self.switching_delay)
                print("but_state", i, but_state)
                output1 = "Button CMD: Switch [#%d,%s]" % (i, str(self.translate_status(value=but_state)))
                self.pub(output1)

    # ###

    # Remote Switching ####
    def switch_state(self, sw, state):
        if state in list(self.system_states.keys()):
            state = self.system_states[state]
        elif state in list(self.system_states.values()):
            pass
        else:
            print("illegal switch value- ", sw, state)

        # case of UP/Down Switch
        if type(self.input_hw[sw]) is list and type(self.output_hw[sw]) is list and self.get_rel_state(sw=sw) != state:
            if state in list(self.system_states.values()):
                self.set_sw_off(sw=sw)
                sleep(self.switching_delay)
                if state != [0, 0]:
                    for i, pin in enumerate(self.output_hw[sw]):
                        pin.value(state[i])
                        sleep(self.switching_delay)
                    try:
                        self.mqtt_client.publish(self.state_topic[sw],
                                                 "%d,%s" % (sw, self.translate_status(value=state)),
                                                 retain=True)
                    except AttributeError:
                        print("Fail to publish1")

        # case of on/off switch
        elif type(self.input_hw[sw]) is not list and type(self.output_hw[sw]) is not list and self.get_rel_state(
                sw=sw) != state:
            self.output_hw[sw].value(state)
            try:
                self.mqtt_client.publish(self.state_topic, "%d,%s" % (sw, self.translate_status(value=state)),
                                         retain=True)

            except AttributeError:
                print("Fail to publish3")

    # ###

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

    def get_rel_state(self, sw=None):
        if sw is not None:
            if type(self.output_hw[sw]) is list:
                return [pin.value() for pin in self.output_hw[sw]]
            else:
                return [self.output_hw[sw].value()]
        else:
            return [pin.value() for pin in self.output_hw]

    def get_buttons_state(self):
        conv_list, temp = [1, 0], []

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

    def translate_status(self, value):
        # print(type(value),value)
        if type(value) is list and len(value) == 1:
            value = value[0]
        try:
            a = list(self.system_states.keys())[list(self.system_states.values()).index(value)]
            return a
        except ValueError:
            return "state error"

    def mqtt_commands(self, topic, msg):
        if msg.lower() == "status":
            vv = []
            for i, switch in enumerate(self.output_hw):
                vv.append(self.get_rel_state(sw=i))
            bs = self.get_buttons_state()
            print(bs)

            output1 = "Topic:[%s], Status: Switches %s, Relays %s" % (
                topic.decode("UTF-8").strip(), str([self.translate_status(value=state) for state in bs]),
                str([self.translate_status(value=state) for state in vv]))
            self.pub(output1)

        elif msg.lower() == "info":
            t = self.time_stamp(time_tup=self.boot_time)
            output1 = "Topic:[%s], Info: boot %s, rev [%s]" % (
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
                self.switch_state(sw=i, state="up")
                sleep(self.switching_delay * 8)
                self.switch_state(sw=i, state="down")
                sleep(self.switching_delay * 8)
                self.switch_state(sw=i, state="stop")
                sleep(self.switching_delay * 8)
            else:
                self.switch_state(sw=i, state="on")
                sleep(self.switching_delay * 8)
                self.switch_state(sw=i, state="off")
                sleep(self.switching_delay * 8)


# ################### Program Starts Here ####################
rev = '2.2'
config_file = 'config.json'
saved_data = jReader.JSONconfig('config.json')
con_data = saved_data.data_from_file
client_id = hexlify(unique_id())
# sw_type can be : "sw" for momentary switch or "tog" for toggle switch
# ############################################################
SmartRelay = MultiRelaySwitcher(server=con_data["server"], client_id=client_id, listen_topics=con_data["listen_topics"],
                                msg_topic=con_data["out_topic"], static_ip=con_data["static_ip"], user=con_data["user"],
                                device_topic=con_data["client_topic"], password=con_data["password"], rev=rev,
                                state_topic=con_data["state_topic"], avail_topic=con_data["avail_topic"],
                                sw_amount=con_data["sw_amount"], sw_type=con_data["sw_type"],
                                port_type=con_data["port_type"])

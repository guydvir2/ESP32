def get_key(value):
    try:
        a = list(system_states.keys())[list(system_states.values()).index(value)]
    except ValueError:
        a = None
    return a


def commands(msg, hw_state):
    output_hw = hw_state
    if msg.lower() == "status":
        vv = []
        for i, switch in enumerate(output_hw):
            if type(switch) is list:
                v_temp = []
                for m, rel in enumerate(switch):
                    v_temp.append(rel)
                vv.append(get_key(v_temp))
            else:
                vv.append(get_key(value=switch))
        print(vv)

        # output1 = "Topic:[%s], Status: Switches %s, Relays %s" % (
        #     topic.decode("UTF-8").strip(), str(self.get_buttons_state()),
        #     str([self.get_rel_state(i) for i in range(len(output_hw))]))


def get_hw(input_pins=[[12, 13], 0, 2], output_pins=[[14, 15], 16, 17]):
    input_hw, output_hw = [], []

    for i, switch in enumerate(input_pins):
        # state_topic_temp = []
        if type(switch) is list:
            # state_topic_temp.append(state_topic + '_%d' % i)
            output_hw.append([])
            input_hw.append([])

            for m, pin in enumerate(switch):
                input_hw[i].append('in_%d%d' % (i, input_pins[i][m]))
                output_hw[i].append('sw_%d%d' % (i, output_pins[i][m]))
        else:
            # state_topic_temp = state_topic

            input_hw.append('in_%d' % i)
            output_hw.append('sw_%d' % i)
    print(input_hw, output_hw)


def pins(amount=1, sw_type='sw'):
    in_vector = [14, 12, 13, 15, 3, 1]
    out_vector = [5, 4, 0, 2, 10, 9]
    if sw_type is "sw" and amount <= len(in_vector):
        return in_vector[:amount], out_vector[: amount]

    elif sw_type is "tog" and amount <= len(in_vector)/2:
        return [[in_vector[2 * i], in_vector[2 * i + 1]] for i in range(amount)], \
               [[out_vector[2 * i], out_vector[2 * i + 1]] for i in range(amount)]


system_states = {"on": 1, "off": 0, "up": [1, 0], "down": [0, 1], "stop": [0, 0]}

if __name__ == "__main__":
    print(pins(amount=4, sw_type="tog"))
    # get_hw()
    # commands(msg="status", hw_state=[[0, 1], 1, 0])
    # c = get_key(value=[1, 0])
    # print(c)

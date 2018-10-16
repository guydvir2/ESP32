def get_key(value):
    try:
        a = list(system_states.keys())[list(system_states.values()).index(value)]
    except ValueError:
        a = None
    return a


system_states = {"on": 1, "off": 0, "up": [1, 0], "down": [0, 1], "stop": [0, 0]}

if __name__ == "__main__":
    c = get_key(value=[1, 1])
    print(c)

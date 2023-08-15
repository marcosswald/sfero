import argparse
import os
import yaml

parser = argparse.ArgumentParser(description='Convert a servo calibration file in yaml format to a C++ array.')
parser.add_argument('filename')
args = parser.parse_args()

filepath = args.filename

if os.path.isfile(filepath):
    with open(filepath,'r') as file:
        item_dict = yaml.load(file, Loader=yaml.FullLoader)

# store calib data in flattened list [board_id][channel]
servo_list = ["{ { 0, 0 }, { 0, 0 } }, // channel " + str(i) for i in range(8)]
calib_list = [servo_list.copy() for i in range(3)]

# parse calib data
for servo in item_dict:
    board = item_dict[servo]["board_id"]
    channel = item_dict[servo]["channel"]
    p = item_dict[servo]["coefficients"]
    r = item_dict[servo]["input_limits"]
    calib_list[board][channel] = "{ { " + str(p[0]) + ", " + str(p[1]) +  " }, { " + str(int(r[0])) + ", " + str(int(r[1])) +  " } }, // channel " + str(int(channel)) + ": " +  servo

# print list
for i, s_list in enumerate(calib_list):
    print("{ // board " + str(int(i)))
    for j, entry in enumerate(s_list):
        print(entry)
    print(" }, ")
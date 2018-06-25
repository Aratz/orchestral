import sys
import json
import parse

config_file = sys.argv[1]
network_file = sys.argv[2]

with open(config_file, 'r') as f:
    config = json.load(f)

with open(network_file, 'r') as f:
    network = json.load(f)

mech_step = int(parse.parse(config["network_file"],
        network_file.split("/")[-1][:-4])["step"])

for event in network["events"]:
    if event[1][0] == "birth":
        with open("{}/{}.in".format(
            config["data_folder"],
            config["cell_file"].format(
                step=mech_step,
                substep=0,
                cell_id=event[1][1][1])), 'w') as f:
            f.write("1 1 {0} {0} {0}\n".format(config["cell_types"]["1"]["wsize"]/2))


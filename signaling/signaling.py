CROSSING_RATE = 1

import json
import argparse
import numpy as np
import numpy.random as npr

parser = argparse.ArgumentParser(description="Simulate signaling between two cells.")
parser.add_argument('-seed', type=int)
parser.add_argument('-e', help="End time", type=float)
parser.add_argument('-in', help="Input file")
parser.add_argument('-out', help="Output file")

args = vars(parser.parse_args())

seed = args['seed']
end_time = args['e']
input_file = args['in']
output_file = args['out']

npr.seed(seed)

with open(input_file, 'r') as f:
    data = json.load(f)

cids = list(data["cells"].keys())
inverted_cid = dict(zip(cids, reversed(cids)))

diff_pos = np.array(data["cells"][cids[0]]) - np.array(data["cells"][cids[1]])
mid_pos = (np.array(data["cells"][cids[0]]) + np.array(data["cells"][cids[1]]))/2


new_positions = {
        "cells":{cid: pos for cid, pos in data["cells"].items()},
        "particles": [
            (
                inverted_cid[cid],
                "Notch",
                (np.array(pos) - (np.dot((np.array(pos) - mid_pos), diff_pos)
                        /np.linalg.norm(diff_pos)**2)*diff_pos).tolist(),
                    # Absolute position
            ) if npr.random() < 1 - np.exp(-CROSSING_RATE*end_time) else (
                cid,
                species,
                pos,
            )
            for cid, species, pos in data["particles"]
            ]
        }

with open(output_file, 'w') as f:
    json.dump(new_positions, f, indent=True)

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
inverted_cid = {}
for cell_id1 in cids:
    for cell_id2 in cids:
        if np.linalg.norm(
                np.array(data["cells"][cell_id1]["position"])
                - np.array(data["cells"][cell_id2]["position"]),
                ord=np.inf) > data["cells"][cell_id1]["size"] / 2:
            if cell_id1 not in inverted_cid:
                inverted_cid[cell_id1] = []
            inverted_cid[cell_id1].append(cell_id2)

def pick_neighbor(cell_id):
    return npr.choice(inverted_cid[cell_id])

for i, cell_id1 in enumerate(cids):
    for cell_id2 in cids[i+1:]:
        diff_pos = (np.array(data["cells"][cell_id1]["position"])
            - np.array(data["cells"][cell_id2]["position"]))
        mid_pos = diff_pos / 2
        if np.linalg.norm(diff_pos, ord=np.inf) > data["cells"][cell_id1]["size"] / 2:
            break



new_positions = {
        "cells":{cid: cell for cid, cell in data["cells"].items()},
        "particles": [
            (
                pick_neighbor(cid),
                "Notch",
                (   np.array(pos) - 2*(np.dot(np.array(pos) - mid_pos, diff_pos/np.linalg.norm(diff_pos)**2)*diff_pos) - diff_pos
                    if cid == cids[0] else
                    np.array(pos) + diff_pos - 2*(np.dot(np.array(pos) + mid_pos, diff_pos/np.linalg.norm(diff_pos)**2)*diff_pos)
                    ).tolist()
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

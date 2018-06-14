import sys
import ast
import json
import parse
import numpy as np

with open(sys.argv[1], 'r') as f:
    config = json.load(f)

with open(sys.argv[2], 'r') as f:
    network = json.load(f)

target_cell_output_file = sys.argv[3]
target_cell_id = parse.parse(config["cell_file"], sys.argv[3].split('/')[-1][:-4])["cell_id"]

signaling_files = sys.argv[4:-1]

other_cells_ids = [
        cell_id
        for filename in signaling_files
        for cell_id in json.load(open(filename, 'r'))["cells"]
        if str(cell_id) != str(target_cell_id) ]

target_cell_input_file = sys.argv[-1]


cell_sizes = {cell_id:config["cell_types"][network["final"][cell_id]["type"]]["wsize"]
        for cell_id in [target_cell_id] + other_cells_ids}

cell_pos = {cell_id: np.array(network["final"][cell_id]["position"])
        for cell_id in [target_cell_id] + other_cells_ids}
pos = cell_pos[target_cell_id]

neighbor_cell_ids = [
        cell_id
        for cell_id in other_cells_ids
        if np.linalg.norm(cell_pos[cell_id] - pos, ord=np.inf) > cell_sizes[cell_id] / 2]

diff_pos = {cell_id: cell_pos[cell_id] - pos
        for cell_id in neighbor_cell_ids}
mid_pos = {cell_id: (cell_pos[cell_id] + pos) / 2
        for cell_id in [target_cell_id] + neighbor_cell_ids}

target_cell = [(
            target_cell_id,
            sid,
            pos # Relative position
         )
        for sid, pos
        in [(int(sid), np.array([float(x), float(y), float(z)]))
            for _, sid, x, y, z
            in [line.split()
                for line
                in open(
                    # Read output files from cell simulations
                    target_cell_output_file ,'r'
                    ).read().split('Z\n')[-1].split('\n')
                if line
               ]
        ]
        if not any([
            abs(np.dot(diff_pos[cell_id], pos + (cell_pos[target_cell_id] - cell_sizes[target_cell_id]/2 - mid_pos[cell_id])))
            < config["cell_types"][network["final"][target_cell_id]["type"]]["epsilon"]*cell_sizes[target_cell_id]*abs(sum(diff_pos[cell_id]))
            and ((pos < config["cell_types"][network["final"][target_cell_id]["type"]]["epsilon"]*cell_sizes[target_cell_id]).sum()
                + (pos > (1-config["cell_types"][network["final"][target_cell_id]["type"]]["epsilon"])*cell_sizes[target_cell_id]).sum()) == 1
            and sid == 3
            for cell_id in neighbor_cell_ids])
        ]


for signaling_file in signaling_files:
    with open(signaling_file, 'r') as f:
        signaling_data = json.load(f)
        for cid, species, pos in signaling_data["particles"]:
            if cid != target_cell_id:
                continue

            target_cell.append((
                    cid,
                    3 if species == "Delta" else 4,
                    np.array(pos) + cell_sizes[target_cell_id]/2,
                    ))

with open(target_cell_input_file, 'w') as f:
    for i, (cid, sid, pos) in enumerate(target_cell):
       f.write("{} {} {} {} {}\n".format(i + 1, sid, *pos))


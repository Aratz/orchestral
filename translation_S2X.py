import sys
import ast
import json
import numpy as np

step = int(sys.argv[1])

with open(sys.argv[2], 'r') as f:
    network = json.load(f)

data_folder = sys.argv[3]

target_cell_output_file = sys.argv[4]
target_cell_id = target_cell_output_file.split('/')[-1][:-4].split('-')[-1]

signaling_files = sys.argv[5:]
neighbor_cell_tuples = [
        ast.literal_eval(filename.split('/')[-1][:-4].split('-')[-1])
        for filename in signaling_files]
neighbor_cell_ids = [
        t[0] if t[1] == target_cell_id else t[1]
        for t in neighbor_cell_tuples]


cell_sizes = {cell_id:network[cell_id]["size"]
        for cell_id in [target_cell_id] + neighbor_cell_ids}

cell_pos = {cell_id: np.array(network[cell_id]["position"])
        for cell_id in [target_cell_id] + neighbor_cell_ids}
pos = cell_pos[target_cell_id]

diff_pos = {cell_id: cell_pos[cell_id] - pos
        for cell_id in neighbor_cell_ids}
mid_pos = {cell_id: (cell_pos[cell_id] + pos) / 2
        for cell_id in [target_cell_id] + neighbor_cell_ids}

with open(data_folder + '/cell-{}-{}.out'.format(step, target_cell_id), 'r') as f:
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
                        data_folder + '/cell-{}-{}.out'.format(step, target_cell_id), 'r'
                        ).read().split('Z\n')[-1].split('\n')
                    if line
                   ]
            ]
            if not any([
                abs(np.dot(diff_pos[cell_id], (pos + cell_pos[target_cell_id] - cell_sizes[target_cell_id]/2) - mid_pos[cell_id]))
                < network[target_cell_id]["epsilon"]*cell_sizes[target_cell_id]*abs(sum(diff_pos[cell_id]))
                and ((pos < network[target_cell_id]["epsilon"]*cell_sizes[target_cell_id]).sum()
                    + (pos > (1-network[target_cell_id]["epsilon"])*cell_sizes[target_cell_id]).sum()) == 1
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
                    pos - cell_pos[target_cell_id],
                    ))

with open(data_folder + '/cell-{}-{}.in'.format(step + 1, target_cell_id), 'w') as f:
    for i, (cid, sid, pos) in enumerate(target_cell):
       f.write("{} {} {} {} {}\n".format(i + 1, sid, *pos))


import sys
import json
import numpy as np

step = int(sys.argv[1])

with open(sys.argv[2], 'r') as f:
    network = json.load(f)

cell_output_files = sys.argv[3:]

cell_ids = [filename.split('/')[-1][:-4].split('-')[-1]
        for filename in cell_output_files

cell_pos = {cell_id:np.array(network[cell_id]["position"])
        for cell_id in cell_ids}

cell_sizes = {cell_id:network[cell_id]["size"] for cell_id in cell_ids}

diff_pos = cell_pos[cell_ids[1]] - cell_pos[cell_ids[0]]
mid_pos = (cell_pos[cell_ids[1]] + cell_pos[cell_ids[0]]) / 2

input_data = {
        "cells":{cell_id: pos.tolist() for cell_id, pos in cell_pos.items()},
        # Put particles from both cells in the same list
        "particles":sum([
            [(
                cell_id,
                "Delta",
                (pos + cell_pos[cell_id] - cell_sizes[cell_id]/2).tolist()
             )
            for sid, pos
            in [(int(sid), np.array([float(x), float(y), float(z)]))
                for _, sid, x, y, z
                in [line.split()
                    for line
                    in open(
                        # Read output files from cell simulations
                        data_folder + '/cell-{}-{}.out'.format(step, cell_id), 'r'
                        ).read().split('Z\n')[-1].split('\n')
                    if line
                   ]
            ]
            # Only keep particles close to the boundary between the two cells
            if (abs(np.dot(diff_pos, (pos + cell_pos[cell_id] - cell_sizes[cell_id]/2) - mid_pos))
                < network[cell_id]["epsilon"]*cell_sizes[cell_id]*abs(sum(diff_pos)))
                # Discard particles close to edges and corners
                and ((pos < network[cell_id]["epsilon"]*cell_sizes[cell_id]).sum()
                    + (pos > (1-network[cell_id]["epsilon"])*cell_sizes[cell_id]).sum()) == 1
                and sid == 3 # Only keep delta molecules
        ]
            for cell_id in cell_ids
            ], [])
}

with open(data_folder + '/signaling-{}-({},{}).in'.format(step, *(sorted(cell_ids))), 'w') as f:
    json.dump(input_data, f, indent=True)

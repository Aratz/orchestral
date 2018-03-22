import sys
import json
import numpy as np

EPSILON = 1e-1

step = int(sys.argv[1])

with open(sys.argv[2], 'r') as f:
    network = json.load(f)

data_folder = sys.argv[3]

cell_ids = sys.argv[4:]

cell_pos = {cell_id:np.array(network[cell_id]["position"])
        for cell_id in cell_ids}

cell_sizes = {cell_id:network[cell_id]["size"] for cell_id in cell_ids}

diff_pos = cell_pos[cell_ids[1]] - cell_pos[cell_ids[0]]
mid_pos = diff_pos / 2

particle_pos = {
    cell_id:
    [(sid, pos.tolist())
        for sid, pos
        in [(int(sid), np.array([float(x), float(y), float(z)]))
            for _, sid, x, y, z
            in [line.split()
                for line
                in open(
                    data_folder + '/cell-{}-{}.out'.format(step, cell_id), 'r'
                    ).read().split('Z\n')[-1].split('\n')
                if line
               ]
        ]
        if abs(np.dot(diff_pos, (pos + cell_pos[cell_id] - cell_sizes[cell_id]/2 ) - mid_pos)) < EPSILON*network[cell_id]["size"]*abs(sum(diff_pos))
            and ((pos < EPSILON*cell_sizes[cell_id]).sum()
                + (pos > (1-EPSILON)*cell_sizes[cell_id]).sum()) == 1
        #TODO add comment to explain this gem
    ]
    for cell_id in cell_ids
}

with open(data_folder + '/signaling-{}-({},{}).in'.format(step, *cell_ids), 'w') as f:
    json.dump(particle_pos, f, indent=True)

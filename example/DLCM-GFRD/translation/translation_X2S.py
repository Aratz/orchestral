import sys
import json
import parse
import numpy as np

with open(sys.argv[1], 'r') as f:
    config = json.load(f)
with open(sys.argv[2], 'r') as f:
    network = json.load(f)

cells = network['final']

cell_output_files = sys.argv[3:-1]

signaling_input_file = sys.argv[-1]
signal = parse.parse(config["signaling_file"],
        signaling_input_file.split('/')[-1][:-3])["signaling_id"].split(',')

cell_ids = [parse.parse(config["cell_file"], filename.split('/')[-1][:-4])["cell_id"]
        for filename in cell_output_files]

cell_pos = {cell_id:np.array(cells[cell_id]["position"])
        for cell_id in cell_ids}

cell_sizes = {cell_id:config["cell_types"][cells[cell_id]["type"]]["wsize"]
        for cell_id in cell_ids}

for i, cell_id1 in enumerate(signal):
    for cell_id2 in signal:
        diff_pos = cell_pos[cell_id1] - cell_pos[cell_id2]
        mid_pos = (cell_pos[cell_id1] + cell_pos[cell_id2]) / 2
        if np.linalg.norm(diff_pos, ord=np.inf) > cell_sizes[cell_id1] / 2:
            break
    if np.linalg.norm(diff_pos, ord=np.inf) > cell_sizes[cell_id1] / 2:
        break


if np.linalg.norm(diff_pos, ord=np.inf) == 0.:
    raise Exception("Null diff pos vector")

input_data = {
        "cells":{cell_id:
            {
                "position": cell_pos[cell_id].tolist(),
                "size": cell_sizes[cell_id],
                }
            for cell_id in cell_pos
            },
        # Put particles from both cells in the same list
        "particles":sum([
            [(
                cell_id,
                "Delta",
                (pos - cell_sizes[cell_id]/2).tolist()
                )
                for sid, pos
                in [(int(sid), np.array([float(x), float(y), float(z)]))
                    for _, sid, x, y, z
                    in [line.split()
                        for line
                        in open(
                            # Read output files from cell simulations
                            cell_file, 'r'
                            ).read().split('Z\n')[-1].split('\n')
                        if line
                        ]
                    ]
                # Only keep particles close to the boundary between the two cells
                if (abs(np.dot(diff_pos, pos + (cell_pos[cell_id] - cell_sizes[cell_id]/2 - mid_pos)))
                    < config["cell_types"][cells[cell_id]["type"]]["epsilon"]*cell_sizes[cell_id]*abs(sum(diff_pos)))
                # Discard particles close to edges and corners
                and ((pos < config["cell_types"][cells[cell_id]["type"]]["epsilon"]*cell_sizes[cell_id]).sum()
                    + (pos > (1-config["cell_types"][cells[cell_id]["type"]]["epsilon"])*cell_sizes[cell_id]).sum()) == 1
                and sid == 3 # Only keep delta molecules
                ]
            for cell_file, cell_id in zip(cell_output_files, cell_ids)
            ], [])
        }

with open(signaling_input_file, 'w') as f:
    json.dump(input_data, f, indent=True)

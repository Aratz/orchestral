import sys
import json

config_file = sys.argv[1]
N = int(sys.argv[2])

with open(config_file, 'r') as f:
    config = json.load(f)

def hash(x, y):
    return int(round((x+y)*(x+y+1)/2 + y))

size = config["cell_types"]["1"]["wsize"]

# Generate two layer of overlapping 2x2 cells
final = { hash(0, hash(n_x, n_y)):{
    "seed":hash(0, hash(n_x, n_y)),
    "type":"1",
    "position": [n_x*size, n_y*size, 0.0],
    **(config["cell_types"]["1"])
    }
    for n_x in range(N) for n_y in range(N)}

signaling = [
    sorted([
        str(hash(0, hash(n_x, n_y))),
        str(hash(0, hash(n_x + dx, n_y + dy))),
        ])
        for n_x in range(N) for n_y in range(N)
        for dx, dy in [(1, 0), (0, 1),]
        if 0 <= n_x + dx and n_x + dx < N
        and 0 <= n_y + dy and n_y + dy < N
        ]

with open("{}/{}".format(config["data_folder"], config["network_file"].format(step=0) + '.out'), 'w') as f:
    json.dump({"final":final, "signaling":signaling}, f, indent=4)

for cell_id in final:
    with open("{}/{}".format(config["data_folder"], config["cell_file"].format(
        step=0,
        substep=0,
        cell_id=cell_id,
        )) + '.in', 'w') as f:
        f.write("1 1 {0} {0} {0}\n".format(final[cell_id]["wsize"]/2))

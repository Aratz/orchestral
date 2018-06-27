import sys
import json

N = int(sys.argv[1])
filename = sys.argv[2]
data_folder = sys.argv[3]

size = 1e-6
end_time = 0.1
epsilon = 1e-1

def hash(x, y):
    return int((x+y)*(x+y+1)/2 + y)

network = { hash(n_x, n_y):{
    "seed":hash(n_x, n_y),
    "end_time":end_time,
    "wsize":size,
    "position": [n_x*size, n_y*size, 0.0],
    "neighbors": [hash(n_x + dx, n_y + dy)
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if 0 <= n_x + dx and n_x + dx < N
        and 0 <= n_y + dy and n_y + dy < N],
    "epsilon":epsilon,
    }
    for n_x in range(N) for n_y in range(N)}

with open(filename, 'w') as f:
    json.dump(network, f)

for n_x in range(N):
    for n_y in range(N):
        with open(data_folder+'/cell-1-{}.in'.format(hash(n_x, n_y)), 'w') as f:
            f.write("1 1 5e-7 5e-7 5e-7\n")

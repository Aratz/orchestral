import json
import argparse
from fenics import *
import numpy as np
import numpy.random as npr

D0 = 10.
D1 = 1.
BIRTH_RATE = 2.
DEATH_RATE = 1.


parser = argparse.ArgumentParser(description="Simulate cell mechanics and division")
parser.add_argument('-seed', type=int)
parser.add_argument('-tstep', type=int)
parser.add_argument('-e', help="End time", type=float)
parser.add_argument('-in', help="Input file")
parser.add_argument('-out', help="Output file")

args = vars(parser.parse_args())

seed = args['seed']
tstep = args['tstep']
end_time = args['e']
input_file = args['in']
output_file = args['out']

with open(input_file, 'r') as f:
    init_data = json.load(f)

data = init_data.copy()
event_list = []

npr.seed(seed)

cell_size = list(data.values())[0]['size']

next_cell_id = 0
def hash(t, i):
    return str(int((t+i)*(t+i+1)/2) + i)
t = 0

while t < end_time:
    margin = 3

    min_x = min([cell['position'][0] for cell in data.values()]) - margin*cell_size
    max_x = max([cell['position'][0] for cell in data.values()]) + margin*cell_size
    min_y = min([cell['position'][1] for cell in data.values()]) - margin*cell_size
    max_y = max([cell['position'][1] for cell in data.values()]) + margin*cell_size

    n_x = int((max_x - min_x)/cell_size)
    n_y = int((max_y - min_y)/cell_size)

    cell_n_index = {cell_id: (
        int((cell['position'][0]-min_x)/cell_size),
        int((cell['position'][1]-min_y)/cell_size)
        )
        for cell_id, cell in data.items()}

    pos2cells = {}
    for cell_id, pos in cell_n_index.items():
        if pos in pos2cells:
            pos2cells[pos].append(cell_id)
        else:
            pos2cells[pos] = [cell_id]


    mesh = RectangleMesh(
            Point(min_x, min_y),
            Point(max_x, max_y),
            n_x, n_y)

    V = FunctionSpace(mesh, "Lagrange", 1)


    def boundary(x, on_boundary):
        return on_boundary

    bc = DirichletBC(V, Constant(0.0), boundary)

    p = TrialFunction(V)
    v = TestFunction(V)
    a = inner(grad(p), grad(v))*dx
    L = Constant(0.0)*v*dx

    A, b = assemble_system(a, L, bc)

    sources = {}
    for i, j in cell_n_index.values():
        sources[(i, j)] = 1 if (i, j) in sources else 0

    point_sources = PointSource(V, [(Point(i*cell_size + min_x, j*cell_size + min_y), 1.0)
        for i, j in sources if sources[(i, j)] == 1])
    point_sources.apply(b)

    p = Function(V)
    solve(A, p.vector(), b)

    #import matplotlib.pyplot as plt
    #plot(p)
    #plt.show()


    index_coordinates = {
            (int((c[0]-min_x)/cell_size), int((c[1]-min_y)/cell_size)): p
            for p, c in zip(p.vector(), V.tabulate_dof_coordinates().reshape(-1, 2))}

    #Get transition rates
    neighbors = {cell_id_1:
        [
            (i + di, j + dj)
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            if i + di >= 0 and i + di < n_x and j + dj >= 0 and j + dj < n_y
        ]
        for cell_id_1, (i, j) in cell_n_index.items()
    }

    transition_rates = {
            ('move', cell_id, origin, destination):
            max(
                (index_coordinates[origin] - index_coordinates[destination])*
                    (D1 if destination in pos2cells else D0),
                0.0
                )
            for cell_id, origin in cell_n_index.items()
            for destination in neighbors[cell_id]
            }

    # TODO add birth and death rates
    transition_rates[('birth', cell_id)] = BIRTH_RATE
    for cell_id in cell_n_index:
        transition_rates[('death', cell_id)] = DEATH_RATE

    p_sum = sum(transition_rates.values())
    for key in transition_rates:
        transition_rates[key] /= p_sum

    tau = -np.log(npr.uniform())/p_sum
    r = npr.choice(list(transition_rates.keys()), size=1, p=list(transition_rates.values()))[0]

    def index2coordinates(c):
        return [
                c[0]*cell_size + min_x,
                c[1]*cell_size + min_y
                ]

    t += tau
    if t > end_time:
        break

    print(t, r)
    event_list.append((t, r))
    if r[0] == 'birth':
        new_id = hash(tstep, next_cell_id)
        data[new_id] = {
            "position":index2coordinates(cell_n_index[r[1]]),
            "size":data[r[1]]["size"],
            }
        next_cell_id += 1
    elif r[0] == 'death':
        data.pop(r[1])
    elif r[0] == 'move':
        data[r[1]]["position"] = index2coordinates(r[3])

with open(output_file, 'w') as f:
    json.dump(
            {
                "init":init_data,
                "final":data,
                "events":event_list,
                },
            f)

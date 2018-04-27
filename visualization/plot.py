import re
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

with open(sys.argv[1], 'r') as f:
    config = json.load(f)

with open(sys.argv[2], 'r') as f:
    network = json.load(f)

tstep = 1

raw_data = {cell_id:{
    "particles":[(float(re.split(" [TN]=", particles.split('\n')[0])[1]),
        [(int(sid), (float(x), float(y), float(z)))
        for _, sid, x, y, z in [particle.split()
        for particle in particles.split('\n')[2:] if particle]])
        for particles in open(config["data_folder"]+"/cell-{}-{}.out".format(tstep, cell_id),
            'r').read().split("ParticlePositions")[1:]],
    "cell": network[cell_id]["position"]}
        for cell_id in network}

n_local_steps = len(raw_data["1"]["particles"])

color_map = {
        1: 'k',
        2: 'b',
        3: 'r',
        4: 'y',
        }
bias = 1

fig, ax = plt.subplots()
plot = ax.scatter([], [])

def init():
    ax.set_xlim(0, np.sqrt(len(network))*network["1"]["wsize"])
    ax.set_ylim(0, np.sqrt(len(network))*network["1"]["wsize"])
    return plot

def animate(i):
    tstep = i // n_local_steps + 1 # Global timestep
    T = i % n_local_steps # Local timestep

    if not T:
        print(tstep)
        for cell_id in network:
            raw_data[cell_id] ={
                "particles":[(float(re.split(" [TN]=", particles.split('\n')[0])[1]),
                    [(int(sid), (float(x), float(y), float(z)))
                    for _, sid, x, y, z in [particle.split()
                    for particle in particles.split('\n')[2:] if particle]])
                    for particles in open(config["data_folder"]+"/cell-{}-{}.out".format(tstep, cell_id),
                        'r').read().split("ParticlePositions")[1:]],
                "cell": network[cell_id]["position"]
                }

    formated_data = np.array(sum([
        [[
            x + raw_data[cell_id]["cell"][0],
            y + raw_data[cell_id]["cell"][1],
            color_map[sid],
            (100*(z/network[cell_id]["wsize"]) + bias),
            ]
            for sid, (x, y, z) in raw_data[cell_id]["particles"][T][1]]
            for cell_id in raw_data], []))

    x, y, c, s = formated_data.T
    plot.set_offsets(np.array(list(zip(x,y))))
    plot.set_sizes(s.astype(float))
    plot.set_color(c)
    return plot

ani = animation.FuncAnimation(fig, animate, range(config["n_steps"]*n_local_steps),
        interval=10, init_func=init)
ani.save("notchdelta.mp4")

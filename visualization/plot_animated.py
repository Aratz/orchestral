import re
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches

color_map = {
        1: 'k',
        2: 'k',
        3: '#de2d26',
        4: '#3182bd',
        }
bias = 1

fig, ax = plt.subplots()
plot = ax.scatter([], [])

with open(sys.argv[1], 'r') as f:
    config = json.load(f)

mech_step = 0
with open("{}/{}.out".format(config["data_folder"],
    config["network_file"].format(step=mech_step)), 'r') as f:
    network = json.load(f)["final"]

raw_data = {cell_id:{
    "particles":[(float(re.split(" [TN]=", particles.split('\n')[0])[1]),
        [(int(sid), (float(x), float(y), float(z)))
        for _, sid, x, y, z in [particle.split()
        for particle in particles.split('\n')[2:] if particle]])
        for particles in open("{}/{}.out".format(config["data_folder"],
            config["cell_file"].format(step=mech_step, substep=0, cell_id=cell_id)), 'r'
            ).read().split("ParticlePositions")[1:]],
    "cell": network[cell_id]["position"]}
        for cell_id in network}

n_local_steps = len(raw_data["1"]["particles"])

ax.set_xlim(
        min([network[cell_id]["position"][0]
                - network[cell_id]["wsize"]/2
            for cell_id in network]),
        max([network[cell_id]["position"][0]
                + network[cell_id]["wsize"]/2
            for cell_id in network])
        )
ax.set_ylim(
        min([network[cell_id]["position"][1]
                - network[cell_id]["wsize"]/2
            for cell_id in network]),
        max([network[cell_id]["position"][1]
                + network[cell_id]["wsize"]/2
            for cell_id in network])
        )

def init():
    return plot

def animate(i):
    mech_step = i // (config["n_mech_steps"]*config["n_kin_substeps"])
    kin_substep = (i % (config["n_mech_steps"]*config["n_kin_substeps"]))\
            // config["n_kin_substeps"]
    local_timestep = (i % (config["n_mech_steps"]*config["n_kin_substeps"]))\
            % config["n_kin_substeps"]

    print(i, mech_step, kin_substep, local_timestep)
    if not kin_substep:
        with open("{}/{}.out".format(config["data_folder"],
            config["network_file"].format(step=mech_step)), 'r') as f:
            network_t = json.load(f)["final"]
        network.clear()
        for k, v in network_t.items():
            network[k] = v
        ax.set_xlim(
                min(ax.get_xlim()[0],
                    min([network[cell_id]["position"][0]
                        - network[cell_id]["wsize"]/2
                    for cell_id in network])),
                max(ax.get_xlim()[1],
                    max([network[cell_id]["position"][0]
                        + network[cell_id]["wsize"]/2
                    for cell_id in network]))
                )
        ax.set_ylim(
                min(ax.get_ylim()[0],
                    min([network[cell_id]["position"][1]
                        - network[cell_id]["wsize"]/2
                    for cell_id in network])),
                max(ax.get_ylim()[1],
                    max([network[cell_id]["position"][1]
                        + network[cell_id]["wsize"]/2
                    for cell_id in network]))
                )

    print(network.keys())
    if not local_timestep:
        raw_data.clear()
        for cell_id in network:
            raw_data[cell_id] = {
                "particles":[(float(re.split(" [TN]=", particles.split('\n')[0])[1]),
                    [(int(sid), (float(x) - network[cell_id]["wsize"]/2,
                                 float(y) - network[cell_id]["wsize"]/2,
                                 float(z) - network[cell_id]["wsize"]/2))
                    for _, sid, x, y, z in [particle.split()
                    for particle in particles.split('\n')[2:] if particle]])
                    for particles in open("{}/{}.out".format(config["data_folder"],
                        config["cell_file"].format(step=mech_step, substep=0, cell_id=cell_id)), 'r'
                        ).read().split("ParticlePositions")[1:]],
                "cell": network[cell_id]["position"]}

    formated_data = np.array(sum([
        [[
            x + raw_data[cell_id]["cell"][0],
            y + raw_data[cell_id]["cell"][1],
            color_map[sid],
            (100*(z/network[cell_id]["wsize"]) + bias),
            ]
            for sid, (x, y, z) in raw_data[cell_id]["particles"][local_timestep][1]]
            for cell_id in raw_data], []))

    x, y, c, s = formated_data.T
    plot.set_offsets(np.array(list(zip(x,y))))
    plot.set_sizes(s.astype(float))
    plot.set_color(c)

    #for cell_id in raw_data:
    #    ax.add_patch(patches.Rectangle((raw_data[cell_id]["cell"][0],
    #                                  raw_data[cell_id]["cell"][1]),
    #                                  network[cell_id]["wsize"], network[cell_id]["wsize"],
    #                                  facecolor='none', edgecolor='k',
    #                                  linewidth=2))
    return plot

ani = animation.FuncAnimation(fig, animate, range(config["n_mech_steps"]*config["n_kin_substeps"]*n_local_steps),
        interval=10, init_func=init)
#ani.save("notchdelta.mp4")
plt.show()

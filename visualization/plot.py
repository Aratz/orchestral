import re
import json
import numpy as np
import matplotlib.pyplot as plt
import numpy

with open("32/config.json", 'r') as f:
    config = json.load(f)

with open("32/network.json", 'r') as f:
    network = json.load(f)

tstep = config["n_steps"]

raw_data = {cell_id:{


    "particles":[(float(re.split(" [TN]=", particles.split('\n')[0])[1]),
        [(int(sid), (float(x), float(y), float(z)))
        for _, sid, x, y, z in [particle.split()
        for particle in particles.split('\n')[2:] if particle]])
        for particles in open("32/data/cell-{}-{}.out".format(tstep, cell_id),
            'r').read().split("ParticlePositions")[1:]],
    "cell": network[cell_id]["position"]}
        for cell_id in network}

n_local_steps = len(raw_data["1"]["particles"])


# In[3]:


color_map = {
        1: 'k',
        2: 'k',
        3: '#de2d26',
        4: '#3182bd',
        }

bias = 5

fig, ax = plt.subplots(figsize=(10, 10))
#plot = ax.scatter([], [])



formated_data = np.array(sum([
    [[
        x + raw_data[cell_id]["cell"][0],
        y + raw_data[cell_id]["cell"][1],
        color_map[sid],
        (20*(z/network[cell_id]["wsize"]) + bias),
        ]
        for sid, (x, y, z) in raw_data[cell_id]["particles"][-1][1] if sid != 2]
        for cell_id in raw_data], []))

bound_dna = np.array(sum([
    [[
        x + raw_data[cell_id]["cell"][0],
        y + raw_data[cell_id]["cell"][1],
        color_map[sid],
        (20*(z/network[cell_id]["wsize"]) + bias),
        ]
        for sid, (x, y, z) in raw_data[cell_id]["particles"][-1][1] if sid == 2]
        for cell_id in raw_data], []))

from matplotlib.patches import Rectangle
current_axis = plt.gca()
for cell_id in raw_data:
    size = network[cell_id]["wsize"]
    current_axis.add_patch(Rectangle((raw_data[cell_id]["cell"][0],
                                      raw_data[cell_id]["cell"][1]),
                                      size, size, facecolor='none', edgecolor='k',
                                      linewidth=2))

x, y, c, s = formated_data.T
plt.scatter(x.astype(float), y.astype(float), s=s.astype(float), c=c, alpha=0.5)

x, y, c, s = bound_dna.T
plt.scatter(x.astype(float), y.astype(float), marker='v', s=s.astype(float), color=c, alpha=0.5)

plt.xlim(0, np.sqrt(len(network))*network["1"]["wsize"])
plt.ylim(0, np.sqrt(len(network))*network["1"]["wsize"])
plt.ticklabel_format(style='sci', axis='both', scilimits=(0, 0))
plt.savefig("32.svg")

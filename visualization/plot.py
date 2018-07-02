import re
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

with open(sys.argv[1], 'r') as f:
    config = json.load(f)

output_folder = sys.argv[2]

xmin = float(sys.argv[3])
xmax = float(sys.argv[4])
ymin = float(sys.argv[5])
ymax = float(sys.argv[6])

color_map = {
        1: 'k',
        2: 'k',
        3: 'r',
        4: 'b',
        }
bias = 1

for mech_step in range(config["n_mech_steps"]):
    with open("{}/{}.out".format(
        config["data_folder"],
        config["network_file"].format(step=mech_step))) as f:
            network = json.load(f)["final"]

    for kin_step in range(config["n_kin_substeps"]):
        plt.figure(figsize=(7.5,7.5))
        raw_data = {cell_id:{
            "particles":[(float(re.split(" [TN]=", particles.split('\n')[0])[1]),
                [(int(sid), (float(x), float(y), float(z)))
                for _, sid, x, y, z in [particle.split()
                for particle in particles.split('\n')[2:] if particle]])
                for particles in open(
                    "{}/{}.out".format(
                        config["data_folder"],
                        config["cell_file"].format(
                            step=mech_step,
                            substep=kin_step,
                            cell_id=cell_id
                            )
                        )
                    ).read().split("ParticlePositions")[1:]],
            "cell": network[cell_id]["position"]}
                for cell_id in network}

        #kin_step+mech_step*kin_step
        formated_data = np.array(sum([
            [[
                x + raw_data[cell_id]["cell"][0],
                y + raw_data[cell_id]["cell"][1],
                color_map[sid],
                (1*(z/network[cell_id]["wsize"]) + bias),
                ]
                for sid, (x, y, z) in raw_data[cell_id]["particles"][0][1]]
                for cell_id in raw_data], []))


        x, y, c, s = formated_data.T
        plt.scatter(x.astype(float), y.astype(float), s=s.astype(float), c=c, alpha=0.3)
        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        plt.title("{h:3d}h{m:02d}m".format(h=mech_step, m=int(round(kin_step*60./config["n_kin_substeps"]))))
        plt.xlabel("x")
        plt.ylabel("y")
        plt.savefig("{}/{}.png".format(
            output_folder,
            "network-{}".format(kin_step+mech_step*config["n_kin_substeps"])))
        plt.close()


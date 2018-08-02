import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['text.usetex'] = True
matplotlib.rcParams.update({'font.family': 'serif'})
matplotlib.rcParams.update({'font.size': '16'})


with open(sys.argv[1], 'r') as f:
    data = json.load(f)

df = pd.DataFrame.from_dict(data)

data = {key:df.loc[df['name'] == key]
        for key in ['task map 1s tasks', 'task map 100ms tasks', 'task map fast tasks']}
data = {key:list(zip(*sorted(zip(value['n'], value['rate']), key=lambda x:x[0])))
        for key, value in data.items()}

f, ax = plt.subplots(2, 1, figsize=(6, 12.5))

for i, key in enumerate(['task map 1s tasks', 'task map 100ms tasks']):
    ax[i].set_title(key)
    ax[i].plot(data[key][0], data[key][1],'-o')
    ax[i].set_xticks(data[key][0])
    ax[i].grid(linestyle='dotted')

    ax[i].plot([0, 1.1*max(data[key][0])], [0, 1.1*max(data[key][0])*min(data[key][1])/data[key][0][0]],
            ':', color='0.5')
    ax[i].set_ylim(0, 2*max(data[key][1]))
    ax[i].set_xlim(0, 1.1*max(data[key][0]))
    ax[i].set_xlabel(r"\# cores")
    ax[i].set_ylabel(r"tasks/s")

plt.tight_layout()

plt.subplots_adjust(hspace=0.5)
plt.savefig("latency.eps")
plt.savefig("latency.png")
plt.show()

import json
import parse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['text.usetex'] = True
matplotlib.rcParams.update({'font.family': 'serif'})
matplotlib.rcParams.update({'font.size': '16'})


def m2s(string):
    """
    Parses output of time command
    """
    p = parse.parse("real\t{m:d}m{s:f}s", string)
    if p:
        return 60*p['m'] + p['s']

data = {
        stepsize:{
            ncore:[
                m2s(line)
                for line in open("{}_total_time_{}.txt".format(ncore, stepsize), 'r').readlines()
                if m2s(line)
                ]
            for ncore in [1, 4, 8, 12, 16, 20]
            }
        for stepsize in ["1.0", "0.5", "0.1"]
        }

#print(json.dumps(data, indent=4))


#plt.xscale('log')
for stepsize in sorted(data.keys()):
    x = sorted(list(data[stepsize].keys()))
    y = np.array([100 * np.mean(data[stepsize][1])
        / (key*np.mean(data[stepsize][key])) for key in x])
    print(stepsize, np.mean(data[stepsize][1]))
    plt.plot(x, y, '-o', label=stepsize)
    plt.xticks(x, x)

#plt.legend(loc=0)
plt.title(r"Strong scaling efficiency for a $8\times8$ cell grid")
plt.xlabel(r"\# cores")
plt.ylabel(r"Strong Scaling Efficiency (\%)")
plt.ylim(0, 105)
plt.grid(linestyle='dotted')
plt.legend(loc=0)

#plt.savefig("strong_scaling.eps")
plt.show()

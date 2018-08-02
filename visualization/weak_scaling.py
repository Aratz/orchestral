import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['text.usetex'] = True
matplotlib.rcParams.update({'font.family': 'serif'})
matplotlib.rcParams.update({'font.size': '16'})

data = {
        0.1: {
            8: 181.1099841594696,
            16: 232.18067455291748,
            32: 268.0214204788208,
            64: 292.9651737213135,
            128: 337.1968915462494,
            256: 471.231586933136},
        0.5: {
            8: 406.77178621292114,
            16: 465.4719977378845,
            32: 503.0786962509155,
            64: 524.950754404068,
            128: 576.5768313407898,
            256: 730.0078234672546
            },
        1.0: {
            8: 646.2594635486603,
            16: 691.4401707649231,
            32: 744.5248830318451,
            64: 774.2930459976196,
            128: 830.3566310405731,
            256: 1017.5472323894501
            }
        }

plt.xscale('log', basex=2)

for stepsize in sorted(data.keys()):
    x = sorted(list(data[stepsize].keys()))
    y = np.array([100 * np.mean(data[stepsize][8]) / np.mean(data[stepsize][key]) for key in x])
    plt.plot(x, y, '-o', label=stepsize)
    #plt.xticks(x, x)

plt.legend(loc=0)
plt.title(r"Weak scaling efficiency")
plt.xlabel(r"\# cores")
plt.ylabel(r"Weak Scaling Efficiency (\%)")
plt.ylim(0, 105)
plt.grid(linestyle='dotted')

#plt.savefig("weak_scaling.eps")
#plt.savefig("weak_scaling.png")
plt.show()

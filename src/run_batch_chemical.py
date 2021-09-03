"""
Run a batch reactor model to compare final yield of a chemical species for
each feedstock using the Debiagi 2018 kinetics.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import reactor as rct
from feedstock import Feedstock

# Parameters
# ----------------------------------------------------------------------------

# Chemical species used to predict final yield
# C6H5OH is phenol
chemical = 'FURFURAL'

temp = 773.15                       # reactor temperature [K]
p = 101325.0                        # reactor pressure [Pa]
time = np.linspace(0, 20.0, 100)    # reaction time steps [s]

energy = 'off'                      # reactor energy
cti = 'data/debiagi_sw_meta.cti'    # Cantera input file

# Feedstocks
# ----------------------------------------------------------------------------

with open("data/feedstocks.json") as json_file:
    fdata = json.load(json_file)

feedstocks = [Feedstock(fd) for fd in fdata]

# Cantera batch reactor
# ----------------------------------------------------------------------------

n = len(feedstocks)

names = []
y_chemical = np.zeros(n)

# Run batch reactor model for each feedstock
for i in range(n):
    feedstock = feedstocks[i]
    names.append(feedstock.name)

    # Calculate optimized biomass composition (daf) and splitting parameters
    bc, splits = feedstock.calc_biocomp()
    cell, hemi, ligc, ligh, ligo, tann, tgl = bc['y_daf']

    # Get feedstock moisture content as mass fraction
    yh2o = feedstock.prox_ad[3] / 100

    # Perform batch reactor simulation
    y0 = {'CELL': cell, 'GMSW': hemi, 'LIGC': ligc, 'LIGH': ligh, 'LIGO': ligo,
          'TANN': tann, 'TGL': tgl, 'ACQUA': yh2o}

    states = rct.run_batch_simulation(cti, p, temp, time, y0, energy='off')

    y_chemical[i] = states(chemical).Y[-1]

# Plot
# ----------------------------------------------------------------------------

y = np.arange(n)

_, ax = plt.subplots(tight_layout=True)
ax.barh(y, y_chemical)
ax.set_xlabel('Furfural mass fraction [-]')
ax.set_yticks(y)
ax.set_yticklabels(names)
ax.invert_yaxis()
ax.set_frame_on(False)
ax.set_axisbelow(True)
ax.tick_params(color='0.8')
ax.xaxis.grid(True, color='0.8')

plt.show()

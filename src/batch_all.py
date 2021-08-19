"""
Run a batch reactor model for every FCIC feedstock using the Debiagi 2018
biomass pyrolysis kinetics. All reactions and chemical species are defined in
Cantera `cti` files where `debiagi_sw.cti` is for softwood reactions,
`debiagi_hw.cti` is for hardwood reactions, and `debiagi_gr.cti` is for grass
reactions. Biomass compositions for each feedstock were determined from the
`biocomp.py` file.

Note
----
The `debiagi_sw.cti` uses the original reaction rates from Debiagi 2018 while
`debiagi_sw_meta.cti` uses modified rates for the metaplastic reactions.

Reference
---------
P. Debiagi, G. Gentile, A. Cuoci, A. Frassoldati, E. Ranzi, and T. Faravelli.
A predictive model of biochar formation and characterization. Journal of
Analytical and Applied Pyrolysis, vol. 134, pp. 326-335, 2018.
"""

import cantera as ct
import matplotlib.pyplot as plt
import numpy as np

ct.suppress_thermo_warnings()

# Parameters
# ----------------------------------------------------------------------------

tk = 773.15                         # reactor temperature [K]
p = 101325.0                        # reactor pressure [Pa]
time = np.linspace(0, 10.0, 100)    # reaction time steps [s]
cfile = 'data/debiagi_sw_meta.cti'  # Cantera input file

# Feedstock biomass compositions

feedstocks = [
    {'name': 'residues', 'biocomp': [28.98, 22.02, 0.58, 8.79, 27.16, 1.60, 10.88], 'ash': 1.45},
    {'name': 'stem wood', 'biocomp': [39.91, 25.42, 0.89, 26.20, 3.20, 0.01, 4.37], 'ash': 0.28},
    {'name': 'bark', 'biocomp': [31.38, 22.99, 35.14, 0.0, 0.0, 7.15, 3.34], 'ash': 0.70},
    {'name': 'needles', 'biocomp': [23.59, 17.57, 0.63, 5.43, 37.30, 3.00, 12.48], 'ash': 3.78},
    {'name': 'bark + needles', 'biocomp': [23.91, 16.82, 6.94, 6.74, 34.53, 2.84, 8.22], 'ash': 2.52},
    {'name': 'residues2', 'biocomp': [27.45, 20.81, 0.0, 3.71, 32.79, 1.98, 13.27], 'ash': 1.65}
]

# Chemical species representing gas, liquid, solid, metaplastic phases

sp_gases = ('C2H4', 'C2H6', 'CH2O', 'CH4', 'CO', 'CO2', 'H2')

sp_liquids = (
    'C2H3CHO', 'C2H5CHO', 'C2H5OH', 'C5H8O4', 'C6H10O5', 'C6H5OCH3', 'C6H5OH',
    'C6H6O3', 'C24H28O4', 'CH2OHCH2CHO', 'CH2OHCHO', 'CH3CHO', 'CH3CO2H',
    'CH3OH', 'CHOCHO', 'CRESOL', 'FURFURAL', 'H2O', 'HCOOH', 'MLINO', 'U2ME12',
    'VANILLIN'
)

sp_solids = (
    'CELL', 'CELLA', 'GMSW', 'HCE1', 'HCE2', 'ITANN', 'LIG', 'LIGC', 'LIGCC',
    'LIGH', 'LIGO', 'LIGOH', 'TANN', 'TGL', 'CHAR', 'ACQUA'
)

sp_metaplastics = (
    'GCH2O', 'GCO2', 'GCO', 'GCH3OH', 'GCH4', 'GC2H4', 'GC6H5OH', 'GCOH2',
    'GH2', 'GC2H6'
)

# Cantera batch reactor
# ----------------------------------------------------------------------------

gas = ct.Solution(cfile)

n = len(feedstocks)
names = []
ash = np.zeros(n)
yf_gases = np.zeros(n)
yf_liquids = np.zeros(n)
yf_solids = np.zeros(n)
yf_metas = np.zeros(n)

print('\nLumped species final yields as mass fraction, dry ash-free basis\n')
print('Feedstock              Gases    Liquids  Solids   Metaplastics')

for i, feed in enumerate(feedstocks):

    bc = feed['biocomp']
    y0 = np.array(bc) / 100

    y00 = f'CELL:{y0[0]} GMSW:{y0[1]} LIGC:{y0[2]} LIGH:{y0[3]} LIGO:{y0[4]} TANN:{y0[5]} TGL:{y0[6]}'
    gas.TPY = tk, p, y00
    r = ct.IdealGasReactor(gas, energy='off')

    sim = ct.ReactorNet([r])
    states = ct.SolutionArray(gas, extra=['t'])

    for t in time:
        sim.advance(t)
        states.append(r.thermo.state, t=t)

    y_gases = states(*sp_gases).Y.sum(axis=1)
    y_liquids = states(*sp_liquids).Y.sum(axis=1)
    y_solids = states(*sp_solids).Y.sum(axis=1)
    y_metaplastics = states(*sp_metaplastics).Y.sum(axis=1)

    names.append(feed['name'])
    ash[i] = feed['ash']
    yf_gases[i] = y_gases[-1]
    yf_liquids[i] = y_liquids[-1]
    yf_solids[i] = y_solids[-1]
    yf_metas[i] = y_metaplastics[-1]

    name = feed['name']
    print(f'{name:20} {y_gases[-1]:8.4f} {y_liquids[-1]:8.4f} {y_solids[-1]:8.4f} {y_metaplastics[-1]:8.4f}')


# Plot
# ----------------------------------------------------------------------------

def style_barh(ax):
    ax.invert_yaxis()
    ax.set_axisbelow(True)
    ax.set_frame_on(False)
    ax.tick_params(color='0.8')
    ax.xaxis.grid(True, color='0.8')


y = np.arange(n)

_, ax = plt.subplots(tight_layout=True)
ax.barh(y, yf_gases, color='C6')
ax.set_yticks(y)
ax.set_yticklabels(names)
ax.set_xlabel('Mass fraction [-]')
ax.set_title('Gases')
style_barh(ax)

_, ax = plt.subplots(tight_layout=True)
ax.barh(y, yf_liquids, color='C4')
ax.set_yticks(y)
ax.set_yticklabels(names)
ax.set_xlabel('Mass fraction [-]')
ax.set_title('Liquids')
style_barh(ax)

_, ax = plt.subplots(tight_layout=True)
ax.barh(y, yf_solids, color='C2')
ax.set_yticks(y)
ax.set_yticklabels(names)
ax.set_xlabel('Mass fraction [-]')
ax.set_title('Solids')
style_barh(ax)

_, ax = plt.subplots(tight_layout=True)
ax.barh(y, yf_metas, color='C1')
ax.set_yticks(y)
ax.set_yticklabels(names)
ax.set_xlabel('Mass fraction [-]')
ax.set_title('Metaplastics')
style_barh(ax)

# ---

_, ax = plt.subplots(tight_layout=True)
b1 = ax.barh(y, yf_gases, color='C6', label='Gases')
b2 = ax.barh(y, yf_liquids, left=yf_gases, color='C4', label='Liquids')
b3 = ax.barh(y, yf_solids, left=yf_gases + yf_liquids, color='C2', label='Solids')
b4 = ax.barh(y, yf_metas, left=yf_gases + yf_liquids + yf_solids, color='C1', label='Metaplastics')
ax.bar_label(b1, label_type='center', fmt='%.2f')
ax.bar_label(b2, label_type='center', fmt='%.2f')
ax.bar_label(b3, label_type='center', fmt='%.2f')
ax.bar_label(b4, label_type='center', fmt='%.2f')
ax.legend(bbox_to_anchor=[0.5, 1.02], loc='center', ncol=4, frameon=False)
ax.set_yticks(y)
ax.set_yticklabels(names)
ax.set_xlabel('Mass fraction [-]')
style_barh(ax)

# ---

# yf_gases2 = np.array([0.147, 0.141, 0.114, 0.145, 0.151])
# yf_liquids2 = np.array([0.635, 0.723, 0.583, 0.554, 0.555])
# yf_solids2 = np.array([0.152, 0.109, 0.319, 0.256, 0.165])

# h = 0.40

# _, ax = plt.subplots(tight_layout=True)

# b1 = ax.barh(y, yf_gases, height=h, color='C6', label='Gases')
# e1 = ax.barh(y + h, yf_gases2, height=h, color='C6', alpha=0.5)

# b2 = ax.barh(y, yf_liquids, height=h, left=yf_gases, color='C4', label='Liquids')
# e2 = ax.barh(y + h, yf_liquids2, height=h, left=yf_gases2, color='C4', alpha=0.5)

# b3 = ax.barh(y, yf_solids, height=h, left=yf_gases + yf_liquids, color='C2', label='Solids')
# e3 = ax.barh(y + h, yf_solids2, height=h, left=yf_gases2 + yf_liquids2, color='C2', alpha=0.5)

# b4 = ax.barh(y, yf_metas, height=h, left=yf_gases + yf_liquids + yf_solids, color='C1', label='Metaplastics')

# ax.bar_label(b1, label_type='center', fmt='%.2f')
# ax.bar_label(e1, label_type='center', fmt='%.2f')
# ax.bar_label(b2, label_type='center', fmt='%.2f')
# ax.bar_label(e2, label_type='center', fmt='%.2f')
# ax.bar_label(b3, label_type='center', fmt='%.2f')
# ax.bar_label(e3, label_type='center', fmt='%.2f')
# ax.bar_label(b4, label_type='center', fmt='%.2f')

# ax.legend(bbox_to_anchor=[0.5, 1.02], loc='center', ncol=4, frameon=False)
# ax.set_yticks(y + h / 2)
# ax.set_yticklabels(names)
# ax.set_xlabel('Mass fraction [-]')
# style_barh(ax)

# ---

z = np.polyfit(ash, yf_liquids, 1)
p = np.poly1d(z)

_, ax = plt.subplots()
ax.plot(ash, yf_liquids * 100, 'o')
ax.plot(ash, p(ash) * 100)
ax.set_xlabel('Ash [wt. %]')
ax.set_ylabel('Liquids [wt. %]')

plt.show()

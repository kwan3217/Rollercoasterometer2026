import numpy as np
import matplotlib.pyplot as plt
from allan_variance import compute_avar, estimate_parameters

data = np.load('data/zed_f9r_processed.npz')

# Dataset in question seems to have a glitch after 3 million samples. Maybe a cat jumped on it?
# gravity data not clean after 2M samples.

t_gyros = data['t_gyros'][:2_000_000]
x_gyros = data['x_gyros'][:2_000_000]
y_gyros= data['y_gyros'][:2_000_000]
z_gyros= data['z_gyros'][:2_000_000]
T_gyros=data['T_gyros'][:2_000_000]

t_accs = data['t_accs'][:2_000_000]
x_accs = data['x_accs'][:2_000_000]
y_accs= data['y_accs'][:2_000_000]
z_accs= data['z_accs'][:2_000_000]

x_accs_ug=x_accs/9.80665*1e6
y_accs_ug=y_accs/9.80665*1e6
z_accs_ug=z_accs/9.80665*1e6

x_gyros_degphr=x_gyros*3600.0
y_gyros_degphr=y_gyros*3600.0
z_gyros_degphr=z_gyros*3600.0

plt.figure("Allan deviation in acceleration")
for i, (ts,data,color) in enumerate(((t_accs,x_accs_ug,'r'), (t_accs,y_accs_ug,'g'), (t_accs,z_accs_ug,'b'))):
    data-=np.mean(data)
    taus, sigma2s = compute_avar(data, (ts[-1] - ts[0]) / len(data))
    params, avar_pred = estimate_parameters(taus, sigma2s)
    plt.loglog(taus, np.sqrt(avar_pred), 'k-')
    plt.loglog(taus, np.sqrt(sigma2s), color)
    print(f"---\n{params}")
plt.xlabel(r'$\tau$/s')
plt.ylabel(r'acceleration/$\mu$g')
plt.figure("Allan deviation in rotation rate")
for i, (ts,data,color) in enumerate(((t_accs,x_gyros_degphr,'r'), (t_accs,y_gyros_degphr,'g'), (t_accs,z_gyros_degphr,'b'))):
    data-=np.mean(data)
    taus, sigma2s = compute_avar(data, (ts[-1] - ts[0]) / len(data))
    params, avar_pred = estimate_parameters(taus, sigma2s)
    plt.loglog(taus, np.sqrt(avar_pred), 'k-')
    plt.loglog(taus, np.sqrt(sigma2s), color)
    plt.xlabel(r'$\tau$/s')
    plt.ylabel(r'acceleration/$\mu$g')
    print(f"---\n{params}")
plt.xlabel(r'$\tau$/s')
plt.ylabel(r'rotation rate/(deg/hr)')
plt.show()

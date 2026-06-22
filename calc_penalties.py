import numpy as np

eb = 500 # epoch blocks
c_r = 1.01 # reward
m = 10 # fanout

T_max = 10 # max rehab period

probs = {
    "pi-EU": {
        "alfa_C": 94.3e-2,
        "alfa_F": 71.2e-2,
        "gama_C": 2.0e-2,
        "gama_F": 25.2e-2,
        "delta_C": 0.2e-2,
        "delta_F": 0.4e-2,
    },
    "pi-EB": {
        "alfa_C": 94.1e-2,
        "alfa_F": 73.0e-2,
        "gama_C": 2.2e-2,
        "gama_F": 24.3e-2,
        "delta_C": 0.01e-2,
        "delta_F": 0.4e-2,
    },
    "iota-EB": {
        "alfa_C": 85.9e-2,
        "alfa_F": 83.4e-2,
        "gama_C": 0.2e-2,
        "gama_F": 1.9e-2,
        "delta_C": 0.005e-2,
        "delta_F": 0.3e-2,
    },
}



# probs
alfa_C  = probs["pi-EU"]["alfa_C"]
alfa_F  = probs["pi-EU"]["alfa_F"]
gama_C  = probs["pi-EU"]["gama_C"]
gama_F  = probs["pi-EU"]["gama_F"]
delta_C = probs["pi-EU"]["delta_C"]
delta_F = probs["pi-EU"]["delta_F"]

step = 0.05

options = map(lambda x: x*step, list(range(0, int((T_max+1)/step)))[1:])
for c_r in [1.0001]:
    for T in options:
        c_I0 = c_r**(-eb*T)
        #c_I1 = c_I0**(1/m)

        c_p_inf = np.e**(-(alfa_C*np.log(c_r)+delta_C*np.log(c_I0))/gama_C)#+delta_C1*np.log(c_I1))/gama_C)
        c_p_sup = np.e**(-(alfa_F*np.log(c_r)+delta_F*np.log(c_I0))/gama_F)#+delta_F1*np.log(c_I1))/gama_F)
        c_p_med = (c_p_inf+(c_p_sup if c_p_sup < 1 else 1))/2

        c_p_string = f"[{c_p_inf}, {c_p_sup}]" if c_p_sup > c_p_inf else "Ø"
        c_p_med_string = "" if c_p_string == "Ø" else f"\nc_p  = {c_p_med}"

        T_alt = - np.log(c_p_med)/np.log(c_r*eb)
        T_real = T_alt if T_alt > T else T

        txt_impossivel = f"T = {T:0.2f} épocas, {int(T*eb)} blocos\nCalibração impossível - c_r = {c_r} c_p_inf = {c_p_inf}\n"
        txt_possivel = f"""T = {T:0.2f} épocas, {int(T*eb)} blocos
c_r  = {c_r}
c_I0 = {c_I0}
c_p  = {c_p_string}{c_p_med_string}
T_real = {T_real:0.2f}

"""
        if not c_p_inf>1: # demasiados prints, dar print só aos casos possíveis
            print(txt_impossivel if c_p_inf>1 else txt_possivel)
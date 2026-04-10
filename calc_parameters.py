import sys
import numpy as np

print_model1_template = """[MODEL 1]:
n_h = {n_h}
h = {h}
h_mean = {h_mean}

P_Internal = {P_Internal}

alfa_a = {alfa_a}
alfa_c = {alfa_c}

beta_a = {beta_a}
beta_c = {beta_c}

gama_a = {gama_a}
gama_c = {gama_c}

------------------
"""

print_model2_template = """[MODEL 2]:
n_h = {n_h}
h = {h}
h_mean = {h_mean}

P_Internal = {P_Internal}

alfa_a_ = {alfa_a_}
alfa_c_ = {alfa_c_}

beta_a_ = {beta_a_}
beta_c_ = {beta_c_}

gama_a_ = {gama_a_}
gama_c_ = {gama_c_}

------------------

alfa_a = {alfa_a}
alfa_c = {alfa_c}

beta_a = {beta_a}
beta_c = {beta_c}

gama_a = {gama_a}
gama_c = {gama_c}

delta = {delta}
delta_i = {delta_i}

------------------
"""

print_params_template = """k_c = {k_c}
{k_p_c} < k_p < {k_p_a}
k_p ∈ {interval}
k_p_mean = {k_p_mean}
k_I = {k_I}

------------------
"""

print_attenuation_template = """ω -> observed frequency of node p as leader
λ -> attenuation function
λ(ω) = ω/({a_inv}) + {b}

------------------
"""

def model1(m,N,f,fa,b_v,v_e,P_biz):
    h = int(np.log(N)/np.log(m)) # height of tree
    n_h = N - (m**h-1)/(m-1) # nodes at max height
    h_mean = sum([l*m**l if l != h else l*n_h for l in range(h+1)])/N # mean height of tree
    if h_mean <= 1:
        print(f"[WARNING]: This is probably too short of a tree, mean height = {h_mean}")

    P_Internal = int((N-1+m-1)/m)/N # probability of being an internal node
    P_biz_action = P_Internal if P_biz<0 else P_biz # probability of bizantine action

    # beta = P(algum vizinho falhar) + P(eu agir de forma bizantina)
    beta_a = ((1-1/N) + m*P_Internal) * (fa-1)/(N-1) * P_biz_action + P_biz_action
    beta_c = ((1-1/N) + m*P_Internal) * fa/(N-1) * P_biz_action + 0

    gama_a = max(h_mean-1,0) * (fa-1)/(N-1) * P_biz_action
    gama_c = max(h_mean-1,0) * fa/(N-1) * P_biz_action

    alfa_a = 1 - beta_a - gama_a
    alfa_c = 1 - beta_c - gama_c

    print(print_model1_template.format(n_h=n_h,h=h,h_mean=h_mean,P_Internal=P_Internal,
                                       alfa_a=alfa_a,alfa_c=alfa_c,beta_a=beta_a,beta_c=beta_c,gama_a=gama_a,gama_c=gama_c))
    
    k_c_references = [1.01+0.01*i for i in range(1)] # reference values for compensation coefficient

    I = int((N-1+m-1)/m)
    INILL = I - (m**(h-1)-1)/(m-1) # Internal Nodes In Lowest Level
    
    for k_c in k_c_references:
        k_I = "N/S"
        k_p_c = np.e**(-(alfa_c*np.log(k_c))/beta_c)
        k_p_a = np.e**(-(alfa_a*np.log(k_c))/beta_a)

        interval = "Ø" if k_p_c >= k_p_a else f"[{k_p_c}, {k_p_a}]"
        print(print_params_template.format(k_c=k_c,k_p_c=k_p_c,k_p_a=k_p_a,k_I=k_I,interval=interval,k_p_mean=(k_p_a+k_p_c)/2))


def model2(m, N, f, fa, b_v, v_e):
    h = int(np.log(N)/np.log(m)) # height of tree
    n_h = N - (m**h-1)/(m-1) # nodes at max height
    h_mean = sum([l*m**l if l != h else l*n_h for l in range(h+1)])/N # mean height of tree
    if h_mean <= 1:
        print(f"[WARNING]: This is probably too short of a tree, mean height = {h_mean}")

    P_Internal = int((N-1+m-1)/m)/N # probability of being an internal node

    # beta = [Prob(falhar) || Prob(vizinho falhar)] && P(todo ascendente ignorando o pai não falhar)
    beta_a_ = (P_Internal + (P_Internal*m + 1-1/N)*(fa-1)/(N-1) - P_Internal * (P_Internal*m + 1-1/N)*(fa-1)/(N-1)) * (1 - max(0, h_mean-1) * (fa-1)/(N-1))

    beta_c_ = (P_Internal*m + 1-1/N) * fa/(N-1) * (1 - max(0, h_mean-1) * fa/(N-1))

    # gama = P(algum ascendente ignorando o pai falhar)
    gama_a_ = max(0, h_mean-1) * (fa-1)/(N-1)

    gama_c_ = max(0, h_mean-1) * fa/(N-1)

    # alfa = 1- beta - gama
    alfa_a_ = 1 - beta_a_ - gama_a_

    alfa_c_ = 1 - beta_c_ - gama_c_

    beta_i_ = beta_a_ * fa/N + beta_c_* (N-fa)/N
    gama_i_ = gama_a_ * fa/N + gama_c_* (N-fa)/N
    delta = (gama_i_ + beta_i_ - gama_i_*beta_i_)**(f+1)

    alfa_a = (1-delta)*alfa_a_
    alfa_c = (1-delta)*alfa_c_
    beta_a = (1-delta)*beta_a_
    beta_c = (1-delta)*beta_c_
    gama_a = (1-delta)*gama_a_
    gama_c = (1-delta)*gama_c_

    delta_i = [delta*m**l/N for l in range(h)] # ignore leaf level

    print(print_model2_template.format(n_h=n_h,h=h,h_mean=h_mean,P_Internal=P_Internal,
                                alfa_a_=alfa_a_,alfa_c_=alfa_c_,beta_a_=beta_a_,beta_c_=beta_c_,gama_a_=gama_a_,gama_c_=gama_c_,
                                alfa_a=alfa_a,alfa_c=alfa_c,beta_a=beta_a,beta_c=beta_c,gama_a=gama_a,gama_c=gama_c,
                                delta=delta,delta_i=delta_i))
    
    k_c_references = [1.01+0.01*i for i in range(1)] # reference values for compensation coefficient

    I = int((N-1+m-1)/m)
    INILL = I - (m**(h-1)-1)/(m-1) # Internal Nodes In Lowest Level
    
    for k_c in k_c_references:
        k_I = (k_c**(-b_v*v_e*INILL)) # internal node base penalty - calibrado para a os internors mais inferiores
        sum_delta = 0
        for i, d in enumerate(delta_i):
            I_l = m**i if i < h-1 else INILL # Internal nodes in level l
            sum_delta += d * np.log(k_I**(1/I_l))
        k_p_c = np.e**(-(alfa_c*np.log(k_c)+sum_delta)/beta_c)
        k_p_a = np.e**(-(alfa_a*np.log(k_c)+sum_delta)/beta_a)

        interval = "Ø" if k_p_c >= k_p_a else f"[{k_p_c}, {k_p_a}]"
        print(print_params_template.format(k_c=k_c,k_p_c=k_p_c,k_p_a=k_p_a,k_I=k_I,interval=interval,k_p_mean=(k_p_a+k_p_c)/2))

def attenuation(N,v_e): 
    # attenuation function
    freq_avg = v_e*5/N/4
    a_inv = freq_avg-v_e
    b = 1/(1-5/(4*N))
    print(print_attenuation_template.format(a_inv=a_inv, b=b))

def model(mdl, m, N, f, fa, b_v, v_e, P_biz):
    if mdl == 1:
        model1(m, N, f, fa, b_v, v_e, P_biz)
    elif mdl == 2:
        model2(m, N, f, fa, b_v, v_e)
    else:
        print(f"Model {mdl} not found")

if __name__ == "__main__":
    if len(sys.argv) != 8:
        print("""Usage: python calc_parameters <model> <fanout> <num_nodes> <fa> <blocks_per_view> <views_per_epoch> <P_biz>
              <model> - model 1 or 2 - 2 is the most up-to-date
              <fa> - number of actual faults, fa <= 0 to adopt maximum tolerated failures
              <P_biz> - Probability of bizantine action, P_biz < 0 => P_biz = Prob. of being an internal node""")
        sys.exit(1)
    mdl = int(sys.argv[1]) # model number
    m = int(sys.argv[2]) # fanout
    N = int(sys.argv[3]) # number of nodes
    f = (N-1)//3 # tolerated faults
    fa = int(sys.argv[4]) if int(sys.argv[4]) > 0 else f
    b_v = int(sys.argv[5])
    v_e = int(sys.argv[6])
    P_biz = float(sys.argv[7])
    model(mdl, m, N, f, fa, b_v, v_e, P_biz)
    attenuation(N, v_e)
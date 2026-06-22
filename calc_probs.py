import numpy as np
from scipy.special import comb

N = 111
m = 10
fa = 9
f = 34

def P(f, k, N, n):
    return comb(f, k)*comb(N-f,n-k)/comb(N, n)


# formas de a configuração falhar:
# A líder bizantino
# se líder correto:
# B - 3 biz internos nível 1 com pelo menos 2 biz folha sem pai bizantino
# C - 4 ou mais biz internos nível 1

# A
p_lb = fa/N # prob líder biz -- P(A)
p_A = p_lb

P_delta_C_A = [0, [], None] # P( delta_i | A), p_i in C
P_delta_F_A = [1/fa, [], None] # P( delta_i | A), p_i in F

for i in range(fa):
    p = P(fa-1, i, N-1, 10) # probabilidade de haver i bizantinos internos além do líder
    info_C = {"P(I_biz=i)": p, "delta1": (10-i)/(N-fa), "delta2": (N-fa-(10-i))/(N-fa)}
    info_F = {"P(I_biz=i)": p, "delta1": i/fa, "delta2": (fa-i-1)/fa}
    P_delta_C_A[1].append(info_C)
    P_delta_F_A[1].append(info_F)

res1 = 0
res2 = 0
res3 = 0
res4 = 0
for i in range(fa):
    res1 += P_delta_C_A[1][i]["P(I_biz=i)"]*P_delta_C_A[1][i]["delta1"]
    res2 += P_delta_F_A[1][i]["P(I_biz=i)"]*P_delta_F_A[1][i]["delta1"]
    res3 += P_delta_C_A[1][i]["P(I_biz=i)"]*P_delta_C_A[1][i]["delta2"]
    res4 += P_delta_F_A[1][i]["P(I_biz=i)"]*P_delta_F_A[1][i]["delta2"]
P_delta_C_A[1] = res1
P_delta_F_A[1] = res2
P_delta_C_A[2] = res3
P_delta_F_A[2] = res4

print("p_A =", p_A)
print("p_i in C => P(delta_i | A) =", P_delta_C_A)
print("p_i in F => P(delta_i | A) =", P_delta_F_A)

# B
p_lc = 1-fa/N # prob líder correto
p_3biz = P(9,3,110,10) # prob 3 biz internos sabendo que o lider é correto

P_delta_C_B = [1/(N-fa), (10-3)/(N-fa), (N-fa-1-(10-3))/(N-fa)] # P( delta_i | B), p_i in C
P_delta_F_B = [0, 3/fa, (fa-3)/fa] # P( delta_i | B), p_i in F

p = 0 # probabilidade de haver mais de 2 bizantinos que não são folhas filhas dos 3 bizantinos internos
for i in range(2,fa-3+1): # [2,7[, i.e. 2 ao 6, 3 já estão nos internos
    p += P(6, i, 100, 100-3*10) # probabilidade de haver i bizantinos que não são folhas filhas dos 3 bizantinos internos

p_B = p_lc*p_3biz*p 

print("p_B =", p_B)
print("p_i in C => P(delta_i | B) =", P_delta_C_B)
print("p_i in F => P(delta_i | B) =", P_delta_F_B)

# C
p_total=0

P_delta_C_C = [1/(N-fa), [], None] # P( delta_i | A), p_i in C
P_delta_F_C = [0, [], None] # P( delta_i | A), p_i in F

# prob de haver i internos
for i in range(4, fa+1): # [4, fa+1[ => [4, fa]
    p = P(fa, i, N-1, 10) # probabilidade de haver i bizantinos internos além do líder
    p_total += p
    info_C = {"P(I_biz=i)": p, "delta1": (10-i)/(N-fa), "delta2": (N-fa-1-(10-i))/(N-fa)}
    info_F = {"P(I_biz=i)": p, "delta1": i/fa, "delta2": (fa-i)/fa}
    P_delta_C_C[1].append(info_C)
    P_delta_F_C[1].append(info_F)

res1 = 0
res2 = 0
res3 = 0
res4 = 0
for i, v in enumerate(P_delta_C_C[1]):
    res1 += P_delta_C_C[1][i]["P(I_biz=i)"]*P_delta_C_C[1][i]["delta1"]
    res2 += P_delta_F_C[1][i]["P(I_biz=i)"]*P_delta_F_C[1][i]["delta1"]
    res3 += P_delta_C_C[1][i]["P(I_biz=i)"]*P_delta_C_C[1][i]["delta2"]
    res4 += P_delta_F_C[1][i]["P(I_biz=i)"]*P_delta_F_C[1][i]["delta2"]
P_delta_C_C[1] = res1
P_delta_F_C[1] = res2
P_delta_C_C[2] = res3
P_delta_F_C[2] = res4

p_C = p_lc*p_total

print("p_C =", p_C)
print("p_i in C => P(delta_i | C) =", P_delta_C_C)
print("p_i in F => P(delta_i | C) =", P_delta_F_C)

# fim

delta_C = [None,None,None]
delta_F = [None,None,None]

for i in [0,1,2]:
    d_C_A = P_delta_C_A[i] * p_A
    d_C_B = P_delta_C_B[i] * p_B
    d_C_C = P_delta_C_C[i] * p_C
    d_C = d_C_A + d_C_B + d_C_C
    delta_C[i] = d_C

    d_F_A = P_delta_F_A[i] * p_A
    d_F_B = P_delta_F_B[i] * p_B
    d_F_C = P_delta_F_C[i] * p_C
    d_F = d_F_A + d_F_B + d_F_C
    delta_F[i] = d_F

    print(f"p_i in C => delta_{i} =", d_C)
    print(f"p_i in F => delta_{i} =", d_F)

print("delta_que_pertence_a_beta_C =", delta_C[2])
print("delta_que_pertence_a_beta_F =", delta_F[2])

print("P(no blocks in a config) =", p_A + p_B + p_C)

print()
print()
print()
# votos em falta para casos em que se geram blocos

# todos estes casos contam com um líder correto

# 3 biz internos, com 0 ou 1 folhas bizantinas filhas de nós corretos

p_0folhassoltas = P(6, 0, 100, 100-3*10)
p_1folhasolta = P(6, 1, 100, 100-3*10)

print("p_3biz =", p_3biz)
print("0 folhas biz filha de correto =",  p_0folhassoltas)
print("1 folhas biz filha de correto =",  p_1folhasolta)

beta_0fs_C = (3*m-(fa-3))/(N-fa) # 30 (3*m) folhas sob os 3biz, 6 (fa-3) das quais são também biz => 24 (30-6) corretas
beta_0fs_F = (fa-3)/fa
beta_1fs_C = (3*m-(fa-3-1))/(N-fa) # 30 (3*m) folhas sob os 3biz, 5 (fa-3-1) das quais são também biz => 25 (30-5) corretas
beta_1fs_F = (fa-3-1)/fa

gama_0fs_C = 3/(N-fa)
gama_0fs_F = 3/fa
gama_1fs_C = 4/(N-fa)
gama_1fs_F = 4/fa

# 0, 1, ou 2 bizantinos internos
p_0biz = P(9,0,110,10)
p_1biz = P(9,1,110,10)
p_2biz = P(9,2,110,10)

# 0 biz internos

# 0 biz internos => 0% caso Beta

gama_0biz_C = fa/(N-fa)
gama_0biz_F = 1

# 1 biz interno

beta_1biz_C = []
beta_1biz_F = []

gama_1biz_C = []
gama_1biz_F = []

for i in range(fa-1+1): # fa - 1 biz + 1 pq range é exclusivo
    p = P(fa-1,i, 100, 100-1*m) # probabilidade de i bizantinos serem folhas filhas de um correto
    
    beta_p_C = (1*m-(fa-1-i))/(N-fa)
    beta_p_F = (fa-1-i)/fa

    gama_p_C = (1+i)/(N-fa)
    gama_p_F = (1+i)/fa

    beta_1biz_C.append(p*beta_p_C)
    beta_1biz_F.append(p*beta_p_F)

    gama_1biz_C.append(p*gama_p_C)
    gama_1biz_F.append(p*gama_p_F)

beta_1biz_C = sum(beta_1biz_C)
beta_1biz_F = sum(beta_1biz_F)

gama_1biz_C = sum(gama_1biz_C)
gama_1biz_F = sum(gama_1biz_F)

# 2 biz internos

beta_2biz_C = []
beta_2biz_F = []

gama_2biz_C = []
gama_2biz_F = []

for i in range(fa-2+1): # fa - 2 biz + 1 pq range é exclusivo
    p = P(fa-2,i, 100, 100-1*m) # probabilidade de i bizantinos serem folhas filhas de um correto
    
    beta_p_C = (1*m-(fa-2-i))/(N-fa)
    beta_p_F = (fa-2-i)/fa

    gama_p_C = (2+i)/(N-fa)
    gama_p_F = (2+i)/fa

    beta_2biz_C.append(p*beta_p_C)
    beta_2biz_F.append(p*beta_p_F)

    gama_2biz_C.append(p*gama_p_C)
    gama_2biz_F.append(p*gama_p_F)

beta_2biz_C = sum(beta_2biz_C)
beta_2biz_F = sum(beta_2biz_F)

gama_2biz_C = sum(gama_2biz_C)
gama_2biz_F = sum(gama_2biz_F)

# pesar estes valores de acordo com a distribuição dos acontecimentos
w_beta_0fs_C = beta_0fs_C*p_0folhassoltas*p_3biz*p_lc
w_beta_0fs_F = beta_0fs_F*p_0folhassoltas*p_3biz*p_lc

w_beta_1fs_C = beta_1fs_C*p_1folhasolta*p_3biz*p_lc
w_beta_1fs_F = beta_1fs_F*p_1folhasolta*p_3biz*p_lc

w_beta_1biz_C = beta_1biz_C*p_1biz*p_lc
w_beta_1biz_F = beta_1biz_F*p_1biz*p_lc

w_beta_2biz_C = beta_2biz_C*p_2biz*p_lc
w_beta_2biz_F = beta_2biz_F*p_2biz*p_lc

w_gama_0fs_C = gama_0fs_C*p_0folhassoltas*p_3biz*p_lc
w_gama_0fs_F = gama_0fs_F*p_0folhassoltas*p_3biz*p_lc

w_gama_1fs_C = gama_1fs_C*p_1folhasolta*p_3biz*p_lc
w_gama_1fs_F = gama_1fs_F*p_1folhasolta*p_3biz*p_lc

w_gama_0biz_C = gama_0biz_C*p_0biz*p_lc
w_gama_0biz_F = gama_0biz_F*p_0biz*p_lc

w_gama_1biz_C = gama_1biz_C*p_1biz*p_lc
w_gama_1biz_F = gama_1biz_F*p_1biz*p_lc

w_gama_2biz_C = gama_2biz_C*p_2biz*p_lc
w_gama_2biz_F = gama_2biz_F*p_2biz*p_lc

beta_C = sum([w_beta_0fs_C, w_beta_1fs_C, w_beta_1biz_C, w_beta_2biz_C, delta_C[2]])
beta_F = sum([w_beta_0fs_F, w_beta_1fs_F, w_beta_1biz_F, w_beta_2biz_F, delta_F[2]])
gama_C = sum([w_gama_0fs_C, w_gama_1fs_C, w_gama_0biz_C, w_gama_1biz_C, w_gama_2biz_C])
gama_F = sum([w_gama_0fs_F, w_gama_1fs_F, w_gama_0biz_F, w_gama_1biz_F, w_gama_2biz_F])

print()
print("bizantinos crashados:")
print("   alfa_C =",1-(beta_C+gama_C+delta_C[0]+delta_C[1]))
print("   alfa_F =",1-(beta_F+gama_F+delta_F[0]+delta_F[1]))
print("   beta_C =",beta_C)
print("   beta_F =",beta_F)
print("   gama_C =",gama_C)
print("   gama_F =",gama_F)
print("delta_0_C =",delta_C[0])
print("delta_0_F =",delta_F[0])
print("delta_1_C =",delta_C[1])
print("delta_1_F =",delta_F[1])
print()

beta_C = beta_C/4
beta_F = beta_F/4
gama_C = gama_C/4
gama_F = gama_F/4
delta_C[0] = delta_C[0]/4
delta_C[1] = delta_C[1]/4
delta_F[0] = delta_F[0]/4
delta_F[1] = delta_F[1]/4

print()
print("ataques de 4 em 4 árvores:")
print("   alfa_C =",1-(beta_C+gama_C+delta_C[0]+delta_C[1]))
print("   alfa_F =",1-(beta_F+gama_F+delta_F[0]+delta_F[1]))
print("   beta_C =",beta_C)
print("   beta_F =",beta_F)
print("   gama_C =",gama_C)
print("   gama_F =",gama_F)
print("delta_0_C =",delta_C[0])
print("delta_0_F =",delta_F[0])
print("delta_1_C =",delta_C[1])
print("delta_1_F =",delta_F[1])
print("delta_C =",delta_C[1]+delta_C[0])
print("delta_F =",delta_F[1]+delta_F[0])
print()
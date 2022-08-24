from re import split
from spacetrack import SpaceTrackClient
from astropy.time import Time
import time
from test.io_functions import LocalFrame, TleFileRead, noradfileread, writetrn,  writedots, writetle,\
    dellfiles, ConfRead, writecsvdata, writecsvconf, TrnH0FileRead, writesatnum

from source.lib.orbit_functions import  PropagInit

import numpy as np

import os

# os.remove("confH0.csv")

norad = noradfileread("confNorad.txt")

trn = TrnH0FileRead("trn") #ler todos arquivos trn da pasta

print("Satnum adicionados a lista:")
for elemento in trn.satnum:
    if elemento not in norad:
        norad.append(elemento)
        print(elemento)

norad = sorted( norad)

writesatnum("confNorad.txt", norad)

writecsvconf('confH0.csv', trn.satnum, trn.h0 , trn.npoints)
# ----------------------------------------------------------------------
# Configurações

confupdate = 0  # 0 - não atualiza TLEs
                # 1 - atualiza TLEs

conftragetoria = 1  # 0 - Procura H0 e gera tragetórias
                    # 1 - gera tragetórias a partir das configurações confH0

sample_time = 1     # Tempo de amostragem desejado para a tragetória

# tempo de busca por tragetórias viáveis conftragetoria = 0
t_inic = Time.strptime('2021-9-15 10:00:00', '%Y-%m-%d %H:%M:%S')
t_final = Time.strptime('2021-9-15 19:00:00', '%Y-%m-%d %H:%M:%S')

dist_min_in = 1500000       # distância de início da tragetória em m
dist_min = 1100000           # máxima distância ao ponto mais próximo da tragetória em m

# ----------------------------------------------------------------------
# Fim das configurações

# Apaga arquivos de resultado
dellfiles('results/*.tle')
dellfiles('results/*.trn')
dellfiles('results/*.txt')
dellfiles('results_comp/*.trn')

# Atualiza as TLEs a partir dos numeros dos satélites listados em confNorad.txt
if confupdate == 1:
    print('atualizando TLEs')
    #norad = noradfileread("confNorad.txt") # confNoradObterH0
    st = SpaceTrackClient(identity='francisval20@yahoo.com.br', password='4mQivHD4CU934ZV')
    tlevec_enu_p = st.tle_latest(ordinal=1, norad_cat_id=norad, orderby='norad_cat_id', format='tle')
    writetle("conftle.txt", tlevec_enu_p) # salva as TLEs atualizadas em arquivo
    print('TLEs atualizadas')
ini = time.time()
# Ler as configurações
tle = TleFileRead('conftle.txt')

confh0 = ConfRead('confH0.csv')

# for j in range(0, len(confh0.satnum) ):
#     print(confh0.satnum[j])

lc = LocalFrame(-5.92256, -35.1615, 32.704)

print('iniciando propagação')

#Inicializa listas de armazenamento de informação relevantes dos objetos
sel_satnum = []
sel_tle_epc = []
sel_h0 = []
sel_dist_h0 = []
sel_h_min = []
sel_point_min = []
sel_dist_min = []
sel_hf = []
sel_npoints = []
sel_dist_hf = []

trajet_all_2 = []

# verificar possivel bug quando conftragetoria = 1 e tiver mais de uma trajetória por objeto
for idx in range(0, len(tle.satellite)): # len(tle.satellite) 
    if conftragetoria == 0:
        print(tle.satellite[idx].satnum)
        print(t_inic.value)
        print(t_final.value)
        propag = PropagInit(tle.satellite[idx], lc, sample_time)
        pos = propag.searchh0(t_inic, t_final, dist_min_in, dist_min, 10000)
    elif (conftragetoria == 1) and (tle.satellite[idx].satnum in confh0.satnum):
        propag = PropagInit(tle.satellite[idx], lc, sample_time)
        for i in range(0, len(confh0.satnum)):
            if confh0.satnum[i] == tle.satellite[idx].satnum:
                break
        print(confh0.satnum[i])
        print(confh0.h0[i])
        pos = propag.orbitpropag(confh0.h0[i], confh0.hrf[i])

    if (conftragetoria == 0) or (tle.satellite[idx].satnum in confh0.satnum):
        for i in range(0, len(pos.traj)):
            writetle("results/" + str(tle.satellite[idx].satnum) + ".tle", tle.l1[idx] + "\n" + tle.l2[idx])
            tempo = pos.tempo[i]
            posenu = pos.traj[i]
            distenu = pos.dist[i]

            ttxt = tempo[0].value[0:19]
            ttxt = ttxt.replace(":", "_")
            ttxt = ttxt.replace("-", "_")
            ttxt = ttxt.replace("T", "-H0-")
            writetrn("results/" + "obj-" + str(tle.satellite[idx].satnum) + "-" + ttxt + "TU.trn", posenu)
            trajet_all_2.append(posenu)
            writedots("results/" + "pontos-" + str(tle.satellite[idx].satnum) + "-" + ttxt + "TU.txt", tempo,
                      distenu, posenu)

            # Summarized data set of the trajectories obtained
            sel_satnum.append(tle.satellite[idx].satnum)
            sel_tle_epc.append(tle.satellite[idx].epochdays)
            sel_h0.append(tempo[0].value[0:10] + ' ' + tempo[0].value[11:19])
            sel_dist_h0.append(distenu[0])
            sel_h_min.append(pos.hdmin[i].value[11:19])
            sel_point_min.append(pos.hrmin[i])
            sel_dist_min.append(pos.dmin[i])
            sel_hf.append(tempo[len(tempo) - 1].value[11:19])
            sel_npoints.append(len(distenu) - 1)
            sel_dist_hf.append(distenu[len(distenu) - 1])

for i in range(0, len(sel_satnum)):
    print([sel_satnum[i], sel_h0[i], sel_dist_h0[i], sel_dist_min[i], sel_dist_hf[i] ])

writecsvdata("results/" + 'planilhapy.csv', sel_satnum, sel_tle_epc, sel_h0, sel_dist_h0, sel_h_min,
             sel_point_min, sel_dist_min, sel_hf, sel_npoints, sel_dist_hf)

writecsvconf('confH0.csv', sel_satnum, sel_h0, sel_npoints)



print("\nAnalise do erro:")
for k in range(0, len(trajet_all_2)):
    traj_atual1 = np.asarray(trn.trajet_all[k])
    traj_atual2 = np.asarray(trajet_all_2[k])
    err = traj_atual1 - traj_atual2
    # norma_erro = np.linalg.norm(err[1:len(err)-1])
    no = []
    for i in range(1, len(err)-1):
        no.append(np.linalg.norm(err[i]))
    n2 = np.asarray(no)

    print("objeto: {}, err max = {:.3f}, err mmed = {:.3f}".format(sel_satnum[k], np.max(n2), np.mean(n2) ))

    ttxt = sel_h0[k]
    ttxt = ttxt.replace("/", "_")
    ttxt = ttxt.replace(":", "_")
    ttxt = ttxt.replace(" ", "-H0-")
    writetrn("results_comp/" +"erro_" + str(sel_satnum[k])  + '-' + ttxt + ".trn", err)

fim = time.time()
print("Tempo: ", fim - ini)
from re import split
from spacetrack import SpaceTrackClient
from astropy.time import Time # astropy==4.3.1
import time
from io_functions import LocalFrame, noradfileread, writetrn,  writedots, writetle,\
    dellfiles, dellfile, ConfRead, writecsvdata, write2csvdata, writecsvconf, TrnH0FileRead, T32leFileRead, RcsRead

from orbit_functions import  PropagInit
import json
import os

from sgp4 import omm
from sgp4.api import Satrec


# class Sistem:
#     def __init__(self, satellite, lc, sample_time=1):
#         self.satellite = satellite

    # def Rumm(self, t_inic):
    #     tvar = t_inic
    #     return self


def update_elements(norad_ids, loguin, password):
    st = SpaceTrackClient(identity=loguin, password=password)
    tlevec_json = st.gp(norad_cat_id=norad_ids, orderby='norad_cat_id', format='json')
    dellfile('confTle.txt')
    dellfile('confElem.json')
    tlevec_json = json.loads(tlevec_json)
    with open("confElem.json", "wt") as fp:
        json.dump(tlevec_json, fp)
    # theele = ''
    # for line in tlevec_json:
    #     theele = theele + line["TLE_LINE0"] +'\n'+ line["TLE_LINE1"] +'\n'+ line["TLE_LINE2"] +'\n' 
    # writetle("conftle.txt", theele)
    return  tlevec_json   

def rumm(localizacao,
         t_inic=Time('2021-11-26T13:00:00.000', format='isot'),
         t_final= Time('2021-11-26T15:10:00.000', format='isot'),
         sample_time = 1,
         conftragetoria = 0 ,
         dist_min_in = 1000000,       # distância de início da tragetória em m
         dist_min = 900000           # máxima distância ao ponto mais próximo da tragetória em m
         ):
    # ----------------------------------------------------------------------
    # Configurações

    # confElements =   'json' # 'tle' ou 'json'

    # confupdate = 0    # 0 - não atualiza TLEs
                        # 1 - atualiza TLEs

    # conftragetoria = 0    # 0 - Procura H0 e gera tragetórias
                            # 1 - gera tragetórias a partir das configurações confH0

    #sample_time = 1     # Tempo de amostragem desejado para a tragetória

    # tempo de busca por tragetórias viáveis conftragetoria = 0
    # t_inic = Time.strptime('2021-11-26 13:00:00', '%Y-%m-%d %H:%M:%S')
    # t_inic = Time('2021-11-26T13:00:00.000', format='isot')

    # t_final = Time('2021-11-26T15:10:00.000', format='isot')

    # dist_min_in = 1000000       # distância de início da tragetória em m
    # dist_min = 900000           # máxima distância ao ponto mais próximo da tragetória em m

    # ----------------------------------------------------------------------
    # Fim das configurações

    # Ler as configurações
    ini = time.time()

    try:
        with open('confElem.json', 'r') as fp:
            tlevec_json = json.load(fp)
        confElements = 'json'
    except OSError as e:
        print(f"Error:{e.strerror}"+" ao ler o arquivo confElem.json")
        try:
            tle = T32leFileRead('conftle.txt')
            confElements = 'tle'
        except OSError as e:
            print(f"Error:{e.strerror}"+"ao ler o arquivo conftle.txt")


    # if (confElements == 'json') :
    #     with open('confElem.json', 'r') as fp:
    #         tlevec_json = json.load(fp)
    #     len_satt = len(tlevec_json)
    #     theele = ''
    #     for line in tlevec_json:
    #         theele = theele + line["TLE_LINE0"] +'\n'+ line["TLE_LINE1"] +'\n'+ line["TLE_LINE2"] +'\n' 
    #     writetle("conftle.txt", theele)

    if (confElements == 'json'):
        len_satt = len(tlevec_json)
        # theele = ''
        # for line in tlevec_json:
        #     theele = theele + line["TLE_LINE0"] +'\n'+ line["TLE_LINE1"] +'\n'+ line["TLE_LINE2"] +'\n' 
        # writetle("conftle.txt", theele)
    else:
        tle = T32leFileRead('conftle.txt')
        len_satt = len(tle.l2)

    if conftragetoria == 1:
        confh0 = ConfRead('results/' + 'confH0.csv')

    rcs = RcsRead("RCS.csv")

    lc = LocalFrame(localizacao["latitude"], localizacao["longitude"], localizacao["altura"])

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
    sel_3le = ''
    sel_name = []
    sel_rcs = []
    sel_json = []

    # verificar possivel bug quando conftragetoria = 1 e tiver mais de uma trajetória por objeto
    for idx in range(0, len_satt): # len(tle.satellite)
        if confElements == 'tle':
            satellite = Satrec.twoline2rv(tle.l1[idx], tle.l2[idx])
        elif confElements == 'json':
            satellite = Satrec()
            omm.initialize(satellite, tlevec_json[idx])
        else:
            print("confElements deve ser 'tle' ou 'json'")    
            break

        if conftragetoria == 0:
            print(satellite.satnum)
            print(t_inic.value)
            print(t_final.value)
            propag = PropagInit(satellite, lc, sample_time)
            pos = propag.searchh0(t_inic, t_final, dist_min_in, dist_min, 10000)
        elif (conftragetoria == 1) and (satellite.satnum in confh0.satnum):
            propag = PropagInit(satellite, lc, sample_time)
            for i in range(0, len(confh0.satnum)):
                if confh0.satnum[i] == satellite.satnum:
                    break
            print(confh0.satnum[i])
            print(confh0.h0[i])
            pos = propag.orbitpropag(confh0.h0[i], confh0.hrf[i])

        if (conftragetoria == 0) or (satellite.satnum in confh0.satnum):
            for i in range(0, len(pos.traj)):
                # writetle("results/" + str(satellite.satnum) + ".tle", tle.l1[idx] + "\n" + tle.l2[idx])

                if confElements == 'tle':
                    sel_3le = sel_3le +  tle.l0[idx] + "\n" + tle.l1[idx]  + "\n" + tle.l2[idx] + "\n"
                    sel_name.append(tle.l0[idx][2:])
                elif confElements == 'json':
                    sel_3le = sel_3le + tlevec_json[idx]["TLE_LINE0"] +'\n'+ tlevec_json[idx]["TLE_LINE1"] +'\n'+ tlevec_json[idx]["TLE_LINE2"] +'\n'
                    sel_name.append(tlevec_json[idx]["NORAD_CAT_ID"]) 
                    sel_json.append(tlevec_json[idx]) 

                tempo = pos.tempo[i]
                posenu = pos.traj[i]
                distenu = pos.dist[i]
                # print(tempo[0].value)
                ttxt = tempo[0].value[0:19]
                ttxt = ttxt.replace(":", "_")
                ttxt = ttxt.replace("-", "_")
                ttxt = ttxt.replace("T", "-H0-")
                writetrn("results/" + "obj-" + str(satellite.satnum) + "-" + ttxt + "TU.trn", posenu)
                writedots("results/" + "pontos-" + str(satellite.satnum) + "-" + ttxt + "TU.txt", tempo,
                        distenu, posenu)

                # Summarized data set of the trajectories obtained
                if satellite.satnum in rcs.satnum:
                    sel_rcs.append(rcs.rcs[rcs.satnum.index(satellite.satnum)])
                else:
                    sel_rcs.append(0)

                sel_satnum.append(satellite.satnum)
                sel_tle_epc.append(satellite.epochdays)
                sel_h0.append(tempo[0].value)
                sel_dist_h0.append(distenu[0])
                sel_h_min.append(pos.hdmin[i].value[11:])
                sel_point_min.append(pos.hrmin[i])
                sel_dist_min.append(pos.dmin[i])
                sel_hf.append(tempo[len(tempo) - 1].value[11:])
                sel_npoints.append(len(distenu) - 1)
                sel_dist_hf.append(distenu[len(distenu) - 1])

    for i in range(0, len(sel_satnum)):
        print([sel_satnum[i], sel_h0[i], sel_dist_h0[i], sel_dist_min[i], sel_dist_hf[i] ])

    # Apaga arquivos de resultado
    dellfiles('results/*.tle')
    dellfiles('results/*.trn')
    dellfiles('results/*.txt')
    dellfiles('results/*.json')
    dellfiles('results/*.csv')

    writetle("results/" + "3le.txt", sel_3le)

    if confElements == 'tle':
        writecsvdata("results/" + 'planilhapy.csv', sel_satnum, sel_name, sel_tle_epc, sel_h0, sel_dist_h0, sel_h_min,
                sel_point_min, sel_dist_min, sel_hf, sel_npoints, sel_dist_hf, sel_rcs)
    elif confElements == 'json':
        write2csvdata("results/" + 'planilhapy.csv', sel_satnum, sel_name, sel_tle_epc, sel_h0, sel_dist_h0, sel_h_min,
                sel_point_min, sel_dist_min, sel_hf, sel_npoints, sel_dist_hf, sel_json, sel_rcs)
        with open("results/" + "confElem.json", "wt") as fp:
            json.dump(sel_json, fp)

    writecsvconf('results/' + 'confH0.csv', sel_satnum, sel_h0, sel_npoints)

    fim = time.time()
    print("Tempo: ", fim - ini)
    return 0

   



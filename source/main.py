# https://blog.jcharistech.com/2020/11/08/working-with-file-uploads-in-streamlit-python/
# https://celestrak.com/satcat/search.php
import streamlit as st
import pandas as pd
# import datetime
from datetime import datetime
from datetime import time

import json
import shutil
from astropy.time import Time

from sgp4 import omm
from sgp4.api import Satrec

import os
import tempfile
import glob

#from lib.sistem import update_elements
from lib.io_functions import LocalFrame, RcsRead, writetrn, writedots
from lib.orbit_functions import  PropagInit

from spacetrack import SpaceTrackClient
from io import StringIO

# ----------------------------------------------------------------------
# Atualiza a ultima versão dos elementos orbitais no site do Space-Track
# ----------------------------------------------------------------------
def update_elements(norad_ids, loguin, password):
    stc = SpaceTrackClient(identity=loguin, password=password)    
    try:
        stc.authenticate()
    except:
        log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Space-Track Loguin Error</p>'
        st.markdown(log_error, unsafe_allow_html=True)
        print('space-track loguin error')
        return False
    tlevec_csv = stc.gp(norad_cat_id=norad_ids, orderby='norad_cat_id', format='csv')
    elem_df = pd.read_csv(StringIO(tlevec_csv), sep=",")
    st.session_state.ss_elem_df = elem_df
    return  True

def get_orbital_element():
    # Seleção do modo de atualização dos elementos orbitais
    st.sidebar.title("Elementos orbitais:")
    help=('Space-Track: Obtem os elementos orbitais automaticamente do Space-Track (exige cadastro no Space-Track e não aceita configuração de proxy)  \n'
        'Arquivo de elementos: Carregar arquivo de elementos de outra fonte ou obtido manualmento do Space-Track (TLE, 3LE ou JSON).')

    menuUpdate = ["Space-Track","Arquivo de elementos"]
    choiceUpdate = st.sidebar.selectbox("Fonte dos elementos orbitais:",menuUpdate,help=help)
    if choiceUpdate == "Space-Track":

        SpaceTrackLoguin = st.sidebar.text_input('Space-Track login:')        
        if SpaceTrackLoguin=="":
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Carregue o login Space-Track</p>'
            st.sidebar.markdown(log_error, unsafe_allow_html=True)       
        SpaceTracksenha = st.sidebar.text_input('Space-Track senha:',type="password")

        st.sidebar.markdown("Lista de NORAD_ID a propagar:")
        data_norad = st.sidebar.file_uploader("Utilizar lista de NORAD_CAT_ID padrão ou carregar lista de NORAD_CAT_ID:", type=['csv'], help='Arquivo de texto com extensão .csv com uma unica coluna com os numeros NORAD_CAT_ID e com o texto NORAD_CAT_ID na primeira linha, se não for carregado será utilizada uma lista padrão')
    
        if st.sidebar.button("Obter Elementos Orbitais"):
            if data_norad is not None:
                st.markdown('Arquivo de NORAD_CAT_ID carregado:')
                file_details = {"Filename":data_norad.name,"FileType":data_norad.type,"FileSize":data_norad.size}
                st.write(file_details)
                df_norad_ids = pd.read_csv(data_norad) 
            else:
                st.markdown("arquivo NORAD_CAT_ID não carregado")
                df_norad_ids = pd.read_csv("data/norad_id.csv")

            st.dataframe(df_norad_ids)
            if update_elements(df_norad_ids.to_dict('list')["NORAD_CAT_ID"],SpaceTrackLoguin,SpaceTracksenha):
                st.markdown('Elementos orbitais obtidos do Space-Track:')
               

    elif choiceUpdate == "Arquivo de elementos":
        data_elements = st.sidebar.file_uploader("Upload Json/csv",type=['csv','json'])
        if st.sidebar.button("Carregar Elementos Orbitais"):
            if data_elements is not None:
                file_details = {"Filename":data_elements.name,"FileType":data_elements.type,"FileSize":data_elements.size}
                st.write(file_details)
                st.markdown("Elementos orbitais atualizados manualmente:")    
                if data_elements.type == "application/json":
                    st.session_state.ss_elem_df = pd.read_json(data_elements)

                elif data_elements.type == "text/csv":
                    st.session_state.ss_elem_df = pd.read_csv(data_elements)


def main():  

    st.title("OPTR - Orbit Propagator Tracking Radar") #

    st.subheader('**Propagação de orbita de satélites e geração de trajetória, para rastreio por radar de trajetografia**')
    st.markdown('Este app faz a busca de um ponto de aproximação de um objeto espacial em órbita da terra, utilizando o SGP4, e traça um intervalo \
        de trajetória em um referecial plano local (ENU), para ser utilizado como direcionamento para rastreio por radar de trajetografia ')
    st.markdown('Por: Francisval Guedes Soares, Email: francisvalg@gmail.com')

    st.subheader('**Saídas:**')

    get_orbital_element()
    if "ss_elem_df" not in st.session_state:
        log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Carregue os elementos orbitais</p>'
        st.markdown(log_error, unsafe_allow_html=True)
    else:
        elem_df = st.session_state["ss_elem_df"]
        st.dataframe(elem_df)

    st.sidebar.title("Configurações")

    # Seleção do tempo de amostragem
    sample_time = st.sidebar.number_input('Taxa de amostragem (s):', 0.1, 10.0, 1.0, step = 0.1)
    st.write('Taxa de amostragem (s): ', sample_time)

    dmax = st.sidebar.number_input('Distâcia máxima para limites da trajetória (Km)',
        min_value = 400,
        max_value = 10000,
        value = 1100,
        step = 50)

    st.write('Distância máxima (Km): ', dmax)

    dmin = st.sidebar.number_input('O ponto de distância mínima da trajetória a partir do qual a trajetória é salva (Km)',
        min_value = 200,
        max_value = 5000,
        value = 1000,
        step = 50)

    st.write('Distância mínima (Km): ', dmin)

    initial_date = st.sidebar.date_input("Data de inicio da busca automática do H0", key=1)
    initial_time = st.sidebar.time_input("Hora de inicio da busca automática do H0 TU", time(11, 0,0),  key=2)
    initial_datetime = datetime.combine(initial_date, initial_time)
    initial_datetime=Time(initial_datetime)
    initial_datetime.format = 'isot'
    st.write('Momento do final da busca: ', initial_datetime)

    final_date = st.sidebar.date_input("Data Final da busca automática do H0", key=3)
    final_time = st.sidebar.time_input("Hora de final da busca automática do H0 TU", time(19, 0,0),  key=4)
    final_datetime = datetime.combine(final_date, final_time)
    final_datetime=Time(final_datetime)
    final_datetime.format = 'isot'
    st.write('Momento do final da busca: ', final_datetime)

    st.write('Gerenciar localização:')
    latitude = st.sidebar.number_input('Latitude',-90.0, 90.0,value= -5.923568, format="%.6f")
    longitude = st.sidebar.number_input('longitude', -180.0, 80.0, value=-35.167801, format="%.6f")
    altitude = st.sidebar.number_input('Altitude (m)',-1000.0, 2000.0,value= 50.0, format="%.6f")

    # localizacao = {'Nome': nomeLoc, 'latitude': latitude, 'longitude': longitude, 'altitude': altitude }
    lc = LocalFrame(latitude, longitude, altitude)
    st.write('latitude: ', latitude)
    st.write('longitude: ', longitude)
    st.write('altitude: ', altitude)
    st.sidebar.title("Executar:")


    if st.sidebar.button("Calcular trajetórias"):
        if "ss_elem_df" not in st.session_state:
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Carregue os elementos orbitais</p>'
            st.markdown(log_error, unsafe_allow_html=True)
        elif len(st.session_state["ss_elem_df"].index)>250:
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Numero máximo de objetos 250</p>'
            st.markdown(log_error, unsafe_allow_html=True)
        else:
            st.write('Numero de objetos: ', len(st.session_state["ss_elem_df"].index))
            elem_df = st.session_state["ss_elem_df"]

            orbital_elem = elem_df.to_dict('records')
            lc = LocalFrame(latitude, longitude, altitude)

            sel_orbital_elem = []

            sel = { "H0":[], "DIST_H0":[],"H_DIST_MIN":[],"PT_DIST_MIN":[],"DIST_MIN":[],"HF":[], "N_PT":[], "DIST_HF":[],"RCS":[] }

            rcs = RcsRead("data/RCS.csv")   
            date_time = datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
            dir_name = tempfile.gettempdir()+"/optr_temp_"+ date_time
            print(dir_name)
            os.mkdir(dir_name)

            for idx in range(0, len(orbital_elem)):
                satellite = Satrec()
                omm.initialize(satellite, orbital_elem[idx])
                propag = PropagInit(satellite, lc, sample_time)
                pos = propag.searchh0(initial_datetime, final_datetime, dmax*1000, dmin*1000, 10000)
                for i in range(0, len(pos.traj)):
                    sel_orbital_elem.append(orbital_elem[idx]) 
                    tempo = pos.tempo[i]
                    posenu = pos.traj[i]
                    distenu = pos.dist[i]
                    
                    ttxt = tempo[0].strftime('%Y_%m_%d-H0-%H_%M_%S')
                    writetrn(dir_name +"/" + "obj-" + str(satellite.satnum) + "-" + ttxt + "TU.trn", posenu)
                    writedots(dir_name + "/" + "pontos-" + str(satellite.satnum) + "-" + ttxt + "TU.txt", tempo,
                            distenu, posenu)

                    # Summarized data set of the trajectories obtained
                    if satellite.satnum in rcs.satnum:
                        sel["RCS"].append(rcs.rcs[rcs.satnum.index(satellite.satnum)])
                    else:
                        sel["RCS"].append(orbital_elem[idx]['RCS_SIZE'])
                    sel["H0"].append(tempo[0].value)
                    sel["DIST_H0"].append(distenu[0])
                    sel["H_DIST_MIN"].append(pos.hdmin[i].value[11:])
                    sel["PT_DIST_MIN"].append(pos.hrmin[i])
                    sel["DIST_MIN"].append(pos.dmin[i])
                    sel["HF"].append(tempo[len(tempo) - 1].value[11:])
                    sel["N_PT"].append(len(distenu) - 1)
                    sel["DIST_HF"].append(distenu[len(distenu) - 1])
            
            df_traj = pd.DataFrame(sel)
            df_orb = pd.DataFrame(sel_orbital_elem)
            df_orb.to_csv(dir_name + "/orbital_elem.csv", index=False)

            df_traj = df_traj.join(df_orb)
            df_traj.to_csv(dir_name + "/traj_data.csv", index=False)

            st.subheader('Arquivos:')
            # f = tempfile.TemporaryFile()
            # f.write('something on temporaryfile')
            # f.seek(0) # return to beginning of file
            # print f.read() # reads data back from the file
            # f.close() # temporary file is automatically deleted here        
            shutil.make_archive(dir_name, 'zip', dir_name)

            with open(dir_name + ".zip", "rb") as fp:
                btn = st.download_button(
                    label="Download",
                    data=fp,
                    file_name="orbit_results.zip",
                    mime="application/zip"
                )

    st.sidebar.write('End')
    
    # txt_files = glob.glob(tempfile.gettempdir() + '/*/')
    # for line in txt_files:
    #     st.markdown(line)

if __name__== '__main__':
    main()
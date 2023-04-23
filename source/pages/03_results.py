"""
Creator: Francisval Guedes Soares
Date: 2021
"""

import streamlit as st
import pandas as pd

from datetime import datetime
from datetime import time
import time as tm

import shutil
from astropy.time import Time
from astropy.time import TimeDelta
from astropy import units as u

import os
import tempfile
import numpy as np

from lib.orbit_functions import  PropagInit
from lib.constants import  ConstantsNamespace

from spacetrack import SpaceTrackClient
import spacetrack.operators as op
from io import StringIO

import glob

import pymap3d as pm
import re
import os.path


cn = ConstantsNamespace()
FILE_NAME_XLSX = "00_traj_summary.xlsx"

# Analisa as possibilidades de rastreio
def highlight_rows(row):
    teste_rcs = row.loc['RCS']
    teste_rcs_min = row.loc['RCS_MIN']
    teste_range_pt = row.loc['MIN_RANGE_PT']
    teste_range = row.loc['MIN_RANGE']
    teste_decay = row.loc['DECAY_DATE']
    color = '#FF4500'
    amarelo = '#ffda6a'
    verde = '#75b798'
    vermelho = '#ea868f'
    azul = '#6ea8fe'

    #TESTA SE EXISTE A COLUNA RCS_SIZE
    if 'RCS_SIZE' in row :
        teste_rcs_size = row.loc['RCS_SIZE']
    else :
        teste_rcs_size = 'none'

    if teste_rcs > 0:  #TESTA O TAMANHO DO RCS
        if teste_rcs_min <= teste_rcs*1.16:
            color = verde
        else:
            color = vermelho
    else:              # TESTA A CLASSIFICAÇÃO DO RCS
        if teste_rcs_size == 'MEDIUM':
            if teste_range > 500: #422.88 é o valor mínimo teorico
                color = vermelho
            else:
                color = amarelo
        elif teste_rcs_size == 'LARGE':
            color = azul
        else:
            if teste_range > 300: #237.8 é o valor mínimo teorico
                color = vermelho
            else:
                color = verde
    
    if teste_range_pt < 90:  # TESTA O NÚMERO MÍNIMO DE PONTOS
        color = vermelho

    x=teste_decay  # TESTA SE O OBJETO JA SAIU DE ORBITA
    s_nan = str(x)
    if s_nan != "nan" : 
        color = vermelho

    return ['background-color: {}'.format(color) for r in row]

def geodetic_circ(r,center_lat,center_lon, center_h):
    """calculates a circle in the geodetic system.

        Args:
            r (float): circle radius (km)
            center_lat, center_lon, center_h (float): circle center point             
        Returns:
            pandas DataFrame
        """
    theta = np.linspace(0, 2*np.pi, 30)
    e =  1000*r*np.cos(theta)
    n =  1000*r*np.sin(theta)
    u =  np.zeros(len(theta))
    lat, lon, _ = pm.enu2geodetic(e, n, u,center_lat, center_lon, center_h)
    dfn = pd.DataFrame(np.transpose([lat, lon]), columns=['lat', 'lon'])
    return dfn


def main():

    st.set_page_config(
    page_title="Result analisis",
    page_icon="🌏", # "🤖",  # "🧊",
    # https://raw.githubusercontent.com/omnidan/node-emoji/master/lib/emoji.json
    layout="wide",
    initial_sidebar_state="expanded",
    # menu_items={
    #     'Get Help': 'https://www.sitelink.com',
    #     'Report a bug': "https://www.sitelink.com",
    #     'About': "# A cool app"
    # }
    )
        
    st.subheader('Data visualization:')

    if "ss_result_df" not in st.session_state:
        st.info('Run propagation for visualization',   icon=cn.INFO)
        st.stop()
    # elif "ss_lc" not in st.session_state:
    #     st.info('Load geodetic wgs84 location',   icon=cn.INFO)
      
    st.write('The data summary:')                   
    st.write('Approaching the reference point: ', len(st.session_state.ss_result_df.index))

    #Mudança feita por André para colorir a linha
    df_traj = st.session_state.ss_result_df.style.apply(highlight_rows, axis=1) 
    with pd.ExcelWriter(st.session_state.ss_dir_name + "/"+ FILE_NAME_XLSX) as writer:
        df_traj.to_excel(writer, sheet_name='Sheet 1', engine='openpyxl')

    st.dataframe(df_traj)

    if os.path.isfile(st.session_state.ss_dir_name + "/"+ FILE_NAME_XLSX):
        st.write('Download highlight File:')
        with open(st.session_state.ss_dir_name + "/"+ FILE_NAME_XLSX, "rb") as fp:
            btn = st.download_button(
                label="Download",
                data=fp,
                file_name=FILE_NAME_XLSX,
                mime="application/txt"
            )

# prints a map of the region with the trajectory
    files_map = glob.glob(st.session_state.ss_dir_name + '/*TU.csv')        
    files_m = []
    for files in files_map:
        files_m.append(files.split('data-')[-1])

    choice_file_map = st.sidebar.selectbox("Select file for map:",files_m, key='choice_file_map') #format_func=format_func_map

    df_data = pd.read_csv(st.session_state.ss_dir_name + '/data-' + choice_file_map,
                    usecols= ['lat', 'lon', 'ELEVATION'])

    dmax = st.session_state.d_max
    # idx = np.arange(0, len(df_data.index), +2)
    # df_data = df_data.loc[idx]
    dfn = geodetic_circ(6,df_data.iloc[-1].lat ,df_data.iloc[-1].lon, 0 )  
    df = pd.concat([df_data, dfn], axis=0)    
    dfn = geodetic_circ(4,st.session_state["ss_lc"]['lat'],
                        st.session_state["ss_lc"]['lon'],
                        st.session_state["ss_lc"]['height'])  
    df = pd.concat([df, dfn], axis=0)  
    dfn = geodetic_circ(dmax * np.cos(np.radians(df_data.iloc[-1]['ELEVATION'])),
                        st.session_state["ss_lc"]['lat'],
                        st.session_state["ss_lc"]['lon'],
                        st.session_state["ss_lc"]['height'])
    df = pd.concat([df, dfn], axis=0) 
    dfn = geodetic_circ(dmax ,st.session_state["ss_lc"]['lat'],
                        st.session_state["ss_lc"]['lon'],
                        st.session_state["ss_lc"]['height'])
    df = pd.concat([df, dfn], axis=0) 
        
    st.write('The map:') 
    st.map(df)
    st.sidebar.markdown('The map can be seen on the right')
    st.sidebar.markdown('Thanks')

    st.info('To compare the orbital elements trajectories, go to the next page.', icon=cn.INFO)

if __name__== '__main__':
    main()
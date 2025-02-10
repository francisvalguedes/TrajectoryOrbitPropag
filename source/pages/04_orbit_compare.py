import numpy as np
import pandas as pd
from io import StringIO
from spacetrack import SpaceTrackClient
import spacetrack.operators as op
from astropy.time import Time
from astropy.time import TimeDelta
import glob
import os
from astropy import units as u

from lib.orbit_functions import  PropagInit
from lib.pages_functions import  *
from lib.constants import  ConstantsNamespace

import datetime as dt
from datetime import datetime, timezone

import streamlit as st
import tempfile
import plotly.express as px

# Constants
err_max = 3000 # m
MENU_UPDATE = "Space-Track Update"
MENU_NUPDATE = "Space-Track already loaded in orbital elements page"
menu_update = [ MENU_NUPDATE, MENU_UPDATE]

cn = ConstantsNamespace()


def plot_compare(df):
    # Seleção de NORAD_CAT_ID
    selected_norad = st.selectbox("Select the NORAD_CAT_ID", df["NORAD_CAT_ID"].unique())
    # Filtrando os dados
    filtered_df = df[df["NORAD_CAT_ID"] == selected_norad]
    # Criando o eixo x como um array de índices negativos
    filtered_df = filtered_df.sort_values(by="EPOCH")
    n = len(filtered_df)
    filtered_df["x_axis"] = np.arange(-n + 1, 1)

    # Criando o gráfico
    fig = px.line(filtered_df, x="x_axis", y="D_ERR_MAX", title=f"Error over last orbital elements for NORAD_CAT_ID {selected_norad}",
                markers=True, labels={"D_ERR_MAX": "Erro Máximo(m)", "x_axis": "Índice relativo"})

    st.plotly_chart(fig)

def main():
    st.set_page_config(
    page_title="Compare orbital elements trajectories",
    page_icon="🌏", # "🤖",  # "🧊",
    # https://raw.githubusercontent.com/omnidan/node-emoji/master/lib/emoji.json
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items = menu_itens()
    )

    page_links(insidebar=True)

    if "date_time" not in st.session_state:
        date_time = datetime.now(timezone.utc).strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
        st.session_state.date_time = date_time

    if "ss_dir_name" not in st.session_state:
        dir_name = tempfile.gettempdir()+"/top_tmp_"+ date_time
        st.session_state.ss_dir_name = dir_name

    if os.path.exists(st.session_state.ss_dir_name) == False:
        os.mkdir(st.session_state.ss_dir_name)

    if "stc_loged" not in st.session_state:
        st.session_state.stc_loged=False

    if "ss_lc" not in st.session_state:
        lc_df = pd.read_csv('data/confLocalWGS84.csv')
        lc = lc_df.iloc[0].to_dict()
        st.session_state["ss_lc"] = lc

    st.title('Orbit trajetory compare')
    st.markdown('Use the orbital elements loaded on previous pages or update from space track')

# #################################################################
    if 'ss_result_df' in st.session_state:                
        norad_comp  = st.session_state.ss_result_df[['NORAD_CAT_ID', 'OBJECT_NAME']].drop_duplicates(subset=['NORAD_CAT_ID'], keep='first')
        st.success('Norads loaded from last orbital propagation results', icon=cn.SUCCESS)
    else:
        st.info('Run Orbit propagation', icon=cn.INFO)            
        page_stop()

    norad_comp_list =norad_comp.to_dict('list')['NORAD_CAT_ID']

    if "ss_elem_df" not in st.session_state:
        st.info('Upload the orbital elements with two or more sets of orbital elements na página específica', icon=cn.INFO)         
        page_stop()
    else: 
        df_selected = st.session_state.ss_elem_df[st.session_state.ss_elem_df['NORAD_CAT_ID'].isin(norad_comp['NORAD_CAT_ID'].tolist())]       
        df_oe_group = df_selected.groupby(df_selected['NORAD_CAT_ID'],as_index=False).size()['size']
        # print(max(df_oe_group))

        if max(df_oe_group) <2:
            st.info('Insufficient orbital element data, download above by choosing option ' + MENU_UPDATE +\
                    ' or from orbital elements page on this site by custom list from NORAD, or from\
                    Space-Track site, by epoch: more than two days, so as to get more than two sets\
                    of orbital elements per object', icon=cn.INFO)            
            page_stop()
        else:
            st.success('Enough orbital elements to perform comparison already loaded ', icon= cn.SUCCESS)
            if min(df_oe_group) <2:
                st.warning('there are objects with less than two sets of orbital elements, it will not be possible to compare them', icon=cn.WARNING)


    st.write('Perform propagation calculations and trajectory comparison:')
    compare_oe_bt = st.button("run trajectory comparison")
    if compare_oe_bt:
        sel_resume = {  "NORAD_CAT_ID":[], "OBJECT_NAME":[], "EPOCH":[],"EPOCH_1":[], "D_ERR_MEAN":[],"D_ERR_MAX":[],
                        "TRACK":[], "RCS_SIZE":[], "X_ERR_MEAN":[], "Y_ERR_MEAN":[],"Z_ERR_MEAN":[],"PERIAPSIS":[],
                        "ECCENTRICITY":[], "MEAN_MOTION":[], "DECAY_DATE":[] }
        st.write('Progress bar:')
        my_bar = st.progress(0)
        for idxi, norad in enumerate(norad_comp_list):
            orbital_elem = st.session_state.ss_elem_df.loc[st.session_state.ss_elem_df['NORAD_CAT_ID'] == norad]

            orbital_elem = orbital_elem.reset_index(drop=True)

            for idxj, prev_orbital_elem_row in orbital_elem.iterrows():
                if idxj > 0:

                    start_time = Time(prev_orbital_elem_row['EPOCH'], format='isot') - TimeDelta( 0.5 * u.d)
                    start_time = Time(start_time, precision=0)

                    propag = PropagInit(prev_orbital_elem_row, st.session_state["ss_lc"], cn.COMP_SAMPLE_TIME) 
                    pos = propag.traj_calc(start_time, cn.COMP_NUMBER_SAMPLES)  #orbital_elem_row['EPOCH'] '2023-02-21T05:56:47'

                    prev_traj = pos.enu[0]

                    propag = PropagInit(orbital_elem_row, st.session_state["ss_lc"], cn.COMP_SAMPLE_TIME) 
                    pos = propag.traj_calc(start_time, cn.COMP_NUMBER_SAMPLES)

                    curr_traj = pos.enu[0]

                    traj_error = prev_traj - curr_traj

                    traj_error_norm = np.linalg.norm(traj_error, axis=1)
                
                    sel_resume["NORAD_CAT_ID"].append( orbital_elem_row['NORAD_CAT_ID'])
                    sel_resume["OBJECT_NAME"].append( orbital_elem_row['OBJECT_NAME'])
                    sel_resume["EPOCH"].append( orbital_elem_row['EPOCH'])
                    sel_resume["EPOCH_1"].append( prev_orbital_elem_row['EPOCH'])
                    sel_resume["D_ERR_MEAN"].append( np.mean(traj_error_norm))
                    sel_resume["D_ERR_MAX"].append( np.max(traj_error_norm))
                    if np.mean(traj_error_norm)<err_max:
                        sel_resume["TRACK"].append( 1)
                    else:
                        sel_resume["TRACK"].append( 0)            
                    sel_resume["RCS_SIZE"].append( orbital_elem_row['RCS_SIZE'])
                    sel_resume["X_ERR_MEAN"].append( np.mean(np.abs(traj_error[:,0])))
                    sel_resume["Y_ERR_MEAN"].append( np.mean(np.abs(traj_error[:,1])))
                    sel_resume["Z_ERR_MEAN"].append( np.mean(np.abs(traj_error[:,2])))
                    sel_resume["PERIAPSIS"].append( orbital_elem_row['PERIAPSIS'])
                    sel_resume["ECCENTRICITY"].append( orbital_elem_row['ECCENTRICITY'])
                    sel_resume["MEAN_MOTION"].append( orbital_elem_row['MEAN_MOTION'])
                    sel_resume["DECAY_DATE"].append( orbital_elem_row['DECAY_DATE'])           

                orbital_elem_row = prev_orbital_elem_row
            my_bar.progress((idxi+1)/len(norad_comp_list))

        df_orb = pd.DataFrame(sel_resume)
        df_orb= df_orb[df_orb['D_ERR_MEAN'] != 0]

        st.session_state["df_orb"] = df_orb

    if "df_orb" not in st.session_state:
        st.info('run compare', icon=cn.INFO)
        page_stop()

    st.dataframe(st.session_state.df_orb)    

    st.session_state.df_orb.to_csv(st.session_state.ss_dir_name + "/"+ "orbital_elem_compare.csv", index=False)

    # st.write('Files can be downloaded:')
    # with open(st.session_state.ss_dir_name + "/"+ "orbital_elem_compare.csv", "rb") as fp:
    #     btn = st.download_button(
    #         label="Download",
    #         data=fp,
    #         file_name="orbital_elem_compare.csv",
    #         mime="application/txt"
    #     )

    st.markdown("Data visualization:")

    plot_compare(st.session_state.df_orb)

    page_links()



if __name__== '__main__':
    main()
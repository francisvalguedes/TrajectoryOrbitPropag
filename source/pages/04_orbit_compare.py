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
import time as tm

# https://raw.githubusercontent.com/omnidan/node-emoji/master/lib/emoji.json
st.set_page_config(page_title="Compare orbital elements trajectories",
                    page_icon="🌏", layout="wide", initial_sidebar_state="auto",
                    menu_items=menu_itens())


# apenas para tradução
domain_name = os.path.basename(__file__).split('.')[0]
_ = gettext_translate(domain_name)


# Constants
err_max = 3000 # m
max_process_time = 60*2 # 2 min

cn = ConstantsNamespace()



def page_links(insidebar=False):
    if insidebar:
        stlocal = st.sidebar
    else:
        stlocal = st.expander("", expanded=True)
    stlocal.subheader(_("*Pages:*"))
    stlocal.page_link("main.py", label=_("Home page"), icon="🏠")
    stlocal.page_link("pages/00_Simplified.py", label=_("Simplified Setup - APP Basic Functions"), icon="0️⃣")
    stlocal.markdown(_("Pages with specific settings:"))
    stlocal.page_link("pages/01_orbital_elements.py", label=_("Get Orbital Elements"), icon="1️⃣")
    stlocal.page_link("pages/02_orbit_propagation.py", label=_("Orbit Propagation"), icon="2️⃣")
    stlocal.page_link("pages/03_map.py", label=_("Map View Page"), icon="3️⃣")
    stlocal.page_link("pages/04_orbit_compare.py", label=_("Object Orbital Change/Maneuver"), icon="4️⃣")
    stlocal.page_link("pages/05_trajectory.py", label=_("Sensor-Specific Trajectory Selection"), icon="5️⃣")


def page_stop():
    page_links()
    st.stop()


def plot_compare(df):
    # Seleção de NORAD_CAT_ID
    col1, col2 = st.columns(2)
    selected_norad = col1.selectbox("Select the NORAD_CAT_ID", df["NORAD_CAT_ID"].unique())
    # Filtrando os dados
    filtered_df = df[df["NORAD_CAT_ID"] == selected_norad]

    col2.dataframe(filtered_df.get(["NORAD_CAT_ID", "OBJECT_NAME"], default=None).head(1))
    # Criando o eixo x como um array de índices negativos
    filtered_df = filtered_df.sort_values(by="EPOCH")
    n = len(filtered_df)
    filtered_df["x_axis"] = np.arange(-n + 1, 1)

    # Criando o gráfico
    fig = px.line(filtered_df, x="x_axis", y="D_ERR_MAX", title=f"Error over last orbital elements for NORAD_CAT_ID {selected_norad}",
                markers=True, labels={"D_ERR_MAX": "Erro Máximo(m)", "x_axis": "Índice relativo"})

    st.plotly_chart(fig)


def main():

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

    st.subheader(_('Orbit Trajectory Compare'))
    st.markdown(_('Use the orbital elements loaded on page 01 - Orbital Elements'))

    url = 'https://www.space-track.org/basicspacedata/query/class/gp_history/NORAD_CAT_ID/25544,53323/EPOCH/2024-07-02--2024-07-09/orderby/NORAD_CAT_ID%20desc/format/csv'

    st.write(_('Obtain the orbital elements from the Space-Track website or API more than two sets of'
               'orbital elements per object and upload to page 01 - Orbital Elements, which also has'
               'a tool for accessing the API.'))

    st.write(_('Example of a link for direct access to the Space-Track API (registration and login required): [link](%s)') % url)

    if 'ss_result_df' in st.session_state:                
        norad_comp  = st.session_state.ss_result_df.drop_duplicates(subset=['NORAD_CAT_ID'], keep='first')
        st.success(_('Norads loaded from last orbital propagation results'), icon=cn.SUCCESS)
    else:
        st.info(_('Run Orbit propagation'), icon=cn.INFO) 
        st.write(_('That is it'))           
        page_stop()

    norad_comp_list = norad_comp.to_dict('list')['NORAD_CAT_ID']

    if "ss_elem_df" not in st.session_state:
        st.info(_('Upload the orbital elements with two or more sets of orbital elements on the specific page'), icon=cn.INFO)         
        page_stop()
    else:
        df_selected = st.session_state.ss_elem_df[st.session_state.ss_elem_df['NORAD_CAT_ID'].isin(norad_comp['NORAD_CAT_ID'].tolist())]       
        df_oe_group = df_selected.groupby(df_selected['NORAD_CAT_ID'], as_index=False).size()['size']

        if len(df_oe_group) > 0:
            if max(df_oe_group) < 2:
                st.info(_('Insufficient orbital elements, obtain from the Space-Track website or API more than two sets of orbital'
                          'elements per object and upload to page 01 - Orbital Elements, which also has a tool for accessing the API.'), icon=cn.INFO)
                st.write(_('Example of a link for direct access to the Space-Track API (registration and login required): [link](%s)') % url)
                page_stop()
            else:
                st.success(_('Enough orbital elements to perform comparison already loaded'), icon=cn.SUCCESS)
                if min(df_oe_group) < 2:
                    st.warning(_('There are objects with less than two sets of orbital elements, it will not be possible to compare them'), icon=cn.WARNING)
        else:
            st.warning(_('There are no orbital elements for comparison'), icon=cn.WARNING)

    st.write(_('Perform propagation calculations and trajectory comparison:'))
    compare_oe_bt = st.button(_('Run trajectory comparison'))
    if compare_oe_bt:
        sel_resume = {  "NORAD_CAT_ID":[], "OBJECT_NAME":[], "EPOCH":[],"EPOCH_1":[], "D_ERR_MEAN":[],"D_ERR_MAX":[],
                        "TRACK":[], "RCS_SIZE":[], "X_ERR_MEAN":[], "Y_ERR_MEAN":[],"Z_ERR_MEAN":[],"PERIAPSIS":[],
                        "ECCENTRICITY":[], "MEAN_MOTION":[], "DECAY_DATE":[] }
        st.write(_('Progress bar:'))
        ini = tm.time()
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
                    if (tm.time() - ini) > max_process_time:
                        st.warning("Exceeded maximum processing time, limit the number of orbital elements", cn.WARNING)
                        break
                orbital_elem_row = prev_orbital_elem_row
            my_bar.progress((idxi+1)/len(norad_comp_list))
        df_orb = pd.DataFrame(sel_resume)
        df_orb= df_orb[df_orb['D_ERR_MEAN'] != 0]
        st.write(_("Processing time (s): "), tm.time() - ini)
        st.session_state["df_orb"] = df_orb

    if "df_orb" not in st.session_state:
        st.info(_('run compare'), icon=cn.INFO)
        page_stop()

    st.dataframe(st.session_state.df_orb)    

    st.session_state.df_orb.to_csv(st.session_state.ss_dir_name + "/"+ _("orbital_elem_compare.csv"), index=False)

    st.write(_('Files can be downloaded:'))
    with open(st.session_state.ss_dir_name + "/"+ "orbital_elem_compare.csv", "rb") as fp:
        btn = st.download_button(
            label="Download",
            data=fp,
            file_name="orbital_elem_compare.csv",
            mime="application/txt"
        )

    st.markdown(_("Data visualization:"))

    plot_compare(st.session_state.df_orb)

    page_links()



if __name__== '__main__':
    main()
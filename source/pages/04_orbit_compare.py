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

# Constants
err_max = 3000 # m
MENU_UPDATE = "Space-Track Update"
MENU_NUPDATE = "Space-Track already loaded"
menu_update = [ MENU_NUPDATE, MENU_UPDATE]

cn = ConstantsNamespace()

def main():
    st.set_page_config(
    page_title="Compare orbital elements trajectories",
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

    help='Choice'

    st.selectbox("Choice of orbital elements dataset:",menu_update, key="choice_update_comp", help=help)

# menu to configure and update orbital elements based on a loaded list of NORAD_CAT_ID

    if st.session_state["choice_update_comp"] == MENU_UPDATE:
        if not st.session_state.stc_loged:
            st.info('Necessary login Space-Track',   icon= cn.INFO)
            
            link = '[See the link of Space-Track API](https://www.space-track.org/documentation#/api)'
            st.markdown(link, unsafe_allow_html=True)
            # Form to Space-Track loguin 
            form = st.form("my_form")
            stc_log = form.text_input('User name Space-Track:')    
            stc_ss = form.text_input('Space-Track password:',type="password") 
            fcol1, fcol2 = form.columns(2)
            submitted = fcol1.form_submit_button("Submit")
            if submitted:
                st.session_state.stc = SpaceTrackClientInit(stc_log, stc_ss)
                st.session_state.stc_loged = st.session_state.stc.ss()
        
        if st.session_state.stc_loged:
            st.success('Space-Track logged', icon=cn.SUCCESS)
        else: st.warning("Status: Space-Track Unlogged",icon=cn.WARNING)

        norad_file = st.file_uploader("Upload norad list with column name NORAD_CAT ID",type=['csv'])
        #if st.button("Upload NORAD_CAT_ID file"):
        if norad_file is not None:
            st.write("File details:")
            file_details = {"Filename":norad_file.name,"FileType":norad_file.type,"FileSize":norad_file.size}
            st.write(file_details)
            if norad_file.type == "text/csv":
                st.session_state.ss_norad_comp = pd.read_csv(norad_file).drop_duplicates(subset=['NORAD_CAT_ID'], keep='first')
                st.dataframe(st.session_state.ss_norad_comp.style.format(thousands=""))

        elif 'ss_result_df' in st.session_state:                
            st.session_state.ss_norad_comp  = st.session_state.ss_result_df[['NORAD_CAT_ID', 'OBJECT_NAME']].drop_duplicates(subset=['NORAD_CAT_ID'], keep='first')
            st.info('Norad list loaded from last orbital propagation results', icon=cn.INFO)
        else: 
            st.info('Load NORAD_CAT_ID file csv or run propagation', icon=cn.INFO)
            page_stop()

        norad_comp_list = st.session_state.ss_norad_comp.to_dict('list')['NORAD_CAT_ID']

        update_compare_oe_bt = st.button("Orbital elements update to compare")
        if update_compare_oe_bt:

            # elements_csv = st.session_state.stc.get_by_norad(norad_comp_list) 
            
            st.session_state.ss_elem_df = st.session_state.stc.get_by_norad(norad_comp_list) #pd.read_csv(StringIO(elements_csv), sep=",")
            st.dataframe(st.session_state.ss_elem_df.style.format(thousands=""))
            st.session_state.ss_elem_df.to_csv(st.session_state.ss_dir_name + "/" + "orbital_elem_all.txt", index=False)   


    if st.session_state["choice_update_comp"] == MENU_NUPDATE: 
        norad_file = st.file_uploader("Upload norad list with column name NORAD_CAT_ID",type=['csv'])
        if norad_file is not None:
            st.write("File details:")
            file_details = {"Filename":norad_file.name,"FileType":norad_file.type,"FileSize":norad_file.size}
            st.write(file_details)
            if norad_file.type == "text/csv":
                st.session_state.ss_norad_comp = pd.read_csv(norad_file)
                st.dataframe(st.session_state.ss_norad_comp.style.format(thousands=""))
                st.success('Norad list loaded manually', icon=cn.SUCCESS)

        elif 'ss_result_df' in st.session_state:                
            st.session_state.ss_norad_comp  = st.session_state.ss_result_df[['NORAD_CAT_ID', 'OBJECT_NAME']].drop_duplicates(subset=['NORAD_CAT_ID'], keep='first')
            st.success('Norad list loaded from last orbital propagation results', icon=cn.SUCCESS)
        else: 
            st.info('Load NORAD_CAT_ID file csv or run propagation', icon=cn.INFO)            
            page_stop()

        norad_comp_list = st.session_state.ss_norad_comp.to_dict('list')['NORAD_CAT_ID']

    if "ss_elem_df" not in st.session_state:
        st.info('Upload the orbital elements with two or more sets of orbital elements', icon=cn.INFO)         
        page_stop()
    else: 
        df_selected = st.session_state.ss_elem_df[st.session_state.ss_elem_df['NORAD_CAT_ID'].isin(st.session_state.ss_norad_comp['NORAD_CAT_ID'].tolist())]       
        df_oe_group = df_selected.groupby(df_selected['NORAD_CAT_ID'],as_index=False).size()['size']
        # print(max(df_oe_group))
        # print(min(df_oe_group))
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

    st.dataframe(st.session_state.df_orb.style.format(thousands=""))
    st.session_state.df_orb.to_csv(st.session_state.ss_dir_name + "/"+ "orbital_elem_compare.csv", index=False)

    st.write('Files can be downloaded:')
    with open(st.session_state.ss_dir_name + "/"+ "orbital_elem_compare.csv", "rb") as fp:
        btn = st.download_button(
            label="Download",
            data=fp,
            file_name="orbital_elem_compare.csv",
            mime="application/txt"
        )


    page_links()



if __name__== '__main__':
    main()
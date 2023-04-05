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

from lib.pages_functions import  Icons, SpaceTrackClientInit

import datetime as dt
from datetime import datetime

import streamlit as st
import tempfile

sample_time = 60*5 # segundos
n_samples = 80
ic = Icons()


def main():
    if "date_time" not in st.session_state:
        date_time = datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
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
    st.subheader('Objects to be analyzed:')

    MENU_UPDATE = "Update orbital elements"
    MENU_NUPDATE = "Orbital elements already loaded"
    menu_update = [MENU_UPDATE, MENU_NUPDATE]
    help='Choice'

    st.selectbox("Choice of orbital elements dataset:",menu_update, key="choice_update_comp", help=help)

# menu to configure and update orbital elements based on a loaded list of NORAD_CAT_ID

    if st.session_state["choice_update_comp"] == MENU_UPDATE:
        if not st.session_state.stc_loged:
            st.info('Necessary login Space-Track',   icon= ic.info)
            
            link = '[See the link of Space-Track API](https://www.space-track.org/documentation#/api)'
            st.markdown(link, unsafe_allow_html=True)
            # Form to Space-Track loguin 
            form = st.form("my_form")
            stc_log = form.text_input('User name Space-Track:')    
            stc_ss = form.text_input('Space-Track password:',type="password") 
            fcol1, fcol2 = form.columns(2)
            submitted = fcol1.form_submit_button("Submit")
            if submitted:
                stc = SpaceTrackClientInit(stc_log, stc_ss)
                st.session_state.stc_loged = stc.ss()
                st.session_state.stc = stc
                # if st.session_state.stc_loged:          
                #     #del st.session_state.ss_elem_df
                #     st.write("ok")
                # else: 
                #     st.error('Error when logging', icon=ic.error)
        
        if st.session_state.stc_loged:
            st.success('Space-Track logged', icon=ic.success)
        else: st.warning("Status: Space-Track Unlogged",icon=ic.warning)

        norad_file = st.file_uploader("Upload norad list with column name NORAD_CAT ID",type=['csv'])
        #if st.button("Upload NORAD_CAT_ID file"):
        if norad_file is not None:
            st.write("File details:")
            file_details = {"Filename":norad_file.name,"FileType":norad_file.type,"FileSize":norad_file.size}
            st.write(file_details)
            if norad_file.type == "text/csv":
                st.session_state.ss_norad_comp = pd.read_csv(norad_file).drop_duplicates(subset=['NORAD_CAT_ID'], keep='first')
                st.dataframe(st.session_state.ss_norad_comp)

        if 'ss_norad_comp' not in st.session_state:
            st.info('Load NORAD_CAT_ID file csv', icon=ic.info)
            st.stop()

        norad_comp_list = st.session_state.ss_norad_comp.to_dict('list')['NORAD_CAT_ID']

        update_compare_oe_bt = st.button("Orbital elements update to compare")
        if update_compare_oe_bt:
            epoch_end = datetime.utcnow() + dt.timedelta(days=1)
            epoch_start = datetime.utcnow() - dt.timedelta(days=3)

            epoch_end = epoch_end.strftime('-%Y-%m-%d')
            epoch_start = epoch_start.strftime('%Y-%m-%d-')

            epoch = epoch_start + epoch_end

            elements_csv = st.session_state.stc.gp_history( norad_cat_id=norad_comp_list,
                                                            orderby='norad_cat_id desc',epoch=epoch,
                                                            format='csv')
            
            orbital_elem_all = pd.read_csv(StringIO(elements_csv), sep=",")
            st.dataframe(orbital_elem_all)
            orbital_elem_all.to_csv('data/space_track/oe_data_spacetrack.csv', index=False)
    
# menu to configure the comparison based on the orbital elements propagated on the previous page

    if st.session_state["choice_update_comp"] == MENU_NUPDATE: 
        norad_file = st.file_uploader("Upload norad list with column name NORAD_CAT_ID",type=['csv'])
        if norad_file is not None:
            st.write("File details:")
            file_details = {"Filename":norad_file.name,"FileType":norad_file.type,"FileSize":norad_file.size}
            st.write(file_details)
            if norad_file.type == "text/csv":
                st.session_state.ss_norad_comp = pd.read_csv(norad_file)
                st.dataframe(st.session_state.ss_norad_comp)
                st.info('manually loaded item', icon=ic.info)

        elif 'ss_elem_df' in st.session_state:                
            st.session_state.ss_norad_comp  = st.session_state.ss_elem_df[['NORAD_CAT_ID', 'OBJECT_NAME']].drop_duplicates(subset=['NORAD_CAT_ID'], keep='first')
            st.info('loaded from last orbital propagation results', icon=ic.info)
        else: 
            st.info('Load NORAD_CAT_ID file csv or run propagation', icon=ic.info)
            st.stop()

        # if 'ss_norad_comp' not in st.session_state:
        #     st.info('Load NORAD_CAT_ID file csv', icon=ic.info)
        #     st.stop()

        norad_comp_list = st.session_state.ss_norad_comp.to_dict('list')['NORAD_CAT_ID']

    if os.path.exists('data/space_track/oe_data_spacetrack.csv'):
        orbital_elem_all = pd.read_csv('data/space_track/oe_data_spacetrack.csv')
        # norad_comp_list = orbital_elem_all.drop_duplicates(subset=['NORAD_CAT_ID'], keep='first').to_dict('list')['NORAD_CAT_ID']
    else:
        st.warning('Space-track orbital elements file do not exists, please update', icon=ic.warning)

        

    limit=30
    err_max = 3000 # m
    st.write('Perform propagation calculations and trajectory comparison:')
    compare_oe_bt = st.button("run trajectory comparison")
    if compare_oe_bt:
        sel_resume = {  "NORAD_CAT_ID":[], "OBJECT_NAME":[], "EPOCH":[],"EPOCH_1":[], "D_ERR_MEAN":[],"D_ERR_MAX":[],
                        "TRACK":[], "RCS_SIZE":[], "X_ERR_MEAN":[], "Y_ERR_MEAN":[],"Z_ERR_MEAN":[],"PERIAPSIS":[],
                        "ECCENTRICITY":[], "MEAN_MOTION":[], "DECAY_DATE":[] }
        st.write('Progress bar:')
        my_bar = st.progress(0)
        for idxi, norad in enumerate(norad_comp_list):
            orbital_elem = orbital_elem_all.loc[orbital_elem_all['NORAD_CAT_ID'] == norad]

            orbital_elem = orbital_elem.reset_index(drop=True)

            for idxj, prev_orbital_elem_row in orbital_elem.iterrows():
                if idxj > 0:

                    start_time = Time(prev_orbital_elem_row['EPOCH'], format='isot') - TimeDelta( 0.5 * u.d)
                    start_time = Time(start_time, precision=0)

                    propag = PropagInit(prev_orbital_elem_row, st.session_state["ss_lc"], sample_time) 
                    pos = propag.traj_calc(start_time, n_samples)  #orbital_elem_row['EPOCH'] '2023-02-21T05:56:47'

                    prev_traj = pos.enu[0]

                    propag = PropagInit(orbital_elem_row, st.session_state["ss_lc"], sample_time) 
                    pos = propag.traj_calc(start_time, n_samples)

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
        st.info('run compare', icon=ic.info)
        st.stop()

    st.dataframe(st.session_state.df_orb)
    st.session_state.df_orb.to_csv(st.session_state.ss_dir_name + "/"+ st.session_state.date_time[0:19] +"_orbital_elem_compare.csv", index=False)

    with open(st.session_state.ss_dir_name + "/"+ st.session_state.date_time[0:19] +"_orbital_elem_compare.csv", "rb") as fp:
        btn = st.download_button(
            label="Download",
            data=fp,
            file_name="all_orbital_elem" + st.session_state.date_time +".csv",
            mime="application/txt"
        )

if __name__== '__main__':
    main()
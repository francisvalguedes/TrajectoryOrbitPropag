"""
Creator: Francisval Guedes Soares
Date: 2021
"""

import streamlit as st
import pandas as pd

import datetime as dt
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

from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder



cn = ConstantsNamespace()
MAX_NUM_OBJ = 30

# ----------------------------------------------------------------------
# Salva as trajetórias
# ----------------------------------------------------------------------
def save_trajectories(pos,dir_name,time_s):
    """saves trajectories and summarizes important data for tracking analysis.

    Args:

    Returns:
        self
    """ 
    time_arr = pos.time_array[0]    
    ttxt = time_arr[0].strftime('%Y_%m_%d-H0-%H_%M_%S')    
    buf = dir_name +"/trn100Hz/100Hz_" + "obj-" + str(pos.satellite.satnum) + "-" + ttxt + "TU.trn"

    np.savetxt(buf,pos.enu[0],fmt='%.3f',delimiter=",", header=str(time_s), comments='')

def dellfiles(file):
    py_files = glob.glob(file)
    err = 0
    for py_file in py_files:
        try:
            os.remove(py_file)
        except OSError as e:
            err = e.strerror
    return err

def main():
    """main function that provides the simplified interface for configuration,
         visualization and data download. """  

    st.set_page_config(
    page_title="Orbit propagation for Tracking",
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
        date_time = datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
        st.session_state.date_time = date_time

    if "ss_dir_name" not in st.session_state:
        dir_name = tempfile.gettempdir()+"/top_tmp_"+ date_time
        st.session_state.ss_dir_name = dir_name

    if not os.path.exists(st.session_state.ss_dir_name):
        os.mkdir(st.session_state.ss_dir_name)

    if not os.path.exists(st.session_state.ss_dir_name +"/trn100Hz"):
        os.mkdir(st.session_state.ss_dir_name +"/trn100Hz")

    st.subheader('Generate specific trajectories for the sensor:')

    # Select sensor location or record another location

    # help=('Select sensor location or record another location in propagation') 
    # lc_df = pd.read_csv('data/confLocalWGS84.csv')
     
    # st.sidebar.selectbox("Sensor location in the WGS84:",lc_df['name'], key="choice_lc", help=help)
    # for sel in lc_df['name']:
    #     if sel==st.session_state["choice_lc"]:
    #         lc = lc_df.loc[lc_df['name'] == sel].to_dict('records')[0]
    #         st.session_state["ss_lc"] = lc

    lc = st.session_state["ss_lc"]
    st.write('Sensor location in the WGS84 Geodetic ')
    st.write('Name: ', lc['name'])
    # st.write('Latitude: ', lc['lat'])
    # st.write('Longitude: ', lc['lon'] )
    # st.write('Height: ', lc['height'])

    # st.sidebar.subheader("Calculate trajectories:")
    st.subheader('Trajectories:')    

    if "ss_result_df" not in st.session_state:
        st.info('Run propagation for trajectory generation',   icon=cn.INFO)
        st.stop()


    gb = GridOptionsBuilder.from_dataframe(st.session_state.ss_result_df)

    # gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_column(st.session_state.ss_result_df.columns[0], headerCheckboxSelection=True)
    # gb.configure_side_bar()

    gridoptions = gb.build()

    # grid_table = AgGrid(
    #                     st.session_state.ss_result_df,
    #                     height=200,
    #                     gridOptions=gridoptions,
    #                     enable_enterprise_modules=True,
    #                     update_mode=GridUpdateMode.MODEL_CHANGED,
    #                     data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    #                     fit_columns_on_grid_load=False,
    #                     header_checkbox_selection_filtered_only=True,
    #                     use_checkbox=True)
    grid_table = AgGrid(
                      st.session_state.ss_result_df,
                      height=250,
                      gridOptions=gridoptions,
                      update_mode=GridUpdateMode.SELECTION_CHANGED)
    
    st.subheader('Selected:') 
    selected_row = grid_table["selected_rows"]
    selected_row = pd.DataFrame(selected_row)
    st.dataframe(selected_row)

 
    if st.button('Calculate 100Hz trajectories'): 

        if len(selected_row.index)>MAX_NUM_OBJ:
            st.info('Maximum number of objects to propagate: ' + str(MAX_NUM_OBJ) ,icon=cn.INFO)
            st.stop()
        elif len(selected_row.index)==0:
            st.info('Select objects to propagate' ,icon=cn.INFO)
            st.stop()

        dellfiles(st.session_state.ss_dir_name +"/trn100Hz/*.trn")

        ini = tm.time()    

        st.write('Progress bar:')
        my_bar = st.progress(0)

        orbital_elem = selected_row.to_dict('records')
        sample_time = 0.01

        # automatico:                          
        for index in range(len(orbital_elem)):
            propag = PropagInit(orbital_elem[index], lc, 1) 
            # print('teste')
            # print(orbital_elem[index]['H0'])
            # print(orbital_elem[index]['END_PT'])
            pos = propag.traj_calc(Time(orbital_elem[index]['H0']), round(orbital_elem[index]['END_PT']/sample_time) )
            save_trajectories(pos,st.session_state.ss_dir_name, orbital_elem[index]['END_PT'])
            my_bar.progress((index+1)/len(orbital_elem))
            
        fim = tm.time()
        st.write("Processing time (s): ", fim - ini)
        
    st.subheader('*Files:*')

    dir_name = st.session_state.ss_dir_name + '/trn100Hz'
    if os.path.exists(dir_name):       
        shutil.make_archive(dir_name, 'zip', dir_name)
        with open(dir_name + ".zip", "rb") as fp:
            btn = st.download_button(
                label="Download",
                data=fp,
                file_name="trn100Hz_"+ lc['name'] + '_' + st.session_state.date_time +".zip",
                mime="application/zip"
            )

    st.write('*.trn files - Trajectory from H0, in the ENU reference system in 100Hz')

if __name__== '__main__':
    main()
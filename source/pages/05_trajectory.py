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
    buf = dir_name +"/100hz_" + "obj-" + str(pos.satellite.satnum) + "-" + ttxt + "TU.trn"

    np.savetxt(buf,pos.enu[0],fmt='%10.3f',delimiter=",", header=str(time_s), comments='')

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

    if os.path.exists(st.session_state.ss_dir_name) == False:
        os.mkdir(st.session_state.ss_dir_name)

    st.subheader('Orbit propagation and search for approach trajectory to the sensor:')
    st.subheader("*Orbital elements:*")

    st.sidebar.subheader("*Settings:*")
    st.subheader("*Settings:*")


    # Select sensor location or record another location
    help=('Select sensor location or record another location above') 
    lc_df = pd.read_csv('data/confLocalWGS84.csv')
     
    st.sidebar.selectbox("Sensor location in the WGS84:",lc_df['name'], key="choice_lc", help=help)
    for sel in lc_df['name']:
        if sel==st.session_state["choice_lc"]:
            lc = lc_df.loc[lc_df['name'] == sel].to_dict('records')[0]
            st.session_state["ss_lc"] = lc

    st.write('Sensor location in the WGS84 Geodetic ')
    st.write('Name: ', lc['name'])
    # st.write('Latitude: ', lc['lat'])
    # st.write('Longitude: ', lc['lon'] )
    # st.write('Height: ', lc['height'])

    st.sidebar.subheader("Calculate trajectories:")
    st.subheader('*Outputs:*')    

    summary_and_oe = st.file_uploader("Upload norad list with column name NORAD_CAT ID",type=['csv'])
    #if st.button("Upload NORAD_CAT_ID file"):
    if summary_and_oe is not None:
        st.write("File details:")
        file_details = {"Filename":summary_and_oe.name,"FileType":summary_and_oe.type,"FileSize":summary_and_oe.size}
        st.write(file_details)
        if summary_and_oe.type == "text/csv":   
            summary_and_oe_df = pd.read_csv(summary_and_oe) 
            
            if len(summary_and_oe_df.index)>MAX_NUM_OBJ:
                st.info('Maximum number of objects to propagate: ' + str(MAX_NUM_OBJ) ,icon=cn.INFO)
                st.stop()
            # dellfiles(st.session_state.ss_dir_name + os.sep +'*.trn')
 
            ini = tm.time()    

            st.write('Progress bar:')
            my_bar = st.progress(0)

            orbital_elem = summary_and_oe_df.to_dict('records')
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
           
    shutil.make_archive(st.session_state.ss_dir_name, 'zip', st.session_state.ss_dir_name)
    with open(st.session_state.ss_dir_name + ".zip", "rb") as fp:
        btn = st.download_button(
            label="Download",
            data=fp,
            file_name="results_"+ lc['name'] + '_' + st.session_state.date_time +".zip",
            mime="application/zip"
        )

    st.write('*.trn files - Trajectory from H0, in the ENU reference system in 100Hz')

if __name__== '__main__':
    main()
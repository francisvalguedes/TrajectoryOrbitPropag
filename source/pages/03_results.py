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

cn = ConstantsNamespace()

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
    st.subheader('Data visualization:')

    if "ss_result_df" not in st.session_state:
        st.info('Run propagation for visualization',   icon=cn.INFO)
    elif "ss_lc" not in st.session_state:
        st.info('Load geodetic wgs84 location',   icon=cn.INFO)
    else:  
        st.write('The data summary:')                   
        st.write('Approaching the reference point: ', len(st.session_state.ss_result_df.index))
        st.dataframe(st.session_state.ss_result_df)
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

    st.info('To analyze the results, go to the next page.', icon=cn.INFO)

if __name__== '__main__':
    main()
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
from lib.pages_functions import *

from spacetrack import SpaceTrackClient
import spacetrack.operators as op
from io import StringIO

import glob

import pymap3d as pm
import re
import os.path


cn = ConstantsNamespace()


def page_links(insidebar=False):
    if insidebar:
        stlocal = st.sidebar
    else:
        stlocal = st
    
    stlocal.subheader(_("*Pages:*"))
    stlocal.page_link("main.py", label=_("Home page"), icon="🏠")
    # stlocal.markdown(_("Simplified Page:"))
    stlocal.page_link("pages/00_Simplified.py", label=_("Simplified setup with some of the APP functions"), icon="0️⃣")
    stlocal.markdown(_("Pages with specific settings:"))
    stlocal.page_link("pages/01_orbital_elements.py", label=_("Obtaining orbital elements of the space object"), icon="1️⃣")
    stlocal.page_link("pages/02_orbit_propagation.py", label=_("Orbit propagation and trajectory generation"), icon="2️⃣")
    stlocal.page_link("pages/03_map.py", label=_("Map view page"), icon="3️⃣")
    stlocal.page_link("pages/04_orbit_compare.py", label=_("Analysis of object orbital change/maneuver"), icon="4️⃣")
    stlocal.page_link("pages/05_trajectory.py", label=_("Generation of specific trajectories"), icon="5️⃣")

def page_stop():
    page_links()
    st.stop()


def st_data_map(df_data, lc, dmax):
    dfn = geodetic_circ(6,df_data.iloc[-1].lat ,df_data.iloc[-1].lon, 0 )  
    df = pd.concat([df_data, dfn], axis=0)    
    dfn = geodetic_circ(4,lc['lat'],
                        lc['lon'],
                        lc['height'])  
    df = pd.concat([df, dfn], axis=0)  
    dfn = geodetic_circ(dmax * np.cos(np.radians(df_data.iloc[-1]['ELEVATION'])),
                        lc['lat'],
                        lc['lon'],
                        lc['height'])
    df = pd.concat([df, dfn], axis=0) 
    dfn = geodetic_circ(dmax ,lc['lat'],
                        lc['lon'],
                        lc['height'])
    df = pd.concat([df, dfn], axis=0)
    return df

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
    menu_items = menu_itens()
    )

    page_links(insidebar=True)
        
    st.subheader('View of the selected trajectory on the map:')

    if "ss_dir_name" not in st.session_state:
        st.warning('Run propagation for visualization',   icon=cn.WARNING)
        page_stop() 

    if "ss_result_df" not in st.session_state:
        st.warning('Run propagation for visualization',   icon=cn.WARNING)
        page_stop()

# prints a map of the region with the trajectory
    files_map = glob.glob(st.session_state.ss_dir_name + '/csv1Hz/*TU.csv')        
    files_m = []
    for files in files_map:
        files_m.append(files.split('data-')[-1])
    
    if len(files_m) == 0:
        st.warning('no file map', icon=cn.WARNING)
        page_stop()

    st.write('Approaching the reference point: ', len(st.session_state.ss_result_df.index))

    choice_file_map = st.selectbox("Select file for map:",files_m, key='choice_file_map') #format_func=format_func_map

    df_data = pd.read_csv(st.session_state.ss_dir_name + '/csv1Hz/data-' + choice_file_map,
                    #usecols= ['lat', 'lon', 'ELEVATION']
                    )

    dmax = st.session_state.d_max

    tab1, tab2 = st.tabs(['Folium Map','Streamlit Map'])
    with tab1:
        plot_map(df_data, st.session_state["ss_lc"])        
    with tab2:        
        st.map(st_data_map(df_data, st.session_state["ss_lc"], dmax))

    # st.write('Streamlit map:') 
    # st.map(st_data_map(df_data, st.session_state["ss_lc"], dmax))

    # st.write('Folium map:') 
    # plot_map(df_data, st.session_state["ss_lc"])

    # st.markdown('The map can be seen below')
    st.markdown('Thanks')

    st.info('To compare the orbital elements trajectories, go to the next page.', icon=cn.INFO)

    page_links()


if __name__== '__main__':
    main()
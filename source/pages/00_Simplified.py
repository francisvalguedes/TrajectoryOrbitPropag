"""
Creator: Francisval Guedes Soares
Date: 2021
"""

import streamlit as st
import pandas as pd

from datetime import datetime, timedelta, timezone, time
import time as tm

from astropy.time import Time
from astropy.time import TimeDelta
from astropy import units as u

import os
import numpy as np

from lib.orbit_functions import  PropagInit
from lib.constants import  ConstantsNamespace
from lib.pages_functions import *

from streamlit_geolocation import streamlit_geolocation

import pymap3d as pm
import gettext
import requests
from io import StringIO

# import os
# import time
# import requests
# import pandas as pd


cn = ConstantsNamespace()


# st.set_page_config(page_title="Simplified Configuration for Orbit Propagation",
#                     page_icon="🌏", layout="wide", initial_sidebar_state="auto",
#                     menu_items=menu_itens())
# https://raw.githubusercontent.com/omnidan/node-emoji/master/lib/emoji.json

# apenas para tradução
domain_name = os.path.basename(__file__).split('.')[0]
_ = gettext_translate(domain_name)


# Constants
Celestrak = "Celestrak"
oe_file = "Orbital elements file"

menuUpdate = [Celestrak, oe_file]

sample_time = 5.0 # tempo de amostragem da trajetória    
dmax = 900 # distancia de aproximação para busca    
dmin = 800 # distancia de aproximação para salvar a trajetória
max_num_obj = 1000 # numero máximo de objetos


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


def menu_itens():
    menu_items={
        'Get Help': 'https://github.com/francisvalguedes/TrajectoryOrbitPropag',
        'About': "A cool app for orbit propagation and trajectory generation, report a bug: francisvalg@gmail.com"
    }
    return menu_items


def get_celestrack_oe2():
    norad_id = st.number_input(_('Select the NORAD_CAT_ID of the space object to obtain orbital elements:'), 0, 999999, value=25544, format="%d")
    current_day = datetime.now(timezone.utc).strftime('%Y_%m_%d_')
    celet_fil_n = 'data/celestrak/' + current_day + str(norad_id) + '.csv'
    
    if not os.path.exists(celet_fil_n):                
        urlCelestrak = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=' + str(norad_id) + '&FORMAT=csv'
        try:
            response = requests.get(urlCelestrak)
            if response.status_code == 200:
                elem_df = pd.read_csv(StringIO(response.text))
            else:
                st.error("Failed to load data from Celestrak.")
                elem_df = None
            #elem_df = load_original_data(urlCelestrak) 

            if 'MEAN_MOTION' in elem_df.columns.to_list():
                elem_df.to_csv(celet_fil_n, index=False)                     
            else:
                st.error(_('No orbital elements for this object in Celestrak'), icon=cn.ERROR)
                st.stop()
        except OSError as e:
            st.error(_('Celestrak error, use Space-Track or load orbital elements manually'), icon=cn.ERROR)
            st.stop()
    else:        
        elem_df = pd.read_csv(celet_fil_n)  
    return elem_df


def get_celestrack_oe():
    # Entrada do usuário
    norad_id = st.number_input(_('Select the NORAD_CAT_ID of the space object to obtain orbital elements:'), 0, 999999, value=25544, format="%d")
    
    # Validação do NORAD ID
    if norad_id < 1 or norad_id > 999999:
        st.error(_('Invalid NORAD ID. Please enter a value between 1 and 999999.'), icon=cn.ERROR)
        st.stop()

    # Geração do nome do arquivo
    current_day = datetime.now(timezone.utc).strftime('%Y_%m_%d_')
    celet_fil_n = 'data/celestrak/' + current_day + str(norad_id) + '.csv'

    # Verificação da existência do arquivo
    if not os.path.exists(celet_fil_n):
        urlCelestrak = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=' + str(norad_id) + '&FORMAT=csv'
        
        try:
            with st.spinner(_('Loading data from Celestrak...')):
                response = requests.get(urlCelestrak, timeout=10)  # Timeout de 10 segundos
            
            if response.status_code == 200:
                elem_df = pd.read_csv(StringIO(response.text))
                
                # Verificação de colunas obrigatórias
                required_columns = ['MEAN_MOTION', 'INCLINATION', 'RA_OF_ASC_NODE', 'ECCENTRICITY']
                if all(col in elem_df.columns for col in required_columns):
                    elem_df.to_csv(celet_fil_n, index=False)
                    st.success(_('Data loaded successfully!'))
                else:
                    st.error(_('Required orbital elements are missing in the data.'), icon=cn.ERROR)
                    st.stop()
            else:
                st.error(_('Failed to load data from Celestrak.'), icon=cn.ERROR)
                st.stop()
        
        except requests.exceptions.Timeout:
            st.error(_('Request to Celestrak timed out. Please try again later.'), icon=cn.ERROR)
            st.stop()
        except requests.exceptions.RequestException as e:
            st.error(_('An error occurred while connecting to Celestrak: {}').format(e), icon=cn.ERROR)
            st.stop()
    else:
        elem_df = pd.read_csv(celet_fil_n)
    
    return elem_df

# Limpeza de arquivos antigos
def clear_old_files(directory, days=7):
    current_time = tm.time()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_time = os.path.getmtime(file_path)
            if (current_time - file_time) > (days * 86400):  # 86400 segundos em um dia
                os.remove(file_path)


# def get_celestrack_oe():
#     norad_id = st.number_input('Select the NORAD_CAT_ID of the space object to obtain orbital elements:', 0, 999999, value=25544, format="%d")
#     urlCelestrak = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=' + str(norad_id) + '&FORMAT=csv'
#     elem_df = pd.read_csv(urlCelestrak)
#     return elem_df

def upload_oe():
    data_elements = st.file_uploader(_('Upload orbital elements: OMM csv format'), type='csv')
    
    if data_elements is not None:            
        if data_elements.type == "text/csv":
            st.write(_('Orbital elements uploaded:'))
            elem_df = pd.read_csv(data_elements)
        else:
            st.warning(_('File error'), icon=cn.WARNING)
            st.stop()
    else:
        st.info(_('Upload the file'), icon=cn.INFO)
        st.stop()
    
    return elem_df


def get_date_time():    
    max_time = TimeDelta(10*u.d)
    expander_date = st.expander(_('Start time for proximity search - UTC 00:'), expanded=True)
    col1, col2 = expander_date.columns(2)
    initial_date = col1.date_input(_('Start date'))
    initial_time = col2.time_input(_('Start time'), time(10, 0))
    initial_datetime = Time(datetime.combine(initial_date, initial_time))
    initial_datetime.format = 'isot'

    final_date = col1.date_input(_('End date'), datetime.today() + timedelta(days=1))
    final_time = col2.time_input(_('End time'), time(20, 0))
    final_datetime = Time(datetime.combine(final_date, final_time))
    final_datetime.format = 'isot'

    if (final_datetime - initial_datetime) > max_time:      
        final_datetime = initial_datetime + max_time 
        st.warning(_('Maximum period: ') + str(max_time) + _(' days'), icon=cn.WARNING)
    elif (final_datetime - initial_datetime) < TimeDelta(0.0001*u.d):
        st.error(_('End time must be greater than start time'), icon=cn.ERROR)
        st.stop()
    return initial_datetime, final_datetime

def dell_elem_df():
    if 'ss_elem_df' in st.session_state:
        del st.session_state.ss_elem_df

def data_input_geodesicas():
    st.write(_(
        'Set with my current location by clicking on the icon below (low precision), '
        'alternatively you can get the coordinates of the location on Google Earth or Google Maps:'
    ))
    loc = streamlit_geolocation()
    lat = loc['latitude'] if loc['latitude'] is not None else -5.92455
    lon = loc['longitude'] if loc['longitude'] is not None else -35.2658
    h = loc['altitude'] if loc['altitude'] is not None else 100.0
    expander = st.expander(_('Enter the reference point coordinates:'), expanded=True)
    col1, col2, col3 = expander.columns(3)
    latitude = col1.number_input(_('Latitude (degrees)'), -90.0, 90.0, lat, format="%.6f", key='Latitude')
    longitude = col2.number_input(_('Longitude (degrees)'), -180.0, 180.0, lon, format="%.6f", key='Longitude')
    height = col3.number_input(_('Altitude (m)'), -1000000.0, 50000000.0, h, format="%.2f", key='Altura')
    return pd.DataFrame({"name": ['Manual'], "lat": [latitude], "lon": [longitude], "height": [height]})


def main():
    """Main function that provides a simplified interface for configuration,
         visualization, and data download."""    
   
    #translate_page(page="00_Simplified")
    
    page_links(insidebar=True)

    st.subheader(_("Simplified Configuration for Orbit Propagation and Approximation Trajectory Calculation to the Reference Point (Sensor):"))
    
    st.subheader(_("*Obtaining Orbital Elements:*"))

    helptxt = _( "Choose the source of orbital elements for propagation")
    oe_source = st.selectbox(_("Source of orbital elements:"), menuUpdate, key="oe_source", help=helptxt, on_change=dell_elem_df)  
        
    # arquivos = glob.glob('data/celestrak/*.csv') 
    # for arquivo in arquivos:
    #     st.write(arquivo)
    # Chamada da função para limpar arquivos antigos
    clear_old_files('data/celestrak/')

    if oe_source == Celestrak:
        st.session_state.ss_elem_df = get_celestrack_oe()
    elif oe_source == oe_file:
        st.session_state.ss_elem_df = upload_oe()

    st.dataframe(st.session_state.ss_elem_df)  

    st.subheader(_("*Configurations for Orbit Propagation:*"))
   
    lc = data_input_geodesicas().to_dict('records')[0]

    st.write(_('Sampling period (s):'), sample_time)
    st.write(_('Maximum trajectory distance (km):'), dmax)
    st.write(_('Distance to save trajectory (km):'), dmin)
    st.write(_('Maximum number of objects:'), max_num_obj)

    # Period for trajectory search
    initial_datetime, final_datetime = get_date_time()
     
    st.subheader(_("*Obtain Approximation Data and Calculate Trajectories:*"))
    
    if st.button(_("Execute Propagation")):
        if "ss_elem_df" not in st.session_state:
            st.info(_('Upload the orbital elements'), icon=cn.INFO)
            st.stop()
        elif 'MEAN_MOTION' not in st.session_state["ss_elem_df"].columns.to_list():
            st.error(_('Orbital elements do not match OMM format'), icon=cn.ERROR)
            st.stop()

        elem_df = st.session_state.ss_elem_df.drop_duplicates(subset=['NORAD_CAT_ID'], keep='first')
        st.write(_('Number of orbital elements: '), len(elem_df.index))

        if len(elem_df.index) > max_num_obj:
            st.warning(_('Maximum number of objects for propagation: ') + str(max_num_obj) +
                    _(', for the period of ') + str(final_datetime - initial_datetime) + _(' days'),
                        icon=cn.WARNING)
            st.stop()

        orbital_elem = elem_df.to_dict('records')
        del elem_df

        rcs = pd.read_csv('data/RCS.csv').to_dict('list')        

        ini = tm.time()    

        st.write(_('Progress bar:'))
        my_bar = st.progress(0)

        sdf = Summarize2DataFiles()

        # Automatic processing                          
        for index in range(len(orbital_elem)):
            propag = PropagInit(orbital_elem[index], lc, sample_time) 
            pos = propag.search2h0(initial_datetime, final_datetime, dmax*1000, dmin*1000)
            sdf.save_trajectories(pos, orbital_elem[index], rcs)
            my_bar.progress((index+1)/len(orbital_elem))

        df_orb = pd.DataFrame(sdf.sel_orbital_elem)
        obj_aprox = len(df_orb.index)

        if obj_aprox > 0:
            col_first = ['EPOCH', 'CREATION_DATE', 'DECAY_DATE']
            df_orb = columns_first(df_orb, col_first)

            df_traj = pd.DataFrame(sdf.sel_resume)

            common = set(df_traj.columns.tolist()).intersection(df_orb.columns.tolist())
            if len(common) > 0:
                st.error(_('Upload a file containing only orbital elements in OMM format'), icon=cn.ERROR)
                st.stop()

            df_traj = df_traj.join(df_orb)

            col_first = ['NORAD_CAT_ID', 'OBJECT_NAME', 'RCS_SIZE']
            df_traj = columns_first(df_traj, col_first)

            st.session_state.ss_result_df = df_traj.sort_values(by='H0') 
            st.session_state.tr_data = sdf.tr_data
                            
        else:
            if "ss_result_df" in st.session_state:
                del st.session_state.ss_result_df
            st.warning(_('The space object does not approach the specified location within this time period'), icon=cn.WARNING)

        fim = tm.time()
        st.write(_("Processing time (s): "), np.round(fim - ini, 3))

    if "ss_result_df" in st.session_state: 
        st.success(_('Trajectories successfully calculated: ') + str(len(st.session_state.ss_result_df.index)), icon=cn.SUCCESS)                      
        st.write(_('Summary of calculated trajectories:'))
        st.dataframe(st.session_state.ss_result_df.style.format(thousands="")) 
        
        st.selectbox(_("Select the approach time to view the trajectory:"), st.session_state.ss_result_df['H0'], key="choice_obj", help=_("help"))
        sel_index = st.session_state.ss_result_df.loc[st.session_state.ss_result_df['H0'] == st.session_state["choice_obj"]].index 
        if 'tr_data' in st.session_state:
            st.dataframe(st.session_state.tr_data[sel_index[0]])
            st.write(_('The button to download the tables appears when you hover over the upper right corner of the tables'))
            st.write(_('Visualization on the map:'))             
            plot_map(st.session_state.tr_data[sel_index[0]], lc)


    page_links()
    
if __name__== '__main__':
    main()
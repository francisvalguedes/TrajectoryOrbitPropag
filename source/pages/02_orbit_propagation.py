"""
Creator: Francisval Guedes Soares
Date: 2021
"""

import streamlit as st
import pandas as pd

from datetime import datetime, timezone
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

import glob

import pymap3d as pm
import re


st.set_page_config(page_title="Orbit propagation",
                    page_icon="🌏", layout="wide", initial_sidebar_state="auto",
                    menu_items=menu_itens())
# https://raw.githubusercontent.com/omnidan/node-emoji/master/lib/emoji.json

# apenas para tradução
domain_name = os.path.basename(__file__).split('.')[0]
_ = gettext_translate(domain_name)

# constantes
cn = ConstantsNamespace()
max_time = TimeDelta(10*u.d)
max_process_time = 60*2 # 2 min 

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

@st.cache_data
def read_csv_index(file_path):
    # Lê o CSV sem atribuição de índice e apaga linhas vazias
    df = pd.read_csv(file_path).dropna(how='all')
    
    # Verifica se a primeira coluna não tem nome e é candidata a ser índice
    if df.columns[0] == 'Unnamed: 0':
        df.set_index(df.columns[0], inplace=True)
        df.index.name = None 
    return df

def sensor_registration():
    # Add new reference point (sensor)
    lc_expander = st.sidebar.expander(_("Add new reference point in WGS84"), expanded=False)
    lc_name = lc_expander.text_input(_('Name'), "my location")
    latitude = lc_expander.number_input(_('Latitude'), -90.0, 90.0, 0.0, format="%.6f")
    longitude = lc_expander.number_input(_('Longitude'), -180.0, 180.0, 0.0, format="%.6f")
    height = lc_expander.number_input(_('Height (m)'), -1000.0, 2000.0, 0.0, format="%.6f")
    color = lc_expander.text_input(_('Color'), "red")
    
    if lc_expander.button(_("Register new location definitely")):
        lc_add = {'name': [lc_name], 'lat': [latitude], 'lon': [longitude], 'height': [height], 'color': [color]}
        
        if lc_name not in st.session_state.lc_df['name'].to_list():
            if re.match('^[A-Za-z0-9_-]*$', lc_add['name'][0]):
                st.session_state.lc_df = pd.concat([st.session_state.lc_df, pd.DataFrame(lc_add)], axis=0)
                st.session_state.lc_df.to_csv('data/confLocalWGS84.csv', index=False)
                lc_expander.write(_('Location registered'))
            else:
                lc_expander.write(_('Enter a name without special characters'))
        else:
            lc_expander.write(_('Location already exists'))

    if lc_expander.button(_("Register new location current session")):
        lc_add = {'name': [lc_name], 'lat': [latitude], 'lon': [longitude], 'height': [height], 'color': [color]}
        
        if lc_name not in st.session_state.lc_df['name'].to_list():
            if re.match('^[A-Za-z0-9_-]*$', lc_add['name'][0]):
                st.session_state.lc_df = pd.concat([st.session_state.lc_df, pd.DataFrame(lc_add)], axis=0)
                lc_expander.write(_('Location registered'))
            else:
                lc_expander.write(_('Enter a name without special characters'))
        else:
            lc_expander.write(_('Location already exists'))

    # Carregar arquivo CSV
    lc_expander.write(_("Alternatively you can upload a csv file with reference points only for the current session, fields: name, lat, lon height"))
    uploaded_file = lc_expander.file_uploader(_("Points in a CSV for this session"), type="csv")
    if uploaded_file is not None:
        if uploaded_file.type == "text/csv":
            df = read_csv_index(uploaded_file)
            # Verifica se as colunas existem
            required_columns = {'name', 'lat', 'lon', 'height'}
            if required_columns.issubset(df.columns):
                # Verifica os tipos de dados das colunas
                if (df['name'].dtype == 'object' and df['lat'].dtype == 'float64' 
                    and df['lon'].dtype == 'float64' and df['height'].dtype == 'float64'):
                    st.session_state.lc_df = df
                    lc_expander.success(_("loaded successfully"), icon= cn.SUCCESS)
                else:
                    lc_expander.error(_("error: wrong data type - expected: name: string, and lat, lon and height: float "), icon= cn.ERROR)
                    st.stop()
            else:
                lc_expander.error(_("error: expected columns are not present (name, lat, lon and height)"), icon= cn.ERROR)
                st.stop()
        else:
            lc_expander.error(_("error: file is not csv"), icon= cn.ERROR)
            st.stop()

def dellfiles(file):
    py_files = glob.glob(file)
    err = 0
    for py_file in py_files:
        try:
            os.remove(py_file)
        except OSError as e:
            err = e.strerror
    return err

def columns_first(df, col_first):
    col_list = df.columns.to_list()
    for line in col_first:
        if line in col_list: col_list.remove(line)
        else: col_first.remove(line)
    col_first.extend(col_list)
    df = df.reindex(columns=col_first)
    return df

# ----------------------------------------------------------------------
# Salva as trajetórias
# ----------------------------------------------------------------------
class SummarizeDataFiles:
    def __init__(self):
        """initialize the class"""        
        self.sel_orbital_elem = []
        self.sel_resume = {"RCS":[], "H0":[],"H0_H":[], "H0_RANGE":[],"MIN_RANGE_H":[],"MIN_RANGE_PT":[],
                    "MIN_RANGE":[],"END_H":[], "END_PT":[], "END_RANGE":[] }

    def save_trajectories(self,pos,orbital_elem,dir_name,rcs):
        """saves trajectories and summarizes important data for tracking analysis.

        Args:
            pos (PropagInit obj): all calculated trajectories of an sattelite (orbital_elem) 
            orbital_elem (OMM dict): orbital element of sattelite
            dir_name (str): path to save files
        Returns:
            self
        """ 

        for i in range(0, len(pos.time_array)):
            time_arr = pos.time_array[i]
            
            ttxt = time_arr[0].strftime('%Y_%m_%d-H0-%H_%M_%S')

            df_enu = pd.DataFrame(pos.enu[i])
            df_enu.to_csv(dir_name +"/trn1Hz/obj-" + str(pos.satellite.satnum) + "-" + ttxt + "TU.trn",
                            index=False, header=[str(len(df_enu.index)-1),'1000','1'],float_format="%.3f")
            df_enu.to_csv(dir_name +"/trj1Hz/pobj-" + str(pos.satellite.satnum) + "-" + ttxt + "TU.trj", sep=' ',
                            index=False, header=[ '1', str(len(df_enu.index)-1),'1'],float_format="%.3f")

            df_data = pd.DataFrame(time_arr.value.reshape(len(time_arr),1), columns=['Time'])

            df_data = pd.concat([df_data, pd.DataFrame(np.concatenate((
                            pos.az_el_r[i], pos.enu[i], 
                            pos.itrs[i], pos.geodetic[i]), axis=1),
                            columns=[ 'AZIMUTH','ELEVATION','RANGE',
                            'ENU_E','ENU_N','ENU_U', 
                            'ITRS_X','ITRS_Y','ITRS_Z','lat','lon','height'])], axis=1)
            
            df_data.to_csv(dir_name + "/csv1Hz/data-" + str(pos.satellite.satnum) + "-" + ttxt + "TU.csv", index=False)

            enu_d = 0.001*pos.az_el_r[i][:,2]
            min_index = np.argmin(enu_d)
            min_d = enu_d[min_index]

            self.sel_orbital_elem.append(orbital_elem) 
            if pos.satellite.satnum in rcs['NORAD_CAT_ID']:
                self.sel_resume["RCS"].append(rcs['RCS'][rcs['NORAD_CAT_ID'].index(pos.satellite.satnum)])
            else:
                self.sel_resume["RCS"].append(0.0)
            self.sel_resume["H0"].append(time_arr[0].value)
            self.sel_resume["H0_H"].append(time_arr[0].strftime('%H:%M:%S.%f'))
            self.sel_resume["H0_RANGE"].append(enu_d[0])
            self.sel_resume["MIN_RANGE_H"].append(time_arr[min_index].strftime('%H:%M:%S.%f'))
            self.sel_resume["MIN_RANGE_PT"].append(min_index)
            self.sel_resume["MIN_RANGE"].append(min_d)
            self.sel_resume["END_H"].append(time_arr[-1].strftime('%H:%M:%S.%f'))
            self.sel_resume["END_PT"].append(len(enu_d) - 1)
            self.sel_resume["END_RANGE"].append(enu_d[-1]) 

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
    """main function that provides the simplified interface for configuration,
         visualization and data download. """  

    page_links(insidebar=True)

    if "stc_loged" not in st.session_state:
        st.session_state.stc_loged = False
    
    if "d_max" not in st.session_state:
        st.session_state.d_max = 1100

    # path_files = tempfile.gettempdir() + '/top_tmp*'
    # txt_files = glob.glob(path_files)
    # files_count = len(txt_files)

    if "date_time" not in st.session_state:
        date_time = datetime.now(timezone.utc).strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
        st.session_state.date_time = date_time

    if "ss_dir_name" not in st.session_state:
        dir_name = tempfile.gettempdir()+"/top_tmp_"+ date_time
        st.session_state.ss_dir_name = dir_name  

    if os.path.exists(st.session_state.ss_dir_name) == False:
        os.mkdir(st.session_state.ss_dir_name)

    if not os.path.exists(st.session_state.ss_dir_name + "/trn1Hz"):
        os.mkdir(st.session_state.ss_dir_name +"/trn1Hz")
        os.mkdir(st.session_state.ss_dir_name +"/trj1Hz")
        os.mkdir(st.session_state.ss_dir_name +"/csv1Hz")         

    st.subheader(_('Orbit propagation and search for approach trajectory to the sensor:'))

    st.subheader(_("*Orbital elements:*"))

    if "ss_elem_df" not in st.session_state:
        st.warning(_('Upload the orbital elements in previous page'), icon=cn.WARNING)        
    else:
        st.success(_('Orbital Elements loaded!'), icon=cn.SUCCESS )

    if "lc_df" not in st.session_state:
        st.session_state["lc_df"] = pd.read_csv('data/confLocalWGS84.csv')

    st.subheader(_("*Settings:*"))

    sample_time = 1.0 
    st.write(_('Sampling rate (s): '), sample_time)

    help=_('Select sensor location or record another location in the sidebar') 
    sensor_registration()
    
    st.selectbox(_('Sensor location in the WGS84 (a new one can be registered in the sidebar) :'), st.session_state.lc_df['name'], key="choice_lc", help=help)
    for sel in st.session_state.lc_df['name']:
        if sel==st.session_state["choice_lc"]:
            lc = st.session_state.lc_df.loc[st.session_state.lc_df['name'] == sel].to_dict('records')[0]
            st.session_state["ss_lc"] = lc

    st.write(_('Sensor location in the WGS84 Geodetic '))
    st.write(_('Name: '), lc['name'])

    dmax = st.number_input(_('Maximum distance to trajectory limits (Km)'),
        min_value = 400,
        max_value = 10000,
        value = 1100,
        step = 50)
    st.session_state.d_max = dmax

    dmin = st.number_input(_('The minimum distance that the trajectory must reach in order to be accepted (Km)'),
        min_value = 200,
        max_value = 5000,
        value = 1000,
        step = 50)

    if not dmax>1.05*dmin:
        st.error(_('The maximum distance must be greater than the minimum distance in 1.05x'), icon=cn.ERROR)

    st.write(_('Start and end time for H0 search TU:'))
    col1, col2 = st.columns(2)
    initial_date = col1.date_input(_("Start date"))
    initial_time = col2.time_input(_("Start time"), time(10, 0))
    initial_datetime=Time(datetime.combine(initial_date, initial_time))
    initial_datetime.format = 'isot'
    st.write(_('Search start time: '), initial_datetime)

    final_date = col1.date_input(_("End date"))
    final_time = col2.time_input(_("End time"), time(20, 0))
    final_datetime=Time(datetime.combine(final_date, final_time))
    final_datetime.format = 'isot'
    st.write(_('Search end time: '), final_datetime)   
    
    max_num_obj = 5000

    if  (final_datetime - initial_datetime)> max_time:      
        final_datetime = initial_datetime + max_time 
        st.warning(_('Maximum time delta: ') + str(max_time) + _(' days'), icon=cn.WARNING)
    elif  (final_datetime - initial_datetime) < TimeDelta(0.0001*u.d):
        st.error(_('End date must be after start date'), icon=cn.ERROR)
        st.stop()
        
    time_norm = (max_time - (final_datetime - initial_datetime))/max_time
    max_num_obj = np.round(1 + max_num_obj*time_norm)
    st.info(_('Maximum number of objects to propagate: {}, for time delta {:.2f} days').format(max_num_obj, (final_datetime - initial_datetime).to_value('jd', 'decimal')),icon=cn.INFO)

    st.subheader(_("*Calculate trajectories:*"))

    summary_fn = lc['name']+ '_' + st.session_state.date_time[0:19] +"_traj_summary.csv"
    summary_path = st.session_state.ss_dir_name + "/"+ summary_fn

# ##################

    if st.button(_("Run propagation")):
        if "ss_elem_df" not in st.session_state:
            st.info(_("Upload the orbital elements"), icon=cn.INFO)
        elif 'MEAN_MOTION' not in st.session_state["ss_elem_df"].columns.to_list():
            st.error(_("Orbital elements do not match OMM format"), icon=cn.ERROR)
        else:
            elem_df = st.session_state["ss_elem_df"].drop_duplicates(subset=['NORAD_CAT_ID'], keep='first')
            st.write(_("Number of objects: "), len(elem_df.index))

            if len(elem_df.index) > max_num_obj:
                st.warning(_("Maximum number of objects to propagate: ") + str(max_num_obj) +
                        _(", for time delta ") + str(final_datetime - initial_datetime) + _(" days"),
                        icon=cn.WARNING)
                st.stop()

            if 'PERIAPSIS' in elem_df.columns.tolist():
                orbital_elem = elem_df[elem_df['PERIAPSIS'] < dmax]
                orbital_elem_dell = elem_df[~elem_df['NORAD_CAT_ID'].isin(orbital_elem['NORAD_CAT_ID'].tolist())]
                if orbital_elem_dell.shape[0] > 0:
                    st.warning(str(orbital_elem_dell.shape[0]) + _(" objects excluded because they have periapsis greater than dmax: ") +
                            str(dmax) + "Km", icon=cn.WARNING)
            else:
                orbital_elem = elem_df

            del elem_df

            orbital_elem = orbital_elem.to_dict('records')

            rcs = pd.read_csv('data/RCS.csv').to_dict('list')

            dellfiles(st.session_state.ss_dir_name + "/trn1Hz/*.trn")
            dellfiles(st.session_state.ss_dir_name + "/trj1Hz/*.trj")
            dellfiles(st.session_state.ss_dir_name + "/csv1Hz/*.csv")

            ini = tm.time()

            st.write(_("Progress bar:"))
            my_bar = st.progress(0)

            sdf = SummarizeDataFiles()

            for index in range(len(orbital_elem)):
                propag = PropagInit(orbital_elem[index], lc, sample_time)
                pos = propag.search2h0(initial_datetime, final_datetime, dmax * 1000, dmin * 1000)
                sdf.save_trajectories(pos, orbital_elem[index], st.session_state.ss_dir_name, rcs)
                my_bar.progress((index + 1) / len(orbital_elem))
                if (tm.time() - ini) > max_process_time:
                    st.warning(_("Exceeded maximum processing time, limit the number of orbital elements"),icon= cn.WARNING)
                    break
                
            df_orb = pd.DataFrame(sdf.sel_orbital_elem)
            obj_aprox = len(df_orb.index)
            st.write(_("Number of calculated trajectories: "), obj_aprox)

            if obj_aprox > 0:
                df_orb.to_csv(st.session_state.ss_dir_name + "/" + st.session_state.date_time[0:19] + "_orbital_elem.csv", index=False)
                col_first = ['EPOCH', 'CREATION_DATE', 'DECAY_DATE']
                df_orb = columns_first(df_orb, col_first)

                df_traj = pd.DataFrame(sdf.sel_resume)
                common = set(df_traj.columns.tolist()).intersection(df_orb.columns.tolist())
                if len(common) > 0:
                    st.error(_("Column naming conflict: load file with only orbital elements"), icon=cn.ERROR)
                    st.stop()

                df_traj = df_traj.join(df_orb)
                col_first = ['NORAD_CAT_ID', 'OBJECT_NAME', 'RCS_SIZE']
                df_traj = columns_first(df_traj, col_first)
                df_traj = df_traj.sort_values(by=['H0'], ascending=True)
                df_traj = df_traj.reset_index(drop=True)

                st.session_state.ss_result_df = df_traj
                st.session_state.traj_flag = True
                df_traj.to_csv(summary_path, index=False)
            else:
                if "ss_result_df" in st.session_state:
                    del st.session_state.ss_result_df
                st.warning(_("There are no sensor approach points for this configuration"), icon=cn.WARNING)

            fim = tm.time()
            st.write(_("Processing time (s): "), fim - ini)

    st.subheader(_('*Outputs:*'))
    st.write(_("The data summary:"))
    if "ss_result_df" in st.session_state:
        st.success(_("Trajectories calculated successfully"), icon=cn.SUCCESS)
        st.write(_("Approaching the reference point: "), len(st.session_state.ss_result_df.index))
        st.dataframe(st.session_state.ss_result_df.style.format(thousands=""))

    st.subheader(_("*Files:*"))
    if "ss_result_df" not in st.session_state:
        st.info(_("Run propagation to get files"), icon=cn.INFO)
    else:
        if os.path.isfile(summary_path):
            st.write(_("Download Summary File:"))
            with open(summary_path, "rb") as fp:
                btn = st.download_button(
                    label="Download",
                    data=fp,
                    file_name=summary_fn,
                    mime="application/txt"
                )

        st.write(_("Download All Files:"))
        shutil.make_archive(st.session_state.ss_dir_name, 'zip', st.session_state.ss_dir_name)
        with open(st.session_state.ss_dir_name + ".zip", "rb") as fp:
            btn = st.download_button(
                label="Download",
                data=fp,
                file_name="results_" + lc['name'] + '_' + st.session_state.date_time + ".zip",
                mime="application/zip"
            )

    st.write(_("Files can be downloaded on the right side"))
    st.write(_("The resulting files contain:"))
    st.write(_("orbital_elem.csv - Orbital elements of selected objects"))
    st.write(_("orbital_elem_all.csv - All loaded orbital elements"))
    st.write(_("traj_summary.csv - Relevant trajectory and object data"))
    st.write(_("*.trn files - Trajectory from H0, in the ENU reference system 1Hz"))
    st.write(_("*.trj files - Trajectory from H0, in the ENU reference system 1Hz"))
    st.write(_("data *.csv files - Trajectory from H0, in local plane reference (ENU), AltAzRange, ITRS and Geodetic, including times 1Hz"))
    st.info(_("To analyze the results, go to the next page."), icon=cn.INFO)

    page_links()
   

if __name__== '__main__':
    main()
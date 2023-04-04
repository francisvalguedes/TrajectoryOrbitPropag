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

from spacetrack import SpaceTrackClient
import spacetrack.operators as op
from io import StringIO

import glob

import pymap3d as pm
import re

# streamlit run source/main.py

def rcs_min(r_min, pt=59.6, gt=42, gr=42, lt=1.5, lr=1.5, f=5700, sr = -143, snr=0 ):
    """Function that returns the minimum Radar cross section (RCS) for radar detection
    Creators: Francisval Guedes Soares, Marcos Leal
    Date: 2023
    
    Args:
    r_min (array[n] - numpy): minimum object-to-radar distance.
    pt (float in db): radar power
    gt and gr (float in db): radar transmit and receive gain
    lt and lr (float in db): radar transmit and receive loss
    f (float): radar frequency
    sr (float in db): receiver sensitivity
    snr (float in db): signal noise ratio
    Returns:
    rcs (array[n] - numpy) : Radar cross section (RCS) 
    """
    pt_lin = 10**(pt/10)
    gt_lin = 10**(gt/10)
    gr_lin = 10**(gr/10)
    lt_lin = 10**(lt/10)
    lr_lin = 10**(lr/10)
    sr_lin = 10**(sr/10)
    snr_lin = 10**(snr/10)
    lamb =  (3*10**8)/(f * 10**6)
    rcs = (((4*np.pi)**3) * sr_lin * lt_lin * lr_lin * np.power(r_min, 4) * snr_lin )/ (pt_lin * gt_lin * gr_lin * lamb**2)
    return rcs

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
        self.sel_resume = {"RCS":[], "H0":[], "RANGE_H0":[],"MIN_RANGE_H":[],"MIN_RANGE_PT":[],
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
            df_enu.to_csv(dir_name +"/" + "obj-" + str(pos.satellite.satnum) + "-" + ttxt + "TU.trn",
                            index=False, header=[str(len(df_enu.index)-1),'1000','1'],float_format="%.3f")

            df_data = pd.DataFrame(np.concatenate((
                            time_arr.value.reshape(len(time_arr),1), pos.enu[i], pos.az_el_r[i],
                            pos.itrs[i], pos.geodetic[i]), axis=1), columns=[ 'Time',
                            'ENU_E','ENU_N','ENU_U', 'AZIMUTH','ELEVATION','RANGE',
                            'ITRS_X','ITRS_Y','ITRS_Z','lat','lon','HEIGHT'])
            df_data.to_csv(dir_name + "/" + "data-" + str(pos.satellite.satnum) + "-" + ttxt + "TU.csv", index=False)

            enu_d = 0.001*pos.az_el_r[i][:,2]
            min_index = np.argmin(enu_d)
            min_d = enu_d[min_index]

            self.sel_orbital_elem.append(orbital_elem) 
            if pos.satellite.satnum in rcs['NORAD_CAT_ID']:
                self.sel_resume["RCS"].append(rcs['RCS'][rcs['NORAD_CAT_ID'].index(pos.satellite.satnum)])
            else:
                self.sel_resume["RCS"].append(0.0)
            self.sel_resume["H0"].append(time_arr[0].value)
            self.sel_resume["RANGE_H0"].append(enu_d[0])
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

    st.set_page_config(
    page_title="Orbit Tracking",
    page_icon="🌏", # "🤖",  # "🧊",
    # https://raw.githubusercontent.com/omnidan/node-emoji/master/lib/emoji.json
    layout="wide",
    initial_sidebar_state="expanded",
    # menu_items={
    #     'Get Help': 'https://www.extremelycoolapp.com/help',
    #     'Report a bug': "https://www.extremelycoolapp.com/bug",
    #     'About': "# This is a header. This is an *extremely* cool app!"
    # }
    )

    if "stc_loged" not in st.session_state:
        st.session_state.stc_loged = False
    
    if "d_max" not in st.session_state:
        st.session_state.d_max = 1100

    path_files = tempfile.gettempdir() + '/top_tmp*'
    txt_files = glob.glob(path_files)
    files_count = len(txt_files)

    if "date_time" not in st.session_state:
        date_time = datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
        st.session_state.date_time = date_time

    if "ss_dir_name" not in st.session_state:
        dir_name = tempfile.gettempdir()+"/top_tmp_"+ date_time
        st.session_state.ss_dir_name = dir_name 

        if files_count > 100:
            for py_file in txt_files:
                #print('dell file: ' + py_file)
                st.write('dell files :', files_count)
                try:
                    if os.path.isfile(py_file):
                        os.remove(py_file)
                    else:
                        shutil.rmtree(py_file)
                except OSError as e:
                    st.write('Error: ', e.strerror)

            path_files = tempfile.gettempdir() + '/top_tmp*'
            txt_files = glob.glob(path_files)
            files_count = len(txt_files) 

        # if os.path.exists(st.session_state.ss_dir_name) == False:
        #     os.mkdir(st.session_state.ss_dir_name)     

    st.subheader('**Satellite orbit propagation and trajectory generation, for optical and radar tracking of space objects (Debris, Rocket Body, Satellites...), especially for low Earth orbit (LEO) objects.**')
    st.markdown('Using SGP4 this app searches for a point of approach of a space object in Earth orbit and traces a trajectory interval in: local plane reference (ENU), AltAzRange, ITRS and Geodetic, to be used as a target for optical or radar tracking system')
    st.markdown('by: Francisval Guedes Soares, Email: francisvalg@gmail.com')
    
    # st.write('dir name: ',st.session_state.ss_dir_name)
    st.write('tmp folder count: ', files_count)
    # for line in txt_files:
    #     st.markdown(line)

    if "ss_elem_df" not in st.session_state:
        # log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Upload the orbital elements</p>'
        # st.markdown(log_error, unsafe_allow_html=True)
        st.info('Upload the orbital elements', icon="ℹ️")
        
    else:
        st.subheader('Orbital Elements loaded')
    #    st.dataframe(st.session_state["ss_elem_df"])

    if "lc_df" not in st.session_state:
        st.session_state["lc_df"] = pd.read_csv('data/confLocalWGS84.csv')

    st.sidebar.subheader("Settings:")
    st.subheader("Settings:")

    # Select sample time
    sample_time = st.sidebar.number_input('Sampling rate (s):', 0.1, 10.0, 1.0, step = 0.1)
    st.write('Sampling rate (s): ', sample_time)

    # Select sensor location or record another location
    help=('Select sensor location or record another location above') 
    lc_expander = st.sidebar.expander("Add new sensor location in the WGS84", expanded=False)
    lc_name = lc_expander.text_input('Name',"my location")
    latitude = lc_expander.number_input('Latitude',-90.0, 90.0, 0.0, format="%.6f")
    longitude = lc_expander.number_input('longitude', -180.0, 80.0, 0.0, format="%.6f")
    heigth = lc_expander.number_input('heigth (m)',-1000.0, 2000.0, 0.0, format="%.6f")

    lc_df = st.session_state["lc_df"]  

    if lc_expander.button("Gravar nova localização"):
        lc_add = {'name': [lc_name], 'lat': [latitude], 'lon': [longitude], 'height': [heigth] }
        if lc_name not in lc_df['name'].to_list():
            if (lc_add['name'][0]) and (bool(re.match('^[A-Za-z0-9_-]*$',lc_add['name'][0]))==True):
                lc_df = pd.concat([lc_df, pd.DataFrame(lc_add)], axis=0)
                lc_df.to_csv('data/confLocalWGS84.csv', index=False)
                st.session_state["lc_df"]=lc_df
                lc_expander.write('Recorded location')
            else:
                lc_expander.write('write a name without special characters')
        else:
            lc_expander.write('location already exists')
    
    st.sidebar.selectbox("Sensor location in the WGS84:",lc_df['name'], key="choice_lc", help=help)
    for sel in lc_df['name']:
        if sel==st.session_state["choice_lc"]:
            lc = lc_df.loc[lc_df['name'] == sel].to_dict('records')[0]
            st.session_state["ss_lc"] = lc

    # lc_expander = st.sidebar.expander("Sensor location in the WGS84 Geodetic", expanded=True)
    # lc = { "lat":0, "lon":0,"height":0} 
    # lc['lat'] = lc_expander.number_input('Latitude (deg)',-90.0, 90.0,value=-5.919510, format="%.6f")
    # lc['lon'] = lc_expander.number_input('Longitude (deg)', -180.0, 80.0, value=-35.173500, format="%.6f")
    # lc['height'] = lc_expander.number_input('Height (m)',-1000.0, 2000.0,value= 58.954, format="%.6f")
    
    st.write('Sensor location in the WGS84 Geodetic ')
    st.write('Latitude: ', lc['lat'])
    st.write('Longitude: ', lc['lon'] )
    st.write('Height: ', lc['height'])

    # Seleção do modo de obtenção das trajetórias
    automatico="Auto search H0"
    manual="Upload H0 file"

    help=(automatico + ' (D-2 or earlier): fetches approach periods, returns trajectories and configuration files.  \n'
    + manual +' (D-1 to D): recalculates trajectories with updated orbital elements, keeping the H0, using the configuration files obtained in a previous automatic calculate')
    menu = [automatico,manual]
    choice = st.sidebar.selectbox("Trajectory search mode:",menu, help=help, key="mode" )

    max_time = TimeDelta(10*u.d)
    max_num_obj = 5000

    if choice == automatico:
        st.sidebar.subheader("Automatic:")
        dmax = st.sidebar.number_input('Maximum distance to trajectory limits (Km)',
            min_value = 400,
            max_value = 10000,
            value = 1100,
            step = 50)
        st.session_state.d_max = dmax

        st.write('Maximum distance to trajectory limits (Km): ', dmax)

        dmin = st.sidebar.number_input('The minimum distance that the trajectory must reach in order to be accepted (Km)',
            min_value = 200,
            max_value = 5000,
            value = 1000,
            step = 50)

        st.write('The minimum trajectory distance point from which the trajectory is saved (Km): ', dmin)
        if not dmax>1.05*dmin:
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">The maximum distance must be greater than the minimum distance in 1.05x</p>'
            st.sidebar.markdown(log_error, unsafe_allow_html=True)

        st.sidebar.write('Start and end time for H0 search TU:')
        col1, col2 = st.sidebar.columns(2)
        initial_date = col1.date_input("Start date", key=1)
        initial_time = col2.time_input("Start time", time(11, 0),  key=2)
        initial_datetime=Time(datetime.combine(initial_date, initial_time))
        initial_datetime.format = 'isot'
        st.write('Search start time: ', initial_datetime)

        final_date = col1.date_input("End date", key=3)
        final_time = col2.time_input("End time", time(19, 0),  key=4)
        final_datetime=Time(datetime.combine(final_date, final_time))
        final_datetime.format = 'isot'
        st.write('Search end time: ', final_datetime)         
        
        if  (final_datetime - initial_datetime)> max_time:            
            time_norm = 0
            final_datetime = initial_datetime + max_time 
            st.warning('Maximum time delta: ' + str(max_time) + ' days', icon="⚠️")
            # log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Maximum time delta: ' + str(max_time) + ' days </p>'
            # st.markdown(log_error, unsafe_allow_html=True)            
        else:  
            time_norm = (max_time - (final_datetime - initial_datetime))/max_time
    
    elif choice == manual:
        st.sidebar.subheader("Manual:")
        time_norm = 1
        help='Manual config file upload from H0: traj_data.csv file from a previous auto run or edited from it'
        data_conf = st.sidebar.file_uploader("Upload configuração manual de H0 (traj_data.csv)",type=['csv'],help=help)
        if data_conf is not None:
            file_details = {"Filename":data_conf.name,"FileType":data_conf.type,"FileSize":data_conf.size}
            st.write(file_details)
            usecols = ['NORAD_CAT_ID', 'H0', 'END_PT']
            df_conf = pd.read_csv(data_conf,usecols=usecols)
            st.dataframe(df_conf)
    
    max_num_obj = np.round(1 + max_num_obj*time_norm)
    st.info('Maximum number of objects to propagate: ' + str(max_num_obj) + ', for time delta '+ str(final_datetime - initial_datetime) + ' days',icon="ℹ️")

    st.sidebar.subheader("Calculate trajectories:")
    st.subheader('Outputs:')    
    
    if st.sidebar.button("Run propagation"):
        if "ss_elem_df" not in st.session_state:
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Upload the orbital elements</p>'
            st.markdown(log_error, unsafe_allow_html=True)
        elif len(st.session_state["ss_elem_df"].index)>max_num_obj:
            st.warning('Maximum number of objects to propagate: ' + str(max_num_obj) + ', for time delta '+ str(final_datetime - initial_datetime) + ' days', icon="⚠️")
            # log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Maximum number of objects to propagate: ' + str(max_num_obj) + ', for time delta '+ str(final_datetime - initial_datetime) + ' days </p>'
            # st.markdown(log_error, unsafe_allow_html=True)
        elif 'MEAN_MOTION' not in st.session_state["ss_elem_df"].columns.to_list():
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Columns do not match OMM format</p>'
            st.markdown(log_error, unsafe_allow_html=True)
        else:
            st.write('Number of objects: ', len(st.session_state["ss_elem_df"].index))

            #orbital_elem = st.session_state["ss_elem_df"].drop_duplicates(subset=['NORAD_CAT_ID']).to_dict('records')
            orbital_elem = st.session_state["ss_elem_df"].to_dict('records')

            rcs = pd.read_csv('data/RCS.csv').to_dict('list')
        
        date_time = datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
        st.session_state.date_time = date_time
        dir_name = tempfile.gettempdir()+"/top_tmp_"+ date_time
        st.session_state.ss_dir_name = dir_name 

        if os.path.exists(st.session_state.ss_dir_name) == False:
            os.mkdir(st.session_state.ss_dir_name)          

            ini = tm.time()    

            st.write('Progress bar:')
            my_bar = st.progress(0)

            sdf = SummarizeDataFiles()
            if st.session_state["mode"] == automatico:                          
                for index in range(len(orbital_elem)):
                    propag = PropagInit(orbital_elem[index], lc, sample_time) 
                    pos = propag.search2h0(initial_datetime, final_datetime, dmax*1000, dmin*1000)
                    sdf.save_trajectories(pos,orbital_elem[index],st.session_state.ss_dir_name,rcs)
                    my_bar.progress((index+1)/len(orbital_elem))
            elif st.session_state["mode"] == manual:
                for index, row in df_conf.iterrows():
                    orbital_elem_row = next(x for x in orbital_elem if x["NORAD_CAT_ID"] == row['NORAD_CAT_ID'])
                    propag = PropagInit(orbital_elem_row, lc, sample_time) 
                    pos = propag.traj_calc(Time(row['H0'], format='isot'),row['END_PT'])
                    sdf.save_trajectories(pos,orbital_elem_row,st.session_state.ss_dir_name,rcs)
                    my_bar.progress((index+1)/len(df_conf.index))                     
           
            df_orb = pd.DataFrame(sdf.sel_orbital_elem)
            obj_aprox = len(df_orb.index)
            st.write('Number of calculated trajectories: ', obj_aprox)


            if obj_aprox > 0:
                df_orb.to_csv(st.session_state.ss_dir_name + "/"+ st.session_state.date_time[0:19] +"_orbital_elem.csv", index=False)

                col_first = ['EPOCH', 'CREATION_DATE', 'DECAY_DATE']
                df_orb = columns_first(df_orb, col_first )

                df_traj = pd.DataFrame(sdf.sel_resume)
                df_traj = df_traj.join(df_orb)

                df_traj['RCS_MIN'] = rcs_min(1000*df_traj['MIN_RANGE'])

                col_first = ['NORAD_CAT_ID','OBJECT_NAME', 'RCS_MIN', 'RCS_SIZE']
                df_traj = columns_first(df_traj, col_first )

                df_traj = df_traj.sort_values(by=['H0'], ascending=True)
                df_traj = df_traj.reset_index(drop=True)

                df_traj.to_csv(st.session_state.ss_dir_name + "/"+ st.session_state.date_time[0:19] +"_traj_summary.csv", index=False)
                st.write('Approaching the reference point: ', len(df_traj.index ))
                #st.dataframe(df_traj)

                st.session_state.ss_result_df = df_traj
            else:
                if "ss_result_df" in st.session_state:
                    del st.session_state.ss_result_df

            fim = tm.time()
            st.write("Processing time (s): ", fim - ini)
        
    st.subheader('Files:')     
    if "ss_result_df" not in st.session_state:
        st.markdown('Run propagation for get files')
    else:               
        shutil.make_archive(st.session_state.ss_dir_name, 'zip', st.session_state.ss_dir_name)
        with open(st.session_state.ss_dir_name + ".zip", "rb") as fp:
            btn = st.download_button(
                label="Download",
                data=fp,
                file_name="results_"+ lc['name'] + '_' + st.session_state.date_time +".zip",
                mime="application/zip"
            )

    st.sidebar.write('Files can be downloaded on the right side')

    st.write('The resulting files contain:')
    st.write('orbital_elem.csv - Orbital elements of selected objects')
    st.write('traj_data.csv - Relevant trajectory and object data')
    st.write('*.trn files - Trajectory from H0, in the ENU reference system')
    st.write('data *.csv files - Trajectory from H0, in local plane reference (ENU), AltAzRange, ITRS and Geodetic, including times')



        
if __name__== '__main__':
    main()
import streamlit as st
import pandas as pd

from datetime import datetime
from datetime import time

import shutil
from astropy.time import Time

import os
import tempfile
import numpy as np

from lib.orbit_functions import  PropagInit

from spacetrack import SpaceTrackClient
from io import StringIO

# ----------------------------------------------------------------------
# Atualiza a ultima versão dos elementos orbitais no site do Space-Track
# ----------------------------------------------------------------------
def update_elements(norad_ids, loguin, password):
    stc = SpaceTrackClient(identity=loguin, password=password)    
    try:
        stc.authenticate()
    except:
        log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Space-Track Loguin Error</p>'
        st.markdown(log_error, unsafe_allow_html=True)
        print('space-track loguin error')
        return False
    tlevec_csv = stc.gp(norad_cat_id=norad_ids, orderby='norad_cat_id', format='csv')
    elem_df = pd.read_csv(StringIO(tlevec_csv), sep=",")
    st.session_state.ss_elem_df = elem_df
    return  True

def get_orbital_element():
    # Seleção do modo de atualização dos elementos orbitais  
    st.sidebar.title("Orbital elements:")
    # expander = st.sidebar.expander("Orbital elements:", expanded=True)
    help=('Space-Track: Obtains orbital elements automatically from Space-Track (requires registration in Space-Track))  \n'
        'Elements file: Load elements file from another source or manually obtained from Space-Track (TLE, 3LE ou JSON).')

    menuUpdate = ["Celestrak", "Space-Track","Orbital Elements File"]
    choiceUpdate = st.sidebar.selectbox("Source of orbital elements:",menuUpdate,help=help)
    if choiceUpdate == "Celestrak":
        norad_id = st.sidebar.number_input('Unique NORAD_CAT_ID', 0, 999999,value= 25544, format="%d")
        elem_df = pd.read_csv('https://celestrak.org/NORAD/elements/gp.php?CATNR='+ str(norad_id) +'&FORMAT=csv')
        st.session_state.ss_elem_df = elem_df
        st.markdown('Orbital elements obtained from Celestrak:')

    elif choiceUpdate == "Space-Track":
        SpaceTrackLoguin = st.sidebar.text_input('User name Space-Track:')
        if SpaceTrackLoguin=="":
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Load the login Space-Track</p>'
            st.sidebar.markdown(log_error, unsafe_allow_html=True)       
        SpaceTracksenha = st.sidebar.text_input('Space-Track password:',type="password")

        st.sidebar.markdown("List of NORAD_CAT_ID to propagate:")
        help='Text file with .csv extension with a single column with the numbers NORAD_CAT_ID and with the text NORAD_CAT_ID in the first line, if not loaded, a standard list will be used'
        data_norad = st.sidebar.file_uploader("Use APP's default NORAD_CAT_ID list or load NORAD_CAT_ID list:", type=['csv'], help=help)
    
        if st.sidebar.button("Get Orbital Elements"):
            if data_norad is not None:
                st.markdown('NORAD_CAT_ID file loaded:')
                file_details = {"Filename":data_norad.name,"FileType":data_norad.type,"FileSize":data_norad.size}
                st.write(file_details)
                df_norad_ids = pd.read_csv(data_norad) 
            else:
                st.markdown("NORAD_CAT_ID file not loaded")
                df_norad_ids = pd.read_csv("data/norad_id.csv")
            
            st.dataframe(df_norad_ids)
            max_num_norad = 650 
            if len(df_norad_ids.index)<max_num_norad:
                if update_elements(df_norad_ids.to_dict('list')["NORAD_CAT_ID"],SpaceTrackLoguin,SpaceTracksenha):
                    st.markdown('Orbital elements obtained from Space-Track:')
            else:                
                log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Maximum number of objects: ' + str(max_num_norad) + ' , please load orbital elements manually</p>'
                st.markdown(log_error, unsafe_allow_html=True)               

    elif choiceUpdate == "Orbital Elements File":
        data_elements = st.sidebar.file_uploader("Upload orbital elements Json/csv",type=['csv','json'])
        if st.sidebar.button("Upload orbital elements"):
            if data_elements is not None:
                file_details = {"Filename":data_elements.name,"FileType":data_elements.type,"FileSize":data_elements.size}
                st.write(file_details)
                st.markdown("Orbital elements manually updated:")    
                if data_elements.type == "application/json":
                    st.session_state.ss_elem_df = pd.read_json(data_elements)

                elif data_elements.type == "text/csv":
                    st.session_state.ss_elem_df = pd.read_csv(data_elements)


# ----------------------------------------------------------------------
# Salva as trajetórias
# ----------------------------------------------------------------------
class SummarizeDataFiles:
    def __init__(self):
        self.sel_orbital_elem = []
        self.sel_resume = { "H0":[], "RANGE_H0":[],"MIN_RANGE_H":[],"MIN_RANGE_PT":[],
                    "MIN_RANGE":[],"END_H":[], "END_PT":[], "END_RANGE":[],"RCS":[] }

    def save_trajectories(self,pos,orbital_elem,dir_name,rcs): 
        for i in range(0, len(pos.time_array)):
            time_arr = pos.time_array[i]
            
            ttxt = time_arr[0].strftime('%Y_%m_%d-H0-%H_%M_%S')

            df_enu = pd.DataFrame(pos.enu[i])
            df_enu.to_csv(dir_name +"/" + "obj-" + str(pos.satellite.satnum) + "-" + ttxt + "TU.trn",
                            index=False, header=['1',str(len(df_enu.index)),'1'],float_format="%.3f")

            df_data = pd.DataFrame(np.concatenate((
                            time_arr.value.reshape(len(time_arr),1), pos.enu[i], pos.az_el_r[i],
                            pos.itrs[i], pos.geodetic[i]), axis=1), columns=[ 'Time',
                            'ENU_E(m)','ENU_N(m)','ENU_U(m)', 'AZ(deg)','ELEV(deg)','RANGE(m)',
                            'ITRS_X(km)','ITRS_Y(km)','ITRS_Z(km)','LON(deg)','LAT(deg)','HEIGHT(km)'])
            df_data.to_csv(dir_name + "/" + "data-" + str(pos.satellite.satnum) + "-" + ttxt + "TU.csv", index=False)

            enu_d = pos.az_el_r[i][:,2]
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


def main(): 
    st.title("OPTEAS - Orbit Propagator for Tracking Earth's Artificial Satellites")
    st.subheader('**Satellite orbit propagation and trajectory generation, for optical and radar tracking of space objects (Debris, Rocket Body, Satellites...)**')
    st.markdown('Using SGP4 this app searches for a point of approach of a space object in Earth orbit and traces a trajectory interval in: local plane reference (ENU), AltAzRange, ITRS and Geodetic, to be used as a target for optical or radar tracking system')
    st.markdown('by: Francisval Guedes Soares, Email: francisvalg@gmail.com')
    st.subheader('**Saídas:**')

    get_orbital_element()
    if "ss_elem_df" not in st.session_state:
        log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Upload the orbital elements</p>'
        st.markdown(log_error, unsafe_allow_html=True)
    else:
        elem_df = st.session_state["ss_elem_df"]
        st.dataframe(elem_df)

    st.sidebar.title("Settings:")

    # Seleção do tempo de amostragem
    sample_time = st.sidebar.number_input('Sampling rate (s):', 0.1, 10.0, 1.0, step = 0.1)
    st.write('Sampling rate (s): ', sample_time)

    st.write('Reference point location: ')
    lc = { "lat":0, "lon":0,"height":0} 
    lc['lat'] = st.sidebar.number_input('Latitude',-90.0, 90.0,value=-5.919178, format="%.6f")
    lc['lon'] = st.sidebar.number_input('Longitude', -180.0, 80.0, value=-35.173372, format="%.6f")
    lc['height'] = st.sidebar.number_input('Altitude (m)',-1000.0, 2000.0,value= 55.0, format="%.6f")

    st.write('Latitude: ', lc['lat'])
    st.write('Longitude: ', lc['lon'] )
    st.write('Altitude: ', lc['height'])

    # Seleção do modo de obtenção das trajetórias
    automatico="Automatic"
    manual="Manual"

    help='Automatic (D-2 or earlier): fetches approach periods, returns trajectories and configuration files. \n Manual (D-1 to D): recalculates trajectories with updated orbital elements, keeping the H0, using the configuration files obtained in a previous autorun'
    menu = [automatico,manual]
    choice = st.sidebar.selectbox("Trajectory search mode:",menu, help=help, key="mode" )

    if choice == automatico:
        st.sidebar.subheader("Automatic:")
        dmax = st.sidebar.number_input('Maximum distance to trajectory limits (Km)',
            min_value = 400,
            max_value = 10000,
            value = 1100,
            step = 50)

        st.write('Maximum distance to trajectory limits (Km): ', dmax)

        dmin = st.sidebar.number_input('The minimum trajectory distance point from which the trajectory is saved (Km)',
            min_value = 200,
            max_value = 5000,
            value = 1000,
            step = 50)

        st.write('The minimum trajectory distance point from which the trajectory is saved (Km): ', dmin)

        st.sidebar.write('Start and end time for H0 search TU:')
        col1, col2 = st.sidebar.columns(2)
        initial_date = col1.date_input("Start date", key=1)
        initial_time = col2.time_input("Start time", time(11, 0,0),  key=2)
        initial_datetime=Time(datetime.combine(initial_date, initial_time))
        initial_datetime.format = 'isot'
        st.write('Search start time: ', initial_datetime)

        final_date = col1.date_input("End date", key=3)
        final_time = col2.time_input("End time", time(19, 0,0),  key=4)
        final_datetime=Time(datetime.combine(final_date, final_time))
        final_datetime.format = 'isot'
        st.write('Search end time: ', final_datetime)     
    
    elif choice == manual:
        st.sidebar.subheader("Manual:")
        help='Manual config file upload from H0: traj_data.csv file from a previous auto run or edited from it'
        data_conf = st.sidebar.file_uploader("Upload configuração manual de H0 (traj_data.csv)",type=['csv'],help=help)
        if data_conf is not None:
            file_details = {"Filename":data_conf.name,"FileType":data_conf.type,"FileSize":data_conf.size}
            st.write(file_details)
            usecols = ['NORAD_CAT_ID', 'H0', 'N_PT']
            df_conf = pd.read_csv(data_conf,usecols=usecols)
            st.dataframe(df_conf)

    
    st.sidebar.title("Calculate trajectories:")

    max_num_obj = 5000
    if st.sidebar.button("Run propagation"):
        if "ss_elem_df" not in st.session_state:
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Upload the orbital elements</p>'
            st.markdown(log_error, unsafe_allow_html=True)
        elif len(st.session_state["ss_elem_df"].index)>max_num_obj:
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Maximum number of objects: ' + str(max_num_obj) + ' </p>'
            st.markdown(log_error, unsafe_allow_html=True)
        else:
            st.write('Number of objects: ', len(st.session_state["ss_elem_df"].index))

            orbital_elem = st.session_state["ss_elem_df"].drop_duplicates(subset=['NORAD_CAT_ID']).to_dict('records')

            rcs = pd.read_csv('data/RCS.csv').to_dict('list')

            date_time = datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
            dir_name = tempfile.gettempdir()+"/optr_temp_"+ date_time
            os.mkdir(dir_name)          

            st.write('Progress bar:')
            my_bar = st.progress(0)

            sdf = SummarizeDataFiles() 
            mode = st.session_state["mode"]

            if mode == automatico:                          
                for index in range(len(orbital_elem)):
                    propag = PropagInit(orbital_elem[index], lc, sample_time) 
                    pos = propag.search2h0(initial_datetime, final_datetime, dmax*1000, dmin*1000)
                    sdf.save_trajectories(pos,orbital_elem[index],dir_name,rcs)
                    my_bar.progress((index+1)/len(orbital_elem))
            elif mode == manual:
                for index, row in df_conf.iterrows():
                    orbital_elem_row = next(x for x in orbital_elem if x["NORAD_CAT_ID"] == row['NORAD_CAT_ID'])
                    propag = PropagInit(orbital_elem_row, lc, sample_time) 
                    pos = propag.traj_calc(Time(row['H0'], format='isot'),row['N_PT'])
                    sdf.save_trajectories(pos,orbital_elem_row,dir_name,rcs)
                    my_bar.progress((index+1)/len(df_conf.index))                     
           
            df_orb = pd.DataFrame(sdf.sel_orbital_elem)
            df_orb.to_csv(dir_name + "/"+ date_time[0:19] +"_orbital_elem.csv", index=False)

            df_traj = pd.DataFrame(sdf.sel_resume)
            df_traj = df_traj.join(df_orb)

            col_list = df_traj.columns.to_list()
            col_first = ['NORAD_CAT_ID','OBJECT_NAME']
            for line in col_first: col_list.remove(line)
            col_first.extend(col_list)
            df_traj = df_traj.reindex(columns=col_first)

            df_traj.to_csv(dir_name + "/"+ date_time[0:19] +"_traj_summary.csv", index=False)
            st.write('Objects approaching the reference point:')
            st.dataframe(df_traj)

            st.subheader('Files:')       
            shutil.make_archive(dir_name, 'zip', dir_name)

            with open(dir_name + ".zip", "rb") as fp:
                btn = st.download_button(
                    label="Download",
                    data=fp,
                    file_name="results_"+ date_time[0:19] +".zip",
                    mime="application/zip"
                )

    st.sidebar.write('Files can be downloaded on the right side')

    st.write('The resulting files contain:')
    st.write('orbital_elem.csv - Orbital elements of selected objects')
    st.write('traj_data.csv - Relevant trajectory and object data')
    st.write('*.trn files - Trajectory from H0, in the ENU reference system')
    st.write('*.txt files - Trajectory from H0, in the ENU reference system, including distance and times for analysis')

    
    # txt_files = glob.glob(tempfile.gettempdir() + '/*/')
    # for line in txt_files:
    #     st.markdown(line)

if __name__== '__main__':
    main()
"""
Creator: Francisval Guedes Soares
Date: 2021
"""

import streamlit as st
import pandas as pd

from datetime import datetime

import os
import tempfile

from spacetrack import SpaceTrackClient
import spacetrack.operators as op
from io import StringIO


class SpaceTrackClientInit(SpaceTrackClient):
    def __init__(self,identity,password):
        """initialize the class.

        Args:
        https://www.space-track.org/auth/login
        identity (str): login space-track.
        password (str): password space-track.

        Returns:

        """
        super().__init__(identity, password)

    def ss(self):
        """authenticate.

        Returns: True or False
        """
        try:
            self.authenticate()
        except:
            # print('space-track loguin error')
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">space-track loguin error</p>'
            st.markdown(log_error, unsafe_allow_html=True)
            return False
        return  True
    def get_by_norad(self, norad_ids):
        """get the orbital elements from NORAD_CAT_IDs.

        Args:
        norad_ids (list of int): NORAD_CAT_IDs

        Returns:         
        pandas DataFrame: OMM format
        """
        elements_csv = self.gp(norad_cat_id=norad_ids, orderby='norad_cat_id', format='csv')
        elem_df = pd.read_csv(StringIO(elements_csv), sep=",")
        st.write('Updated Orbital Element File:')
        st.session_state.ss_elem_df = elem_df
        return elem_df
    def get_select(self):
        """get the orbital elements from specified filter.

           Selection of 3000+ objects by Space-Track API mean_motion>11.25 (LEO orbit),
           decay_date = null-val (no reentry), rcs_size = Large (greater than 1m),
           periapsis < 700km, epoch = >now-1 (updated until a day ago), orderby= EPOCH desc

        Returns:         
        pandas DataFrame: OMM format
        """
        elements_csv = self.gp(mean_motion = op.greater_than(11.25),
                    decay_date = 'null-val',
                    rcs_size = 'Large',
                    periapsis = op.less_than(700),
                    epoch = '>now-1', 
                    orderby= 'EPOCH desc',
                    format='csv')
        elem_df = pd.read_csv(StringIO(elements_csv), sep=",")
        st.write('Updated Orbital Element File:')
        st.session_state.ss_elem_df = elem_df
        return elem_df
    

def get_orbital_element():
    """Streamlite interface to choose a way to get the orbital elements """
    # Seleção do modo de atualização dos elementos orbitais  
    st.sidebar.subheader("Orbital elements:")
    help=('Celestrack: Gets an orbital element in OMM .csv format, from the NORAD_CAT_ID informed  \n'
        'Space-Track: Gets several orbital elements .csv format, automatically from Space-Track (requires registration)  \n'
        'Orbital elements file: Load elements file manually in OMM .csv format (.csv or .json).')
    
    MENU_UPDATE1="Celestrak"
    MENU_UPDATE2="Space-Track"
    MENU_UPDATE3="Orbital Elements File"
    menuUpdate = [MENU_UPDATE1, MENU_UPDATE2,MENU_UPDATE3]
    # if "choiceUpdate" not in st.session_state:
    #     st.session_state.choiceUpdate = MENU_UPDATE1
    st.sidebar.selectbox("Source of orbital elements:",menuUpdate, key="choiceUpdate", help=help)  

    if st.session_state["choiceUpdate"] == MENU_UPDATE1:
        norad_id = st.sidebar.number_input('Unique NORAD_CAT_ID', 0, 999999,value= 25544, format="%d")

        current_day = datetime.utcnow().strftime('%Y_%m_%d_')
        celet_fil_n = 'data/celestrak/' + current_day + str(norad_id) + '.csv'

        if os.path.exists(celet_fil_n) == False:
            urlCelestrak = 'https://celestrak.org/NORAD/elements/gp.php?CATNR='+ str(norad_id) +'&FORMAT=csv'
            try:
                elem_df = pd.read_csv(urlCelestrak) 
                if 'MEAN_MOTION' in elem_df.columns.to_list():
                    elem_df.to_csv(celet_fil_n, index=False)                     
                else:
                    log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;"> No orbital elements for this object in Celestrat </p>'
                    st.markdown(log_error, unsafe_allow_html=True)
                    elem_df = pd.read_csv('data/oe_celestrac.csv')

            except OSError as e:
                # print(f"Error acess Celestrac") 
                log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Too much access to Celestrak wait 2h or use Space-Track or load orbital elements manually</p>'
                st.markdown(log_error, unsafe_allow_html=True)
                elem_df = pd.read_csv('data/oe_celestrac.csv')

        else:
            elem_df = pd.read_csv(celet_fil_n)
            st.write('Orbital elements obtained from Celestrak:')

        st.session_state.ss_elem_df = elem_df        
        st.write('Updated Orbital Element File:')

    elif st.session_state["choiceUpdate"] == MENU_UPDATE2:   
         
        link = '[See the link of Space-Track API](https://www.space-track.org/documentation#/api)'
        st.markdown(link, unsafe_allow_html=True)
        # Form to Space-Track loguin 
        form = st.sidebar.form("my_form")
        stc_log = form.text_input('User name Space-Track:')    
        stc_ss = form.text_input('Space-Track password:',type="password") 
        fcol1, fcol2 = form.columns(2)
        submitted = fcol1.form_submit_button("Submit")
        if submitted:
            stc = SpaceTrackClientInit(stc_log, stc_ss)
            st.session_state.stc_loged = stc.ss()
            st.session_state.stc = stc
            if st.session_state.stc_loged:          
                #del st.session_state.ss_elem_df
                st.write("ok")
            else: 
                log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Error when logging in</p>'
                st.markdown(log_error, unsafe_allow_html=True)
        if st.session_state.stc_loged:
            fcol2.write("Status: Logged")
        else:  fcol2.write("Status: Unlogged")

        MENU_STC1 = "App's list 200+ NORAD_CAT_ID"
        MENU_STC2 = "App's selection 3000+ NORAD_CAT_ID"
        MENU_STC3 = "Personalized NORAD_CAT_ID file"
        menu_stc = [MENU_STC1, MENU_STC2, MENU_STC3]
        help_stc=(MENU_STC1 + ': local list of 200+ selected LEO objects most with RCS value  \n' 
        + MENU_STC2 + ': Selection of 3000+ objects by Space-Track API mean_motion>11.25, decay_date = null-val, rcs_size = Large, periapsis<700, epoch = >now-1, orderby= EPOCH desc \n'
        + MENU_STC3 + ': Upload any .csv file that contains a NORAD_CAT_ID column with up to 650 desired objects ')

        # if "choice_stc" not in st.session_state:
        #     st.session_state.choice_stc = MENU_STC1
        st.sidebar.selectbox("Choice of orbital elements dataset:",menu_stc, key="choice_stc", help=help_stc)
                
        if st.session_state["choice_stc"] == MENU_STC3:            
            st.write("Personalized NORAD_CAT_ID file")
            help='Text file with .csv extension with a column with the header "NORAD_CAT_ID" and lines NORAD_CAT_ID numbers'
            data_norad = st.sidebar.file_uploader("Upload personalized NORAD_CAT_ID list file:", type=['csv'], help=help)

        get_oe_bt = st.sidebar.button("Get Orbital Elements")
        if get_oe_bt and st.session_state.stc_loged:
            if st.session_state["choice_stc"] == MENU_STC1:
                st.write("App's list +200 LEO NORAD_CAT_ID") 
                df_norad_ids = pd.read_csv("data/norad_id.csv")
                st.write('NORAD_CAT_ID file uploaded for update:')
                st.dataframe(df_norad_ids)
                st.session_state.stc.get_by_norad(df_norad_ids.to_dict('list')["NORAD_CAT_ID"])                 
                      
            if st.session_state["choice_stc"] == MENU_STC2:
                st.write("App's selection +3000 LEO NORAD_CAT_ID")
                link = '[Link used to obtain the LEO orbital elements](https://www.space-track.org/basicspacedata/query/class/gp/MEAN_MOTION/%3E11.25/DECAY_DATE/null-val/RCS_SIZE/Large/PERIAPSIS/%3C700/orderby/EPOCH%20desc/format/csv)'
                st.markdown(link, unsafe_allow_html=True)
                st.session_state.stc.get_select()

            if st.session_state["choice_stc"] == MENU_STC3:            
                if (data_norad is not None):
                    st.write('NORAD_CAT_ID file loaded:')
                    file_details = {"Filename":data_norad.name,"FileType":data_norad.type,"FileSize":data_norad.size}
                    st.write('File details:')
                    st.write(file_details)
                    df_norad_ids = pd.read_csv(data_norad)
                    st.write('NORAD_CAT_ID file uploaded for update:')
                    st.dataframe(df_norad_ids)

                    max_num_norad = 650
                    if len(df_norad_ids.index)<max_num_norad:
                        st.session_state.stc.get_by_norad(df_norad_ids.to_dict('list')["NORAD_CAT_ID"])
                else:
                    st.write("NORAD_CAT_ID file not loaded")
        elif  get_oe_bt and not st.session_state.stc_loged:
            log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">log in to Space-Track</p>'
            st.sidebar.markdown(log_error, unsafe_allow_html=True)           

    elif st.session_state["choiceUpdate"] == MENU_UPDATE3:
        data_elements = st.sidebar.file_uploader("Upload orbital elements Json/csv",type=['csv','json'])
        if st.sidebar.button("Upload orbital elements"):
            if data_elements is not None:
                st.write("File details:")
                file_details = {"Filename":data_elements.name,"FileType":data_elements.type,"FileSize":data_elements.size}
                st.write(file_details)
                st.write("Orbital elements manually updated:")    
                if data_elements.type == "application/json":
                    st.session_state.ss_elem_df = pd.read_json(data_elements)
                elif data_elements.type == "text/csv":
                    st.session_state.ss_elem_df = pd.read_csv(data_elements)

st.title("Get the orbital elements of the satellite")
st.subheader('**Get satellite orbital elements from Celestrack website individually or Space-track allows multiple.**')

if "date_time" not in st.session_state:
    date_time = datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
    st.session_state.date_time = date_time

if "ss_dir_name" not in st.session_state:
    dir_name = tempfile.gettempdir()+"/top_tmp_"+ st.session_state.date_time
    st.session_state.ss_dir_name = dir_name 

if os.path.exists(st.session_state.ss_dir_name) == False:
    os.mkdir(st.session_state.ss_dir_name)

if "stc_loged" not in st.session_state:
    st.session_state.stc_loged = False

get_orbital_element()

if "ss_elem_df" not in st.session_state:
    log_error = '<p style="font-family:sans-serif; color:Red; font-size: 16px;">Upload the orbital elements</p>'
    st.markdown(log_error, unsafe_allow_html=True)
else:        
    elem_df = st.session_state["ss_elem_df"]
    st.dataframe(elem_df)
    elem_df.to_csv(st.session_state.ss_dir_name + "/"+ st.session_state.date_time[0:19] +"_orbital_elem_all.csv", index=False)

    with open(st.session_state.ss_dir_name + "/"+ st.session_state.date_time[0:19] +"_orbital_elem_all.csv", "rb") as fp:
        btn = st.download_button(
            label="Download",
            data=fp,
            file_name="all_orbital_elem" + st.session_state.date_time +".csv",
            mime="application/txt"
        )


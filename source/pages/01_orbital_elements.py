"""
Creator: Francisval Guedes Soares
Date: 2021
"""

import streamlit as st
import pandas as pd

from datetime import datetime
import datetime as dt

import os
import tempfile

from spacetrack import SpaceTrackClient
import spacetrack.operators as op
from io import StringIO

from lib.pages_functions import  SpaceTrackClientInit
from lib.constants import  ConstantsNamespace

def dell_elem_df():
    if 'ss_elem_df' in st.session_state:
        del st.session_state.ss_elem_df

def get_orbital_element():
    """Streamlite interface to choose a way to get the orbital elements """
    # Seleção do modo de atualização dos elementos orbitais  
    st.sidebar.subheader("Orbital elements:")
    st.subheader("*Orbital elements:*")
    help=('Celestrack: Gets an orbital element in OMM .csv format, from the NORAD_CAT_ID informed  \n'
        'Space-Track: Gets several orbital elements .csv format, automatically from Space-Track (requires registration)  \n'
        'Orbital elements file: Load elements file manually in OMM .csv format (.csv or .json).')    

    menuUpdate = [MENU_UPDATE1, MENU_UPDATE2,MENU_UPDATE3]
    # if "choiceUpdate" not in st.session_state:
    #     st.session_state.choiceUpdate = MENU_UPDATE1
    st.sidebar.selectbox("Source of orbital elements:",menuUpdate, key="choiceUpdate", help=help, on_change=dell_elem_df)  

    if st.session_state["choiceUpdate"] == MENU_UPDATE1:
        norad_id = st.sidebar.number_input('Unique NORAD_CAT_ID', 0, 999999,value= 25544, format="%d")

        current_day = datetime.utcnow().strftime('%Y_%m_%d_')
        celet_fil_n = 'data/celestrak/' + current_day + str(norad_id) + '.csv'
        if st.sidebar.button('Get orbital element'):
            if not os.path.exists(celet_fil_n):                
                urlCelestrak = 'https://celestrak.org/NORAD/elements/gp.php?CATNR='+ str(norad_id) +'&FORMAT=csv'
                try:
                    elem_df = pd.read_csv(urlCelestrak) 
                    if 'MEAN_MOTION' in elem_df.columns.to_list():
                        elem_df.to_csv(celet_fil_n, index=False)                     
                    else:
                        st.error('No orbital elements for this object in Celestrac', icon= cn.ERROR)
                        st.stop()
                        # elem_df = pd.read_csv('data/oe_celestrac.csv')

                except OSError as e:
                    # print(f"Error acess Celestrac") 
                    st.error('Too much access to Celestrak wait 2h or use Space-Track or load orbital elements manually', icon=cn.ERROR)
                    # elem_df = pd.read_csv('data/oe_celestrac.csv')
                    st.stop()
            else:
                elem_df = pd.read_csv(celet_fil_n)
                st.write('Orbital elements obtained from Celestrak:')

            st.session_state.ss_elem_df = elem_df        

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
                st.success('Space-track logued', icon=cn.SUCCESS)
            else: 
                st.error('Error when logging Space-Track', icon=cn.ERROR)
                
        if st.session_state.stc_loged:
            fcol2.success("logged")
        else:  fcol2.error("unlogged")

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
                # st.dataframe(df_norad_ids)
                df_norad_ids=df_norad_ids.drop_duplicates(subset=['NORAD_CAT_ID'])
                st.session_state.df_norad_ids = df_norad_ids
                st.session_state.ss_elem_df = st.session_state.stc.get_by_norad(df_norad_ids.to_dict('list')["NORAD_CAT_ID"])                 
                      
            if st.session_state["choice_stc"] == MENU_STC2:
                st.write("App's selection +3000 LEO NORAD_CAT_ID")
                link = '[Link used to obtain the LEO orbital elements](https://www.space-track.org/basicspacedata/query/class/gp/MEAN_MOTION/%3E11.25/DECAY_DATE/null-val/RCS_SIZE/Large/PERIAPSIS/%3C500/orderby/EPOCH%20desc/format/csv)'
                st.markdown(link, unsafe_allow_html=True)
                st.session_state.ss_elem_df = st.session_state.stc.get_select()

            if st.session_state["choice_stc"] == MENU_STC3:            
                if (data_norad is not None):
                    st.write('NORAD_CAT_ID file loaded:')
                    file_details = {"Filename":data_norad.name,"FileType":data_norad.type,"FileSize":data_norad.size}
                    st.write('File details:')
                    st.write(file_details)                    
                    df_norad_ids = pd.read_csv(data_norad)
                    st.write('NORAD_CAT_ID file uploaded for update:')
                    # st.dataframe(df_norad_ids)
                    df_norad_ids=df_norad_ids.drop_duplicates(subset=['NORAD_CAT_ID'])                    
                    
                    if len(df_norad_ids.index)<max_num_norad:
                        st.session_state.df_norad_ids = df_norad_ids
                        st.session_state.ss_elem_df = st.session_state.stc.get_by_norad(df_norad_ids.to_dict('list')["NORAD_CAT_ID"])
                    else:
                        st.warning('max norad_cat_id = '+ str(max_num_norad), icon=cn.WARNING)
                        st.stop()
                else:
                    st.write("NORAD_CAT_ID file not loaded")

            if 'ss_elem_df' in st.session_state:
                st.session_state.ss_elem_df.to_csv(st.session_state.ss_dir_name + "/" + "orbital_elem_all.txt", index=False)
            else:
                st.warning('get orbital elements', icon=cn.WARNING)

        elif  (get_oe_bt and not st.session_state.stc_loged):
            st.info('log in to Space-Track to continue', icon=cn.INFO)

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

            if 'ss_elem_df' in st.session_state:
                st.session_state.ss_elem_df.to_csv(st.session_state.ss_dir_name + "/" + "orbital_elem_all.txt", index=False)
            else:
                st.warning('get orbital elements', icon= cn.WARNING)

MENU_UPDATE1="Celestrak"
MENU_UPDATE2="Space-Track"
MENU_UPDATE3="Orbital Elements File"

MENU_STC1 = "App's list 200+ NORAD_CAT_ID"
MENU_STC2 = "App's selection 3000+ NORAD_CAT_ID"
MENU_STC3 = "Personalized NORAD_CAT_ID file"

max_num_norad = 650
cn = ConstantsNamespace()

def main(): 

    st.set_page_config(
    page_title="Get orbital elements",
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

    st.title("Get the orbital elements of the satellite")
    st.subheader('**Get satellite orbital elements: Celestrack - individually, or Space-track - allows multiple.**')

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
    else:
        if st.session_state.stc_loged:   
            st.success('Logged into spacetrack', icon=cn.SUCCESS)

    get_orbital_element()    

    if "df_norad_ids" in st.session_state:        
        #st.info("Load orbital elements", icon=cn.INFO )
        if ("ss_elem_df" in st.session_state and st.session_state["choiceUpdate"] == MENU_UPDATE2):
            df_norad_ids = st.session_state.df_norad_ids
            not_foud = df_norad_ids[~df_norad_ids['NORAD_CAT_ID'].isin(st.session_state.ss_elem_df['NORAD_CAT_ID'].tolist())]
            elem_decay =  st.session_state.ss_elem_df[~st.session_state.ss_elem_df['DECAY_DATE'].isna()][['NORAD_CAT_ID']]

            col1, col2, col3 = st.columns(3)
            col1.info('Orbital elements requested from Space-Track: '+ str(df_norad_ids.shape[0]), icon=cn.INFO)
            col1.dataframe(df_norad_ids)
            col2.warning('Orbital elements not found on Space-Track (now-3days): '+ str(not_foud.shape[0]), icon=cn.WARNING)
            col2.dataframe(not_foud)
            col3.warning('decayed object: '+ str(elem_decay.shape[0]), icon=cn.WARNING)
            col3.dataframe(elem_decay)

    if "ss_elem_df" not in st.session_state:
        st.info("Load orbital elements", icon=cn.INFO )
    else:
        st.success("Orbital elements loaded", icon=cn.SUCCESS )        
        elem_df = st.session_state["ss_elem_df"]
        st.dataframe(elem_df)        

        if os.path.exists(st.session_state.ss_dir_name + "/"+ "orbital_elem_all.txt"):        
            st.write('Download Orbital Element Files:')
            with open(st.session_state.ss_dir_name + "/"+ "orbital_elem_all.txt", "rb") as fp:
                btn = st.download_button(
                    label="Download",
                    data=fp,
                    file_name="orbital_elem_all.csv",
                    mime="application/txt"
                )

        # else:
        #     st.warning('for download orbital elements use space-track',icon=cn.WARNING )
        st.info('For trajectory generation go to the next page', icon=cn.INFO)
    

if __name__== '__main__':
    main()

"""
Creator: Francisval Guedes Soares
Date: 2021
"""

import streamlit as st
import pandas as pd

from datetime import datetime, timezone

import datetime as dt


import os
import tempfile
import json

from spacetrack import SpaceTrackClient
import spacetrack.operators as op
from io import StringIO

from lib.pages_functions import  *
from lib.constants import  ConstantsNamespace


st.set_page_config(page_title="Get orbital elements",
                    page_icon="🌏", layout="wide", initial_sidebar_state="auto",
                    menu_items=menu_itens())
# https://raw.githubusercontent.com/omnidan/node-emoji/master/lib/emoji.json

# apenas para tradução
domain_name = os.path.basename(__file__).split('.')[0]
_ = gettext_translate(domain_name)

celestrak="Celestrak"
space_track="Space-Track"
upload_oe_file="Orbital Elements File"

menuUpdate = [space_track, celestrak, upload_oe_file]

local_norad_list = "App's list 200+ NORAD_CAT_ID"
local_norad_filter_selection = "App's selection 700 + LEO, Large NORAD_CAT_ID"
upload_norad_list = "Personalized list NORAD_CAT_ID"

MAX_NUM_NORAD = 650
cn = ConstantsNamespace()


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

def dell_elem_df():
    if 'ss_elem_df' in st.session_state:
        del st.session_state.ss_elem_df

def get_orbital_element():
    """Streamlite interface to choose a way to get the orbital elements """
    # Seleção do modo de atualização dos elementos orbitais  
    st.subheader(_("*Orbital elements:*"))
    help = (_('Celestrack: Gets an orbital element in OMM .csv format, from the NORAD_CAT_ID informed'
          'Space-Track: Gets several orbital elements .csv format, automatically from Space-Track'
          '(requires registration) Orbital elements file: Load elements file manually in OMM .csv'
          'format (.csv or .json).'))

    # if "choiceUpdate" not in st.session_state:
    #     st.session_state.choiceUpdate = celestrak
    st.selectbox(_("Source of orbital elements:"),menuUpdate, key="choiceUpdate", help=help, on_change=dell_elem_df)  

    if st.session_state["choiceUpdate"] == celestrak:
        norad_id = st.number_input(_('Unique NORAD_CAT_ID'), 0, 999999,value= 25544, format="%d")

        current_day = datetime.now(timezone.utc).strftime('%Y_%m_%d_')
        celet_fil_n = 'data/celestrak/' + current_day + str(norad_id) + '.csv'
        if st.button(_('Get orbital element')):
            if not os.path.exists(celet_fil_n):                
                urlCelestrak = 'https://celestrak.org/NORAD/elements/gp.php?CATNR='+ str(norad_id) +'&FORMAT=csv'
                try:
                    elem_df = pd.read_csv(urlCelestrak) 
                    if 'MEAN_MOTION' in elem_df.columns.to_list():
                        elem_df.to_csv(celet_fil_n, index=False)                     
                    else:
                        st.error(_('No orbital elements for this object in Celestrac'), icon= cn.ERROR)
                        st.stop()
                        # elem_df = pd.read_csv('data/oe_celestrac.csv')

                except OSError as e:
                    # print(f"Error acess Celestrac") 
                    st.error(_('Celestrak error, use Space-Track or load orbital elements manually'), icon=cn.ERROR)
                    # elem_df = pd.read_csv('data/oe_celestrac.csv')
                    st.stop()
            else:
                elem_df = pd.read_csv(celet_fil_n)
                st.write(_('Orbital elements obtained from Celestrak:'))

            st.session_state.ss_elem_df = elem_df        

    elif st.session_state["choiceUpdate"] == space_track:   
         
        link = '[See the link of Space-Track API](https://www.space-track.org/documentation#/api)'
        st.markdown(link, unsafe_allow_html=True)
        # Form to Space-Track loguin 
        form = st.form("my_form")
        form.write(_("This App does not record user passwords, but we cannot guarantee the"
                     " confidentiality of the password. DO NOT use the password of other online"
                     " services in the Space-Track API, use at your own risk."))
        stc_log = form.text_input(_('User name Space-Track:') )  
        stc_ss = form.text_input(_('Space-Track password:'),type="password") 
        fcol1, fcol2 = form.columns(2)
        submitted = fcol1.form_submit_button(_("Submit"))
        if submitted:
            with open("conf.json", "r") as file:
                config = json.load(file)
            stc = SpaceTrackClientInit(stc_log, stc_ss, config)
            st.session_state.stc_loged = stc.ss()
            st.session_state.stc = stc
            if st.session_state.stc_loged:          
                st.success(_('Space-track logged'), icon=cn.SUCCESS)
            else: 
                st.error(_('Error when logging Space-Track'), icon=cn.ERROR)
                
        if st.session_state.stc_loged:
            fcol2.success(_("logged"))
        else:  fcol2.error(_("unlogged"))

        menu_stc = [local_norad_list, upload_norad_list, local_norad_filter_selection]
        help_stc=local_norad_list + _(': local list of 200+ selected LEO objects most with RCS'
        'value \n')+local_norad_filter_selection + _(':Selection of 700+ objects by Space-Track'
        'API mean_motion>11.25, decay_date = null-val, rcs_size = Large, periapsis<500,'
        ' epoch = >now-1, orderby= EPOCH desc) \n') + upload_norad_list + _(': Upload any .csv'
        ' file that contains a NORAD_CAT_ID column with up to 650 desired objects ')

        # if "choice_stc" not in st.session_state:
        #     st.session_state.choice_stc = local_norad_list
        st.selectbox(_("Choice of orbital elements dataset:"),menu_stc, key="choice_stc", help=help_stc)
                
        if st.session_state["choice_stc"] == upload_norad_list:            
            st.write(_("Personalized NORAD_CAT_ID file"))
            help= _('Text file with .csv extension with a column with the header "NORAD_CAT_ID" and lines NORAD_CAT_ID numbers')
            data_norad = st.file_uploader(_("Upload personalized NORAD_CAT_ID list file:"), type=['csv'], help=help)
            st.markdown(_('Select the epoch range (less than 10 days)'))

        if (st.session_state["choice_stc"] == upload_norad_list) or (st.session_state["choice_stc"] == local_norad_list): 
            oe_col1, oe_col2 = st.columns(2)
            oe_epoch_init = oe_col1.date_input(_("Epoch start"),value=datetime.now(timezone.utc) - dt.timedelta(days=4))
            oe_epoch_end = oe_col2.date_input(_("Epoch end (now+1day)"), value=datetime.now(timezone.utc) + dt.timedelta(days=1))
            if  (oe_epoch_end - oe_epoch_init) < dt.timedelta(days=0.01):
                st.error(_('End must be after start date'), icon=cn.ERROR)
                st.stop()
            elif  (oe_epoch_end - oe_epoch_init) > dt.timedelta(days=10):
                st.error(_('Epoch interval must be less than 10 days'), icon=cn.ERROR)
                st.stop()

        get_oe_bt = st.button(_("Get Orbital Elements"))
        if get_oe_bt and st.session_state.stc_loged:
            if st.session_state["choice_stc"] == local_norad_list:
                st.write(_("App's list +200 LEO NORAD_CAT_ID"))
                df_norad_ids = pd.read_csv("data/norad_id.csv")
                st.write(_('NORAD_CAT_ID file uploaded for update:'))
                # st.dataframe(df_norad_ids)
                df_norad_ids=df_norad_ids.drop_duplicates(subset=['NORAD_CAT_ID'])
                st.session_state.df_norad_ids = df_norad_ids

                st.session_state.ss_elem_df, epoch = st.session_state.stc.get_by_norad(df_norad_ids.to_dict('list')["NORAD_CAT_ID"],
                                                                                        oe_epoch_init, oe_epoch_end)
                st.info(_('Orbital elements epoch ')+ epoch, icon= cn.INFO)


            if st.session_state["choice_stc"] == local_norad_filter_selection:
                st.write(_("App's selection +700 LEO, Large, PERIAPSIS < 500, NORAD_CAT_ID"))
                link = '[Link used to obtain the LEO orbital elements](https://www.space-track.org/basicspacedata/query/class/gp/MEAN_MOTION/%3E11.25/DECAY_DATE/null-val/RCS_SIZE/Large/PERIAPSIS/%3C500/orderby/EPOCH%20desc/format/csv)'
                st.markdown(link, unsafe_allow_html=True)
                st.session_state.ss_elem_df = st.session_state.stc.get_select()

            if st.session_state["choice_stc"] == upload_norad_list:            
                if (data_norad is not None):
                    st.write(_('NORAD_CAT_ID file loaded:'))
                    file_details = {"Filename":data_norad.name,"FileType":data_norad.type,"FileSize":data_norad.size}
                    st.write(_('File details:'))
                    st.write(file_details)                    
                    df_norad_ids = pd.read_csv(data_norad)
                    if 'NORAD_CAT_ID' not in df_norad_ids.columns:
                        st.error(_('load csv file with a column named NORAD_CAT_ID'), icon=cn.ERROR)
                        st.stop()
                    st.write(_('NORAD_CAT_ID file uploaded for update:'))
                    # st.dataframe(df_norad_ids)
                    df_norad_ids=df_norad_ids.drop_duplicates(subset=['NORAD_CAT_ID'])                    
                    
                    if len(df_norad_ids.index)<MAX_NUM_NORAD:
                        st.session_state.df_norad_ids = df_norad_ids
                        st.session_state.ss_elem_df, epoch = st.session_state.stc.get_by_norad(df_norad_ids.to_dict('list')["NORAD_CAT_ID"],
                                                                                               oe_epoch_init, oe_epoch_end)
                        st.info(_('Orbital elements epoch ')+ epoch, icon= cn.INFO)
                    else:
                        st.warning(_('max norad_cat_id = ')+ str(MAX_NUM_NORAD), icon=cn.WARNING)
                        st.stop()
                else:
                    st.write(_("NORAD_CAT_ID file not loaded"))



        elif  (get_oe_bt and not st.session_state.stc_loged):
            st.info(_('log in to Space-Track to continue'), icon=cn.INFO)

    elif st.session_state["choiceUpdate"] == upload_oe_file:
        data_elements = st.file_uploader(_("Upload orbital elements Json/csv"), type=['csv', 'json'])
        if st.button(_("Upload orbital elements")):
            if data_elements is not None:
                st.write(_("File details:"))
                file_details = {"Filename": data_elements.name, "FileType": data_elements.type, "FileSize": data_elements.size}
                st.write(file_details)
                st.write(_("Orbital elements manually updated:"))    
                if data_elements.type == "application/json":
                    st.session_state.ss_elem_df = pd.read_json(data_elements)
                elif data_elements.type == "text/csv":
                    st.session_state.ss_elem_df = pd.read_csv(data_elements)


def main(): 
    page_links(insidebar=True)

    st.subheader(_("Get the orbital elements of the satellite"))
    st.markdown(_('Get satellite orbital elements: Celestrack - individually, or Space-track - allows multiple.'))

    if "date_time" not in st.session_state:
        date_time = datetime.now(timezone.utc).strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
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
            st.success(_('Logged into spacetrack'), icon=cn.SUCCESS)

    get_orbital_element()    

    if "df_norad_ids" in st.session_state:        
        #st.info("Load orbital elements", icon=cn.INFO )
        if ("ss_elem_df" in st.session_state and st.session_state["choiceUpdate"] == space_track):
            df_norad_ids = st.session_state.df_norad_ids
            not_foud = df_norad_ids[~df_norad_ids['NORAD_CAT_ID'].isin(st.session_state.ss_elem_df['NORAD_CAT_ID'].tolist())]
            elem_decay = st.session_state.ss_elem_df[~st.session_state.ss_elem_df.get("DECAY_DATE", pd.NA).isna()][["NORAD_CAT_ID"]]

            col1, col2, col3 = st.columns(3)
            col1.info(_('Orbital elements requested from Space-Track: ')+ str(df_norad_ids.shape[0]), icon=cn.INFO)
            col1.dataframe(df_norad_ids.style.format(thousands=""))
            col2.warning(_('Orbital elements not found on Space-Track (in the epoch range): ')+ str(not_foud.shape[0]), icon=cn.WARNING)
            col2.dataframe(not_foud.style.format(thousands=""))
            col3.warning(_('decayed object: ')+ str(elem_decay.shape[0]), icon=cn.WARNING)
            col3.dataframe(elem_decay.style.format(thousands=""))

    if "ss_elem_df" not in st.session_state:
        st.warning(_("Load orbital elements"), icon=cn.WARNING )
    else:
        st.success(_("Orbital elements loaded"), icon=cn.SUCCESS )
        st.session_state.ss_elem_df.sort_values(['NORAD_CAT_ID', 'EPOCH'], ascending=[False, False] ,inplace=True )
        st.session_state.ss_elem_df = st.session_state.ss_elem_df.reset_index(drop=True)     
        elem_df = st.session_state["ss_elem_df"]
        st.dataframe(elem_df.style.format(thousands=""))
        st.session_state.ss_elem_df.to_csv(st.session_state.ss_dir_name + "/" + "orbital_elem_all.txt", index=False)       

        if os.path.exists(st.session_state.ss_dir_name + "/"+ "orbital_elem_all.txt"):        
            st.write(_('Download Orbital Element Files:'))
            with open(st.session_state.ss_dir_name + "/"+ "orbital_elem_all.txt", "rb") as fp:
                btn = st.download_button(
                    label="Download",
                    data=fp,
                    file_name="orbital_elem_all.csv",
                    mime="application/txt"
                )

        st.info(_('For trajectory generation go to the next page'), icon=cn.INFO)
    
    page_links()
    

if __name__== '__main__':
    main()

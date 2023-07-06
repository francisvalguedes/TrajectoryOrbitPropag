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

from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode, ColumnsAutoSizeMode
from st_aggrid.grid_options_builder import GridOptionsBuilder



cn = ConstantsNamespace()
MAX_NUM_OBJ = 30
FILE_NAME_SEL_CSV = 'selected.csv'

# Analisa as possibilidades de rastreio
def highlight_rows(row):
    teste_rcs = row.loc['RCS']
    teste_rcs_min = row.loc['RCS_MIN']
    teste_range_pt = row.loc['MIN_RANGE_PT']
    teste_range = row.loc['MIN_RANGE']
    teste_decay = row.loc['DECAY_DATE']
    color = '#FF4500'
    amarelo = '#ffda6a'
    verde = '#75b798'
    vermelho = '#ea868f'
    azul = '#6ea8fe'

    #TESTA SE EXISTE A COLUNA RCS_SIZE
    if 'RCS_SIZE' in row :
        teste_rcs_size = row.loc['RCS_SIZE']
    else :
        teste_rcs_size = 'none'

    if teste_rcs > 0:  #TESTA O TAMANHO DO RCS
        if teste_rcs_min <= teste_rcs*1.16:
            color = verde
        else:
            color = vermelho
    else:              # TESTA A CLASSIFICAÇÃO DO RCS
        if teste_rcs_size == 'MEDIUM':
            if teste_range > 500: #422.88 é o valor mínimo teorico
                color = vermelho
            else:
                color = amarelo
        elif teste_rcs_size == 'LARGE':
            color = azul
        else:
            if teste_range > 300: #237.8 é o valor mínimo teorico
                color = vermelho
            else:
                color = verde
    
    if teste_range_pt < 90:  # TESTA O NÚMERO MÍNIMO DE PONTOS
        color = vermelho

    x=teste_decay  # TESTA SE O OBJETO JA SAIU DE ORBITA
    s_nan = str(x)
    if s_nan != "nan" : 
        color = vermelho

    return ['background-color: {}'.format(color) for r in row]

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
    buf = dir_name +"/trn100Hz/100Hz_" + "obj-" + str(pos.satellite.satnum) + "-" + ttxt + "TU.trn"

    np.savetxt(buf,pos.enu[0],fmt='%.3f',delimiter=",", header=str(time_s), comments='')

def dellfiles(file):
    py_files = glob.glob(file)
    err = 0
    for py_file in py_files:
        try:
            os.remove(py_file)
        except OSError as e:
            err = e.strerror
    return err

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

    if not os.path.exists(st.session_state.ss_dir_name):
        os.mkdir(st.session_state.ss_dir_name)

    if not os.path.exists(st.session_state.ss_dir_name +"/trn100Hz"):
        os.mkdir(st.session_state.ss_dir_name +"/trn100Hz")

    st.subheader('Generate specific trajectories for the sensor:')

    if "ss_result_df" not in st.session_state:
        st.info('Run propagation for trajectory generation',   icon=cn.INFO)
        st.stop()

    lc = st.session_state["ss_lc"]
    st.write('Selected Sensor location: ', lc['name'])

    # st.subheader('All:')
    # st.dataframe(st.session_state.ss_result_df.loc[:, st.session_state.ss_result_df.columns!= 'RCS_MIN'])

    st.subheader('Data summary:')                 
    st.write('Approaching the reference point: ', len(st.session_state.ss_result_df.index))

    # ************************************************************
    # FILE_NAME_XLSX = st.session_state["ss_lc"]['name']+"_traj_summary.xlsx"

    # #Mudança feita por André para colorir a linha
    # df_traj = st.session_state.ss_result_df.style.apply(highlight_rows, axis=1) 
    # with pd.ExcelWriter(st.session_state.ss_dir_name + "/"+ FILE_NAME_XLSX) as writer:
    #     df_traj.to_excel(writer, sheet_name='Sheet 1', engine='openpyxl')

    # st.dataframe(df_traj)

    # if os.path.isfile(st.session_state.ss_dir_name + "/"+ FILE_NAME_XLSX):
    #     st.write('Download highlight File:')
    #     with open(st.session_state.ss_dir_name + "/"+ FILE_NAME_XLSX, "rb") as fp:
    #         btn = st.download_button(
    #             label="Download",
    #             data=fp,
    #             file_name=FILE_NAME_XLSX,
    #             mime="application/txt"
    #         )

    # ************************************************************

    st.subheader('Selection:')

    # AgGrid
    # ************************************************************
    # gb = GridOptionsBuilder.from_dataframe(st.session_state.ss_result_df)
    # # gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
    # gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    # gb.configure_column(st.session_state.ss_result_df.columns[0], headerCheckboxSelection=True)
    # # gb.configure_side_bar()
    # gridoptions = gb.build()

    # grid_table = AgGrid(
    #                     st.session_state.ss_result_df,
    #                     # height=250,
    #                     gridOptions=gridoptions,
    #                     columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS, # SELECTION_CHANGED, MANUAL
    #                     # enable_enterprise_modules=True,
    #                     update_mode=GridUpdateMode.GRID_CHANGED,
    #                     theme='streamlit',
    #                     editable=True,
    #                     # data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    #                     # fit_columns_on_grid_load=False,
    #                     # header_checkbox_selection_filtered_only=True,
    #                   )  
   
    # st.subheader('Selected:') 

    # selected_row = grid_table["selected_rows"]
    # selected_row = pd.DataFrame(selected_row)
    # st.write('selected lines')
    # st.dataframe(selected_row.loc[:, selected_row.columns!= '_selectedRowNodeInfo'])

    # ************************************************************
    # Select Line st.data_editor
    # ************************************************************
    st.write('All objects')
    st.session_state.ss_df_ed = st.session_state.ss_result_df.copy(deep=True)
    CHEC_COL_NAME = "SELECTION"
    if CHEC_COL_NAME not in st.session_state.ss_df_ed.columns:
        st.session_state.ss_df_ed.insert(loc=0, column=CHEC_COL_NAME, value=st.session_state.ss_df_ed['NORAD_CAT_ID']>0)
    
    if len(st.session_state.ss_df_ed.index)>MAX_NUM_OBJ: 
        st.session_state.ss_df_ed[CHEC_COL_NAME]= st.session_state.ss_df_ed['NORAD_CAT_ID']<0
    else:
        st.session_state.ss_df_ed[CHEC_COL_NAME]= st.session_state.ss_df_ed['NORAD_CAT_ID']>0


    # edited_df = st.session_state.ss_df_ed
    # tr_col1, tr_col2 = st.columns(2)

    # if tr_col1.button('Clear All'):
    #     st.session_state.ss_df_ed[CHEC_COL_NAME]= st.session_state.ss_df_ed['NORAD_CAT_ID']<0        
    # if tr_col2.button('Select All'):
    #     st.session_state.ss_df_ed[CHEC_COL_NAME]= st.session_state.ss_df_ed['NORAD_CAT_ID']>0
    # edited_df[CHEC_COL_NAME]=st.session_state.ss_df_ed[CHEC_COL_NAME]

    df_col = st.session_state.ss_df_ed.columns.tolist()
    df_col.remove(CHEC_COL_NAME)

    edited_df = st.data_editor(
                    st.session_state.ss_df_ed,
                    column_config={
                        CHEC_COL_NAME: st.column_config.CheckboxColumn(
                            CHEC_COL_NAME,
                            help="Select trajetories",
                            disabled=False, 
                            default=False,
                        )
                        },
                    disabled=df_col,
                    hide_index=False,
                    )
    
    # st.write('Selected objects')
    selected_row=edited_df[edited_df[CHEC_COL_NAME]]

    selected_row=selected_row.loc[:,selected_row.columns!= CHEC_COL_NAME]
    # st.dataframe(selected_row)
    # ************************************************************
    st.write('Calculate trajectories of selected objects:')
    if st.button('Calculate 100Hz trajectories'): 

        if len(selected_row.index)>MAX_NUM_OBJ:
            st.info('Maximum number of objects to propagate: ' + str(MAX_NUM_OBJ) ,icon=cn.INFO)
            st.stop()
        elif len(selected_row.index)==0:
            st.info('Select objects to propagate' ,icon=cn.INFO)
            st.stop()

        dellfiles(st.session_state.ss_dir_name +"/trn100Hz/*.trn")

        ini = tm.time()    

        st.write('Progress bar:')
        my_bar = st.progress(0)

        orbital_elem = selected_row.to_dict('records')
        sample_time = 0.01

        # automatico:                          
        for index in range(len(orbital_elem)):
            propag = PropagInit(orbital_elem[index], lc, sample_time)
            pos = propag.traj_calc(Time(orbital_elem[index]['H0']), round(orbital_elem[index]['END_PT']/sample_time) )
            save_trajectories(pos,st.session_state.ss_dir_name, orbital_elem[index]['END_PT'])
            my_bar.progress((index+1)/len(orbital_elem))
            
        fim = tm.time()
        st.write("Processing time (s): ", fim - ini)
        
    st.write('Download trajetory files *.trn - from H0, in the ENU:')

    dir_name = st.session_state.ss_dir_name + '/trn100Hz'
    if os.path.exists(dir_name):       
        shutil.make_archive(dir_name, 'zip', dir_name)
        with open(dir_name + ".zip", "rb") as fp:
            btn = st.download_button(
                label="Download",
                data=fp,
                file_name="trn100Hz_"+ lc['name'] + '_' + st.session_state.date_time +".zip",
                mime="application/zip"
            )

    # Select Colunm
    # ************************************************************
    st.subheader('Data summary format and column selection:')

    col1s, col2s = st.columns(2)

    columns = col1s.multiselect("Manual selection of desired columns:",selected_row.columns)
    filter = col1s.radio("Choose by:", ("exclusion", "inclusion"))

    if filter == "exclusion":
        columns = [col for col in selected_row.columns if col not in columns]

    selected_row_col = selected_row[columns]
    col_no_comma = 'NORAD_CAT_ID'

    mask_file = col2s.file_uploader('Column selection by config file upload:',type=['csv'])
    if mask_file is not None:
        col2s.write("File details:")
        file_details = {"Filename":mask_file.name,"FileType":mask_file.type,"FileSize":mask_file.size}
        col2s.write(file_details)
        if mask_file.type == "text/csv":
            mask_df = pd.read_csv(mask_file)
            col2s.dataframe(mask_df)
            col_mask_list = mask_df.columns.tolist()
            for col in col_mask_list:
                if col not in selected_row.columns:
                    st.error('Error: dataframe does not have column:' + col, icon=cn.ERROR )
                    st.stop()

            mask_dic = mask_df.to_dict('records')
            df_sel1 = selected_row[col_mask_list]            
            selected_row_col = df_sel1.rename(columns=mask_dic[0], inplace=False)
            col_no_comma = mask_dic[0]['NORAD_CAT_ID']

    st.write('Selected columns and rows from the data summary:')
    # selected_row_col.loc[:, "NORAD_CAT_ID"] = selected_row_col["NORAD_CAT_ID"].map('{:d}'.format)
    st.dataframe(selected_row_col,
                 column_config={
                     col_no_comma:st.column_config.NumberColumn(
                                        col_no_comma,
                                         format='%d',
                                         )
                 }                 
                 )

    st.write('Save dataframe with selected columns and rows:')
    if st.button('Save Selection'): 
        selected_row[columns].to_csv(st.session_state.ss_dir_name + "/"+ FILE_NAME_SEL_CSV,
                            index=False)

    if os.path.isfile(st.session_state.ss_dir_name + "/"+ FILE_NAME_SEL_CSV):
        st.write('Download selected File:')
        with open(st.session_state.ss_dir_name + "/"+ FILE_NAME_SEL_CSV, "rb") as fp:
            btn = st.download_button(
                label="Download",
                data=fp,
                file_name=FILE_NAME_SEL_CSV,
                mime="application/txt"
            )
    # ************************************************************

if __name__== '__main__':
    main()
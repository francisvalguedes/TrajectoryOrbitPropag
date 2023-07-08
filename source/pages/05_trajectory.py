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

@st.cache_data
def df_atrib(df):
    return df.copy(deep=True)

def save_selected_data(sel_data):
    sel_data = sel_data.round({'RCS':3, 'RCS_MIN':3, 'RANGE_H0':3, 'MIN_RANGE':3,'END_RANGE':3})
    sel_data.to_csv(st.session_state.ss_dir_name + "/"+ FILE_NAME_SEL_CSV,
                                index=False)


def columns_first(df, col_first):
    col_list = df.columns.to_list()
    for line in col_first:
        if line in col_list: col_list.remove(line)
        else: col_first.remove(line)
    col_first.extend(col_list)
    df = df.reindex(columns=col_first)
    return df

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

    if "radar_df" not in st.session_state:
        st.session_state["radar_df"] = pd.read_csv('data/confRadar.csv')

    st.subheader('Generate specific trajectories for the sensor:')

    
    # **********************************************************
    # Select radar sensor or record another radar sensor
    help=('Select radar sensor configuration or record another above') 
    sensor_exp = st.sidebar.expander("Add new radar sensor", expanded=False)
    sensor_name = sensor_exp.text_input('Radar Name',"my radar")

    pt = sensor_exp.number_input('radar power (db)',0.0, 100.0, 60.0, format="%.1f")    
    gt = sensor_exp.number_input('radar transmit gain (db)',0.0, 100.0, 42.0, format="%.1f")
    gr = sensor_exp.number_input('radar receive gain (db)',0.0, 100.0, 42.0, format="%.1f")
    lt = sensor_exp.number_input('radar transmit loss (db)',0.0, 50.0, 1.5, format="%.1f")
    lr = sensor_exp.number_input('radar receive loss (db)',0.0, 50.0, 1.5, format="%.1f")
    fhz = sensor_exp.number_input('radar frequence (MHz)',500.0,10000.0, 5400.0, format="%.1f")
    sr = sensor_exp.number_input('radar receiver sensitivity (db)',-300.0,-1.0, -142.0, format="%.1f")
    snr = sensor_exp.number_input('radar signal noise ratio (db)',0.0,20.0, 0.0, format="%.1f")
    sample_time = sensor_exp.number_input('sample time (s)',0.01,1.0, 0.01, format="%.2f")

    radar_df = st.session_state.radar_df

    if sensor_exp.button("Record new radar sensor"):
        sensor_add = {'name': [sensor_name], 'pt': [pt], 'gt': [gt], 'gr': [gr], 'lt': [lt],
                       'lr': [lr], 'fhz': [fhz], 'sr': [sr], 'snr': [snr], 'spt': [sample_time] }
        if sensor_name not in radar_df['name'].to_list():
            if (sensor_add['name'][0]) and (bool(re.match('^[A-Za-z0-9_-]*$',sensor_add['name'][0]))==True):
                radar_df = pd.concat([radar_df, pd.DataFrame(sensor_add)], axis=0)
                radar_df.to_csv('data/confRadar.csv', index=False)
                st.session_state["radar_df"]=radar_df
                sensor_exp.write('Recorded location')
            else:
                sensor_exp.write('write a name without special characters')
        else:
            sensor_exp.write('location already exists')
    
    st.sidebar.selectbox("Radar sensor settings:",radar_df['name'], key="choice_lc", help=help)
    for sel in radar_df['name']:
        if sel==st.session_state["choice_lc"]:
            radar_sel = radar_df.loc[radar_df['name'] == sel].to_dict('records')[0]
            st.session_state["ss_radar_sel"] = radar_sel

    # **********************************************************
    
    if "traj_flag" not in st.session_state:
        st.info('Run propagation for trajectory generation',   icon=cn.INFO)
        st.stop()      
        
    lc = st.session_state["ss_lc"]
    st.info('Selected Sensor location - propagation page: '+ lc['name'], icon=cn.INFO)
               
    st.write('Propagation result, approaching the reference point: ', len(st.session_state.ss_result_df.index))


    st.subheader('Data analysis: RCS_MIN and table coloring:') 


    result_df_ch = st.session_state.ss_result_df.copy(deep=True)

    result_df_ch['RCS_MIN'] = rcs_min(1000*result_df_ch['MIN_RANGE'],
                                      radar_sel['pt'],
                                      radar_sel['gt'],radar_sel['gr'],
                                      radar_sel['lt'],radar_sel['lr'], 
                                      radar_sel['fhz'],radar_sel['sr'],
                                      radar_sel['snr']
                                      )

    col_first = ['NORAD_CAT_ID','OBJECT_NAME', 'RCS_MIN', 'RCS_SIZE']
    result_df_ch = columns_first(result_df_ch, col_first )


    CHEC_COL_NAME = "SELECTION"
    if CHEC_COL_NAME not in result_df_ch.columns:
        result_df_ch.insert(loc=0, column=CHEC_COL_NAME, value=True)
    
    if len(result_df_ch.index)>MAX_NUM_OBJ: 
        result_df_ch[CHEC_COL_NAME]= False
    else:
        result_df_ch[CHEC_COL_NAME]= True

    df_col = result_df_ch.columns.tolist()
    df_col.remove(CHEC_COL_NAME)

    # st.session_state.ss_df_ed = df_atrib(result_df_ch)
    if st.session_state.traj_flag:
        st.session_state.ss_df_ed = result_df_ch.style.apply(highlight_rows, axis=1)
        st.session_state.traj_flag = False
        st.success('Orbit propagation data loaded', icon=cn.SUCCESS)

    if 'ss_df_ed' not in st.session_state:
        st.info('Rum propagation im orbit propagation page', icon= cn.INFO)
        st.stop()  

    st.info('Selected radar setting: ' + radar_sel['name'], icon=cn.INFO)
    st.write('Reload propagation results and calculate RCS_MIN with sidebar selected radar settings:')
    if st.button('Reload data and Calc RCS_MIN',key='bt_RCS_MIN'):
        st.session_state.ss_df_ed = result_df_ch.style.apply(highlight_rows, axis=1)
        st.success('Orbit propagation data reloaded', icon=cn.SUCCESS)

    st.subheader('Object Selection:')

    st.write('Select the trajetories:')
    col1s, col2s, col3s, col4s, col5s = st.columns(5)
    if col2s.button('Clear All',key='bt_clear'):
        st.session_state.ss_df_ed.data[CHEC_COL_NAME] = False
    if col3s.button('Select All',key='bt_select'):
        st.session_state.ss_df_ed.data[CHEC_COL_NAME] = True

    # ************************************************************
    # Select Line st.data_editor
    # ************************************************************
    # st.write('All objects')
    selected_row = st.data_editor(
                    st.session_state.ss_df_ed,
                    column_config={
                        CHEC_COL_NAME: st.column_config.CheckboxColumn(
                            CHEC_COL_NAME,
                            help="Select trajetories",
                            disabled=False, 
                            #default=False,
                        )
                        },
                    disabled= df_col,
                    hide_index=False,
                    )   
     

    if col1s.button('Save selection',key='bt_save'):
        st.session_state.ss_df_ed = selected_row.style.apply(highlight_rows, axis=1)


    # ************************************************************
    col1d, col2d = st.columns(2)
    FILE_NAME_XLSX = st.session_state["ss_lc"]['name']+"_traj_summary.xlsx"
  
    with pd.ExcelWriter(st.session_state.ss_dir_name + "/"+ FILE_NAME_XLSX) as writer:
        st.session_state.ss_df_ed.to_excel(writer, sheet_name='Sheet 1', engine='openpyxl')

    if os.path.isfile(st.session_state.ss_dir_name + "/"+ FILE_NAME_XLSX):
        col1d.write('Download highlight File:')
        with open(st.session_state.ss_dir_name + "/"+ FILE_NAME_XLSX, "rb") as fp:
            btn = col1d.download_button(
                label="Download .xlsx",
                data=fp,
                file_name=FILE_NAME_XLSX,
                mime="application/txt"
            )

    # ************************************************************

    FILE_NAME_CSV = st.session_state["ss_lc"]['name']+"_traj_summary.csv"
  
    st.session_state.ss_df_ed.data.to_csv(st.session_state.ss_dir_name + "/"+ FILE_NAME_CSV, index=False)

    if os.path.isfile(st.session_state.ss_dir_name + "/"+ FILE_NAME_CSV):
        col2d.write('Download csv File:')
        with open(st.session_state.ss_dir_name + "/"+ FILE_NAME_CSV, "rb") as fp:
            btn = col2d.download_button(
                label="Download .csv",
                data=fp,
                file_name=FILE_NAME_CSV,
                mime="application/txt"
            )

    # ************************************************************
    
    # st.dataframe(st.session_state.ss_df_ed)

    # st.write('Selected objects')

    selected_row=selected_row[selected_row[CHEC_COL_NAME]]
    selected_row=selected_row.loc[:,selected_row.columns!= CHEC_COL_NAME]

    st.subheader('Specific ENU Trajectories:')
    # ************************************************************
    st.info('Radarar sensor settings - sample time: ' + str(st.session_state.ss_radar_sel['spt']) + 's', icon=cn.INFO)
    st.write('Calculate trajectories of selected objects:')
    if st.button('Calculate trajectories'): 

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
        sample_time = st.session_state.ss_radar_sel['spt'] #  0.01

        # automatico:                          
        for index in range(len(orbital_elem)):
            propag = PropagInit(orbital_elem[index], lc, sample_time)
            pos = propag.traj_calc(Time(orbital_elem[index]['H0']), round(orbital_elem[index]['END_PT']/sample_time) )
            save_trajectories(pos,st.session_state.ss_dir_name, orbital_elem[index]['END_PT'])
            my_bar.progress((index+1)/len(orbital_elem))
            
        fim = tm.time()
        st.write("Processing time (s): ", fim - ini)

        st.success('Trajectories calculated successfully', icon=cn.SUCCESS)
        
    dir_name = st.session_state.ss_dir_name + '/trn100Hz'
    if os.path.exists(dir_name): 
        txt_files = glob.glob(dir_name + os.sep +'*.trn')
        if  len(txt_files)>0:
            st.write('Download trajetory files *.trn - from H0, in the ENU:')  
            shutil.make_archive(dir_name, 'zip', dir_name)
            with open(dir_name + ".zip", "rb") as fp:
                btn = st.download_button(
                    label="Download .trn files",
                    data=fp,
                    file_name="trn_" + str(sample_time) + 's_' + lc['name'] + '_' + st.session_state.date_time +".zip",
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
        save_selected_data(selected_row[columns])


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
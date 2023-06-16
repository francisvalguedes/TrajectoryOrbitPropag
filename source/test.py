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

from spacetrack import SpaceTrackClient
import spacetrack.operators as op
from io import StringIO

import glob

import pymap3d as pm
import re

from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder




def main():
    """main function that provides the simplified interface for configuration,
         visualization and data download. """  

    st.write('## Antes')
    df =pd.read_csv('data/space_track/oe_data_spacetrack.csv')

    gb = GridOptionsBuilder.from_dataframe(df)

    #gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    #gb.configure_column('first_column', headerCheckboxSelection = True)
    gb.configure_column(df.columns[0], headerCheckboxSelection=True)
    # gb.configure_side_bar()

    gridoptions = gb.build()

    # grid_table = AgGrid(
    #                     df,
    #                     height=200,
    #                     gridOptions=gridoptions,
    #                     enable_enterprise_modules=True,
    #                     update_mode=GridUpdateMode.MODEL_CHANGED,
    #                     data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    #                     fit_columns_on_grid_load=False,
    #                     header_checkbox_selection_filtered_only=True,
    #                     use_checkbox=True)

    grid_table = AgGrid(
                      df,
                      height=250,
                      gridOptions=gridoptions,
                      update_mode=GridUpdateMode.SELECTION_CHANGED)

    st.write('## Selected')
    selected_row = grid_table["selected_rows"]
    selected_row = pd.DataFrame(selected_row)
    st.dataframe(selected_row)

if __name__== '__main__':
    main()
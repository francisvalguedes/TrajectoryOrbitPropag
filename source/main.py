"""
Creator: Francisval Guedes Soares
Date: 2021
"""

import streamlit as st

from datetime import datetime, timezone
from lib.pages_functions import  *

import shutil

import os
import tempfile

import glob


def main():
    """main function that provides the simplified interface for configuration,
         visualization and data download. """  

    st.set_page_config(
    page_title="Orbit Tracking",
    page_icon="🌏", # "🤖",  # "🧊",
    # https://raw.githubusercontent.com/omnidan/node-emoji/master/lib/emoji.json
    layout="wide",
    initial_sidebar_state="expanded",menu_items = menu_itens())

    if "stc_loged" not in st.session_state:
        st.session_state.stc_loged = False
    
    if "d_max" not in st.session_state:
        st.session_state.d_max = 1100

    delete_old_items(50)

    if "date_time" not in st.session_state:
        date_time = datetime.now(timezone.utc).strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
        st.session_state.date_time = date_time

    if "ss_dir_name" not in st.session_state:
        dir_name = tempfile.gettempdir()+"/top_tmp_"+ date_time
        st.session_state.ss_dir_name = dir_name 


    st.title("Orbit Propagator for Tracking Earth's Artificial Satellites in LEO")
    st.subheader('**Satellite orbit propagation and trajectory generation, for optical and radar tracking of space objects (Debris, Rocket Body, Satellites...), especially for low Earth orbit (LEO) objects.**')
    st.markdown('Using SGP4 this app searches for a point of approach of a space object in Earth orbit and traces a trajectory interval in: local plane reference (ENU), AltAzRange, ITRS and Geodetic, to be used as a target for optical or radar tracking system')
    st.markdown('by: Francisval Guedes Soares, Email: francisvalg@gmail.com')
    st.markdown('Contributions/suggestions: Felipe Longo, André Henrique, Hareton, Marcos Leal, Leilson')
    
    page_links()
    

        
if __name__== '__main__':
    main()
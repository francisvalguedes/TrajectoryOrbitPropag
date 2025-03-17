"""
Creator: Francisval Guedes Soares
Date: 2021
"""

import streamlit as st

from datetime import datetime, timezone
from lib.pages_functions import  *

import os
import tempfile

# https://raw.githubusercontent.com/omnidan/node-emoji/master/lib/emoji.json
st.set_page_config(page_title="Orbit Tracking",
                    page_icon="🌏", layout="wide", initial_sidebar_state="auto",
                    menu_items=menu_itens())

# For translate text: _("my text")
domain_name = os.path.basename(__file__).split('.')[0]
_ = gettext_translate(domain_name)


# funções

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


def main():
    """main function that provides the simplified interface for configuration,
         visualization and data download. """  


    # translate_page(page="main")_ = gettext.gettext

    page_links(insidebar=True)

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


    st.title(_("Orbit Propagator for Tracking Earth's Artificial Satellites in LEO"))
    st.subheader(_('**Satellite orbit propagation and trajectory generation, for tracking of space objects (Debris, Rocket Body, Satellites...), especially for low Earth orbit (LEO) objects.**'))
    st.markdown(_('Using SGP4 this app searches for a point of approach of a space object in Earth orbit and traces a trajectory interval in: local plane reference (ENU), AltAzRange, ITRS and Geodetic, to be used as a target for tracking system'))
    st.markdown(_('This APP use Orbit Mean-Elements Message (OMM) format, it contain orbital elements for satellites in a standard format. OMM files are part of the Orbit Data Messages (ODM) Recommended Standard'))

    stex1 = st.expander("", expanded=True)
    stex1.image("figures/orbit_propagator.svg",
             caption=_("block diagram of Orbit Propagation"),
             )
    

    page_links()
    

        
if __name__== '__main__':
    main()
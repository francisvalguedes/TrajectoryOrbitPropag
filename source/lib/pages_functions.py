from spacetrack import SpaceTrackClient
from datetime import datetime, timezone
import datetime as dt
import pandas as pd
from io import StringIO
import spacetrack.operators as op
import streamlit as st
import sys
import re

from lib.constants import  ConstantsNamespace
cn = ConstantsNamespace()

class Icons:
    def __init__(self):
        """
        Creator: Francisval Guedes Soares
        Date: 2021
        icons
        """
        self.warning = "⚠️"
        self.error = "🚨"
        self.info = "ℹ️"
        self.success = "✅"


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
            return False
        return  True
    
    def get_by_norad(self,
                     norad_ids,
                     epoch_start = datetime.now(timezone.utc) - dt.timedelta(days=4),
                     epoch_end = datetime.now(timezone.utc) + dt.timedelta(days=1) ):
        """get the orbital elements from NORAD_CAT_IDs.

        Args:
        norad_ids (list of int): NORAD_CAT_IDs

        Returns:         
        pandas DataFrame: OMM format
        """
        epoch = epoch_start.strftime('%Y-%m-%d-') + epoch_end.strftime('-%Y-%m-%d')
        # print('epoch '+ epoch)
        elements_csv = self.gp_history( norad_cat_id=norad_ids,
                                                            orderby='norad_cat_id desc',epoch=epoch,
                                                            format='csv')

        # elements_csv = self.gp(norad_cat_id=norad_ids, orderby='norad_cat_id', format='csv')
        try:
            elem_df = pd.read_csv(StringIO(elements_csv), sep=",")
        except BaseException as e:
            st.error('Space-Track csv read exception: ' + str(e), icon=cn.ERROR)
            st.stop()

        return elem_df, epoch
    
    def get_select(self):
        """get the orbital elements from specified filter.

           Selection of 3000+ objects by Space-Track API mean_motion>11.25 (LEO orbit),
           decay_date = null-val (no reentry), rcs_size = Large (greater than 1m),
           periapsis < 500km, epoch = >now-1 (updated until a day ago), orderby= EPOCH desc

        Returns:         
        pandas DataFrame: OMM format
        """
        elements_csv = self.gp(mean_motion = op.greater_than(11.25),
                    decay_date = 'null-val',
                    rcs_size = 'Large',
                    periapsis = op.less_than(500),
                    epoch = '>now-1', 
                    orderby= 'EPOCH desc',
                    format='csv')
        elem_df = pd.read_csv(StringIO(elements_csv), sep=",")
        return elem_df     

def sensor_registration():
    # adicionar novo ponto de referência (sensor)
    lc_expander = st.sidebar.expander("Adicionar novo ponto de referência no WGS84", expanded=False)
    lc_name = lc_expander.text_input('Nome', "minha localização")
    latitude = lc_expander.number_input('Latitude', -90.0, 90.0, 0.0, format="%.6f")
    longitude = lc_expander.number_input('Longitude', -180.0, 180.0, 0.0, format="%.6f")
    height = lc_expander.number_input('Altura (m)', -1000.0, 2000.0, 0.0, format="%.6f")
    color = lc_expander.text_input('Cor', "red")
    if lc_expander.button("Registrar nova localização"):
        lc_add = {'name': [lc_name], 'lat': [latitude], 'lon': [longitude], 'height': [height], 'color': [color]}
        if lc_name not in st.session_state.lc_df['name'].to_list():
            if re.match('^[A-Za-z0-9_-]*$', lc_add['name'][0]):
                st.session_state.lc_df = pd.concat([st.session_state.lc_df, pd.DataFrame(lc_add)], axis=0)
                st.session_state.lc_df.to_csv('data/confLocalWGS84.csv', index=False)
                lc_expander.write('Localização registrada')
            else:
                lc_expander.write('Escreva um nome sem caracteres especiais')
        else:
            lc_expander.write('Localização já existe')



def page_links():
    st.markdown("Pages:")
    st.page_link("pages/00_simplificado_pt-br.py",
                 label="PT-BR: Página simplificada com boa parte das funções do APP", icon= "0️⃣")
    st.page_link("pages/01_orbital_elements.py", label="Obtaining orbital elements of the space object", icon= "1️⃣")
    st.page_link("pages/02_orbit_propagation.py", label="Orbit propagation and trajectory generation", icon= "2️⃣")
    st.page_link("pages/03_results.py", label="Map view page", icon= "3️⃣")
    st.page_link("pages/04_orbit_compare.py", label="Analysis of object orbital change/maneuver", icon= "4️⃣")
    st.page_link("pages/05_trajectory.py", label="Generation of specific trajectories", icon= "5️⃣")

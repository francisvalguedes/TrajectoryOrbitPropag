from spacetrack import SpaceTrackClient
from datetime import datetime
import datetime as dt
import pandas as pd
from io import StringIO
import spacetrack.operators as op
import streamlit as st
import sys

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
                     epoch_start = datetime.utcnow() - dt.timedelta(days=4),
                     epoch_end = datetime.utcnow() + dt.timedelta(days=1) ):
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
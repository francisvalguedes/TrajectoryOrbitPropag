import streamlit as st
from streamlit_geolocation import streamlit_geolocation

from spacetrack import SpaceTrackClient
import spacetrack.operators as op

from datetime import datetime, timedelta, timezone, time
import datetime as dt
import pandas as pd
from io import StringIO
import re
import os
import shutil
import glob
import tempfile
import numpy as np

from astropy.time import Time
from astropy.time import TimeDelta
from astropy import units as u

import folium
from folium import plugins

import gettext
import httpx
from urllib.parse import quote

from lib.constants import  ConstantsNamespace

# constants
cn = ConstantsNamespace()


# https://iconscout.com/icons/satellite
icon_sat_tj = "https://raw.githubusercontent.com/francisvalguedes/norad_rcs/refs/heads/master/figures/satellite.svg"
# https://iconduck.com/icons/271693/satellite#
icon_sat_end = "https://raw.githubusercontent.com/francisvalguedes/norad_rcs/refs/heads/master/figures/satellite_duck.svg"
#https://iconduck.com/icons/9737/satellite-radar#
icon_sensor = "https://raw.githubusercontent.com/francisvalguedes/norad_rcs/refs/heads/master/figures/satellite-radar.svg"


# functions
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

def client_proxy(config):
    # Check if proxy is enabled
    if config["proxy"].get("enabled", True):
        if config["proxy"].get("auto", True):
            proxy = os.getenv("https_proxy")  # Proxy HTTPS
            return httpx.Client(proxy=proxy)
        else:
            proxy_server = config["proxy"]["server"]
            proxy_port = config["proxy"]["port"]
            username = config["proxy"]["username"]
            password = config["proxy"]["password"]
            proxy = f"http://{quote(username)}:{quote(password)}@{quote(proxy_server)}:{quote(proxy_port)}"
            return httpx.Client(proxy=proxy)
    else:
        return httpx.Client()

class SpaceTrackClientInit(SpaceTrackClient):
    def __init__(self,identity,password, client):
        """initialize the class.

        Args:
        https://www.space-track.org/auth/login
        identity (str): login space-track.
        password (str): password space-track.

        Returns:

        """
 
        super().__init__(identity, password, httpx_client = client)
        #super().__init__(identity, password)

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


def delete_old_items(max_folders=100):
    try:
        # Pegar o caminho temporário padrão do sistema
        path_files = os.path.join(tempfile.gettempdir(), 'top_tmp*')
        # Listar todas as pastas temporárias e arquivos zip
        items = glob.glob(path_files)
        # Verificar se o número de itens excede o limite
        if len(items) > max_folders:
            # Ordenar itens por data de criação
            items.sort(key=lambda f: datetime.strptime(os.path.basename(f).replace('.zip', ''), "top_tmp_%Y_%m_%d_%H_%M_%S_%f"))
            # Excluir itens antigos além do limite
            for item in items[:-max_folders]:
                if os.path.isdir(item):
                    shutil.rmtree(item)
                elif os.path.isfile(item):
                    os.remove(item)
    except Exception as e:
        st.warning(f"Error: {e}", icon = cn.WARNING)

def data_map_concat(df_p , df_s, df_s1 = pd.DataFrame()):
    if 'name' in df_p.columns: # Forçar a coluna 'name' a ser do tipo string         
        df_p['name'] = df_p['name'].astype(str)

    # Defina o tamanho máximo de pontos para a plotagem
    max_points = 20
    interval = max(len(df_p) // max_points, 1)

    # Se o número de pontos for maior que o limite, reamostrar
    if len(df_p) > max_points:
        # Sempre incluir o primeiro e o último ponto 
        first_point = df_p.iloc[0] 
        last_point = df_p.iloc[-1]
        df_p = df_p.iloc[::interval]
        df_p = pd.concat([pd.DataFrame([first_point]), df_p, pd.DataFrame([last_point])])
        #st.info('Muitos dados para o mapa, selecionados o primeiro, o ultimo e mais ' + str(max_points) + ' pontos intermediários da série de dados', icon=cn.WARNING )

    df_s['sensor'] = 1
    if len(df_s1.index>0):
        df_s1['sensor'] = 1
    df = pd.concat([df_p, df_s, df_s1], axis=0).reset_index(drop=True)
    return df

# https://bikeshbade.com.np/tutorials/Detail/?title=Beginner+guide+to+python+Folium+module+to+integrate+google+earth+engine&code=8
def create_map2(df):
    mapa = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=6)
    # https://leaflet-extras.github.io/leaflet-providers/preview/
    # https://maps.stamen.com/terrain/#10/-5.92375/-35.16127
    # ['blue', 'green', 'orange', 'red', 'purple', 'pink', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'lightblue', 'gray', 'black', 'lightgray']
    
    # Adiciona camadas de terreno com atribuições (usando `attr`)

    # folium.TileLayer(
    #         tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    #         attr = 'Esri',
    #         name = 'Esri Satellite',
    #         # overlay = True,
    #         # control = True,
    #         max_zoom=20,
    #     ).add_to(mapa)

    # folium.TileLayer(
    #     tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    #     name="OpenStreetMap",
    #     attr="&copy; OpenStreetMap contributors"
    # ).add_to(mapa) 

    # Adiciona marcadores como um grupo de camada
    camada_marcadores = folium.FeatureGroup(name="Marcadores", show=True)

    for  _, row in df.iterrows():
        #icon = folium.Icon( color=row.get('color', "red") ) 
        if row['tipo']==0: icon_path = icon_sensor 
        elif row['tipo']==1: icon_path = icon_sat_tj 
        elif row['tipo']==2: icon_path = icon_sat_end

        icon = folium.features.CustomIcon(icon_path, icon_size=(20, 20))
        popup = folium.Popup(row.get('name', ''), show=False, sticky=True)  # , sticky=True Popup exibido automaticamente
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=popup,
            tooltip=f"Azimute: {row['AZIMUTH']:.3f}°, Elevação: {row['ELEVATION']:.3f}°, Distância: {row['RANGE']:.3f} m",
            #tooltip=f"lat: {row['lat']:.5f}°, lon: {row['lon']:.5f}°, h: {row['height']:.2f} m",
            #'AZIMUTH','ELEVATION','RANGE'
            icon=icon,
        ).add_to(camada_marcadores)

    camada_marcadores.add_to(mapa)

    # Adiciona uma linha como um grupo de camada
    camada_linhas = folium.FeatureGroup(name="Linhas", show=True)

    df2 = df[df['sensor']!=1]
    linha = df2[['lat', 'lon']].values.tolist()

    folium.PolyLine(linha, color="blue", weight=2.5, opacity=1).add_to(camada_linhas)
    camada_linhas.add_to(mapa)

    # Adiciona controle de camadas
    folium.LayerControl().add_to(mapa)

    #mouse position
    fmtr = "function(num) {return L.Util.formatNum(num, 3) + ' º ';};"
    plugins.MousePosition(position='bottomright',
                        separator=' | ',
                        prefix="Mouse:",
                        lat_formatter=fmtr,
                        lng_formatter=fmtr).add_to(mapa)

    #Add measure tool
    mapa.add_child(plugins.MeasureControl(position='bottomright',
                                        primary_length_unit='meters',
                                        secondary_length_unit='miles',
                                        primary_area_unit='sqmeters',
                                        secondary_area_unit='acres').add_to(mapa))

    #fullscreen
    plugins.Fullscreen().add_to(mapa)

    #GPS
    plugins.LocateControl().add_to(mapa)

    #Add the draw 
    plugins.Draw(export=True, filename='data.geojson', position='topleft', draw_options=None, edit_options=None).add_to(mapa)  
    return mapa


def plot_map(df, lc):
    lcdf = pd.DataFrame.from_dict([lc])    
    lcdf['tipo'] = 0
    lcdf['name'] = 'Meu Local'
    df['tipo'] = 1
    df.at[df.index[-1], 'tipo'] = 2
    df['name'] = df['Time']

    df_map  = data_map_concat(df, lcdf )
    mapa = create_map2(df_map)
    st.components.v1.html(folium.Figure().add_child(mapa).render(), height=600)


def translate_page(page='base'):
    # https://medium.com/dev-genius/how-to-build-a-multi-language-dashboard-with-streamlit-9bc087dd4243    languages = {"English": "en", "Português": "pt"}
    languages = {"English": "en", "Português": "pt"}
    language = st.radio("Language",
                        options=languages,
                        horizontal=True,
                        label_visibility='hidden',# 'collapsed',
                        #on_change=set_language,
                        #key="selected_language",
                        )
    language = languages[language]
    
    try:
        localizator = gettext.translation(page, localedir='locales', languages=[language])
        localizator.install()
        _ = localizator.gettext 
    except:
        pass


# #######################################################


def columns_first(df, col_first):
    col_list = df.columns.to_list()
    for line in col_first:
        if line in col_list: col_list.remove(line)
        else: col_first.remove(line)
    col_first.extend(col_list)
    df = df.reindex(columns=col_first)
    return df

# ----------------------------------------------------------------------
# Salva as trajetórias
# ----------------------------------------------------------------------
class Summarize2DataFiles:
    def __init__(self):
        """initialize the class"""     
        self.tr_data = []   
        self.sel_orbital_elem = []
        self.sel_resume = {"RCS":[], "H0":[],"H0_H":[], "H0_RANGE":[],"MIN_RANGE_H":[],"MIN_RANGE_PT":[],
                    "MIN_RANGE":[],"END_H":[], "END_PT":[], "END_RANGE":[] }

    def save_trajectories(self,pos,orbital_elem,rcs):
        """saves trajectories and summarizes important data for tracking analysis.
        Args:
            pos (PropagInit obj): all calculated trajectories of an sattelite (orbital_elem) 
            orbital_elem (OMM dict): orbital element of sattelite
        Returns:
            self
        """
        for i in range(0, len(pos.time_array)):
            time_arr = pos.time_array[i]
            df_data = pd.DataFrame(time_arr.value.reshape(len(time_arr),1), columns=['Time'])

            df_data = pd.concat([df_data, pd.DataFrame(np.concatenate((
                            pos.az_el_r[i], pos.enu[i], 
                            pos.itrs[i], pos.geodetic[i]), axis=1),
                            columns=[ 'AZIMUTH','ELEVATION','RANGE',
                            'ENU_E','ENU_N','ENU_U', 
                            'ITRS_X','ITRS_Y','ITRS_Z','lat','lon','height'])], axis=1)

            enu_d = 0.001*pos.az_el_r[i][:,2]
            min_index = np.argmin(enu_d)
            min_d = enu_d[min_index]

            self.tr_data.append(df_data) 
            self.sel_orbital_elem.append(orbital_elem) 
            if pos.satellite.satnum in rcs['NORAD_CAT_ID']:
                self.sel_resume["RCS"].append(rcs['RCS'][rcs['NORAD_CAT_ID'].index(pos.satellite.satnum)])
            else:
                self.sel_resume["RCS"].append(0.0)
            self.sel_resume["H0"].append(time_arr[0].value)
            self.sel_resume["H0_H"].append(time_arr[0].strftime('%H:%M:%S.%f'))
            self.sel_resume["H0_RANGE"].append(enu_d[0])
            self.sel_resume["MIN_RANGE_H"].append(time_arr[min_index].strftime('%H:%M:%S.%f'))
            self.sel_resume["MIN_RANGE_PT"].append(min_index)
            self.sel_resume["MIN_RANGE"].append(min_d)
            self.sel_resume["END_H"].append(time_arr[-1].strftime('%H:%M:%S.%f'))
            self.sel_resume["END_PT"].append(len(enu_d) - 1)
            self.sel_resume["END_RANGE"].append(enu_d[-1]) 

def menu_itens():
    menu_items={
        'Get Help': 'https://github.com/francisvalguedes/TrajectoryOrbitPropag',
        'About': "A cool app for orbit propagation and trajectory generation, report a bug: francisvalg@gmail.com"
    }
    return menu_items


def gettext2_translate(domain_name):
    languages = {"English": "en", "Português-BR": "pt-BR"}

    if "selected_language" not in st.session_state:
        st.session_state.selected_language = list(languages.keys())[0]  # Define o idioma padrão
        print(st.session_state.selected_language)

    previous_language = st.session_state.selected_language  # Salva o idioma anterior

    language = st.radio(
        "Language",
        options=languages,
        horizontal=True,
        label_visibility="hidden",
        key="selected_language"
    )

    # Se o idioma mudou, força a recarga da página para aplicar a mudança corretamente
    if language != previous_language:
        st.rerun()

    st.markdown("""<hr style="height:5px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

    language_code = languages[language]
    # st.session_state.language = language_code  # Atualiza o estado com o código do idioma

    _ = gettext.gettext

    try:
        localizator = gettext.translation(domain_name, localedir="locales", languages=[language_code])
        localizator.install()
        _ = localizator.gettext
    except Exception as e:
        if language_code != "en":
            print(f"Translate error: {e}")
        else:
            pass

    return _

def gettext_translate(domain_name):   
    languages = {"English": "en", "Português-BR": "pt-BR"}

    if 'selected_language_index' in st.session_state:
        rd_index = st.session_state.selected_language_index
    else:
        rd_index = 0

    language = st.radio("Language",
                        options=languages,
                        horizontal=True,
                        label_visibility='hidden',# 'collapsed', hidden
                        #on_change=set_language,
                        key="selected_language",
                        index=rd_index
                        )
    
    st.session_state.selected_language_index = list(languages.keys()).index(language)

    # Se o idioma mudou, força a recarga da página para aplicar a mudança corretamente
    if rd_index != st.session_state.selected_language_index:
        st.rerun()

    rd_index = st.session_state.selected_language_index

    st.markdown("""<hr style="height:5px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)    

    language = languages[language]

    st.session_state.language = language
    _ = gettext.gettext

    try:
        localizator = gettext.translation(domain_name, localedir='locales', languages=[language])
        localizator.install()
        _ = localizator.gettext 
    except:  
        if language != "en":
            print(f"Translate error: {e}")
        else:
            pass
    return _
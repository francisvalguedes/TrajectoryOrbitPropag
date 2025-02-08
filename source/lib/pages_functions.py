from spacetrack import SpaceTrackClient
from datetime import datetime, timezone
import datetime as dt
import pandas as pd
from io import StringIO
import spacetrack.operators as op
import streamlit as st
import re
import os
import shutil
import glob
import tempfile

import folium
from folium import plugins

from lib.constants import  ConstantsNamespace

# constants
cn = ConstantsNamespace()

# https://iconscout.com/icons/satellite
icon_sat_tj = "https://raw.githubusercontent.com/francisvalguedes/radarbands/refs/heads/master/figures/satellite.svg"
# https://iconduck.com/icons/271693/satellite#
icon_sat_end = "https://raw.githubusercontent.com/francisvalguedes/radarbands/refs/heads/master/figures/satellite_duck.svg"
#https://iconduck.com/icons/9737/satellite-radar#
icon_sensor = "https://raw.githubusercontent.com/francisvalguedes/radarbands/refs/heads/master/figures/satellite-radar.svg"

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
    st.markdown("Page with simplified configuration - Português:")
    st.page_link("pages/00_simplificado_pt-br.py",
                 label="PT-BR: Configuração simplificada com parte das funções do APP", icon= "0️⃣")
    
    st.markdown("Page with specific settings - English):")
    st.page_link("pages/01_orbital_elements.py", label="Obtaining orbital elements of the space object", icon= "1️⃣")
    st.page_link("pages/02_orbit_propagation.py", label="Orbit propagation and trajectory generation", icon= "2️⃣")
    st.page_link("pages/03_map.py", label="Map view page", icon= "3️⃣")
    st.page_link("pages/04_orbit_compare.py", label="Analysis of object orbital change/maneuver", icon= "4️⃣")
    st.page_link("pages/05_trajectory.py", label="Generation of specific trajectories", icon= "5️⃣")

def page_stop():
    page_links()
    st.stop()

def menu_itens():
    menu_items={
        'Get Help': 'https://github.com/francisvalguedes/TrajectoryOrbitPropag',
        'About': "A cool app for orbit propagation and trajectory generation, report a bug: francisvalg@gmail.com"
    }
    return menu_items


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
        st.warning(f"Error: {e}", cn.WARNING)

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

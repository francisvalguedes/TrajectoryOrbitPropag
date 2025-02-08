"""
Creator: Francisval Guedes Soares
Date: 2021
"""

import streamlit as st
import pandas as pd

from datetime import datetime, timedelta, timezone, time
import time as tm

from astropy.time import Time
from astropy.time import TimeDelta
from astropy import units as u

import os
import numpy as np

from lib.orbit_functions import  PropagInit
from lib.constants import  ConstantsNamespace
from lib.pages_functions import  page_links

from streamlit_geolocation import streamlit_geolocation

import pymap3d as pm

cn = ConstantsNamespace()

import pandas as pd
import folium

from folium import plugins
import streamlit as st
from lib.constants import  ConstantsNamespace

cn = ConstantsNamespace()

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
class SummarizeDataFiles:
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


def get_celestrack_oe():
    norad_id = st.number_input('Selecione o NORAD_CAT_ID do objeto espacial para obtenção dos elementos orbitais:', 0, 999999,value= 25544, format="%d")
    current_day = datetime.now(timezone.utc).strftime('%Y_%m_%d_')
    celet_fil_n = 'data/celestrak/' + current_day + str(norad_id) + '.csv'
    if not os.path.exists(celet_fil_n):                
        urlCelestrak = 'https://celestrak.org/NORAD/elements/gp.php?CATNR='+ str(norad_id) +'&FORMAT=csv'
        try:
            elem_df = pd.read_csv(urlCelestrak) 
            if 'MEAN_MOTION' in elem_df.columns.to_list():
                elem_df.to_csv(celet_fil_n, index=False)                     
            else:
                st.error('No orbital elements for this object in Celestrac', icon= cn.ERROR)
                st.stop()
        except OSError as e:
            st.error('Celestrak error, use Space-Track or load orbital elements manually', icon=cn.ERROR)
            st.stop()
    else:        
        elem_df = pd.read_csv(celet_fil_n)  
    return elem_df

def upload_oe():
    data_elements = st.file_uploader("Carregue os elementos orbitais: formato OMM csv",type='csv')
    if data_elements is not None:            
        if data_elements.type == "text/csv":
            st.write("Elementos orbitais carregados:")
            elem_df = pd.read_csv(data_elements)
        else:
            st.warning("erro no arquivo", icon = cn.WARNING)
            st.stop()
    else:
        st.info("Carregue o arquivo", icon = cn.INFO)
        st.stop()
    return elem_df
    

def get_date_time():    
    max_time = TimeDelta(10*u.d)
    expander_date = st.expander('Momento para inicio da busca por aproximação - UTC 00:', expanded=True)
    col1, col2 = expander_date.columns(2)
    initial_date = col1.date_input("Data de início")
    initial_time = col2.time_input("Hora de início", time(10, 0))
    initial_datetime=Time(datetime.combine(initial_date, initial_time))
    initial_datetime.format = 'isot'

    final_date = col1.date_input("Data final", datetime.today() + timedelta(days=1))
    final_time = col2.time_input("Hora final", time(20, 0))
    final_datetime=Time(datetime.combine(final_date, final_time))
    final_datetime.format = 'isot'

    if  (final_datetime - initial_datetime)> max_time:      
        final_datetime = initial_datetime + max_time 
        st.warning('Período máximo: ' + str(max_time) + ' dias', icon=cn.WARNING)
    elif  (final_datetime - initial_datetime) < TimeDelta(0.0001*u.d):
        st.error('Hora final tem que ser maior que a inicial', icon=cn.ERROR)
        st.stop()
    return initial_datetime, final_datetime

def dell_elem_df():
    if 'ss_elem_df' in st.session_state:
        del st.session_state.ss_elem_df

def data_input_geodesicas():
    st.write("Configurar com a minha localização atual:")
    loc = streamlit_geolocation()
    lat = loc['latitude'] if loc['latitude'] != None else -5.92455
    lon = loc['longitude'] if loc['longitude'] != None else -35.2658
    h = loc['altitude'] if loc['altitude'] != None else 100.0
    expander = st.expander("Entre com as coordenadas do ponto de referência:", expanded=True)
    col1, col2, col3 = expander.columns(3)
    latitude = col1.number_input('Latitude(graus)', -90.0, 90.0, lat, format="%.6f", key='Latitude')
    longitude = col2.number_input('Longitude(graus)', -180.0, 180.0, lon, format="%.6f", key='Longitude')
    height = col3.number_input('Altitude (m)', -1000000.0, 50000000.0, h, format="%.2f", key='Altura')
    return pd.DataFrame({"name": ['Manual'], "lat": [latitude], "lon": [longitude], "height": [height]})
          
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

# constantes
Celestrak="Celestrak"
oe_file ="Arquivo de elementos orbitais"
menuUpdate = [Celestrak, oe_file]

sample_time = 1.0 # tempo de amostragem da trajetória    
dmax = 900 # distancia de aproximação para busca    
dmin = 800 # distancia de aproximação para salvar a trajetória
max_num_obj = 1000 # numero máximo de objetos

# https://iconscout.com/icons/satellite
icon_sat_tj = "https://raw.githubusercontent.com/francisvalguedes/radarbands/refs/heads/master/figures/satellite.svg"
# https://iconduck.com/icons/271693/satellite#
icon_sat_end = "https://raw.githubusercontent.com/francisvalguedes/radarbands/refs/heads/master/figures/satellite_duck.svg"
#https://iconduck.com/icons/9737/satellite-radar#
icon_sensor = "https://raw.githubusercontent.com/francisvalguedes/radarbands/refs/heads/master/figures/satellite-radar.svg"


def main():
    """main function that provides the simplified interface for configuration,
         visualization and data download. """  

    st.set_page_config(page_title="Configuração simplificada para propagação de órbita", page_icon="🌏", layout="wide" )

    st.subheader('Configuração simplificada para propagação de órbita e obtensão de trajetória de aproximação ao ponto de referência (sensor):')
    
    st.subheader("*Obtensão dos elementos Orbitais:*")

    helptxt = "Escolha a fonte dos elementos orbitais para propagação"
    st.selectbox("Fonte dos elementos orbitais:",menuUpdate, key="oe_source", help=helptxt, on_change=dell_elem_df)  
    if st.session_state["oe_source"] == Celestrak:
        st.session_state.ss_elem_df = get_celestrack_oe()
    elif st.session_state["oe_source"] == oe_file:
        st.session_state.ss_elem_df = upload_oe()

    st.dataframe(st.session_state.ss_elem_df)   

    st.subheader("*Configurações para propagação de orbita:*")
   
    lc = data_input_geodesicas().to_dict('records')[0]

    # Período para busca de trajetórias
    initial_datetime, final_datetime = get_date_time()
     
    st.subheader("Obter dados de aproximação e Calcular trajetórias:")
    
    if st.button("Executar propagação"):
        if "ss_elem_df" not in st.session_state:
            st.info('Upload the orbital elements', icon=cn.INFO)
            st.stop()
        elif 'MEAN_MOTION' not in st.session_state["ss_elem_df"].columns.to_list():
            st.error('Orbital elements do not match OMM format', icon=cn.ERROR)
            st.stop()

        elem_df = st.session_state.ss_elem_df.drop_duplicates(subset=['NORAD_CAT_ID'], keep='first')
        st.write('Numero de elementos orbitais: ', len(elem_df.index))

        if len(elem_df.index)>max_num_obj:
            st.warning('Numero máximo de objetos para propagar: ' + str(max_num_obj) +
                    ', para o periodo de '+ str(final_datetime - initial_datetime) + ' days',
                        icon=cn.WARNING)
            st.stop()

        orbital_elem = elem_df.to_dict('records')
        del elem_df

        rcs = pd.read_csv('data/RCS.csv').to_dict('list')        

        ini = tm.time()    

        st.write('Barra de progresso:')
        my_bar = st.progress(0)

        sdf = SummarizeDataFiles()

        # automatico:                          
        for index in range(len(orbital_elem)):
            propag = PropagInit(orbital_elem[index], lc, sample_time) 
            pos = propag.search2h0(initial_datetime, final_datetime, dmax*1000, dmin*1000)
            sdf.save_trajectories(pos,orbital_elem[index],rcs)
            my_bar.progress((index+1)/len(orbital_elem))

        df_orb = pd.DataFrame(sdf.sel_orbital_elem)
        obj_aprox = len(df_orb.index)
        # st.write('Number of calculated trajectories: ', obj_aprox)

        if obj_aprox > 0:
            col_first = ['EPOCH', 'CREATION_DATE', 'DECAY_DATE']
            df_orb = columns_first(df_orb, col_first )

            df_traj = pd.DataFrame(sdf.sel_resume)

            common = set(df_traj.columns.tolist()).intersection(df_orb.columns.tolist())
            if len(common) > 0:
                st.error('Carregue arquivo apenas com elementos orbitais no formato OMM', icon=cn.ERROR)
                st.stop()

            df_traj = df_traj.join(df_orb)

            col_first = ['NORAD_CAT_ID','OBJECT_NAME', 'RCS_SIZE']
            df_traj = columns_first(df_traj, col_first )

            st.session_state.ss_result_df = df_traj.sort_values(by='H0') 
            st.session_state.tr_data = sdf.tr_data
            # do not reset_index after this
                            
        else:
            if "ss_result_df" in st.session_state:
                del st.session_state.ss_result_df
            st.warning('O objeto espacial não se aproxima da localização inserida nesse periodo de tempo', icon=cn.WARNING)

        
        fim = tm.time()
        st.write("Tempo de processamento (s): ", np.round(fim - ini,3))

      
    if "ss_result_df" in st.session_state: 
        st.success('Trajetórias calculadas com sucesso: '+ str(len(st.session_state.ss_result_df.index)), icon=cn.SUCCESS)                      
        st.write('Resumo das trajetórias calculadas:')
        st.dataframe(st.session_state.ss_result_df.style.format(thousands="")) 
        
        st.selectbox("Selecione a hora de aproximação para ver a trajetória:",st.session_state.ss_result_df['H0'], key="choice_obj", help="help")
        sel_index = st.session_state.ss_result_df.loc[st.session_state.ss_result_df['H0'] == st.session_state["choice_obj"]].index #to_dict('records')[0]
        if 'tr_data' in st.session_state:
            st.dataframe(st.session_state.tr_data[sel_index[0]])
            st.write('O botão para baixar as tabelas aparece ao aproximar o mouse do canto superior direito das tabelas')
            st.write('Visualização no mapa:')             
            plot_map(st.session_state.tr_data[sel_index[0]], lc) 

    page_links()
    

if __name__== '__main__':
    main()
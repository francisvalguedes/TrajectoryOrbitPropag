import pydeck as pdk
import pandas as pd
import streamlit as st
import numpy as np
import pymap3d as pm


usecols = ['lat', 'lon']
df = pd.read_csv('test/data.csv',usecols=usecols)

def geodetic_circ(r,center_lat,center_lon):
    theta = np.linspace(0, 2*np.pi, 30)
    e =  1000*r*np.cos(theta)
    n =  1000*r*np.sin(theta)
    u =  np.zeros(len(theta))
    lat, lon, _ = pm.enu2geodetic(e, n, u,center_lat, center_lon, 0)
    dfn = pd.DataFrame(np.transpose([lat, lon]), columns=['lat', 'lon'])
    return dfn

dfn = geodetic_circ(10,df.iloc[-1].lat ,df.iloc[-1].lon)

df = pd.concat([df, dfn], axis=0)

#68.744825, -123.813838
dfn = geodetic_circ(1000,-5.919178, -35.1733)

df = pd.concat([df, dfn], axis=0)

st.dataframe(df)

st.map(df)



# st.map(df)
# st.write('teste')
# st.pydeck_chart(pdk.Deck(
#      map_style=None,
#      initial_view_state=pdk.ViewState(
#          latitude=-5.9,
#          longitude=-35.17,
#          zoom=8,
#          pitch=50,
#      ),
#      layers=[
#          pdk.Layer(
#             'HexagonLayer',
#             data=df,
#             get_position='[lon, lat]',
#             radius=200,
#             elevation_scale=4,
#             elevation_range=[0, 1000],
#             pickable=True,
#             extruded=True,
#          ),
#          pdk.Layer(
#              'ScatterplotLayer',
#              data=df,
#              get_position='[lon, lat]',
#              get_color='[200, 30, 0, 160]',
#              get_radius=200,
#          ),
#      ],
#  ))
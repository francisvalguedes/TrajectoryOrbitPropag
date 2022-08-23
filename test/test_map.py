import pydeck as pdk
import pandas as pd
import streamlit as st
import numpy as np

df = pd.DataFrame(
    np.random.randn(20, 2) / [30, 30] + [-5.919178, -35.1733],
    columns=['lat', 'lon'])
usecols = ['lat', 'lon']

df = pd.read_csv('test/data.csv',usecols=usecols)

dfn = pd.DataFrame(
            0.05*np.random.randn(100, 2) + [df.iloc[-1].lat ,df.iloc[-1].lon],
            columns=['lat', 'lon'])

df = pd.concat([df, dfn], axis=0)

dfn = pd.DataFrame(
            0.01*np.random.randn(100, 2) + [-5.919178, -35.1733],
            columns=['lat', 'lon'])

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
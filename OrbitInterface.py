# https://blog.jcharistech.com/2020/11/08/working-with-file-uploads-in-streamlit-python/

import streamlit as st
import pandas as pd
import datetime
import csv
import json
import shutil
from astropy.time import Time

from LocalSgp4PropagSistem import update_elements, rumm

from io_functions import dellfile, writetle, read_json


st.title("Propagador SGP4")

st.subheader('**Propagação de orbita e geração de trajetória para radar de trajetografia**')
st.markdown('Este app faz a busca de um ponto de aproximação de um objeto espacial em órbita da terra e traça um intervalo \
     de trajetória em um referecial plano local (ENU), para ser utilizado como direcionamento para rastreio por radar de trajetografia ')
st.markdown('Por: Francisval Guedes Soares, Email: francisval20@yahoo.com.br')

st.subheader('**Saídas:**')

# Seleção do modo de atualização dos elementos orbitais
st.sidebar.title("Elementos orbitais:")
menuUpdate = ["Space Track","Arquivo de elementos"]
choiceUpdate = st.sidebar.selectbox("Fonte dos elementos orbitais:",menuUpdate)
if choiceUpdate == "Space Track":
	SpaceTrackLoguin = st.sidebar.text_input('Space Track loguin',"francisval20@yahoo.com.br")
	SpaceTracksenha = st.sidebar.text_input('Space Track senha',"senha")

	#st.sidebar.markdown("Lista de NORAD_ID a propagar:")
	data_norad = st.sidebar.file_uploader("Carregar lista de NORAD_ID candidatos",type=['txt'])
	if st.sidebar.button("Atualizar Elementos"):
		if data_norad is not None:
			st.markdown('Arquivo de NORAD_IDS carregado:')
			file_details = {"Filename":data_norad.name,"FileType":data_norad.type,"FileSize":data_norad.size}
			st.write(file_details)
			st.markdown("NORAD_IDs:")   
			data = data_norad.read()            
			df_norad_ids = data.decode("UTF-8").strip().splitlines()
			st.dataframe(df_norad_ids)
			elem_json = update_elements(df_norad_ids,SpaceTrackLoguin,SpaceTracksenha)
			st.markdown('Elementos orbitais obtidos do Space Track:')
			st.dataframe(elem_json)		
		else:
			st.markdown("arquivo não carregado")

elif choiceUpdate == "Arquivo de elementos":
	data_elements = st.sidebar.file_uploader("Upload Json/TLE/3LE",type=['txt','json'])
	if st.sidebar.button("Carregar elementos orbitais"):
		if data_elements is not None:
			file_details = {"Filename":data_elements.name,"FileType":data_elements.type,"FileSize":data_elements.size}
			st.write(file_details)
			st.markdown("Elementos orbitais atualizados manualmente:")    
			if data_elements.type == "application/json":
				df = pd.read_json(data_elements)
				st.dataframe(df)
				dellfile('confTle.txt')
				dellfile('confElem.json')
				#df.to_json('confElem.json')
				data = data_elements.read()         
				df = data.decode("UTF-8")
				to_python = json.loads(df)

				with open("confElem.json", "wt") as fp:
					json.dump(to_python, fp)

				# data = data_elements.read()         
				# df = data.decode("UTF-8").replace("'", '"')
				# with open("confElem.json", "wt") as fp:
				# 	json.dump(df, fp)

			elif data_elements.type == "text/plain":
				data = data_elements.read()            
				df = data.decode("UTF-8")
				# txtarea = st.text_area("TLEs/3LEs",df,200) 
				st.dataframe(df.strip().splitlines())
				dellfile('confTle.txt')
				dellfile('confElem.json')
				#writetle('confTle.txt',df)
				dflist = df.strip().splitlines()
				print(dflist)
				with open('confTle.txt', "wt") as fp:
					for line in dflist:
						fp.write(str(line) + '\n')

st.sidebar.title("Configurações")

# Seleção do tempo de amostragem
sample_time = st.sidebar.number_input('Taxa de amostragem (s)', 0.1, 10.0, 1.0, step = 0.1)
st.write('Taxa de amostragem (s): ', sample_time)

# Seleção do modo de obtenção das trajetórias
menu = ["Automático","Manual"]
choice = st.sidebar.selectbox("Modo:",menu)

if choice == "Automático":
	conftragetoria = 0
 
	dmax = st.sidebar.number_input('Distâcia máxima para limites da trajetória (Km)',
		min_value = 400,
		max_value = 10000,
		value = 1000,
		step = 50)

	st.write('Distância máxima (Km): ', dmax)

	dmin = st.sidebar.number_input('O ponto de distância mínima da trajetória a partir do qual a trajetória é salva (Km)',
		min_value = 200,
		max_value = 5000,
		value = 800,
		step = 50)

	st.write('Distância mínima (Km): ', dmin)

	initial_date = st.sidebar.date_input("Data de inicio da busca automática do H0", key=1)
	initial_time = st.sidebar.time_input("Hora de inicio da busca automática do H0 TU", datetime.time(11, 0,0),  key=2)
	initial_datetime = datetime.datetime.combine(initial_date, initial_time)
	initial_datetime=Time(initial_datetime)
	initial_datetime.format = 'isot'
	st.write('Momento do final da busca: ', initial_datetime)

	final_date = st.sidebar.date_input("Data Final da busca automática do H0", key=3)
	final_time = st.sidebar.time_input("Hora de final da busca automática do H0 TU", datetime.time(19, 0,0),  key=4)
	final_datetime = datetime.datetime.combine(final_date, final_time)
	final_datetime=Time(final_datetime)
	final_datetime.format = 'isot'
	st.write('Momento do final da busca: ', final_datetime)

elif choice == "Manual":
	conftragetoria = 1
	st.sidebar.subheader("Manual")
	data_conf = st.sidebar.file_uploader("Upload configuração manual de H0",type=['csv'])
	if st.sidebar.button("Carregar configuração manual"):
		if data_conf is not None:
			file_details = {"Filename":data_conf.name,"FileType":data_conf.type,"FileSize":data_conf.size}
			st.write(file_details)
			df = pd.read_csv(data_conf)
			st.dataframe(df)			
		else:
			st.markdown("arquivo não carregado")
else:
	print("erro")

# Entrada de localização

st.markdown("Localização Geodésica WGS84 do referencial local:")
st.sidebar.title("Localização Geodésica WGS84:")
latitude = st.sidebar.number_input('Latitude',-90.0, 90.0, 0.0, format="%.5f")
longitude = st.sidebar.number_input('longitude', -180.0, 80.0, 0.0, format="%.5f")
altura = st.sidebar.number_input('Altura (m)',-1000.0, 2000.0, 0.0, format="%.5f")
nomeLoc = st.sidebar.text_input('Nome',"my location")

# Salvar a localização

with open("confLocalWGS84.json", 'r') as fp:
    loc = json.load(fp)
# with open("confLocalWGS84.json", "wt") as fp:
#     json.dump(loc, fp)
# lc = LocalFrame(-5.92256, -35.1615, 32.704)
if st.sidebar.button("Gravar localização"):
    localiz = {'Nome': nomeLoc, 'latitude': latitude, 'longitude': longitude, 'altura': altura }
    if nomeLoc not in list(map(str, [row["Nome"] for row in loc])):
        loc.append(localiz)
        with open("confLocalWGS84.json", "wt") as fp:
            json.dump(loc, fp)

menuloc = list(map(str, [row["Nome"] for row in loc]))
choiceLoc = st.sidebar.selectbox("local:",menuloc)
for sel in menuloc:
	if sel==choiceLoc:
		localizacao = loc[menuloc.index(choiceLoc)]
		print(localizacao)

if st.sidebar.button("Apagar localização"):
    if localizacao["Nome"] in list(map(str, [row["Nome"] for row in loc])):
        del loc[menuloc.index(choiceLoc)]
        print("apagar",loc)
        with open("confLocalWGS84.json", "wt") as fp:
            json.dump(loc, fp)
        #st._update_logger()

st.write('Nome: ', localizacao["Nome"])
st.write('latitude: ', localizacao["latitude"])
st.write('longitude: ', localizacao["longitude"])
st.write('altura: ', localizacao["altura"])

st.sidebar.title("Executar:")

if st.sidebar.button("Rodar"):
	if conftragetoria==0:
		rumm(localizacao,initial_datetime,final_datetime,sample_time,conftragetoria,dmin*1000,dmax*1000)
	else:
		rumm(localizacao,sample_time=sample_time ,conftragetoria=conftragetoria)
	
	df = pd.read_csv("results/" + 'planilhapy.csv')
	st.dataframe(df)
	shutil.make_archive('results', 'zip', './', 'results')

st.subheader('Arquivos:')
with open("results.zip", "rb") as fp:
	btn = st.download_button(
		label="Download ZIP",
		data=fp,
		file_name="results.zip",
		mime="application/zip"
	)


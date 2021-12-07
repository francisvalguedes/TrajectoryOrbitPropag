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
menuUpdate = ["Space-Track","Arquivo de elementos"]
choiceUpdate = st.sidebar.selectbox("Fonte dos elementos orbitais:",menuUpdate)
if choiceUpdate == "Space-Track":
	SpaceTrackLoguin = st.sidebar.text_input('Space-Track login:',"francisval20@yahoo.com.br")
	SpaceTracksenha = st.sidebar.text_input('Space-Track senha:',type="password")

	#st.sidebar.markdown("Lista de NORAD_ID a propagar:")
	data_norad = st.sidebar.file_uploader("Carregar lista de NORAD_ID candidatos:",type=['txt'], help='Arquivo de texto com uma unica coluna com os numeros NORAD_ID')
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
			st.markdown('Elementos orbitais obtidos do Space-Track:')
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
sample_time = st.sidebar.number_input('Taxa de amostragem (s):', 0.1, 10.0, 1.0, step = 0.1)
st.write('Taxa de amostragem (s): ', sample_time)

# Seleção do modo de obtenção das trajetórias
menu = ["Automático","Manual"]
choice = st.sidebar.selectbox("Modo de busca da trajetória:",menu)

if choice == "Automático":
	conftrajetoria = 0
 
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
	conftrajetoria = 1
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


# Salvar a localização

with open("confLocalWGS84.json", 'r') as fp:
    loc = json.load(fp)
# with open("confLocalWGS84.json", "wt") as fp:
#     json.dump(loc, fp)
# lc = LocalFrame(-5.92256, -35.1615, 32.704)
st.markdown("Localização Geodésica WGS84 do referencial local:")
st.sidebar.title("Localização Geodésica WGS84:")

menuloc = list(map(str, [row["Nome"] for row in loc]))
choiceLoc = st.sidebar.selectbox("local:",menuloc)
for sel in menuloc:
	if sel==choiceLoc:
		localizacao = loc[menuloc.index(choiceLoc)]
		print(localizacao)

#st.sidebar.markdown("Gravar nova localização:")
my_expander = st.sidebar.expander("Gerenciar localização:", expanded=False)

my_expander.markdown("Apagar localização selecionada:")
if my_expander.button("Apagar selecionada"):
    if localizacao["Nome"] in list(map(str, [row["Nome"] for row in loc])):
        del loc[menuloc.index(choiceLoc)]		
        print("apagar",loc)
        with open("confLocalWGS84.json", "wt") as fp:
            json.dump(loc, fp)
        # st._update_logger()

# Entrada de localização
my_expander.markdown("Gerar uma nova localização:")
# col1, col2 = my_expander.columns(2)
# col1, col2 = my_expander.columns(2)

# latitude = col21.number_input('Latitude',-90.0, 90.0, 0.0, format="%.5f")
# longitude = col22.number_input('longitude', -180.0, 80.0, 0.0, format="%.5f")
# altura = col12.number_input('Altura (m)',-1000.0, 2000.0, 0.0, format="%.5f")
# nomeLoc = col11.text_input('Nome',"my location")
nomeLoc = my_expander.text_input('Nome',"my location")
latitude = my_expander.number_input('Latitude',-90.0, 90.0, 0.0, format="%.5f")
longitude = my_expander.number_input('longitude', -180.0, 80.0, 0.0, format="%.5f")
altura = my_expander.number_input('Altura (m)',-1000.0, 2000.0, 0.0, format="%.5f")

if my_expander.button("Gravar nova localização"):
    localiz = {'Nome': nomeLoc, 'latitude': latitude, 'longitude': longitude, 'altura': altura }
    if nomeLoc not in list(map(str, [row["Nome"] for row in loc])):
        loc.append(localiz)
        with open("confLocalWGS84.json", "wt") as fp:
            json.dump(loc, fp)

st.write('Nome: ', localizacao["Nome"])
st.write('latitude: ', localizacao["latitude"])
st.write('longitude: ', localizacao["longitude"])
st.write('altura: ', localizacao["altura"])

st.sidebar.title("Executar:")

if st.sidebar.button("Calcular trajetórias"):
	if conftrajetoria==0:
		rumm(localizacao,sample_time,conftrajetoria,initial_datetime,final_datetime,dmin*1000,dmax*1000)
	else:
		rumm(localizacao,sample_time ,conftrajetoria)
	
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


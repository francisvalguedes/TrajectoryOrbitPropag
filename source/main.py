# https://blog.jcharistech.com/2020/11/08/working-with-file-uploads-in-streamlit-python/
# https://celestrak.com/satcat/search.php
import streamlit as st
import pandas as pd
import datetime
import json
import shutil
from astropy.time import Time

from lib.sistem import update_elements #, rumm

# from source.io_functions import dellfile, noradfileread

# import sys
# # global variables
# setattr(sys.modules["__main__"], "update_elements", update_elements)
# setattr(sys.modules["__main__"], "rumm", rumm)

def main():
    st.title("OPTR - Orbit Propagator Tracking Radar") #

    st.subheader('**Propagação de orbita de satélites e geração de trajetória, para rastreio por radar de trajetografia**')
    st.markdown('Este app faz a busca de um ponto de aproximação de um objeto espacial em órbita da terra, utilizando o SGP4, e traça um intervalo \
        de trajetória em um referecial plano local (ENU), para ser utilizado como direcionamento para rastreio por radar de trajetografia ')
    st.markdown('Por: Francisval Guedes Soares, Email: francisvalg@gmail.com')

    st.subheader('**Saídas:**')

    # Seleção do modo de atualização dos elementos orbitais
    st.sidebar.title("Elementos orbitais:")
    help=('Space-Track: Obtem os elementos orbitais automaticamente do Space-Track (exige cadastro no Space-Track e não aceita configuração de proxy)  \n'
        'Arquivo de elementos: Carregar arquivo de elementos de outra fonte ou obtido manualmento do Space-Track (TLE, 3LE ou JSON).')
    menuUpdate = ["Space-Track","Arquivo de elementos"]
    choiceUpdate = st.sidebar.selectbox("Fonte dos elementos orbitais:",menuUpdate,help=help)
    if choiceUpdate == "Space-Track":
        SpaceTrackLoguin = st.sidebar.text_input('Space-Track login:',"francisval20@yahoo.com.br")
        SpaceTracksenha = st.sidebar.text_input('Space-Track senha:',type="password")

        #st.sidebar.markdown("Lista de NORAD_ID a propagar:")
        data_norad = st.sidebar.file_uploader("Utilizar lista de NORAD_CAT_ID padrão ou carregar lista de NORAD_CAT_ID:", type=['csv'], help='Arquivo de texto com extensão .csv com uma unica coluna com os numeros NORAD_CAT_ID e com o texto NORAD_CAT_ID na primeira linha, se não for carregado será utilizada uma lista padrão')
        if st.sidebar.button("Atualizar Elementos"):
            if data_norad is not None:
                st.markdown('Arquivo de NORAD_CAT_ID carregado:')
                file_details = {"Filename":data_norad.name,"FileType":data_norad.type,"FileSize":data_norad.size}
                st.write(file_details)
                df_norad_ids = pd.read_csv(data_norad)            
                st.dataframe(df_norad_ids)
                elem_csv = update_elements(df_norad_ids.to_dict('list')["NORAD_CAT_ID"],SpaceTrackLoguin,SpaceTracksenha)
                st.markdown('Elementos orbitais obtidos do Space-Track:')
                st.dataframe(elem_csv)		
            else:
                st.markdown("arquivo NORAD_CAT_ID não carregado")
                df_norad_ids = pd.read_csv("data/norad_id.csv")
                elem_csv = update_elements(df_norad_ids.to_dict('list')["NORAD_CAT_ID"],SpaceTrackLoguin,SpaceTracksenha)
                st.markdown('Elementos orbitais obtidos do Space-Track a partir da lista de NORAD_CAT_ID padrão:')
                st.dataframe(elem_csv)	
                

    elif choiceUpdate == "Arquivo de elementos":
        data_elements = st.sidebar.file_uploader("Upload Json/TLE/3LE",type=['txt','json'])
        if st.sidebar.button("Carregar elementos orbitais"):
            if data_elements is not None:
                file_details = {"Filename":data_elements.name,"FileType":data_elements.type,"FileSize":data_elements.size}
                st.write(file_details)
                st.markdown("Elementos orbitais atualizados manualmente:")    
                if data_elements.type == "application/json":
                    df_elements = pd.read_json(data_elements)
                    st.dataframe(df_elements)

                elif data_elements.type == "application/csv":
                    df_elements = pd.read_csv(data_elements)
                    st.dataframe(df_elements)

    # st.sidebar.title("Configurações")

    # # Seleção do tempo de amostragem
    # sample_time = st.sidebar.number_input('Taxa de amostragem (s):', 0.1, 10.0, 1.0, step = 0.1)
    # st.write('Taxa de amostragem (s): ', sample_time)

    # # Seleção do modo de obtenção das trajetórias
    # automatico="Automático D-2"
    # manual="Manual D-1 e D"

    # help='Automático (D-2 ou antes): busca os periodos de aproximação, retorna as trajetórias e arquivos de configuração.  \n Manual (D-1 a D): recalcula as trajetórias com elementos orbitais atualizados, mantendo o H0, utilizando os arquivos de configuração obtidos em uma execução automática anterior'
    # menu = [automatico,manual]
    # choice = st.sidebar.selectbox("Modo de busca da trajetória:",menu, help=help )

    # if choice == automatico:
    #     conftrajetoria = 0

    #     dmax = st.sidebar.number_input('Distâcia máxima para limites da trajetória (Km)',
    #         min_value = 400,
    #         max_value = 10000,
    #         value = 1100,
    #         step = 50)

    #     st.write('Distância máxima (Km): ', dmax)

    #     dmin = st.sidebar.number_input('O ponto de distância mínima da trajetória a partir do qual a trajetória é salva (Km)',
    #         min_value = 200,
    #         max_value = 5000,
    #         value = 1000,
    #         step = 50)

    #     st.write('Distância mínima (Km): ', dmin)

    #     initial_date = st.sidebar.date_input("Data de inicio da busca automática do H0", key=1)
    #     initial_time = st.sidebar.time_input("Hora de inicio da busca automática do H0 TU", datetime.time(11, 0,0),  key=2)
    #     initial_datetime = datetime.datetime.combine(initial_date, initial_time)
    #     initial_datetime=Time(initial_datetime)
    #     initial_datetime.format = 'isot'
    #     st.write('Momento do final da busca: ', initial_datetime)

    #     final_date = st.sidebar.date_input("Data Final da busca automática do H0", key=3)
    #     final_time = st.sidebar.time_input("Hora de final da busca automática do H0 TU", datetime.time(19, 0,0),  key=4)
    #     final_datetime = datetime.datetime.combine(final_date, final_time)
    #     final_datetime=Time(final_datetime)
    #     final_datetime.format = 'isot'
    #     st.write('Momento do final da busca: ', final_datetime)

    # elif choice == manual:
    #     conftrajetoria = 1
    #     st.sidebar.subheader("Manual")
    #     help='Upload do arquivo de configuração manual de H0: arquivo confH0.csv de uma execução em automático anterior ou editado a partir dele'
    #     data_conf = st.sidebar.file_uploader("Upload configuração manual de H0 (confH0.csv)",type=['csv'],help=help)
    #     if st.sidebar.button("Carregar configuração manual"):
    #         if data_conf is not None:
    #             file_details = {"Filename":data_conf.name,"FileType":data_conf.type,"FileSize":data_conf.size}
    #             st.write(file_details)
    #             df = pd.read_csv(data_conf)
    #             st.dataframe(df)			
    #         else:
    #             st.markdown("arquivo não carregado")
    # else:
    #     print("erro")


    # # Salvar a localização

    # with open("confLocalWGS84.json", 'r') as fp:
    #     loc = json.load(fp)
    # # with open("confLocalWGS84.json", "wt") as fp:
    # #     json.dump(loc, fp)
    # # lc = LocalFrame(-5.92256, -35.1615, 32.704)
    # st.markdown("Localização Geodésica WGS84 do referencial local:")
    # st.sidebar.title("Localização Geodésica WGS84:")

    # menuloc = list(map(str, [row["Nome"] for row in loc]))
    # choiceLoc = st.sidebar.selectbox("local:",menuloc)
    # for sel in menuloc:
    #     if sel==choiceLoc:
    #         localizacao = loc[menuloc.index(choiceLoc)]
    #         print(localizacao)

    # #st.sidebar.markdown("Gravar nova localização:")
    # my_expander = st.sidebar.expander("Gerenciar localização:", expanded=False)

    # my_expander.markdown("Apagar localização selecionada:")
    # if my_expander.button("Apagar selecionada"):
    #     if localizacao["Nome"] in list(map(str, [row["Nome"] for row in loc])):
    #         del loc[menuloc.index(choiceLoc)]		
    #         print("apagar",loc)
    #         with open("confLocalWGS84.json", "wt") as fp:
    #             json.dump(loc, fp)
    #         # st._update_logger()

    # # Entrada de localização
    # my_expander.markdown("Gerar uma nova localização:")
    # # col1, col2 = my_expander.columns(2)
    # # col1, col2 = my_expander.columns(2)

    # # latitude = col21.number_input('Latitude',-90.0, 90.0, 0.0, format="%.5f")
    # # longitude = col22.number_input('longitude', -180.0, 80.0, 0.0, format="%.5f")
    # # altura = col12.number_input('Altura (m)',-1000.0, 2000.0, 0.0, format="%.5f")
    # # nomeLoc = col11.text_input('Nome',"my location")
    # nomeLoc = my_expander.text_input('Nome',"my location")
    # latitude = my_expander.number_input('Latitude',-90.0, 90.0, 0.0, format="%.6f")
    # longitude = my_expander.number_input('longitude', -180.0, 80.0, 0.0, format="%.6f")
    # altura = my_expander.number_input('Altura (m)',-1000.0, 2000.0, 0.0, format="%.6f")

    # if my_expander.button("Gravar nova localização"):
    #     localiz = {'Nome': nomeLoc, 'latitude': latitude, 'longitude': longitude, 'altura': altura }
    #     if nomeLoc not in list(map(str, [row["Nome"] for row in loc])):
    #         loc.append(localiz)
    #         with open("confLocalWGS84.json", "wt") as fp:
    #             json.dump(loc, fp)

    # st.write('Nome: ', localizacao["Nome"])
    # st.write('latitude: ', localizacao["latitude"])
    # st.write('longitude: ', localizacao["longitude"])
    # st.write('altura: ', localizacao["altura"])

    # st.sidebar.title("Executar:")

    # if st.sidebar.button("Calcular trajetórias"):
    #     if conftrajetoria==0:
    #         rumm(localizacao,sample_time,conftrajetoria,initial_datetime,final_datetime,dmax*1000,dmin*1000)
    #     else:
    #         rumm(localizacao,sample_time ,conftrajetoria)
        
    #     df = pd.read_csv("results/" + 'planilhapy.csv')
    #     st.dataframe(df)
    #     shutil.make_archive('results', 'zip', './', 'results')

    #     st.subheader('Arquivos:')
    #     with open("results.zip", "rb") as fp:
    #         btn = st.download_button(
    #             label="Download ZIP",
    #             data=fp,
    #             file_name="results.zip",
    #             mime="application/zip"
    #         )

if __name__== '__main__':
    main()
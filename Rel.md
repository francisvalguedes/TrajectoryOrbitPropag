# Relatório Técnico sobre o Desenvolvimento de Aplicativo para Geração de Trajetórias Espaciais

## 1. Introdução

Este relatório apresenta o desenvolvimento de um aplicativo para geração de trajetórias de rastreamento de objetos espaciais. O aplicativo foi desenvolvido utilizando Python e Streamlit, incorporando bibliotecas como Pandas, Folium, NumPy, SGP4, Astropy e Pymap3d. Seu objetivo é calcular trajetórias que possibilitem o apontamento de sensores de rastreamento, como radares de trajetografia, sensores ópticos e observação a olho nu.

O software processa elementos orbitais extraídos do Space-Track ou Celestrak e, por meio do modelo SGP4, realiza a propagação da órbita dos objetos espaciais. Além disso, implementa conversões de coordenadas para calcular aproximações ao ponto de referência e gerar trajetórias com instante inicial (H0) para rastreamento.

### Modelos e Sistemas de Coordenadas

O modelo SGP4 (Simplified General Perturbations Model 4) é um dos mais utilizados para a propagação de elementos orbitais de satélites. Ele utiliza elementos orbitais no formato OMM (Orbit Mean-Elements Message) para prever a posição de um satélite em determinado instante de tempo.

Os sistemas de coordenadas envolvidos incluem:
- **TEME (True Equator Mean Equinox)**: Sistema de referência orbital associado aos elementos OMM.
- **ITRS (International Terrestrial Reference System)**: Sistema fixo à Terra, base para coordenadas geodésicas.
- **ECEF (Earth-Centered, Earth-Fixed)**: Sistema centrado na Terra e fixo em relação à sua rotação.
- **ENU (East-North-Up)**: Sistema de coordenadas locais relativo a um observador.
- **Coordenadas Geodésicas (Latitude, Longitude e Altitude)**: Sistema utilizado para representar posições na superfície terrestre.
- **Azimute, Elevação e Range**: Representação do apontamento de um sensor, com azimute (direção horizontal), elevação (altura acima do horizonte) e range (distância do alvo).

## 2. Funcionalidades do Aplicativo

O aplicativo possui as seguintes funcionalidades principais:
- **Leitura de Elementos Orbitais**: Importa dados do Space-Track e Celestrak.
- **Propagação de Órbitas**: Utiliza o modelo SGP4 para calcular a trajetória orbital do objeto.
- **Conversões de Coordenadas**: Implementa conversão entre TEME, ITRS, ECEF, ENU e coordenadas geodésicas.
- **Geração de Trajetórias**: Determina pontos de aproximação ao observador e define instantes de rastreamento (H0).
- **Visualização em Mapa**: Utiliza Folium para exibir trajetórias em mapas interativos.
- **Interface Bilíngue**: Suporte a inglês e português utilizando gettext.

## 3. Estrutura do Aplicativo

O aplicativo é organizado em diferentes páginas, cada uma dedicada a uma funcionalidade específica:

### Páginas Principais:
- 🏠 **Página Inicial**: Página de boas-vindas do aplicativo.
- 0️⃣ **Configuração Simplificada - Funções Básicas do APP**: Configuração simplificada com funções essenciais do aplicativo.

### Páginas com Configurações Específicas:
- 1️⃣ **Obter Elementos Orbitais**: Obtenção dos elementos orbitais.
- 2️⃣ **Propagação Orbital**: Propagação da órbita.
- 3️⃣ **Visualização no Mapa**: Exibição das trajetórias em mapas interativos.
- 4️⃣ **Mudança Orbital/Manobra do Objeto**: Modificação orbital e manobras do objeto.
- 5️⃣ **Seleção de Trajetória Específica para Sensores**: Escolha de trajetória personalizada para sensores específicos, incluindo um indicador visual de rastreabilidade por radar, classificado por cores, que considera a equação de radar, a distância e o RCS (Radar Cross Section) do objeto.

## 4. Tecnologias Utilizadas

- **Linguagem**: Python
- **Framework**: Streamlit
- **Bibliotecas**: Pandas, Folium, NumPy, SGP4, Astropy, Pymap3d
- **Internacionalização**: Gettext

Todas as bibliotecas utilizadas são **open-source**, o que permite uma comunidade ativa de desenvolvimento e contribuições constantes para sua melhoria. Isso facilita a manutenção do código, a colaboração entre desenvolvedores e o uso de ferramentas de ponta para cálculos e visualizações.

## 5. Conclusão e Considerações Finais

O aplicativo desenvolvido apresenta uma solução eficiente para auxiliar no rastreamento de objetos espaciais por meio da geração de trajetórias preditivas. Ele possibilita a integração com diferentes tipos de sensores e fornece informações essenciais para a observação precisa de satélites e outros corpos orbitais.

O aprimoramento futuro do aplicativo pode incluir:
- Integração com bases de dados adicionais.
- Melhor visualização 3D das trajetórias.
- Implementação de otimização para redução de erros de previsão.

O desenvolvimento do aplicativo contou com sugestões e ajustes de outros profissionais, garantindo maior precisão e usabilidade para diferentes tipos de usuários na área de rastreamento orbital.

A adoção de tecnologias open-source e a utilização de bibliotecas amplamente testadas reforçam a confiabilidade do software. Além disso, a interface bilíngue torna a ferramenta acessível a uma gama maior de usuários, promovendo a colaboração internacional no monitoramento de objetos espaciais.

## 6. Colaboradores

Este projeto contou com a colaboração dos seguintes profissionais:
- Nome 1
- Nome 2
- Nome 3

## 7. Links e Referências

- **Repositório no GitHub**: [Inserir link aqui]
- **LinkedIn**: [Inserir link aqui]
- **Vídeo Demonstrativo**: [Inserir link aqui]


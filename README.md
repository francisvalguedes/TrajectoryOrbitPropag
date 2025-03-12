# Orbit Propagator for Tracking Earth's Artificial Satellites in LEO

Satellite orbit propagation and trajectory generation, for optical and radar tracking of space objects (Debris, Rocket Body, Payload) i.e. artificial satellites, especially for low Earth orbit (LEO) objects.

### Links and References

- **LinkedIn**: [[link](https://www.linkedin.com/pulse/aplicativo-streamlit-de-m%25C3%25BAltiplas-p%25C3%25A1ginas-bil%25C3%25ADngue-e-guedes-soares-1zi9f)]
- **Medium**: [[link](https://trajectoryorbitpropag.streamlit.app/)]
- **App**: [[link](https://trajectoryorbitpropag.streamlit.app/)]
  
## 1. Introduction

The software processes orbital elements extracted from Space-Track or Celestrak and, through the SGP4 model, propagates the orbit of space objects. Additionally, it implements coordinate conversions to calculate approximations to the reference point and generate trajectories with an initial instant (H0) for tracking.

### Models and Coordinate Systems

The SGP4 (Simplified General Perturbations Model 4) is one of the most widely used models for propagating satellite orbital elements. It uses orbital elements in the OMM (Orbit Mean-Elements Message) format to predict a satellite's position at a given time.

The coordinate systems involved include:
- **TEME (True Equator Mean Equinox)**: Orbital reference system associated with OMM elements.
- **ITRS (International Terrestrial Reference System)**: Earth-fixed system, serving as the basis for geodetic coordinates.
- **ECEF (Earth-Centered, Earth-Fixed)**: Earth-centered system fixed relative to its rotation.
- **ENU (East-North-Up)**: Local coordinate system relative to an observer.
- **Geodetic Coordinates (Latitude, Longitude, and Altitude)**: System used to represent positions on Earth's surface.
- **Azimuth, Elevation, and Range**: Sensor pointing representation, with azimuth (horizontal direction), elevation (height above the horizon), and range (target distance).

### Block diagram

<img src="figures/bloc.png" width="600" />

## 2. Application Features

The application has the following main features:
- **Reading Orbital Elements**: Imports data from Space-Track and Celestrak.
- **Orbit Propagation**: Uses the SGP4 model to compute the object's orbital trajectory.
- **Coordinate Conversions**: Implements conversion between TEME, ITRS, ECEF, ENU, and geodetic coordinates.
- **Trajectory Generation**: Determines approximation points to the observer and defines tracking instants (H0).
- **Map Visualization**: Uses Folium to display trajectories on interactive maps.
- **Bilingual Interface**: Supports English and Portuguese using gettext.

## 3. Application Structure

The application is organized into different pages, each dedicated to a specific functionality:

### Main Pages:
- 🏠 **Home Page**: Welcome page of the application.
- 0️⃣ **Simplified Configuration - Basic Functions of the APP**: Simplified setup with essential application functions.

### Pages with Specific Settings:
- 1️⃣ **Obtain Orbital Elements**: Acquisition of orbital elements.
- 2️⃣ **Orbit Propagation**: Orbit propagation.
- 3️⃣ **Map Visualization**: Display of trajectories on interactive maps.
- 4️⃣ **Orbital Change/Object Maneuvering**: Orbital modification and object maneuvers.
- 5️⃣ **Selection of Specific Trajectories for Sensors**: Choice of custom trajectory for specific sensors, including a visual indicator of radar traceability, classified by colors, considering the radar equation, distance, and the object's RCS (Radar Cross Section).

## 4. Technologies Used

- **Language**: Python
- **Framework**: Streamlit
- **Libraries**: Pandas, Folium, NumPy, SGP4, Astropy, Pymap3d
- **Internationalization**: Gettext

All libraries used are **open-source**, which enables an active development community and constant contributions for improvement. This facilitates code maintenance, developer collaboration, and the use of cutting-edge tools for calculations and visualizations.


## Pré-requisitos  

### Windows  
1. Instale o Python (>= 3.8) através do [site oficial do Python](https://www.python.org/).  
2. Certifique-se de que o **pip** está instalado. Você pode verificar usando:  

```bash  
   pip --version  
   python -m pip install --upgrade pip  
```  

### Linux (Debian/Ubuntu)  
1. Atualize os pacotes do sistema e instale o Python caso não tenha instalado:  
```bash  
   sudo apt update && sudo apt upgrade -y  
   sudo apt install python3-pip 
```  

---

## Installation - script

1. Clone this repository:
```bash  
git clone https://github.com/francisvalguedes/TrajectoryOrbitPropag.git
cd TrajectoryOrbitPropag
```

For debian/ubuntu: clone repository then without sudo:

```bash 
./install_debian.sh
```

the install_debian.sh file will create a python environment in an env folder located in the repository folder and install the dependencies in the file requirements.txt

## Installation - manual

1. Clone this repository:

```bash  
   sudo apt install git
   git clone https://github.com/francisvalguedes/TrajectoryOrbitPropag.git  
   cd TrajectoryOrbitPropag 
``` 

2. Create and activate a virtual environment:
   
   - On Windows:

```bash  
     python -m venv env  
     env\Scripts\activate
     pip install --upgrade pip
```  

   - On Linux:

```bash  
     sudo apt install virtualenv
     virtualenv env     
     source env/bin/activate 
     pip install --upgrade pip
```  

3. Install the project dependencies:

```bash  
   pip install -r requirements.txt  
```  

## Run the streamlit application:

Activate env and run streamlit app

```bash  
cd TrajectoryOrbitPropag
streamlit run source/main.py  --server.port 8080
```  
or

```bash 
./run.sh
```

3. Open the link in shel (`http://localhost:8080`).  


### In a server: if necessary redirect port 80 to 8080

Test if the web server works on port 8080: my_ip_address:8080

to redirect the port: 
~~~
netstat -i
~~~

Redirect app port 8080 to web server port 80 according to connection name obtained above:
~~~
sudo iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8080
~~~

test if web server works without specifying port, by typing in browser: my_ip_address. If it works then make the redirect permanent:
~~~
sudo apt-get install iptables-persistent
~~~

if already isntalled then restart it:
~~~
sudo dpkg-reconfigure iptables-persistent
~~~

now save iptables permenantley to files:
~~~
sudo iptables-save | sudo tee /etc/iptables/rules.v4
sudo ip6tables-save | sudo tee /etc/iptables/rules.v6
~~~

## Estrutura do Projeto  
```
.
├── source/  
│   ├── main.py  
│   ├── pages/  
|   |   └── 00_Simplified.py 
|   |   └── 01_orbital_elements.py 
|   |   └── 02_orbit_propagation.py 
|   |   └── 03_map.py 
|   |   └── 04_orbit_compare.py 
│   │   └── 05_trajectory.py  
├── lib/  
│   ├── constants.py  
│   └── orbit_functions.py 
│   └── pages_functions.py 
├── data/  
│   └── confLocalWGS84.csv 
│   └── ...celestrak.csv 
├── locales/  
│   └── map_tilelayer.json 
├── requirements.txt  
├── LICENSE
├── install_debian.sh
├── run.sh 
└── README.md 
```  

## Libraries Used

- SGP4 - MIT License
- Astropy - BSD-3-Clause
- pandas - BSD-3-Clause
- numpy - BSD-3-Clause
- streamlit - Apache 2.0
- pymap3d - BSD-2-Clause
- Geopandas - BSD 3-Clause License
- Folium - MIT License
  
## Contribution

- Contributions are welcome! Feel free to open issues and pull requests.

## License

- This project is licensed under the MIT License. See the LICENSE file for more details.

## Author

- Autor: Francisval Guedes Soares,- 
- Contributions/suggestions from: Felipe Longo, Hareton, André Henrique, Marcos Leal, Leilson, Alan Karlo.

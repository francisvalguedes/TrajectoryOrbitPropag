# Orbit Propagator for Tracking Earth's Artificial Satellites in LEO

Satellite orbit propagation and trajectory generation for tracking of space objects—including debris, rocket bodies, and payloads—focusing primarily on artificial satellites in low Earth orbit (LEO).

### Links

- **LinkedIn**: [[linkedin](https://www.linkedin.com/pulse/aplicativo-streamlit-de-m%C3%BAltiplas-p%C3%A1ginas-bil%C3%ADngue-e-guedes-soares-1zi9f)]
- **Medium**: [[medium](https://medium.com/@francisvalg/aplicativo-streamlit-de-multiplas-multilingual-streamlit-app-for-orbital-propagation-and-space-1b7068fd4914)]
- **App**: [[Link1](http://www.orbittracking.duckdns.org/)]
- **App**: [[Link2](https://trajectoryorbitpropag.streamlit.app/)]

# Table of Contents

- [Orbit Propagator for Tracking Earth's Artificial Satellites in LEO](#orbit-propagator-for-tracking-earths-artificial-satellites-in-leo)
    - [Links](#links)
- [Table of Contents](#table-of-contents)
  - [1. Introduction](#1-introduction)
    - [Models and Coordinate Systems](#models-and-coordinate-systems)
    - [Block diagram](#block-diagram)
  - [2. Application Features](#2-application-features)
  - [3. Application Structure](#3-application-structure)
    - [Main Pages:](#main-pages)
    - [Pages with Specific Settings:](#pages-with-specific-settings)
  - [4. Technologies Used](#4-technologies-used)
  - [5. Prerequisites](#5-prerequisites)
    - [Windows](#windows)
    - [Linux (Debian/Ubuntu)](#linux-debianubuntu)
  - [6. Installation](#6-installation)
    - [Installation Script](#installation-script)
    - [Installation - manual](#installation---manual)
  - [7. Usage](#7-usage)
    - [In a server: if necessary redirect port 80 to 8080](#in-a-server-if-necessary-redirect-port-80-to-8080)
  - [8. Project Structure](#8-project-structure)
  - [9. Libraries Used](#9-libraries-used)
  - [10. Contribution](#10-contribution)
  - [11. License](#11-license)
  - [12. Author](#12-author)
  
## 1. Introduction

The software processes orbital elements extracted from Space-Track or Celestrak and, through the SGP4 model, propagates the orbit of space objects. Additionally, it implements coordinate conversions to calculate approximations to the reference point and generate trajectories with an initial instant (H0) for tracking.

### Models and Coordinate Systems

The python implementation of SGP4 (Simplified General Perturbations Model 4) uses orbital elements in the OMM (Orbit Mean-Elements Message) format to predict the position of a satellite at a given time.

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
- 5️⃣ **Selection of Specific Trajectories for Sensors**: Choice of custom trajectory for specific sensors.

## 4. Technologies Used

- **Language**: Python
- **Framework**: Streamlit
- **Libraries**: Pandas, Folium, NumPy, SGP4, Astropy, Pymap3d
- **Internationalization**: Gettext

## 5. Prerequisites  

### Windows  
1. Install Python (>= 3.11) from the [official Python website](https://www.python.org/).  
2. Ensure that **pip** is installed. You can verify this by running:  

```bash  
pip --version  
python -m pip install --upgrade pip  
```  

### Linux (Debian/Ubuntu)  
1. Update system packages and install Python if it is not already installed:  

```bash  
sudo apt update && sudo apt upgrade -y  
sudo apt install python3-pip  
```  

---  

## 6. Installation

### Installation Script

1. Clone this repository:  

```bash  
git clone https://github.com/francisvalguedes/TrajectoryOrbitPropag.git  
cd TrajectoryOrbitPropag  
```  

For Debian/Ubuntu: Clone the repository and run the installation script without sudo:  

```bash  
./install_debian.sh  
```

the install_debian.sh file will create a python environment in an env folder located in the repository folder and install the dependencies in the file requirements.txt

### Installation - manual

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

## 7. Usage

Activate env and run streamlit app

```bash  
cd TrajectoryOrbitPropag
streamlit run source/main.py  --server.port 8080
```  
or

```bash 
./run.sh
```

Open the link in shel (`http://localhost:8080`).  


### In a server: if necessary redirect port 80 to 8080

with the app running

confirm that the server is running on port 8080

~~~
curl http://localhost:8080
~~~

check active rules in iptables

~~~
sudo iptables -t nat -L PREROUTING -n -v
sudo iptables -L OUTPUT -n -v
~~~

Redirect app port 8080 to web server port 80:

~~~
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
~~~

test if web server works without specifying port, by typing in browser: my_ip_address. If it works then make the redirect permanent:

~~~
sudo apt-get install iptables-persistent
~~~

if already isntalled then restart it:

~~~
sudo dpkg-reconfigure iptables-persistent
~~~

## 8. Project Structure

```
TrajectoryOrbitPropag/
├─ .streamlit/
│  └─ config.toml
├─ data/
│  ├─ celestrak/
│  │  └─ teste.md
│  ├─ confLocalWGS84.csv
│  ├─ confRadar.csv
│  ├─ norad_id.csv
│  └─ RCS.csv
├─ figures/
│  └─ ...
├─ locales/
│  ├─ pt-BR/
│  │  └─ LC_MESSAGES/
│  │     └─ ...
│  └─ README.md
├─ source/
│  ├─ lib/
│  │  ├─ constants.py
│  │  ├─ orbit_functions.py
│  │  └─ pages_functions.py
│  ├─ pages/
│  │  ├─ 00_Simplified.py
│  │  ├─ 01_orbital_elements.py
│  │  ├─ 02_orbit_propagation.py
│  │  ├─ 03_map.py
│  │  ├─ 04_orbit_compare.py
│  │  └─ 05_trajectory.py
│  └─ main.py
├─ .gitignore
├─ conf.json
├─ get_translate.py
├─ install_debian.sh
├─ LICENSE
├─ localazy.json
├─ README.md
├─ requirements.txt
└─ run.sh
```  


## 9. Libraries Used

- SGP4 - MIT License
- Astropy - BSD-3-Clause
- pandas - BSD-3-Clause
- numpy - BSD-3-Clause
- streamlit - Apache 2.0
- pymap3d - BSD-2-Clause
- Geopandas - BSD 3-Clause License
- Folium - MIT License
  
## 10. Contribution

- Contributions are welcome! Feel free to open issues and pull requests.

## 11. License

- This project is licensed under the MIT License. See the LICENSE file for more details.

## 12. Author

- Autor: Francisval Guedes Soares,- 
- Contributions/suggestions from: Felipe Longo, Hareton, André Henrique, Marcos Leal, Leilson, Alan Karlo.

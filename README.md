# Orbit Propagator for Tracking Earth's Artificial Satellites in LEO

Satellite orbit propagation and trajectory generation, for optical and radar tracking of space objects (Debris, Rocket Body, Payload) i.e. artificial satellites, especially for low Earth orbit (LEO) objects.

## Developer:

Francisval Guedes, Email: francisvalg@gmail.com

## Introduction

Using SGP4 this app searches for a period of sensor approach of a space object in Earth orbit and traces a trajectory interval in: local plane reference (ENU), AltAzRange, ITRS and Geodetic, to be used as a target for optical or radar tracking system.

## Installation

For debian/ubuntu: clone repository then without sudo:

~~~ 
./install_debian.sh
~~~

the install_debian.sh file will create a python environment in an env folder located in the repository folder and install the dependencies in the file requirements.txt

## Run App streamlit server:

Activate env and run streamlit app
~~~ 
./run.sh
~~~

## If necessary redirect port 80 to 8080

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

# Switchport Capacity Dashboard

The purpose of this project was to build a simple dashboard to display current switch port capacity/availablity within a network. For example, maybe a network admin needs to onboard a handful of new users - using this dashboard, they could quickly look across their network for a switch that has enough available ports. 

The current state of the dashboard:
 - Collect version/hardware/port info from IOS-XE/NX-OS devices
 - Display summary dashboard
 - Individual switch detail page, reachable by clicking on switch hostname
 - Network-wide aggregate statistics (Total ports, port types, top 5 hardware/software versions, etc)

The web dashboard is built on top of scrapli, Cisco Genie, flask, and bootstrap.

More details can be found in my blog post: [here](https://0x2142.com/web-dashboard-flask-and-bootstrap).


*As a note: This is just a side project of mine & is not neccessarily ready for production use. Feel free to use / modify / etc at your own risk*

## Primary components

`data_collector.py` - This script handles connecting out to IOS-XE / NX-OS devices and collecting inventory & switchport information. One the data is collected and processed, it is inserted into a sqlite database.

`config.yml` - Configuration file that will hold all of the target devices to be monitored. 

`switchdb.py` - This module contains all logic related to the sqlite database management.

`switchport_web.py` - This contains all code for the frontend Flask dashboard. Handles inbound user requests, pulling information from the database, and rendering the HTML templates to return.

`/templates/` - This folder holds all of the HTML / Jinja2 templates that are used with Flask to render web pages.

`/static/` - This folder holds static CSS and image files.


## Installation

1. Clone repo
2. Install requirements: `pipenv install`
3. Edit `config.yml` to add target devices to monitor 
4. Set up cron to run `data_collector.py` at your preferred interval
5. Run `switchport_web.py` for the web portion


## Screenshots

Example of the main dashboard page: 

<p align="center">
<img src="https://github.com/0x2142/switchport-web-dashboard/blob/main/screenshots/dashboard-example.PNG?raw=true"></img>
</p>

Example of the switch detail page: 

<p align="center">
<img src="https://github.com/0x2142/switchport-web-dashboard/blob/main/screenshots/dashboard-detail-example.PNG"></img>
</p>

Example of the network-wide aggregate stats:

<p align="center">
<img src="https://github.com/0x2142/switchport-web-dashboard/blob/main/screenshots/dashboard-aggregate-example.PNG"></img>
</p>

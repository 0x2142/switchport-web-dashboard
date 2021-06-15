from collections import Counter

from flask import Flask, render_template
from flask_bootstrap import Bootstrap

import switchdb


app = Flask(__name__)


@app.route("/", methods=["GET"])
def switch_inventory():
    """
    Main web page, displays summary statistics of all switches
    """
    lastupdate = getLastUpdate()
    switchdata = getSwitchInfo()
    return render_template("main.html", switches=switchdata, lastupdate=lastupdate)


@app.route("/<serial>", methods=["GET"])
def switch_info(serial):
    """
    This page shows detailed stats on an individual switch
    queried by serial number
    """
    detail = getSwitchDetail(serial)
    intdetail = getInterfaceDetail(serial)
    try:
        raw_data = open(f"raw_output/{serial}.txt", "r").read().splitlines()
    except:
        raw_data = "None collected yet"
    return render_template(
        "detail.html",
        title=serial,
        switch=detail,
        interfaces=intdetail,
        raw_data=raw_data,
    )


@app.route("/network-wide", methods=["GET"])
def network_wide():
    """
    This page shows a summary of all port counts, etc
    across the entire network
    """
    network = getNetworkWide()
    return render_template("network-wide.html", network=network)


@app.route("/lastupdate", methods=["GET"])
def getLastUpdate():
    """
    Check DB for last runtime of backend script
    This is published on the main page to see when stats were last updated
    """
    swDB = switchdb.DB()
    lastupdate = swDB.getLastUpdate()
    swDB.close()
    return lastupdate


def getSwitchInfo():
    """
    Query DB for summary info on all
    switches currently monitored
    """
    swDB = switchdb.DB()
    raw_info = swDB.getAllSummary()
    switchList = []
    for row in raw_info:
        row = list(row)
        switch = {}
        switch["name"] = row[0]
        switch["serial"] = row[1]
        switch["swver"] = row[2]
        switch["ip"] = row[3]
        switch["check"] = row[4]
        switch["total"] = row[5]
        switch["up"] = row[6]
        switch["down"] = row[7]
        switch["disabled"] = row[8]
        if switch["total"] == 0:
            switch["capacity"] = 0
        else:
            switch["capacity"] = (switch["up"] / switch["total"]) * 100
        switchList.append(switch)
    swDB.close()
    return switchList


def getSwitchDetail(serial):
    """
    Query DB for details on one specific device
    by serial number
    """
    swDB = switchdb.DB()
    raw_info = swDB.getSwitchDetail(serial)
    switch = {}
    for row in raw_info:
        switch["name"] = row[0]
        switch["serial"] = row[1]
        switch["model"] = row[2]
        switch["swver"] = row[3]
        switch["ip"] = row[4]
        switch["check"] = row[5]
        switch["total"] = row[6]
        switch["up"] = row[7]
        switch["down"] = row[8]
        switch["disabled"] = row[9]
        switch["int10m"] = row[10]
        switch["int100m"] = row[11]
        switch["int1g"] = row[12]
        switch["int10g"] = row[13]
        switch["int25g"] = row[14]
        switch["int40g"] = row[15]
        switch["int100g"] = row[16]
        switch["copper"] = row[17]
        switch["sfp"] = row[18]
        switch["virtual"] = row[19]
        if switch["total"] == 0:
            switch["capacity"] = 0
        else:
            switch["capacity"] = int((switch["up"] / switch["total"]) * 100)
    swDB.close()
    return switch


def getInterfaceDetail(serial):
    """
    Query DB for interface details on one specific device
    by management IP
    """
    swDB = switchdb.DB()
    raw_info = swDB.getInterfaceDetail(serial)
    interfaceList = []
    for row in raw_info:
        row = list(row)
        interface = {}
        interface["name"] = row[0]
        interface["description"] = row[1]
        interface["physical_address"] = row[2]
        interface["oper_status"] = row[3]
        interface["oper_speed"] = row[4]
        interface["oper_duplex"] = row[5]
        interfaceList.append(interface)
    return interfaceList


def getNetworkWide():
    """
    Query DB for all switch statistcs,
    then tally results & return to web page
    """
    swDB = switchdb.DB()
    result = swDB.getNetworkWideStats()
    swDB.close()
    network = {
        "models": [],
        "swvers": [],
        "total": 0,
        "up": 0,
        "down": 0,
        "disabled": 0,
        "int10m": 0,
        "int100m": 0,
        "int1g": 0,
        "int10g": 0,
        "int25g": 0,
        "int40g": 0,
        "int100g": 0,
        "copper": 0,
        "sfp": 0,
        "virtual": 0,
    }
    modellist = []
    swlist = []
    for row in result:
        if "N/A" not in row[0]:
            modellist.append(row[0])
        if "N/A" not in row[1]:
            swlist.append(row[1])
        network["total"] += row[2]
        network["up"] += row[3]
        network["down"] += row[4]
        network["disabled"] += row[5]
        network["int10m"] += row[6]
        network["int100m"] += row[7]
        network["int1g"] += row[8]
        network["int10g"] += row[9]
        network["int25g"] += row[10]
        network["int40g"] += row[11]
        network["int100g"] += row[12]
        network["copper"] += row[13]
        network["sfp"] += row[14]
        network["virtual"] += row[15]
    # Get 5 most common models / software versions
    network["models"] = Counter(modellist).most_common(5)
    network["swvers"] = Counter(swlist).most_common(5)
    return network


def deleteDevice(serial):
    """
    Call to DB to delete a device by serial number
    """
    swDB = switchdb.DB()
    swDB.deleteBySerial(serial)
    swDB.close()


if __name__ == "__main__":
    Bootstrap(app)
    app.run(debug=True)

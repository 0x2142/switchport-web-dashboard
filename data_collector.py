import os

import yaml
from scrapli.driver.core import IOSXEDriver, NXOSDriver

import switchdb



def loadDevices():
    """
    Load device inventory from config.yml
    """
    print("Loading devices from config file...")
    with open("config.yml", "r") as config:
        devicelist = yaml.full_load(config)
    return devicelist["Devices"]


def connectToDevice(deviceconfig):
    """
    Parse device config data & open SSH connection
    """
    print("Loading device configuration...")
    device = {}
    device["host"] = deviceconfig["address"]
    device["auth_username"] = deviceconfig["username"]
    device["auth_password"] = deviceconfig["password"]
    device["auth_strict_key"] = False
    device["timeout_socket"] = 10
    device["timeout_ops"] = 10
    try:
        device["port"] = deviceconfig["port"]
    except KeyError:
        pass
    if deviceconfig["type"] == "ios-xe":
        conn = IOSXEDriver(**device)
    elif deviceconfig["type"] == "nx-os":
        conn = NXOSDriver(**device)
    try:
        print(f"Attempting connection to {device['host']}")
        conn.open()
        print(f"Successfully connected to {device['host']}")
    except Exception as e:
        print(f"Failed connection to {device['host']}")
        print("Error message is: %s" % e)
        return None
    return conn


def getInterfaceInfo(device):
    """
    Issue 'Show Interfaces' command to device
    Process data & populate dict with interface status
    """
    # Send command to device
    if type(device) == IOSXEDriver:
        resp = device.send_command("show interfaces")
    if type(device) == NXOSDriver:
        resp = device.send_command("show interface")
    # Save a copy of the raw output
    save_raw_output(resp)
    # Parse raw CLI using Genie
    intdata = resp.genie_parse_output()
    interfaceStats = {
        "total_port": 0,
        "up_port": 0,
        "down_port": 0,
        "disabled_port": 0,
        "intop10m": 0,
        "intop100m": 0,
        "intop1g": 0,
        "intop10g": 0,
        "intop25g": 0,
        "intop40g": 0,
        "intop100g": 0,
        "intmedcop": 0,
        "intmedsfp": 0,
        "intmedvirtual": 0,
    }
    # Init dict for detailed interface operational stat collection
    intDetailed = {}
    # Process each interface
    for iface in intdata:
        # Skip VLAN / PortChannel Interfaces
        if "Ethernet" not in iface:
            print(f"found non-ethernet interface: {iface}")
            continue
        if "GigabitEthernet0/0" in iface:
            print(f"found management interface: {iface}")
            continue
        print(f"Working on interface {iface}")
        # Collect detailed interface stats (name, oper status, description, MAC)
        intDetailed[iface] = {}
        intDetailed[iface]["oper_status"] = intdata[iface]["oper_status"]
        try:
            intDetailed[iface]["description"] = intdata[iface]["description"]
        except:
            intDetailed[iface]["description"] = "N/A"
        intDetailed[iface]["phys_addr"] = intdata[iface]["phys_address"]
        intDetailed[iface]["oper_speed"] = intdata[iface]["port_speed"]
        intDetailed[iface]["oper_duplex"] = intdata[iface]["duplex_mode"]
        # Count all Ethernet interfaces
        interfaceStats["total_port"] += 1
        # Count admin-down interfaces
        if not intdata[iface]["enabled"]:
            interfaceStats["disabled_port"] += 1
        # Count 'not connected' interfaces
        elif intdata[iface]["enabled"] and intdata[iface]["oper_status"] == "down":
            interfaceStats["down_port"] += 1
        # Count up / connected interfaces - Then collect current speeds
        elif intdata[iface]["enabled"] and intdata[iface]["oper_status"] == "up":
            interfaceStats["up_port"] += 1
            speed = intdata[iface]["bandwidth"]
            if speed == 10_000:
                interfaceStats["intop10m"] += 1
            if speed == 100_000:
                interfaceStats["intop100m"] += 1
            if speed == 1_000_000:
                interfaceStats["intop1g"] += 1
            if speed == 10_000_000:
                interfaceStats["intop10g"] += 1
            if speed == 25_000_000:
                interfaceStats["intop25g"] += 1
            if speed == 40_000_000:
                interfaceStats["intop40g"] += 1
            if speed == 100_000_000:
                interfaceStats["intop100g"] += 1
        # Count number of interfaces by media type
        try:
            media = intdata[iface]["media_type"]
            if "1000BaseTX" in media:
                interfaceStats["intmedcop"] += 1
            elif "Virtual" in media:
                interfaceStats["intmedvirtual"] += 1
            else:
                interfaceStats["intmedsfp"] += 1
        except KeyError:
            interfaceStats["intmedsfp"] += 1
    # When complete - return int stats list
    return interfaceStats, intDetailed


def save_raw_output(data):
    """
    Creates a local working directory where all raw CLI
    output is stored.
    """
    # Create local directory to store raw output
    if not os.path.exists("raw_output"):
        os.makedirs("raw_output")
    # Dump port information to file
    with open(f"raw_output/{system_serial}.txt", "w") as a:
        a.write(data.result)


def getSystemInfoXE(device):
    """
     -- FOR IOS-XE DEVICES --
    Issue 'Show Version' command to device
    Return serial number, model, current software version
    """
    resp = device.send_command("show version")
    parsed = resp.genie_parse_output()
    sysinfo = {}
    sysinfo["serial"] = parsed["version"]["chassis_sn"]
    sysinfo["model"] = parsed["version"]["chassis"]
    sysinfo["sw_ver"] = parsed["version"]["version"]
    global system_serial
    system_serial = sysinfo["serial"]
    return sysinfo


def getSystemInfoNX(device):
    """
     -- FOR NX-OS DEVICES --
    Issue 'Show Version' command to device
    Return serial number, model, current software version
    """
    resp = device.send_command("show version")
    parsed = resp.genie_parse_output()
    sysinfo = {}
    sysinfo["serial"] = parsed["platform"]["hardware"]["processor_board_id"]
    sysinfo["model"] = parsed["platform"]["hardware"]["model"]
    sysinfo["sw_ver"] = parsed["platform"]["software"]["system_version"]
    global system_serial
    system_serial = sysinfo["serial"]
    return sysinfo


def addDeviceToDB(devicelist):
    """
    Update DB entries for each switch from the config file
    """
    print("Opening DB connection...")
    swDB = switchdb.DB()
    # Get a list of current switches in the database
    # Compare between new config file - see what should be added/removed
    curswitches = swDB.getAllSummary()
    currentSwitches = [row[3] for row in curswitches]
    newSwitches = [devicelist[switch]["address"] for switch in devicelist]
    swRemove = set(currentSwitches).difference(newSwitches)
    swAdd = set(newSwitches).difference(currentSwitches)
    # If switches to remove, purge from the database
    if len(swRemove) > 0:
        print(f"Found {len(swRemove)} switches no longer in config file")
        for switchIP in swRemove:
            print(f"Removing switch ({switchIP}) from DB...")
            swDB.deleteSwitch(switchIP)

    print("Adding devices to DB...")
    for switch in devicelist:
        switchIP = devicelist[switch]["address"]
        if switchIP in swAdd:
            print(f"Adding switch ({switch} / {switchIP}) to DB...")
            swDB.addSwitch(str(switch), str(switchIP))
        else:
            print(f"Switch ({switch} / {switchIP}) already in DB. Skipping...")
    swDB.close()


def updateDB(device, ip, sysinfo, portinfo, detailedinfo):
    """
    Insert new system & port information
    into the database
    """
    swDB = switchdb.DB()
    print(f"Updating system info for {device} in DB...")
    swDB.updateSysInfo(device, ip, sysinfo)
    print(f"Updating port info for {device} in DB...")
    swDB.updatePorts(device, ip, portinfo)
    print(f"Updating detailed port info for {device} in DB...")
    swDB.updateInterfaceDetails(device, ip, sysinfo, detailedinfo)
    swDB.close()


def updateLastRun():
    """
    Call to DB - update last run time
    """
    swDB = switchdb.DB()
    print("Updating last run time in DB...")
    swDB.updateLastRun()
    swDB.close()


def updateCheckStatus(device, ip, status):
    """
    Update the last_check database field,
    which indicates if the check passed or failed
    """
    swDB = switchdb.DB()
    print(f"Updating check status for {device} to {status}")
    swDB.updateStatus(device, ip, status)
    swDB.close()


def run():
    """
    Primay function to manage device data collection
    """
    # Load all of our devices from config, then add to DB
    devicelist = loadDevices()
    addDeviceToDB(devicelist)
    # Iterate through each device for processing
    for device in devicelist:
        dev = device
        ip = devicelist[device]["address"]
        # Open device connection
        devcon = connectToDevice(devicelist[device])
        if devcon:
            try:
                # Query device for system & port info
                if type(devcon) == IOSXEDriver:
                    sysinfo = getSystemInfoXE(devcon)
                if type(devcon) == NXOSDriver:
                    sysinfo = getSystemInfoNX(devcon)
                portinfo, detailedinfo = getInterfaceInfo(devcon)
            except Exception as e:
                print(f"ERROR: {e}")
                updateCheckStatus(device, ip, False)
                continue
            # Update database with new info
            updateDB(dev, ip, sysinfo, portinfo, detailedinfo)
            # Update database with interface detail info
            # Update if check succeeeded
            updateCheckStatus(dev, ip, True)
        else:
            # Update DB if last check failed
            updateCheckStatus(device, ip, False)
    # Finally, update the last-run time!
    updateLastRun()


if __name__ == "__main__":
    run()

import sqlite3
from datetime import datetime
from sqlite3 import Error


class DB:
    def __init__(self):
        self.openDB()
        self.createDB()
        self.initLastUpdate()

    def openDB(self):
        """
        Open SQLlite DB
        """
        self.conn = None
        try:
            self.conn = sqlite3.connect("./sw-util.db")
        except Error as e:
            print(e)

    def createDB(self):
        """
        Create new table to contain switch info & port utilization data
        """
        sw_info_table = """ CREATE TABLE IF NOT EXISTS switches (
            name text NOT NULL,
            serial text DEFAULT "Not Polled Yet",
            model text DEFAULT "N/A",
            sw_ver text DEFAULT "N/A",
            mgmt_ip text NOT NULL PRIMARY KEY,
            last_check boolean DEFAULT False,
            total_port integer DEFAULT 0,
            up_port integer DEFAULT 0,
            down_port integer DEFAULT 0,
            disabled_port integer DEFAULT 0,
            intop10m integer DEFAULT 0,
            intop100m integer DEFAULT 0,
            intop1g integer DEFAULT 0,
            intop10g integer DEFAULT 0,
            intop25g integer DEFAULT 0,
            intop40g integer DEFAULT 0,
            intop100g integer DEFAULT 0,
            intmedcop integer DEFAULT 0,
            intmedsfp integer DEFAULT 0,
            intmedvirt integer DEFAULT 0
        ); """
        last_update_table = """ CREATE TABLE IF NOT EXISTS last_update (
            id integer NOT NULL PRIMARY KEY,
            lastrun text NOT NULL
        ); """
        interface_detail_table = """ CREATE TABLE IF NOT EXISTS interface_detailed (
            sw_name text NOT NULL,
            mgmt_ip text NOT NULL,
            int_name text NOT NULL,
            oper_status text NOT NULL,
            description text DEFAULT "N/A",
            phys_address text NOT NULL PRIMARY KEY,
            serial text NOT NULL,
            oper_speed text NOT NULL,
            oper_duplex text NOT NULL
        ); """
        cur = self.conn.cursor()
        cur.execute(sw_info_table)
        cur.execute(last_update_table)
        cur.execute(interface_detail_table)

    def addSwitch(self, name, mgmt_ip):
        """
        Insert new switch into DB
        """
        sql = """ INSERT INTO switches(name,mgmt_ip) values(?,?); """
        cur = self.conn.cursor()
        try:
            cur.execute(sql, (name, mgmt_ip))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"Switch {name} with IP: {mgmt_ip} already exists in DB.")

    def updateSysInfo(self, name, mgmt_ip, sysinfo):
        """
        Update switch system info:
        Model number, software version, and serial number
        """
        sql = """ UPDATE switches
                  SET serial = ?,
                  model = ?,
                  sw_ver = ?
                  WHERE name = ?
                  AND mgmt_ip = ?;
        """
        cur = self.conn.cursor()
        cur.execute(
            sql, (sysinfo["serial"], sysinfo["model"], sysinfo["sw_ver"], name, mgmt_ip)
        )
        self.conn.commit()
        return

    def updatePorts(self, name, mgmt_ip, portinfo):
        """
        Update port count information
        """
        sql = """ UPDATE switches
                  SET
                  total_port = ?,
                  up_port = ?,
                  down_port = ?,
                  disabled_port = ?,
                  intop10m = ?,
                  intop100m = ?,
                  intop1g = ?,
                  intop10g = ?,
                  intop25g = ?,
                  intop40g = ?,
                  intop100g = ?,
                  intmedcop = ?,
                  intmedsfp = ?,
                  intmedvirt = ?
                  WHERE name = ?
                  AND mgmt_ip = ?;
        """
        cur = self.conn.cursor()
        cur.execute(
            sql,
            (
                portinfo["total_port"],
                portinfo["up_port"],
                portinfo["down_port"],
                portinfo["disabled_port"],
                portinfo["intop10m"],
                portinfo["intop100m"],
                portinfo["intop1g"],
                portinfo["intop10g"],
                portinfo["intop25g"],
                portinfo["intop40g"],
                portinfo["intop100g"],
                portinfo["intmedcop"],
                portinfo["intmedsfp"],
                portinfo["intmedvirtual"],
                name,
                mgmt_ip,
            ),
        )
        self.conn.commit()
        return

    def updateInterfaceDetails(self, name, mgmt_ip, sysinfo, portdetails):
        """
        Update interface detailed status per switch:
        Interface name, operational status, description, and physical address
        """
        sql = """ INSERT INTO interface_detailed(
                    int_name,
                    oper_status,
                    description,
                    phys_address,
                    oper_speed,
                    oper_duplex,
                    sw_name, 
                    mgmt_ip,
                    serial
                  )
                  VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                  ON CONFLICT(phys_address) DO UPDATE
                  SET int_name = ?,
                  oper_status = ?,
                  description = ?,
                  phys_address = ?,
                  oper_speed = ?,
                  oper_duplex = ?,
                  serial = ?
                  WHERE sw_name = ?
                  AND mgmt_ip = ?;
        """
        cur = self.conn.cursor()
        for interface in portdetails:
            cur.execute(
                sql,
                (
                    interface,
                    portdetails[interface]["oper_status"],
                    portdetails[interface]["description"],
                    portdetails[interface]["phys_addr"],
                    portdetails[interface]["oper_speed"],
                    portdetails[interface]["oper_duplex"],
                    name,
                    mgmt_ip,
                    sysinfo["serial"],
                    interface,
                    portdetails[interface]["oper_status"],
                    portdetails[interface]["description"],
                    portdetails[interface]["phys_addr"],
                    portdetails[interface]["oper_speed"],
                    portdetails[interface]["oper_duplex"],
                    sysinfo["serial"],
                    name,
                    mgmt_ip,
                ),
            )
            self.conn.commit()
        return

    def getSwitch(self, name, mgmt_ip):
        """
        Retrieve switch information
        """
        sql = """ SELECT * FROM switches
                  WHERE name = ? AND mgmt_ip = ?; """
        cur = self.conn.cursor()
        cur.execute(sql, (name, mgmt_ip))
        result = cur.fetchall()
        return result

    def deleteSwitch(self, mgmt_ip):
        """
        Remove switch from database
        """
        sql = """ DELETE FROM switches
                  WHERE mgmt_ip = ?; """
        cur = self.conn.cursor()
        cur.execute(sql, [mgmt_ip])
        result = cur.fetchall()
        return result

    def getNetworkWideStats(self):
        """
        Retrieve network-wide port count information
        """
        sql = """ SELECT model, sw_ver, total_port, up_port, down_port,
                  disabled_port, intop10m, intop100m, intop1g, intop10g,
                  intop25g, intop40g, intop100g,intmedcop, intmedsfp,
                  intmedvirt FROM switches; """
        cur = self.conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        return result

    def getAllSummary(self):
        """
        Retrieve info from ALL switches in DB.
        """
        sql = """ SELECT name, serial, sw_ver, mgmt_ip, last_check,
                  total_port, up_port, down_port, disabled_port
                  FROM switches; """
        cur = self.conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        return result

    def getSwitchDetail(self, serial):
        """
        Retrieve info from ALL switches in DB.
        """
        sql = """ SELECT * FROM switches WHERE serial = ?; """
        cur = self.conn.cursor()
        cur.execute(sql, [serial])
        result = cur.fetchall()
        return result

    def getInterfaceDetail(self, serial):
        """
        Retrieve interface detailed info
        """
        sql = """ SELECT int_name, description, phys_address, oper_status,
                  oper_speed, oper_duplex
                  FROM interface_detailed WHERE serial = ? """
        cur = self.conn.cursor()
        cur.execute(sql, [serial])
        result = cur.fetchall()
        return result

    def updateStatus(self, name, mgmt_ip, status):
        """
        Update only the last_check column with
        whether or not the last polling succeeded
        """
        sql = """ UPDATE switches SET last_check = ?
                  WHERE name = ? AND mgmt_ip = ?; """
        cur = self.conn.cursor()
        cur.execute(sql, (status, name, mgmt_ip))
        self.conn.commit()
        print("DB Update completed")
        return

    def updateLastRun(self):
        """
        Updates single entry that contains last run time
        """
        sql = """ UPDATE last_update
                  SET lastrun = ?
                  WHERE id = 1;
        """
        now = datetime.now()
        timestamp = now.strftime("%B, %d, %Y %H:%M:%S")
        cur = self.conn.cursor()
        cur.execute(sql, [timestamp])
        self.conn.commit()
        return

    def getLastUpdate(self):
        """
        Return last runtime
        """
        sql = """ SELECT lastrun from last_update WHERE id = 1;
        """
        cur = self.conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        try:
            lastupdate = result[0][0]
        except:
            lastupdate = None
        return lastupdate

    def initLastUpdate(self):
        """
        Initialize data in last_update table
        """
        sql = """ INSERT INTO last_update(lastrun) values(?); """
        if not self.getLastUpdate():
            cur = self.conn.cursor()
            cur.execute(sql, ["Never"])
            self.conn.commit()

    def close(self):
        self.conn.close()

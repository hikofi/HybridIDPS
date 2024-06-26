import time
import importlib
import os, sys
sys.path.append(os.path.abspath("../helperFiles"))
from sqlConnector import MySQLConnection  

try:
    import mysql.connector
except ImportError:
    print("\033[91mmysql.connector is not installed. Run 'pip install mysql-connector-python' \033[0m")

class InnerLayer():
    def __init__(self) -> None:
        self.database = MySQLConnection()
        self.database.setVerbose(False)
        self.database.hazmat_wipe_Table('innerLayer')
        self.database.hazmat_wipe_Table('innerLayerThreats')
        self.devices = {}
        # self.threat_counts = {} #This may needs to be removed, work in progress
        self.threatTable = {
            "spamCredentials":     0.2,
            "massReporting":       0.3,
            "massAccountCreation": 0.5,
        }
        self.central_analyzer()

    def central_analyzer(self):
        interval = 1
        start_time = time.time()

        while True:
            if time.time() - start_time >= interval:
                self.database.connect()
                self.add_devices()
                ###### Analyzer Functions ######
                
                self.analyze_spam_credentials()

                self.analyze_mass_reporting()

                self.analyze_mass_account_creation()
                
                ###### Analyzer Functions ######

                self.display_Events_and_calc_threat_level()
                start_time = time.time()
                self.database.disconnect()
    

    def analyze_spam_credentials(self):
        event_type = 'invalidCredentials'
        threatName = "spamCredentials"
        threat_level = self.threatTable[threatName]
        results = self.database.execute_query(f"SELECT * from hybrid_idps.innerLayer WHERE event_type = '{event_type}' ORDER BY timestamp DESC")
        results = self.extract_ips(results)
        for ip, all_events in results.items():
            count = 0
            for event in all_events:
                count += 1
                if count > 10:
                    logName = f"{threatName}-{event['timestamp']}"
                    self.add_threat(logName, threatName,  event['username'], event['target_username'], event['ip_address'], event['geolocation'], event['timestamp'],
                                    threatName, threat_level, event['payload'])
                    count = 0

                    # I have this one here but it seems to always be called so it is just constanly being added 1, my logic may be wrong
                    # self.threat_counts[threatName] = self.threat_counts.get(threatName, 0) + 1

    def analyze_mass_reporting(self):
        event_type = 'reportUserByUsername'
        threatName = "massReporting"
        threat_level = self.threatTable[threatName]
        results = self.database.execute_query(f"SELECT * from hybrid_idps.innerLayer WHERE event_type = '{event_type}' ORDER BY timestamp DESC")
        results = self.extract_ips(results)
        for ip, all_events in results.items():
            count = 0
            for event in all_events:
                count += 1
                if count > 3:
                    logName = f"{threatName}-{event['timestamp']}"
                    self.add_threat(logName, threatName,  event['username'], event['target_username'], event['ip_address'], event['geolocation'], event['timestamp'],
                                    threatName, threat_level, event['payload'])
                    count = 0


##    This thing will need to be altered and depends on how we are going to handle registering, cause you are already classified as registered on our lauched computers ## 

    def analyze_mass_account_creation(self):   
        event_type = 'register'
        threatName = "massAccountCreation"
        threat_level = self.threatTable[threatName]
        results = self.database.execute_query(f"SELECT * from hybrid_idps.innerLayer WHERE event_type = '{event_type}' ORDER BY timestamp DESC")
        results = self.extract_ips(results)
        for ip, all_events in results.items():
            count = 0
            for event in all_events:
                count += 1
                if count > 3:
                    logName = f"{threatName}-{event['timestamp']}"
                    # self.add_threat(ip, logName, all_events[:1])
                    self.add_threat(logName, threatName,  event['username'], event['target_username'], event['ip_address'], event['geolocation'], event['timestamp'],
                                    threatName, threat_level, event['payload'])
                    count = 0
        
    def display_Events_and_calc_threat_level(self):
        for ip, deviceData in self.devices.items():
            print("\n")
            print(f"IP: {ip}")
            logs = deviceData["logs"]
            threatLevel = 0
            for threatName, threadType in logs.items():
                print(f"        {threatName}")
                threatLevel += self.threatTable[threadType]
                
            if threatLevel > 1: threatLevel = 1
            self.set_threat_level(ip, threatLevel)
            color_code = "\033[92m"  # Green
            if threatLevel > 0.5:
                color_code = "\033[91m"  # Red
            elif 0 < threatLevel < 0.5:
                color_code = "\033[93m"  # Yellow
            reset_color = "\033[0m"
            print(f"    {color_code}[Threat Level]:   {threatLevel} {reset_color}")
            
    def extract_ips(self, results):
        ip_dict = {}
        for entry in results:
            ip = entry['ip_address']
            if ip not in ip_dict:
                ip_dict[ip] = []
            ip_dict[ip].append(entry)
        return ip_dict

    def add_devices(self):
        results = self.database.execute_query(f"SELECT DISTINCT ip_address from hybrid_idps.innerLayer")
        ip_addresses = [ip['ip_address'] for ip in results] #Possibly IPV6
        
        for ip in ip_addresses:
            if ip.startswith("::ffff:"):     # ip_address ::ffff:192.168.1.99
                ip = ip.split(":")[-1]       # ip_address 192.168.1.99
            if ip not in self.devices:
                self.devices[ip] = {'threatLevel': 0, 'logs': {}}
        
        
    def add_threat(self, logName, threatName, username, target_username, ip_address, geolocation, timestamp, event_type, threat_level, payload):
        if ip_address.startswith("::ffff:"):     # ip_address ::ffff:192.168.1.99
            ip_address = ip_address.split(":")[-1] # ip_address 192.168.1.99
        
        if ip_address in self.devices:
            device = self.devices[ip_address]
            threatLevel = self.threatTable[threatName]

            if logName not in device['logs']:
                device = self.devices[ip_address]
                device['logs'][logName] = threatName
                self.database.add_threat_to_inner_Layer_Threats_DB(username, target_username, ip_address, geolocation, timestamp, event_type, threat_level, payload)
        else:
            print(f"Failed to add_threat. Device with IP address {ip_address} does not exist.")
            
    def set_threat_level(self, ip_address, newThreatLevel):
        if ip_address in self.devices:
            device = self.devices[ip_address]['threatLevel'] = newThreatLevel
        else:
            print(f"Failed to set_threat_level. Device with IP address {ip_address} does not exist.")

if __name__ == "__main__":
    x = InnerLayer()

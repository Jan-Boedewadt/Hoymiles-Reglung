import requests, time, paho.mqtt.client as mqtt
from requests.auth import HTTPBasicAuth
from datetime import datetime

# Diese Daten müssen angepasst werden: zeile 5 - 19
serial = "114183145407" # Seriennummern der Hoymiles Wechselrichter
maximum_wr = 800 # Maximum ausgabe des wechselrichters in Watt
minimum_wr = 20 # Mimimalwert fuer Wechselrichter in Watt

dtuIP = '192.168.178.34' # IP Adresse von OpenDTU
dtuNutzer = 'admin' # OpenDTU Nutzername
dtuPasswort = 'geheim' # OpenDTU Passwort

shellyIP = '192.168.178.20' #IP Adresse von Shelly Pro3EM
NetzSollwert = 50   #Sollwert in Watt für den Netzwert, negative werte bedeuten Einspeisung

batteriebetrieb = True  # Quelle fuer Wechselrichter Akku? (True/False)
minimum_voltage = 49 # Minimaler Spannungswert in V
low_voltage = 51 # Beginn der abregelung in V
setpoint = 0

while True:
    oldsetpoint = setpoint
    
    # Nimmt Daten von der openDTU Rest-API und übersetzt sie in ein json-Format
    r = requests.get(url = f'http://{dtuIP}/api/livedata/status/inverters' ).json()
    
    # Zeit ausgeben
    now = datetime.now()
    dt_string = now.strftime("%d.%m.%Y %H:%M:%S")
    #print(dt_string)

    # Selektiert spezifische Daten aus der json response
    reachable   = r['inverters'][0]['reachable'] # ist DTU erreichbar ?
    producing   = int(r['inverters'][0]['producing']) # produziert der Wechselrichter etwas ?
    altes_limit = int(r['inverters'][0]['limit_absolute']) # wo war das alte Limit gesetzt
    #power_dc    = r['inverters'][0]['0']['Power DC']['v']  # Lieferung DC vom Panel
    power       = round(r['inverters'][0]['AC']['0']['Power']['v'],4) # Abgabe BKW AC in Watt
    voltage     = round(r['inverters'][0]['DC']['0']['Voltage']['v'],2)  #  DC Spannung

    # Nimmt Daten von der Shelly 3EM Rest-API und übersetzt sie in ein json-Format
    grid_sum    = round(requests.get(f'http://{shellyIP}/rpc/EM.GetStatus?id=0', headers={"Content-Type": "application/json"}).json()['total_act_power'],1)
    setpoint    = 0     # Neues Limit in Watt

    # Setzt ein limit auf das Wechselrichter
    def setLimit(Serial, Limit):
        if setpoint >= 5:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            payload = f'''data={{"serial":"{Serial}", "limit_type":0, "limit_value":{Limit}}}'''
            newLimit = requests.post(url=f'http://{dtuIP}/api/limit/config', data=payload, auth=HTTPBasicAuth(dtuNutzer, dtuPasswort), headers=headers)
            print('Konfiguration Status:', newLimit.json()['type'], newLimit.json()['message'])
        if setpoint == 0 and producing == True:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            payload = f'''data={{"serial":"{Serial}", "power":0}}'''
            newStatus = requests.post(url=f'http://{dtuIP}/api/power/config', data=payload, auth=HTTPBasicAuth(dtuNutzer, dtuPasswort), headers=headers)
            print('Power Konfiguration Status off:', newStatus.json()['type'], newStatus.json()['message'])
        
        if setpoint > 5 and producing == False:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            payload = f'''data={{"serial":"{Serial}", "power":1}}'''
            newStatus = requests.post(url=f'http://{dtuIP}/api/power/config', data=payload, auth=HTTPBasicAuth(dtuNutzer, dtuPasswort), headers=headers)
            print('Power Konfiguration Status on:', newStatus.json()['type'] , newStatus.json()['message'])
        
    # Werte setzen
    #print("aktueller Netzwert:    ",grid_sum,"W")
    #print("Wechselrichterleistung:",power,"W")
    if voltage < low_voltage:
        print("low DC-Spannung:       ",voltage,"V")
    #else:
    #    print("DC-Spannung:           ",voltage,"V")
    if not producing:
        time.sleep(5) # wait

    if reachable and (producing or voltage >= low_voltage):
        # Setzen Sie den Grenzwert auf den höchsten Wert, wenn er über dem zulässigen Höchstwert liegt.
        if (altes_limit > maximum_wr or (grid_sum+power-NetzSollwert) >= maximum_wr or setpoint >= maximum_wr):
            #print("setze Limiter auf maximum: ",maximum_wr,"W")
            setpoint = maximum_wr

        # wir weniger bezogen als maximum_wr dann neues Limit ausrechnen
        if (grid_sum+power-NetzSollwert) <= maximum_wr:
            setpoint = round(grid_sum + power - NetzSollwert,1)
            #print("setpoint:",grid_sum,"+",power,"-",NetzSollwert,"=",setpoint)
        if setpoint <= minimum_wr:
            setpoint = minimum_wr
            print("setpoint: ",setpoint,"W minimum gesetzt")
       
       # Akku als Quelle?
        if batteriebetrieb:
            # Spannung kleiner low Voltage
            if voltage > minimum_voltage and voltage < low_voltage:
                faktor = ((low_voltage-minimum_voltage)-(low_voltage-voltage))/(low_voltage-minimum_voltage)
                setpoint = faktor * setpoint
                print("low Volage Batteriebetrieb: WR_Sollwert abgereglt auf: ",setpoint,"W")
                
            if voltage <= minimum_voltage:
                setpoint = 0
                print("Batteriebetrieb: Akku Leer! WR_Sollwert abgereglt auf: ",setpoint,"W")
                    
            #if voltage >= low_voltage:
                #print("setze Einspeiselimit auf: ",setpoint,"W")
        # Wenn der Wechselrichter nicht erreicht werden kann, wird der limit auf minimum gestellt
        #if setpoint == 0: setpoint = grid_sum
        if not reachable:
            setpoint = minimum_wr
            print("Hoymiles nicht erreichbar! Sollwert auf minimum gesetzt:",setpoint)
        if not batteriebetrieb:
               print("setze Einspeiselimit auf: ",setpoint,"W")
        
        # neues limit setzen
        if abs(oldsetpoint-setpoint)>=5:
            setLimit(serial, setpoint)
        #print(dt_string,"aktueller Netzwert:",grid_sum,"W"," Wechselrichterleistung:",power,"W"," DC-Spannung:",voltage,"V"," setpoint:",grid_sum,"+",power,"-",NetzSollwert,"=",setpoint,"W")
        time.sleep(9) # wait

    
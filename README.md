# Hoymiles-Reglung
Pythonskript zur Regelung von Hoymlies Microinvertern via OpenDTU auf einen Sollwert eines Zählers
Im Moment sind folgende Zähler umgesetzt:
  Shelly Pro3EM via HTTP API

Anwendungsmöglichkeiten:
- Selbstbau Akku Balkonkraftwerk. zum Beispiel:
Solarmodule die über MPPT Regler eine Akku füllen. Ein Microwechselrichter, der von diesem Skript in Abhängikeit des Hausverbrauchs, gemessen durch Shelly Pro3EM, geregelt wird.

- Erweiterung einer bestehenden Inselanlage um Microinverter zum Ausbau der Gesamtleistung des Systems
    
Im Skript kann unter anderem die Spannung eingestellt werden bei der die Wechselrichter abgeregelt werden, wenn der Akuu leer wird. Bei unterschreiten der Miminmumspannung werden die Inverter abgeschaltet.

Diese Repository ist ein Fork von Selbstbau-PV-Hoymiles-nulleinspeisung-mit-OpenDTU-und-Shelly3EM:
https://github.com/Selbstbau-PV/Selbstbau-PV-Hoymiles-nulleinspeisung-mit-OpenDTU-und-Shelly3EM

# DHT22 Datalogger & Migratie Project (Trixie)

Dit project is ontworpen voor de Raspberry Pi (OS Trixie) om temperatuur en luchtvochtigheid te loggen in een MariaDB database. Het bevat een geautomatiseerd installatiescript dat ook de migratie van oude data (vanaf Bookworm) ondersteunt.

## Snelle Start

### 1. Clone de repository
Open de terminal op je Raspberry Pi en typ:
```bash
git clone [https://github.com/jmo2300/DataloggerTrixie](https://github.com/jmo2300/DataloggerTrixie)
cd DataloggerTrixie

```
### 2. Start de installatie
```bash
chmod +x install_datalogger.sh
./install_datalogger.sh

```
## Belangrijke Hardware Waarschuwing

Sluit de sensor **NOOIT** aan terwijl de Raspberry Pi onder spanning staat! Dit kan de GPIO-pinnen of de processor onherstelbaar beschadigen. Schakel de Pi altijd volledig uit en verwijder de voedingskabel voordat je wijzigingen aanbrengt in de bedrading.



### Aansluitschema (DHT22)

| DHT22 Pin | Raspberry Pi Pin | Functie |
| :--- | :--- | :--- |
| **VCC** | Pin 1 (3.3V) | Voeding |
| **Data** | Pin 15 (GPIO 22) | Digitaal Signaal |
| **GND** | Pin 14 (Ground) | Massa |

---

## Projectstructuur

Na het uitvoeren van het installatiescript wordt de software georganiseerd in de volgende mappen in je home-directory (`~`):

* **`~/bashscripts/`**: Bevat dit `README.md` bestand en het hoofd-installatiescript.
* **`~/pythonscripts/`**: Bevat alle Python-scripts voor het loggen en de grafieken, inclusief de virtuele omgeving (`dhtvenv`).
* **`~/web/`**: De map waar je jouw eigen HTML/PHP ontwerp beheert. Bestanden hier worden door het script gekopieerd naar de webserver.

---

## Data Migratie (Van Bookworm naar Trixie)

Dit project ondersteunt het importeren van bestaande data van een oudere Raspberry Pi (bijv. versie Bookworm).

### 1. Backup maken op de Bookworm Pi
Gebruik het volgende commando op de **oude** Pi om een backup met tijdstempel te maken:
```bash
sudo mysqldump -u root -p temperatures > temperaturesdump_`date +%Y%m%d%H%M`.sql
```

### 2. Bestand kopiëren via SCP
Kopieer het zojuist gemaakte bestand naar de nieuwe Pi (Trixie). Vervang gebruiker door je eigen username en IP-ADRES door het adres van de nieuwe Pi:
```bash
scp temperaturesdump_*.sql gebruiker@IP-ADRES-TRIXIE:~/
```

### 3. Importeer op Trixie Pi
Importeer de data in de nieuwe database. Het installatiescript zal je hierom vragen, of gebruik dit commando:
```bash
mariadb -u root -p temperatures < ~/temperaturesdump_DATUMCODE.sql
```
# Handige commando's
## Data controleren in de terminal
Gebruik het meegeleverde script om snel de laatste 10 metingen uit de database te tonen:

Via venv:
```bash
cd
cd pythonscripts/
source /home/$USER/pythonscripts/dhtvenv/bin/activate
python toondata.py
```

of rechtstreeks:
```bash
~/pythonscripts/dhtvenv/bin/python ~/pythonscripts/toondata.py
```
## Tabel leegmaken (Reset)
Als je de database wilt legen (bijv. na een mislukte test-import) zonder de tabelstructuur te verliezen:
```bash
mariadb -u logger -p -e "TRUNCATE TABLE temperatures.temperaturedata;"
```

# Automatisering (Cron)
De datalogger werkt volledig automatisch via een cron-configuratie in /etc/cron.d/datalogger.

* Logging: Elke 15 minuten (0, 15, 30, 45) wordt de sensor uitgelezen en de data opgeslagen.
* Grafiek: Elke 15 minuten (met 2 minuten vertraging op de meting) wordt de grafiek ververst en naar de webmap gekopieerd.

Je kunt de actieve taken bekijken met:
```bash
cat /etc/cron.d/datalogger
```
of
```bash
crontab -l
```

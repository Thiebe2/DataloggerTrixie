# DHT22 Datalogger & Migratie Project (Trixie)

Dit project is ontworpen voor de Raspberry Pi (OS Trixie) om temperatuur en luchtvochtigheid te loggen in een MariaDB database. Het bevat een geautomatiseerd installatiescript dat ook de migratie van oude data (vanaf Bookworm) ondersteunt.

### Mappenstructuur van dit project:
```text
.
├── install_datalogger.sh    # Het hoofdscript (in de root)
├── README.md                # De handleiding (in de root)
├── pythonscripts/           # Map voor Python logica
│   ├── leesdht.py
│   ├── temperatuurlogger.py
│   ├── toondata.py
│   └── BewaarTempGrafiek.py
└── web/                     # Map voor webbestanden
    └── index.php            # (En de eigen bestanden van leerlingen)
```

#  Installatiestappen Datalogger (Script Overzicht)

Het installatiescript doorloopt de volgende 6 stappen om je Raspberry Pi volledig in te richten als datalogger.

---

### STAP 1: Mappen en Bestanden organiseren
In deze stap wordt de mappenstructuur in je home-directory (`~`) aangemaakt. De bestanden uit de repository worden naar hun definitieve plek verplaatst:
* **`~/bashscripts/`**: Voor het installatiescript en documentatie.
* **`~/pythonscripts/`**: Voor de Python-logica en scripts.
* **`~/web/`**: Voor je bronbestanden van de website.

---

### STAP 2: Systeem Update & Software
Het script werkt het besturingssysteem bij en installeert de noodzakelijke pakketten:
* **Updates:** `sudo apt update && sudo apt upgrade -y` (met `$DPKG_OPTS` om configuratievragen te omzeilen).
* **Webserver:** Apache2 en PHP 8.4.
* **Database:** MariaDB Server.
* **Python Tools:** `python3-venv` en `pip` voor bibliotheekbeheer.

---

### STAP 3: Database Configuratie
De SQL-omgeving wordt ingericht voor de data-opslag:
1. De database `temperatures` wordt aangemaakt.
2. Een specifieke gebruiker `logger` krijgt rechten op deze database.
3. De tabel `temperaturedata` wordt aangemaakt met kolommen voor:
   * `dateandtime` (Datum en tijd van de meting)
   * `sensor` (Naam/ID van de sensor)
   * `temperature` (Temperatuur in Celsius)
   * `humidity` (Luchtvochtigheid in %)



---

### STAP 4: Python Omgeving (venv)
Er wordt een geïsoleerde virtuele omgeving (`dhtvenv`) aangemaakt in `~/pythonscripts/`. Hierin worden de bibliotheken geïnstalleerd die nodig zijn voor de hardware en dataverwerking:
* `adafruit-circuitpython-dht`: Voor het uitlezen van de DHT22.
* `matplotlib`: Voor het genereren van de temperatuurgrafieken.
* `mysql-connector-python`: Om data naar de MariaDB database te sturen.

---

### INTERSPECTIE: Data Migratie
Vóór de afronding biedt het script de mogelijkheid om oude data te importeren:
* Er worden instructies getoond voor `mysqldump` op de bron-Pi.
* Er wordt een `scp` commando gegenereerd met het actuele IP-adres van deze Pi.
* Je kunt een `.sql` backup bestand importeren in de nieuwe tabel.

---

### STAP 5: Webserver Inrichten
De bestanden uit je lokale `~/web/` map worden "live" gezet:
* De bestanden worden gekopieerd naar `/var/www/html/`.
* De juiste rechten (`www-data`) worden toegekend zodat de webserver de bestanden kan lezen.

---

### STAP 6: Automatisering (Cron)
Er wordt een configuratiebestand aangemaakt in `/etc/cron.d/datalogger`:
* **Meting:** Elke 15 minuten voert de Pi `temperatuurlogger.py` uit.
* **Grafiek:** Elke 15 minuten wordt `BewaarTempGrafiek.py` uitgevoerd. De resulterende afbeelding wordt automatisch naar de webmap gekopieerd.



---

## ✅ Installatie Voltooid
Na deze stappen is het systeem volledig operationeel. Je kunt het dashboard bekijken via het IP-adres van de Raspberry Pi.



---

## Snelle Start

### 1. Clone de repository
Open de terminal op je Raspberry Pi en typ:
```bash
git clone https://github.com/jmo2300/DataloggerTrixie
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
* Grafiek: Elke 15 minuten (met 1 minuut vertraging op de meting) wordt de grafiek ververst en naar de webmap gekopieerd.

Je kunt de actieve taken bekijken met:
```bash
cat /etc/cron.d/datalogger
```
of
```bash
crontab -l
```

```txt
# Elke 15 minuten de sensor uitlezen
0,15,30,45 * * * * ~/pythonscripts/dhtvenv/bin/python ~/pythonscripts/temperatuurlogger.py

# Elke 15 minuten de afbeelding verversen
1,16,31,46 * * * * ~/pythonscripts/dhtvenv/bin/python ~/pythonscripts/BewaarTempGrafiek.py

# Elke 15 minuten de afbeelding kopiëren naar webroot
2,17,32,47 * * * * sudo cp ~/Raspi25Temperatuur.png /var/www/html/afbeeldingen/Raspi25Temperatuur.png
```

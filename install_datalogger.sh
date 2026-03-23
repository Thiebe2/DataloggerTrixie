#!/bin/bash

# =================================================================
# Installatiescript voor Datalogger - Raspberry Pi OS (Trixie)
# Met Data Migratie Module (Bookworm -> Trixie)
# JMO 09/03/2026
# =================================================================

# Stop direct bij fouten
set -e

# Voorkom interactieve vragen (Niet-interactieve modus)
export DEBIAN_FRONTEND=noninteractive

# Functie voor een duidelijke sectietitel
print_titel() {
    echo -e "\n*************************************************************"
    echo "  $1"
    echo "*************************************************************"
}

# Functie voor ja/nee vragen
stel_vraag() {
    read -p "$1 (j/N): " antwoord
    if [[ "${antwoord,,}" == "j" || "${antwoord,,}" == "ja" ]]; then
        return 0
    else
        return 1
    fi
}

# -----------------------------------------------------------------
# START & OVERZICHT
# -----------------------------------------------------------------
clear
print_titel "Datalogger Installatie & Migratie (Trixie)"

REPO_DIR=$(pwd)
BASH_DEST="$HOME/bashscripts"
PYTHON_DEST="$HOME/pythonscripts"
WEB_DEST="$HOME/web"

echo "GEPLANDE MAPPENSTRUCTUUR:"
echo " - Scripts & Docs: $BASH_DEST"
echo " - Python Logica:  $PYTHON_DEST"
echo " - Web Design:     $WEB_DEST"
echo "============================================================="

# Hardware Veiligheid Check
echo -e "\n   BELANGRIJK: HARDWARE VEILIGHEID!"
echo "Sluit NOOIT sensoren aan terwijl de Pi aan staat."
echo "-------------------------------------------------------------"
echo "1. DHT22 op GPIO pin 22 (Pin 15)?"
echo "2. Voeding op 3.3V (Pin 1) en GND (Pin 14)?"
echo "-------------------------------------------------------------"

if ! stel_vraag "Is de hardware veilig aangesloten en wil je de installatie starten?"; then
    echo "Installatie afgebroken."
    exit 0
fi

# -----------------------------------------------------------------
# STAP 1: Mappen en Bestanden organiseren
# -----------------------------------------------------------------
if stel_vraag "Stap 1: Bestanden organiseren naar de nieuwe mappenstructuur?"; then
    print_titel "STAP 1: BESTANDEN ORGANISEREN"
    mkdir -p "$BASH_DEST" "$PYTHON_DEST" "$WEB_DEST"

    cp "$REPO_DIR/install_datalogger.sh" "$BASH_DEST/" 2>/dev/null || true
    cp "$REPO_DIR/README.md" "$BASH_DEST/" 2>/dev/null || true

    if [ -d "$REPO_DIR/pythonscripts" ]; then
        cp "$REPO_DIR/pythonscripts/"*.py "$PYTHON_DEST/" 2>/dev/null || true
    fi

    if [ -d "$REPO_DIR/web" ]; then
        cp -r "$REPO_DIR/web/"* "$WEB_DEST/" 2>/dev/null || true
    fi
    echo "Bestanden zijn verplaatst naar $HOME."
fi

# -----------------------------------------------------------------
# STAP 2: Systeem Update & Software
# -----------------------------------------------------------------
if stel_vraag "Stap 2: Systeem updaten en software (Apache, PHP, MariaDB) installeren?"; then
    print_titel "STAP 2: SYSTEEM & SOFTWARE UPDATE"
    echo "Dit kan even duren (geen interactie vereist)..."

    sudo apt-get update -y

    # Directe aanroep van opties om dpkg errors te voorkomen
    sudo apt-get upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"

    sudo apt-get install -y apache2 php php-mysql mariadb-server \
                         python3-venv python3-pip libopenblas-dev \
                         python3-dev pkg-config
fi

# -----------------------------------------------------------------
# STAP 3: Database Configuratie
# -----------------------------------------------------------------
if stel_vraag "Stap 3: MariaDB Database en Tabel inrichten?"; then
    print_titel "STAP 3: DATABASE CONFIGURATIE"
    sudo mariadb -u root <<_EOF_
CREATE DATABASE IF NOT EXISTS temperatures;
CREATE USER IF NOT EXISTS 'logger'@'localhost' IDENTIFIED BY 'paswoord';
GRANT ALL PRIVILEGES ON temperatures.* TO 'logger'@'localhost';
FLUSH PRIVILEGES;
USE temperatures;
CREATE TABLE IF NOT EXISTS temperaturedata (
    dateandtime DATETIME,
    sensor VARCHAR(32),
    temperature DOUBLE,
    humidity DOUBLE
);
_EOF_
    echo "Database 'temperatures' en tabel 'temperaturedata' zijn gereed."
fi

# -----------------------------------------------------------------
# STAP 4: Python Omgeving (venv)
# -----------------------------------------------------------------
if stel_vraag "Stap 4: Python Virtual Environment (venv) instellen?"; then
    print_titel "STAP 4: PYTHON OMGEVING"
    python3 -m venv "$PYTHON_DEST/dhtvenv"
    echo "Libraries installeren (Adafruit DHT, Matplotlib, MySQL)..."
    "$PYTHON_DEST/dhtvenv/bin/python" -m pip install --upgrade pip
    "$PYTHON_DEST/dhtvenv/bin/python" -m pip install adafruit-circuitpython-dht matplotlib mysql-connector-python
fi

# -----------------------------------------------------------------
# INTERSPECTIE: DATA MIGRATIE
# -----------------------------------------------------------------
print_titel "DATA MIGRATIE MODULE"
if stel_vraag "Wil je nu data importeren van een andere (Bookworm) Raspberry Pi?"; then
    IP_TRIXIE=$(hostname -I | awk '{print $1}')
    BACKUP_CMD="sudo mysqldump -u root -p temperatures > ~/temperaturesdump_\$(date +%Y%m%d%H%M).sql"

    echo "-------------------------------------------------------------"
    echo "VOER DIT UIT OP DE OUDE PI (BRON):"
    echo "1. Backup maken:"
    echo "   $BACKUP_CMD"
    echo "2. Kopieer naar deze Pi (vervang de bestandsnaam):"
    echo "   scp ~/temperaturesdump_*.sql $USER@$IP_TRIXIE:~/"
    echo "-------------------------------------------------------------"
    echo "VOER DIT UIT OP DEZE PI (TRIXIE) NA DE OVERDRACHT:"
    echo "   mariadb -u root -p temperatures < ~/temperaturesdump_*.sql"
    echo "-------------------------------------------------------------"

    read -p "Druk op [Enter] zodra je klaar bent om verder te gaan..."
fi

# -----------------------------------------------------------------
# STAP 5: Webserver Inrichten
# -----------------------------------------------------------------
if stel_vraag "Stap 5: Jouw web-ontwerp naar de webroot (/var/www/html) kopiëren?"; then
    print_titel "STAP 5: WEBSERVER CONFIGURATIE"

    # Maak de benodigde mappen aan
    sudo mkdir -p /var/www/html/afbeeldingen

    # TEST: Bestaat de standaard Apache index.html? Zo ja, verwijder deze.
    if [ -f /var/www/html/index.html ]; then
        echo "Standaard Apache index.html gevonden. Bezig met verwijderen..."
        sudo rm /var/www/html/index.html
    fi

    # Kopieer jouw bestanden naar de webroot
    if [ -d "$WEB_DEST" ]; then
        sudo cp -r "$WEB_DEST/"* /var/www/html/ 2>/dev/null || true
    fi

    # Rechten goedzetten zodat de webserver alles kan lezen en schrijven
    sudo chown -R www-data:www-data /var/www/html/
    sudo chmod -R 775 /var/www/html/

    echo "Webserver is ingericht en de oude index.html is opgeruimd."
fi


# -----------------------------------------------------------------
# STAP 6: Automatisering (Cron via crontab -e methode)
# -----------------------------------------------------------------
if stel_vraag "Stap 6: Cronjobs instellen in jouw persoonlijke crontab?"; then
    print_titel "STAP 6: AUTOMATISERING (crontab -e stijl)"

    # 1. Bestaande crontab ophalen, maar oude regels van dit project verwijderen
    # Zo voorkomen we dubbele regels als het script vaker wordt gedraaid.
    crontab -l 2>/dev/null | grep -v "pythonscripts" | grep -v "Raspi25Temperatuur.png" > temp_cron || true

    # 2. De nieuwe regels toevoegen aan het tijdelijke bestand
    echo "" >> temp_cron
    echo "# Elke 15 minuten de sensor uitlezen" >> temp_cron
    echo "0,15,30,45 * * * * ~/pythonscripts/dhtvenv/bin/python ~/pythonscripts/temperatuurlogger.py" >> temp_cron
    echo "" >> temp_cron
    echo "# Elke 15 minuten de afbeelding verversen" >> temp_cron
    echo "1,16,31,46 * * * * ~/pythonscripts/dhtvenv/bin/python ~/pythonscripts/MatplotlibDagTemperatuur.py" >> temp_cron
    echo "1,16,31,46 * * * * ~/pythonscripts/dhtvenv/bin/python ~/pythonscripts/MatplotlibWeekTemperatuur.py" >> temp_cron
    echo "1,16,31,46 * * * * ~/pythonscripts/dhtvenv/bin/python ~/pythonscripts/MatplotlibMaandTemperatuur.py" >> temp_cron
    echo "1,16,31,46 * * * * ~/pythonscripts/dhtvenv/bin/python ~/pythonscripts/MatplotlibDagVochtigheid.py" >> temp_cron
    echo "1,16,31,46 * * * * ~/pythonscripts/dhtvenv/bin/python ~/pythonscripts/MatplotlibWeekVochtigheid.py" >> temp_cron
    echo "1,16,31,46 * * * * ~/pythonscripts/dhtvenv/bin/python ~/pythonscripts/MatplotlibMaandVochtigheid.py" >> temp_cron
    echo "" >> temp_cron
    echo "# Elke 15 minuten de afbeelding kopiëren naar webroot" >> temp_cron
    echo "2,17,32,47 * * * * sudo cp ~/RaspiDagTemperatuur.png /var/www/html/afbeeldingen/RaspiDagTemperatuur.png" >> temp_cron
    echo "2,17,32,47 * * * * sudo cp ~/RaspiWeekTemperatuur.png /var/www/html/afbeeldingen/RaspiWeekTemperatuur.png" >> temp_cron
    echo "2,17,32,47 * * * * sudo cp ~/RaspiMaandTemperatuur.png /var/www/html/afbeeldingen/RaspiMaandTemperatuur.png" >> temp_cron
    echo "2,17,32,47 * * * * sudo cp ~/RaspiDagVochtigheid.png /var/www/html/afbeeldingen/RaspiDagVochtigheid.png" >> temp_cron
    echo "2,17,32,47 * * * * sudo cp ~/RaspiWeekVochtigheid.png /var/www/html/afbeeldingen/RaspiWeekVochtigheid.png" >> temp_cron
    echo "2,17,32,47 * * * * sudo cp ~/RaspiMaandVochtigheid.png /var/www/html/afbeeldingen/RaspiMaandVochtigheid.png" >> temp_cron

    # 3. Het tijdelijke bestand inladen als de nieuwe crontab
    crontab temp_cron
    rm temp_cron

    # 4. Cron service herstarten/activeren voor Trixie
    sudo systemctl enable cron
    sudo systemctl start cron

    echo "De regels zijn toegevoegd aan je crontab."
    echo "Controleer met: crontab -l"
fi


print_titel "INSTALLATIE VOLTOOID!"
echo "Dashboard: http://$(hostname -I | awk '{print $1}')"

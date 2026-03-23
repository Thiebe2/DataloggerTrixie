#!/usr/bin/python3
import mysql.connector
import matplotlib
matplotlib.use('Agg') # Nodig voor draaien zonder scherm (headless)
import matplotlib.pyplot as plt
import time
import os

# Automatisch het pad naar de home-folder van de huidige gebruiker bepalen
home_folder = os.path.expanduser("~")
bestandsnaam = "RaspiWeekTemperatuur.png"
temp_pad = os.path.join(home_folder, bestandsnaam)
web_pad = os.path.join("/var/www/html", bestandsnaam)

# Zoek datum vandaag
vandaag = time.strftime("%d-%m-%Y, %H:%M")
print(f"Grafiek genereren op: {vandaag}")

# Connect to MariaDB database
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="logger",
        passwd="paswoord",
        db="temperatures"
    )
    cur = conn.cursor()

    # Selecteer de laatste 672 metingen (7 dagen bij 96 metingen per dag)
    query = "SELECT dateandtime, temperature FROM temperaturedata ORDER BY dateandtime DESC LIMIT 672"
    cur.execute(query)
    data = cur.fetchall()

    cur.close()
    conn.close()

    # Data uitpakken (we draaien de data om zodat de tijd van links naar rechts loopt)
    data.reverse()
    dateandtime, temperature = zip(*data)

    # Grafiek maken
    plt.figure(figsize=(10, 7))
    plt.plot(dateandtime, temperature, marker='o', linestyle='-', markersize=2)

    plt.title(f"Temperatuur RaspiTP - {vandaag}")
    plt.xlabel("Tijdstip")
    plt.ylabel("Graden Celsius")
    plt.grid(True)

    # Automatisch de labels op de X-as schuin zetten voor leesbaarheid
    plt.gcf().autofmt_xdate()

    # Sla direct op in de web-map (werkt omdat we chmod 775 hebben gedaan in het installatiescript)
    plt.savefig(web_pad, dpi=100)
    print(f"Grafiek succesvol opgeslagen in: {web_pad}")

except Exception as e:
    print(f"Fout opgetreden: {e}")

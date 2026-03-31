#!/usr/bin/python3
import mysql.connector
import matplotlib
matplotlib.use('Agg')  # Nodig voor draaien zonder scherm (headless)
import matplotlib.pyplot as plt
import time
import os

# Automatisch het pad naar de home-folder van de huidige gebruiker bepalen
home_folder = os.path.expanduser("~")
bestandsnaam = "RaspiWeekVochtigheid.png"
web_pad = os.path.join("/var/www/html", bestandsnaam)

# Zoek datum vandaag
vandaag = time.strftime("%d-%m-%Y, %H:%M")
print(f"Grafiek genereren op: {vandaag}")

# Connect to MariaDB database
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="logger",
        password="paswoord",   # was: passwd=
        database="temperatures" # was: db=
    )
    cur = conn.cursor()

    # Selecteer de laatste 672 metingen (7 dagen bij 96 metingen per dag)
    query = "SELECT dateandtime, humidity FROM temperaturedata ORDER BY dateandtime DESC LIMIT 672"
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    conn.close()

    # Controleer of er data is
    if not data:
        print("Geen data gevonden in de database.")
    else:
        # Data omdraaien zodat de tijd van links naar rechts loopt
        data.reverse()
        dateandtime, humidity = zip(*data)

        # Grafiek maken
        plt.figure(figsize=(10, 7))
        plt.plot(dateandtime, humidity, marker='o', linestyle='-', markersize=2)
        plt.title(f"Temperatuur RaspiTP - {vandaag}")
        plt.xlabel("Tijdstip")
        plt.ylabel("Graden Celsius")
        plt.grid(True)

        # X-as labels schuin zetten voor leesbaarheid
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()  # Voorkomt dat labels worden afgeknipt

        plt.savefig(web_pad, dpi=100)
        print(f"Grafiek succesvol opgeslagen in: {web_pad}")

except mysql.connector.Error as db_err:
    print(f"Database fout: {db_err}")
except Exception as e:
    print(f"Fout opgetreden: {e}")

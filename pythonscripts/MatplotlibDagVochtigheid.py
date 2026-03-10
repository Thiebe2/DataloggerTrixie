#!/usr/bin/python3

#  Jan Moeskops - 22 september 2019
#  MatplotlibTest2 : test toegang tot de database
#   indien 4 keer per uur temperatuur gelogd wordt,
#   dan zijn er 96 meetresultaten per dag
#   toon de laatste dag,  zet foto in /var/www/html als sudo

import matplotlib.pyplot as plt 
import matplotlib     # deze lijn commentariëren wanneer niet op achtergrond gerenderd word (crontab)
matplotlib.use('Agg') # deze lijn commentariëren wanneer niet op achtergrond gerenderd word (crontab)
import matplotlib.pyplot as plt
import mysql.connector
import time
import shutil

# Zoek datum vandaag
vandaag=time.strftime("%d-%m-%Y, %H:%M")
# vandaag=time.strftime("%Y-%m-%d")
print(vandaag)

# connect to MySQL database
conn = mysql.connector.connect(host="localhost", user="logger", passwd="paswoord", db="temperatures")

# prepare a cursor
cur = conn.cursor()

# in deze query selecteren we de 96 laatste metingen
query = """
SELECT dateandtime,humidity FROM temperaturedata
ORDER BY dateandtime DESC LIMIT 96;
"""

# execute the query
cur.execute(query)

# retrieve the whole result set
data = cur.fetchall()

# close cursor and connection
cur.close()
conn.close()

# unpack data in TimeStamp (x axis) and Pac (y axis)
dateandtime, humidity = zip(*data)

##print(temperature, end='\n')

# graph code, plot lijntjes,  scatter puntjes
plt.plot(dateandtime, humidity)

# set title, X/Y labels
plt.title("Relatieve vochtigheid "+" Raspi19 " + vandaag)
plt.xlabel("Time of Day")
plt.ylabel("Rel. Vochtigheid (%)")
fig = plt.gcf()

# plt.xticks(TimeStamp, (hour))
fig.set_size_inches(10,7)
plt.grid(True)
plt.draw()

# plt.show()
fig.savefig('/home/pi19/vochtigheiddag.png', dpi=100)

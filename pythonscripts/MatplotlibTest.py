#!/usr/bin/python3

#  Jan Moeskops - 14 september 2021
#  Update mysql connector 09/10/24
#  MatplotlibTest2 : test toegang tot de database -  zet alle data in een grafiek

import matplotlib.pyplot as plt
import mysql.connector
import time

# connect to MySQL database
# conn = MySQLdb.connect(host="localhost", user="logger", passwd="paswoord", db="temperatures")
conn = mysql.connector.connect(
        host="localhost",
        user="logger",
        passwd="paswoord",
        db="temperatures"
)

# prepare a cursor
cur = conn.cursor()

# in deze query selecteren we alle data
query = """
SELECT dateandtime,temperature FROM temperaturedata ORDER BY dateandtime
"""

# execute the query
cur.execute(query)

# retrieve the whole result set
data = cur.fetchall()

# close cursor and connection
cur.close()
conn.close()

# unpack data in TimeStamp (x axis) and Pac (y axis)
dateandtime, temperature = zip(*data)

##print(temperature, end='\n')

# graph code, plot lijntjes,  scatter puntjes
plt.plot(dateandtime, temperature)

# set title, X/Y labels
plt.title("Temperatuur"+" Raspi19 ")
plt.xlabel("Time of Day")
plt.ylabel("graden Celsius")
fig = plt.gcf()

# plt.xticks(TimeStamp, (hour))
fig.set_size_inches(10,7)
plt.grid(True)
plt.draw()

plt.show()

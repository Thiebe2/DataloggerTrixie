#!/usr/bin/env python3
"""
OLED Display met Rotary Encoder voor Raspberry Pi - Systeem Info + DHT22
Gebruikt luma.oled library en polling (geen event callbacks)
Met auto-sleep na 30 minuten inactiviteit
"""

import time
import psutil
import socket
import RPi.GPIO as GPIO
import board
import adafruit_dht
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106

# OLED configuratie
serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

# DHT22 sensor configuratie
try:
    dht_sensor = adafruit_dht.DHT22(board.D22)
    dht_available = True
except:
    dht_available = False
    print("Waarschuwing: DHT22 sensor niet beschikbaar")

# Rotary encoder pinnen
CLK_PIN = 27  # GPIO27 (pin 13) - gewisseld!
DT_PIN = 17   # GPIO17 (pin 11) - gewisseld!
SW_PIN = 23   # GPIO23 (pin 16) - drukknop

# GPIO setup met cleanup
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variabelen
clk_last = GPIO.input(CLK_PIN)
sw_last = GPIO.input(SW_PIN)
current_page = 0
info_pages = ["CPU & RAM", "Opslag", "Netwerk", "Temperatuur", "DHT22 Sensor", "Uptime", "Systeem", "Datum & Tijd"]
last_update = 0
rotation_counter = 0  # Teller voor rotary stappen
STEPS_PER_PAGE = 2    # Aantal stappen voordat pagina verandert
detailed_mode = False  # Toggle tussen normale en gedetailleerde weergave

# Slaapstand variabelen
last_activity = time.time()  # Tijdstip van laatste activiteit
SLEEP_TIMEOUT = 1800  # 30 minuten in seconden (30 * 60)
is_sleeping = False  # Of display in slaapstand is

# DHT22 sensor cache
dht_last_read = 0
dht_temp = None
dht_humidity = None
DHT_READ_INTERVAL = 3  # Lees sensor elke 3 seconden (DHT22 heeft minimaal 2 sec nodig)

def wake_display():
    """Wakker maken van display"""
    global is_sleeping, last_activity
    if is_sleeping:
        is_sleeping = False
        device.show()
        print("✓ Display wakker")
    last_activity = time.time()
    update_display()

def sleep_display():
    """Zet display in slaapstand"""
    global is_sleeping
    if not is_sleeping:
        is_sleeping = True
        device.hide()
        print("💤 Display slaapstand (draai rotary om te wekken)")

def check_sleep_timeout():
    """Controleer of display in slaapstand moet"""
    global last_activity
    if not is_sleeping:
        if time.time() - last_activity > SLEEP_TIMEOUT:
            sleep_display()

def get_cpu_temp():
    """Haal CPU temperatuur op"""
    try:
        temps = psutil.sensors_temperatures()
        if 'cpu_thermal' in temps:
            return temps['cpu_thermal'][0].current
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            return float(f.read()) / 1000.0
    except:
        return 0.0

def get_dht22_data():
    """Haal DHT22 temperatuur en vochtigheid op met caching"""
    global dht_last_read, dht_temp, dht_humidity

    if not dht_available:
        return None, None

    current_time = time.time()

    # Gebruik gecachte waarden als recente lezing beschikbaar is
    if current_time - dht_last_read < DHT_READ_INTERVAL:
        return dht_temp, dht_humidity

    # Probeer sensor uit te lezen
    try:
        temperature = dht_sensor.temperature
        humidity = dht_sensor.humidity

        # Valideer waarden
        if temperature is not None and humidity is not None:
            if temperature >= -40 and temperature <= 80 and humidity >= 0 and humidity <= 100:
                dht_temp = round(temperature, 1)
                dht_humidity = round(humidity, 1)
                dht_last_read = current_time
                return dht_temp, dht_humidity
    except RuntimeError as e:
        # DHT22 geeft vaak RuntimeError, dit is normaal
        pass
    except Exception as e:
        print(f"DHT22 fout: {e}")

    # Geef gecachte waarden terug bij fout
    return dht_temp, dht_humidity

def get_ip_address():
    """Haal IP adres op"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Geen IP"

def get_uptime():
    """Haal uptime op"""
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)

        if days > 0:
            return f"{days}d {hours}u {minutes}m"
        elif hours > 0:
            return f"{hours}u {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "N/A"

def get_pi_model():
    """Haal Raspberry Pi model op"""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().strip().replace('\x00', '')
            # Kort het af als te lang
            if len(model) > 20:
                model = model[:17] + "..."
            return model
    except:
        return "Raspberry Pi"

def get_os_version():
    """Haal OS versie op"""
    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('PRETTY_NAME='):
                    os_name = line.split('=')[1].strip().replace('"', '')
                    # Kort naam
                    if 'Raspbian' in os_name or 'Debian' in os_name:
                        parts = os_name.split()
                        return f"{parts[0]} {parts[1] if len(parts) > 1 else ''}"
                    return os_name[:18]
        return "Linux"
    except:
        return "Linux"

def draw_bar(draw, x, y, width, height, percentage):
    """Teken een progress bar"""
    # Rand
    draw.rectangle((x, y, x + width, y + height), outline="white")
    # Vulling
    fill_width = int(width * percentage / 100)
    if fill_width > 0:
        draw.rectangle((x, y, x + fill_width, y + height), fill="white")

def draw_circle(draw, x, y, radius, percentage):
    """Teken een cirkel met percentage vulling"""
    # Teken lege cirkel
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="white")

    # Bereken hoeveel van de cirkel gevuld moet zijn
    # percentage naar graden (0-360), start van boven (270 graden in PIL)
    if percentage > 0:
        start_angle = 270  # Start boven
        end_angle = start_angle + (360 * percentage / 100)

        # Teken gevulde arc (taartpunt)
        draw.pieslice((x - radius, y - radius, x + radius, y + radius),
                     start=start_angle, end=end_angle, fill="white", outline="white")

def update_display():
    """Update het OLED display met de huidige pagina"""
    # Niet updaten als display slaapt
    if is_sleeping:
        return
    
    page = info_pages[current_page]

    with canvas(device) as draw:
        # Header alleen in normale modus
        if not detailed_mode:
            draw.rectangle((0, 0, 128, 9), fill="white")
            draw.text((2, 0), page, fill="black")
            y = 11
        else:
            y = 0

        if page == "CPU & RAM":
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()

            # CPU
            draw.text((0, y), f"CPU: {cpu_percent:.0f}%", fill="white")
            draw_bar(draw, 40, y+1, 88, 5, cpu_percent)

            y += 9
            # RAM
            draw.text((0, y), f"RAM: {ram.percent:.0f}%", fill="white")
            draw_bar(draw, 40, y+1, 88, 5, ram.percent)

            y += 9
            # RAM details
            draw.text((0, y), f"Vrij: {ram.available/1024**3:.1f}GB", fill="white")
            y += 8
            draw.text((0, y), f"Gebr: {ram.used/1024**3:.1f}GB", fill="white")

        elif page == "Opslag":
            disk = psutil.disk_usage('/')

            if not detailed_mode:
                # Normale modus - hoofdinfo met cirkel
                draw.text((0, y), f"Schijf: {disk.percent:.0f}%", fill="white")
                draw_circle(draw, 110, y+3, 8, disk.percent)

                y += 18
                draw.text((0, y), f"Gebr: {disk.used/1024**3:.1f}GB", fill="white")
            else:
                # Gedetailleerde modus - alleen belangrijkste info
                draw.text((0, y), f"Totaal: {disk.total/1024**3:.1f}GB", fill="white")
                y += 8
                draw.text((0, y), f"Vrij: {disk.free/1024**3:.1f}GB", fill="white")
                y += 8
                draw.text((0, y), f"Gebruikt: {disk.used/1024**3:.1f}GB", fill="white")

                y += 10
                net_io = psutil.disk_io_counters()
                draw.text((0, y), f"Lees MB: {net_io.read_bytes/1024**2:.0f}", fill="white")
                y += 8
                draw.text((0, y), f"Schrijf MB: {net_io.write_bytes/1024**2:.0f}", fill="white")

        elif page == "Netwerk":
            ip = get_ip_address()
            hostname = socket.gethostname()

            if not detailed_mode:
                # Normale modus - hoofdinfo
                draw.text((0, y), f"Host:", fill="white")
                y += 9
                # Kort hostname af als te lang
                if len(hostname) > 16:
                    hostname = hostname[:13] + "..."
                draw.text((2, y), hostname, fill="white")

                y += 10
                draw.text((0, y), f"IP:", fill="white")
                y += 9
                draw.text((2, y), ip, fill="white")
            else:
                # Gedetailleerde modus - alleen belangrijkste statistieken
                net_io = psutil.net_io_counters()

                draw.text((0, y), f"RX: {net_io.bytes_recv/1024**2:.1f}MB", fill="white")
                y += 8
                draw.text((0, y), f"TX: {net_io.bytes_sent/1024**2:.1f}MB", fill="white")

                y += 10
                draw.text((0, y), f"Pakket RX: {net_io.packets_recv}", fill="white")
                y += 8
                draw.text((0, y), f"Pakket TX: {net_io.packets_sent}", fill="white")

        elif page == "Temperatuur":
            cpu_temp = get_cpu_temp()
            cpu_percent = psutil.cpu_percent(interval=0.1)

            if not detailed_mode:
                # Normale modus - hoofdinfo met cirkel
                # Temperatuur (groot)
                y_start = 18
                draw.text((25, y_start), f"{cpu_temp:.1f}C", fill="white")

                y = y_start + 14
                draw.text((0, y), f"CPU: {cpu_percent:.0f}%", fill="white")
                draw_circle(draw, 110, y+3, 8, cpu_percent)
            else:
                # Gedetailleerde modus - alleen belangrijkste info
                cpu_freq = psutil.cpu_freq()

                draw.text((0, y), f"Temp: {cpu_temp:.1f}C", fill="white")
                y += 8
                draw.text((0, y), f"Freq: {cpu_freq.current:.0f}MHz", fill="white")

                y += 10
                cpu_per_core = psutil.cpu_percent(percpu=True, interval=0.1)
                draw.text((0, y), "CPU cores:", fill="white")
                y += 8

                # Toon cores met compacte cirkels
                for i, core_pct in enumerate(cpu_per_core[:4]):
                    draw.text((0, y), f"{i}:", fill="white")
                    draw_circle(draw, 118, y+3, 6, core_pct)
                    y += 10

        elif page == "DHT22 Sensor":
            temp, humidity = get_dht22_data()

            if temp is not None and humidity is not None:
                if not detailed_mode:
                    # Normale modus - hoofdinfo met cirkel
                    # Temperatuur (groot)
                    y_start = 16
                    draw.text((5, y_start), f"Temp:", fill="white")
                    draw.text((48, y_start), f"{temp:.1f}C", fill="white")

                    # Vochtigheid (groot)
                    y = y_start + 14
                    draw.text((5, y), f"Vocht:", fill="white")
                    draw.text((50, y), f"{humidity:.1f}%", fill="white")
                    draw_circle(draw, 110, y+3, 8, humidity)
                else:
                    # Gedetailleerde modus - alleen belangrijkste berekeningen
                    # Voelt aan temperatuur
                    feels_like = temp + (humidity - 50) * 0.05
                    draw.text((0, y), f"Voelt aan: {feels_like:.1f}C", fill="white")
                    y += 8

                    # Dauwpunt
                    dewpoint = temp - ((100 - humidity) / 5)
                    draw.text((0, y), f"Dauwpunt: {dewpoint:.1f}C", fill="white")
                    y += 10

                    # Comfort niveau
                    if 18 <= temp <= 24 and 30 <= humidity <= 60:
                        comfort = "Optimaal"
                    elif temp < 15:
                        comfort = "Te koud"
                    elif temp > 26:
                        comfort = "Te warm"
                    elif humidity < 30:
                        comfort = "Te droog"
                    elif humidity > 60:
                        comfort = "Te vochtig"
                    else:
                        comfort = "Acceptabel"
                    draw.text((0, y), f"Status: {comfort}", fill="white")
                    y += 10

                    # Cirkels voor temp en vocht
                    temp_pct = max(0, min(100, (temp / 40) * 100))
                    draw.text((0, y), "Temp", fill="white")
                    draw_circle(draw, 35, y+3, 6, temp_pct)
                    draw.text((50, y), "Vocht", fill="white")
                    draw_circle(draw, 90, y+3, 6, humidity)
            else:
                y = 24
                draw.text((10, y), "DHT22 Sensor", fill="white")
                y += 10
                draw.text((5, y), "Geen data...", fill="white")

        elif page == "Uptime":
            uptime = get_uptime()
            boot_time = time.strftime("%d-%m %H:%M", time.localtime(psutil.boot_time()))

            if not detailed_mode:
                # Normale modus - hoofdinfo
                draw.text((0, y), "Uptime:", fill="white")
                y += 9
                draw.text((5, y), uptime, fill="white")
            else:
                # Gedetailleerde modus - alleen belangrijkste info
                draw.text((0, y), f"Boot: {boot_time}", fill="white")

                y += 10
                load_avg = psutil.getloadavg()
                draw.text((0, y), f"Load 1m: {load_avg[0]:.2f}", fill="white")
                y += 8
                draw.text((0, y), f"Load 5m: {load_avg[1]:.2f}", fill="white")

                y += 10
                num_processes = len(psutil.pids())
                draw.text((0, y), f"Processen: {num_processes}", fill="white")

        elif page == "Systeem":
            pi_model = get_pi_model()
            os_version = get_os_version()

            if not detailed_mode:
                # Normale modus - hoofdinfo
                # Model (korter)
                if len(pi_model) > 18:
                    pi_model = pi_model[:15] + "..."
                draw.text((0, y), pi_model, fill="white")

                y += 10
                draw.text((0, y), os_version, fill="white")
            else:
                # Gedetailleerde modus - alleen belangrijkste specs
                cpu_count = psutil.cpu_count()
                mem_total = psutil.virtual_memory().total / 1024**3
                disk_total = psutil.disk_usage('/').total / 1024**3

                draw.text((0, y), f"CPU cores: {cpu_count}", fill="white")
                y += 8
                draw.text((0, y), f"RAM: {mem_total:.1f}GB", fill="white")
                y += 8
                draw.text((0, y), f"Disk: {disk_total:.1f}GB", fill="white")

                y += 10
                num_processes = len(psutil.pids())
                draw.text((0, y), f"Processen: {num_processes}", fill="white")

                y += 10
                if len(os_version) > 18:
                    os_version = os_version[:15] + "..."
                draw.text((0, y), os_version, fill="white")

        elif page == "Datum & Tijd":
            current_time = time.strftime("%H:%M:%S")
            current_date = time.strftime("%d-%m-%Y")
            weekday = time.strftime("%A")
            # Vertaal weekdag naar Nederlands
            weekdays = {
                "Monday": "Maandag",
                "Tuesday": "Dinsdag",
                "Wednesday": "Woensdag",
                "Thursday": "Donderdag",
                "Friday": "Vrijdag",
                "Saturday": "Zaterdag",
                "Sunday": "Zondag"
            }
            weekday_nl = weekdays.get(weekday, weekday)

            if not detailed_mode:
                # Normale modus - hoofdinfo
                # Grote tijd display
                y_start = 20
                draw.text((20, y_start), current_time, fill="white")

                y = y_start + 13
                draw.text((0, y), weekday_nl, fill="white")
            else:
                # Gedetailleerde modus - alleen belangrijkste info
                draw.text((0, y), current_date, fill="white")
                y += 8
                draw.text((0, y), weekday_nl, fill="white")

                y += 10
                week_num = time.strftime("%W")
                draw.text((0, y), f"Week: {week_num}", fill="white")

                y += 10
                # Percentage van de dag met cirkel
                now = time.localtime()
                seconds_today = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
                day_pct = (seconds_today / 86400) * 100
                draw.text((0, y), f"Dag: {day_pct:.1f}%", fill="white")
                draw_circle(draw, 110, y+3, 8, day_pct)

        # Pagina indicator (onderaan) - alleen in normale modus
        if not detailed_mode:
            draw.text((0, 52), f"< {current_page+1}/{len(info_pages)} >", fill="white")

def check_rotary():
    """Check rotary encoder status (polling)"""
    global clk_last, current_page, rotation_counter

    clk_state = GPIO.input(CLK_PIN)
    dt_state = GPIO.input(DT_PIN)

    if clk_state != clk_last:
        # Rotary activiteit gedetecteerd - wek display wakker
        if is_sleeping:
            wake_display()
        else:
            # Normaal gebruik - wissel pagina
            if dt_state != clk_state:
                # Rechtsom - volgende pagina
                rotation_counter += 1
            else:
                # Linksom - vorige pagina
                rotation_counter -= 1

            # Verander pagina alleen na STEPS_PER_PAGE stappen
            if abs(rotation_counter) >= STEPS_PER_PAGE:
                if rotation_counter > 0:
                    # Rechtsom = volgende pagina
                    current_page = (current_page + 1) % len(info_pages)
                    print(f"→ Pagina {current_page + 1}: {info_pages[current_page]}")
                else:
                    # Linksom = vorige pagina
                    current_page = (current_page - 1) % len(info_pages)
                    print(f"← Pagina {current_page + 1}: {info_pages[current_page]}")

                rotation_counter = 0  # Reset counter
                last_activity = time.time()  # Reset slaap timer
                update_display()

        clk_last = clk_state
        time.sleep(0.01)  # Debounce

def check_button():
    """Check button status (polling)"""
    global sw_last, detailed_mode, last_activity

    sw_state = GPIO.input(SW_PIN)

    if sw_state == 0 and sw_last == 1:  # Knop ingedrukt
        # Wek display wakker als het slaapt
        if is_sleeping:
            wake_display()
        else:
            # Normaal gebruik - wissel modus
            detailed_mode = not detailed_mode
            mode_text = "Gedetailleerd" if detailed_mode else "Normaal"
            print(f"✓ Knop - Modus: {mode_text}")
            last_activity = time.time()  # Reset slaap timer
            update_display()
        time.sleep(0.3)  # Debounce

    sw_last = sw_state

# Start
print("OLED + Rotary Encoder + DHT22 gestart")
print("Draai de encoder om te navigeren")
print("Druk op de knop om normale/gedetailleerde weergave te wisselen")
print(f"Display gaat automatisch uit na {SLEEP_TIMEOUT//60} minuten inactiviteit")
print("Druk Ctrl+C om te stoppen")

update_display()

try:
    while True:
        # Check rotary encoder
        check_rotary()

        # Check button
        check_button()

        # Check slaapstand timeout
        check_sleep_timeout()

        # Auto-refresh display elke 2 seconden (alleen als niet slapend)
        if not is_sleeping:
            current_time = time.time()
            if current_time - last_update > 2:
                update_display()
                last_update = current_time

        time.sleep(0.001)  # Kleine delay om CPU niet te overbelasten

except KeyboardInterrupt:
    print("\nProgramma gestopt")

finally:
    device.clear()
    GPIO.cleanup()
    if dht_available:
        dht_sensor.exit()

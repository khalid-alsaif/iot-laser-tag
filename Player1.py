from machine import Pin, PWM, time_pulse_us
import time
import network
import umqtt.simple as mqtt

# ─── WiFi ──────────────────────────────────────────────────

WIFI_SSID     = "YOUR_WIFI_NAME"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"
BROKER_IP     = "YOUR_BROKER_IP"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    print("Connecting to WiFi", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\nWiFi connected:", wlan.ifconfig()[0])

# ─── MQTT ──────────────────────────────────────────────────

PLAYER_ID = 0x01  # Change to 0x02 on second ESP32
CLIENT_ID = f"player{PLAYER_ID}"

TOPIC_HEALTH = f"lasertag/player{PLAYER_ID}/health"
TOPIC_HIT    = f"lasertag/player{PLAYER_ID}/hit"
TOPIC_STATUS = b"lasertag/game/status"
TOPIC_RESTART = b"lasertag/game/restart"

client = None

def on_message(topic, msg):
    global hits, alive, last_shot_time
    if topic == TOPIC_RESTART:
        print("Game restarted!")
        hits = 0
        alive = True
        last_shot_time = 0
        update_leds(0)
        safe_publish(TOPIC_HEALTH, str(MAX_HITS), retain=True)
        safe_publish(TOPIC_HIT, "-", retain=True)
        safe_publish(TOPIC_STATUS, f"Player {PLAYER_ID} ready!", retain=True)
        
def connect_mqtt():
    global client
    c = mqtt.MQTTClient(CLIENT_ID, BROKER_IP, port=1883)
    c.set_callback(on_message)
    c.connect()
    c.subscribe(TOPIC_RESTART)
    print("MQTT connected!")
    client = c

def safe_publish(topic, msg, retain=False):
    global client
    try:
        client.publish(topic, msg, retain=retain)
    except Exception as e:
        print("MQTT publish failed:", e)
        try:
            connect_mqtt()
            client.publish(topic, msg, retain=retain)
        except:
            print("Reconnect failed, skipping publish")

# ─── Hardware ──────────────────────────────────────────────

ir_tx  = Pin(18, Pin.OUT)
ir_rx  = Pin(9, Pin.IN, Pin.PULL_UP)
button = Pin(2, Pin.IN, Pin.PULL_UP)

LED_PINS = [13, 12, 11]
leds = [PWM(Pin(p), freq=1000, duty=0) for p in LED_PINS]

DUTY_OFF  = 0
DUTY_HALF = 512
DUTY_FULL = 1023

def update_leds(hits):
    for i in range(3):
        hits_into_this_led = hits - (i * 2)
        if hits_into_this_led <= 0:
            leds[i].duty(DUTY_OFF)
        elif hits_into_this_led == 1:
            leds[i].duty(DUTY_HALF)
        else:
            leds[i].duty(DUTY_FULL)

# ─── IR Transmitter ────────────────────────────────────────

def carrier_burst(duration_us):
    pwm = PWM(ir_tx, freq=38000, duty=512)
    time.sleep_us(duration_us)
    pwm.deinit()
    ir_tx.value(0)

def send_nec(address, command):
    carrier_burst(9000)
    time.sleep_us(4500)
    frame  =  (address & 0xFF)
    frame |= ((~address & 0xFF) << 8)
    frame |= ((command  & 0xFF) << 16)
    frame |= ((~command & 0xFF) << 24)
    for i in range(32):
        carrier_burst(560)
        if (frame >> i) & 1:
            time.sleep_us(1690)
        else:
            time.sleep_us(565)
    carrier_burst(560)

# ─── IR Receiver ───────────────────────────────────────────

def read_nec():
    low = time_pulse_us(ir_rx, 0, 100000)
    if not (8000 < low < 10000):
        return None, None
    high = time_pulse_us(ir_rx, 1, 100000)
    if not (3500 < high < 5500):
        return None, None
    value = 0
    for i in range(32):
        low  = time_pulse_us(ir_rx, 0, 20000)
        high = time_pulse_us(ir_rx, 1, 20000)
        if not (400 < low < 800):
            return None, None
        if 400 < high < 900:
            bit = 0
        elif 1200 < high < 2000:
            bit = 1
        else:
            return None, None
        value |= bit << i
    address = value & 0xFF
    command = (value >> 16) & 0xFF
    return address, command

# ─── Game State ────────────────────────────────────────────

SHOOT_CMD   = 0x01
COOLDOWN_MS = 500
MAX_HITS    = 6

hits           = 0
last_shot_time = 0
alive          = True
last_ping      = 0
PING_INTERVAL  = 10000  # ping broker every 10 seconds

# ─── Boot ──────────────────────────────────────────────────

connect_wifi()
connect_mqtt()
update_leds(0)

safe_publish(TOPIC_STATUS, f"Player {PLAYER_ID} online", retain=True)
safe_publish(TOPIC_HEALTH, str(MAX_HITS - hits), retain=True)
safe_publish(TOPIC_HIT, "-", retain=True)

print(f"Player {PLAYER_ID} ready!")

# ─── Main Loop ─────────────────────────────────────────────

while True:
    now = time.ticks_ms()
    try:
        client.check_msg()
    except:
        connect_mqtt()
        #print("fwefw")
    if not alive:
        continue

    # ── Keepalive ping ──
#     if time.ticks_diff(now, last_ping) > PING_INTERVAL:
#         try:
#             client.ping()
#             last_ping = now
#         except:
#             connect_mqtt()

    # ── Shoot ──
    if button.value() == 0:
        if time.ticks_diff(now, last_shot_time) > COOLDOWN_MS:
            print("Pew!")
            send_nec(PLAYER_ID, SHOOT_CMD)
            last_shot_time = time.ticks_ms()
            time.sleep_ms(50)

    # ── Receive ──
    if ir_rx.value() == 0:
        address, command = read_nec()
        if address is not None and address != PLAYER_ID:
            hits += 1
            update_leds(hits)
            remaining_health = MAX_HITS - hits
            print(f"HIT by player {address}! Health: {remaining_health}/{MAX_HITS}")
            safe_publish(TOPIC_HIT,    f"Hit by player {address}", retain=True)
            safe_publish(TOPIC_HEALTH, str(remaining_health), retain=True)

            if hits >= MAX_HITS:
                alive = False
                safe_publish(TOPIC_STATUS, f"Player {PLAYER_ID} DEAD - Player {address} wins!", retain=True)
                print("YOU ARE DEAD!")
                for _ in range(3):
                    for led in leds:
                        led.duty(DUTY_FULL)
                    time.sleep_ms(300)
                    for led in leds:
                        led.duty(DUTY_OFF)
                    time.sleep_ms(300)
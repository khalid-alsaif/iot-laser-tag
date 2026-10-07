# instruction_manual

IoT Laser Tag System

Instruction Manual

Setup Instructions, Limitations & Known Issues

Saud Alsaleem  |  Khalid Alsaif

COE 454: Internet of Things — Term 252

King Fahd University of Petroleum and Minerals



1. System Overview

This manual describes how to set up and run the IoT Laser Tag system. The system consists of two ESP32-S3-DevKitC microcontrollers (one per player), a Mosquitto MQTT broker running on a local machine, and a Node-RED dashboard for real-time game monitoring and control.

Each player's device handles all game logic locally (IR shooting, hit detection, LED health display) and publishes game events to the broker over WiFi. The Node-RED dashboard visualizes health, hit logs, and game status, and can trigger a game restart remotely.

1.1 Required Hardware (per player)

Component

Quantity

Notes

ESP32-S3-DevKitC

1

Main MCU

IR Transmitter Module

1

38 kHz, pre-built PCB module

IR Receiver Module

1

TSOP-based, pre-built PCB module

Red LED

3

Health display

220Ω Resistors

3

One per LED

Push Button

1

Trigger / fire button

Breadboard + jumper wires

1 set

For prototyping



1.2 Required Software

MicroPython firmware flashed on both ESP32-S3 devices

Python 3.x (for flashing tools — esptool, mpremote, or Thonny)

Eclipse Mosquitto 2.x (MQTT broker, runs on the server machine)

Node.js + Node-RED v4.x (dashboard, runs on the same or different machine)

node-red-dashboard v3.6.6 plugin (classic dashboard, NOT FlowFuse)

umqtt.simple MicroPython library (installed on each ESP32)



2. Hardware Wiring

Wire each ESP32-S3-DevKitC as follows. Both player devices use identical wiring — the only difference is the PLAYER_ID variable in the firmware.

2.1 Pin Assignment

ESP32 Pin

Connected To

Notes

GPIO 18

IR Transmitter — DATA pin

Output. Module VCC → 3.3V, GND → GND

GPIO 9

IR Receiver — OUT pin

Input, PULL_UP. Module VCC → 3.3V, GND → GND

GPIO 13

LED 1 (anode via 220Ω)

PWM output. LED cathode → GND

GPIO 12

LED 2 (anode via 220Ω)

PWM output. LED cathode → GND

GPIO 11

LED 3 (anode via 220Ω)

PWM output. LED cathode → GND

GPIO 2

Push button (one leg)

Input, PULL_UP. Other leg → GND

3.3V

IR Transmitter VCC, IR Receiver VCC

Do NOT use 5V for receiver

GND

IR Transmitter GND, IR Receiver GND, LED cathodes, Button

Common ground



Important: GPIO 35, 36, and 37 on the ESP32-S3-DevKitC are reserved for internal PSRAM/flash and cannot be used as general-purpose I/O. Do not assign any component to these pins.

Both IR modules used are pre-built PCB modules with onboard resistors. Do NOT add external resistors to the IR transmitter DATA line or IR receiver OUT line — the modules handle this internally.



3. Software Setup

3.1 Flashing MicroPython on the ESP32-S3

Download the latest MicroPython firmware for ESP32-S3 from https://micropython.org/download/ESP32_GENERIC_S3/

Install esptool: pip install esptool

Erase the flash:

esptool.py --chip esp32s3 erase_flash

Flash MicroPython:

esptool.py --chip esp32s3 --baud 460800 write_flash -z 0x0 firmware.bin

Verify the device boots and shows the MicroPython REPL over USB serial (use Thonny or mpremote).

3.2 Installing umqtt on the ESP32

In the MicroPython REPL on each ESP32, run:

import mip

mip.install("umqtt.simple")

This requires the ESP32 to have an active WiFi connection. Connect to WiFi first using network.WLAN() in the REPL if needed before running mip.install().

3.3 Uploading the Firmware

Open Thonny (or use mpremote) and connect to the ESP32.

Create a new file named main.py and paste the full game firmware code.

Set PLAYER_ID = 0x01 for Player 1's device.

Set PLAYER_ID = 0x02 for Player 2's device.

Set the correct WiFi credentials and broker IP in the code:

WIFI_SSID     = "YOUR_WIFI_NAME"

WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

BROKER_IP     = "YOUR_BROKER_IP"

Save the file to the ESP32 as main.py so it runs automatically on boot.

Repeat for the second ESP32, changing only PLAYER_ID to 0x02.

3.4 Installing and Configuring Mosquitto

Download Eclipse Mosquitto from https://mosquitto.org/download/ and install it.

Locate the mosquitto.conf file (typically C:\Program Files\mosquitto\mosquitto.conf on Windows).

Add the following two lines at the very top of the file:

listener 1883

allow_anonymous true

Start the broker from PowerShell:

& "C:\Program Files\mosquitto\mosquitto.exe" -c "C:\Program Files\mosquitto\mosquitto.conf" -v

Verify it shows:

mosquitto version 2.x.x running

Opening ipv4 listen socket on port 1883

Keep this terminal open while the game is running. If the broker stops, all MQTT communication between players and the dashboard will fail.

3.5 Installing Node-RED and the Dashboard

Install Node.js from https://nodejs.org if not already installed.

Install Node-RED globally:

npm install -g --unsafe-perm node-red

Start Node-RED:

node-red

Open a browser and go to http://localhost:1880

Install the dashboard plugin: click the hamburger menu (top right) → Manage palette → Install tab → search node-red-dashboard → install version 3.6.6.

CRITICAL: Do NOT install @flowfuse/node-red-dashboard alongside node-red-dashboard. Having both installed simultaneously causes a TypeError that prevents all dashboard widgets from rendering. Use only the classic node-red-dashboard v3.6.6.

3.6 Importing the Node-RED Flow

In Node-RED, click hamburger menu → Import → paste the project flow JSON → click Import.

After importing, open each gauge and text node and assign it to the [Laser Tag] Game group. The Group field will show an orange warning if it is not set — click the + button next to Group, name it Game, then create a Tab named Laser Tag.

Update the MQTT broker IP in all mqtt in and mqtt out nodes: double-click any mqtt in node → click pencil next to broker → change Server to the IP of the machine running Mosquitto → click Update.

Click Deploy (red button, top right).

Open the dashboard at http://localhost:1880/ui — you should see the Laser Tag tab with both health gauges.



4. Running the Game

4.1 Startup Sequence

Follow this order every time you start the system:

Start the Mosquitto broker on the server machine (see Section 3.4).

Start Node-RED on the dashboard machine and open http://localhost:1880/ui.

Power on both ESP32 devices (connect via USB or battery).

Verify in the broker terminal that both players connected:

New client connected from ... as player1

New client connected from ... as player2

Verify on the dashboard that both health gauges show 6 and Game Status shows Player 1 online / Player 2 online.

The system is now ready to play.

4.2 Playing the Game

Press the button to fire. The IR transmitter sends a NEC-encoded signal carrying your player ID.

Point the transmitter directly at the opponent's IR receiver to register a hit.

Each confirmed hit reduces the opponent's health by 1 step on their LED display.

Health is displayed on the 3 LEDs: first LED goes half-bright at hit 1, fully bright at hit 2. Second LED follows at hits 3-4. Third LED follows at hits 5-6.

At 6 hits, all 3 LEDs flash 3 times and the player is declared dead. The Game Status on the dashboard updates to show the winner.

A 500 ms cooldown prevents multiple shots from registering from a single button press.

4.3 Restarting the Game

Press the Restart Game button on the Node-RED dashboard (http://localhost:1880/ui).

The dashboard publishes 6 MQTT messages simultaneously: a restart command to both ESP32s, health reset to 6 for both players, hit logs cleared, and game status updated.

Both ESP32s receive the restart command via MQTT and reset their health, alive flag, and LEDs automatically.

Both gauges on the dashboard return to 6 and the game is ready to play again.

If the dashboard gauges do not reset, check that the MQTT broker is still running and both ESP32s are connected. The ESP32 REPL should print 'Game restarted!' when the restart command is received.



5. Limitations

5.1 Hardware Limitations

IR range is limited to approximately 2–5 meters with direct line-of-sight between transmitter and receiver. Beyond this distance, hit detection becomes unreliable.

The IR transmitter has a narrow beam angle (~20°). Players must aim directly at the opponent's receiver. Angled or reflected shots will not register.

Strong ambient IR sources such as sunlight or incandescent lighting can interfere with the IR receiver, causing false triggers or missed hits. Avoid playing in direct sunlight.

There is no physical separation between the transmitter and receiver on the same device. A player's own shot can occasionally reflect off nearby surfaces and register as a self-hit. The software filters this by discarding received signals that match the local PLAYER_ID, but extreme reflections in enclosed spaces may still cause issues.

The system supports exactly two players. Multi-player team modes are not implemented.

There is no ammo limit. Players can fire continuously subject only to the 500 ms cooldown.

There is no game timer. A match ends only when one player reaches 6 hits.

5.2 Software and Network Limitations

Both ESP32 devices must be on the same local network as the Mosquitto broker. Client isolation on mobile phone hotspots will prevent the ESP32 from reaching the broker — use a router or laptop hotspot instead.

The MQTT broker must be running before the ESP32 devices are powered on. If the broker starts after the ESP32 boots, the ESP32 will not automatically reconnect without a reboot (unless the safe_publish reconnection logic triggers a retry).

Node-RED must be running on the same machine or a machine with network access to the broker at port 1883. Firewall rules blocking port 1883 will prevent Node-RED from receiving messages.

If the WiFi connection drops mid-game, the ESP32 will not automatically reconnect to WiFi. A hardware reset is required. The game logic continues locally but MQTT updates to the dashboard will fail.

MQTT messages are sent with QoS 0 (fire and forget). In poor network conditions, health updates or hit events may not be delivered to the broker.

The health gauge on the dashboard shows 0 on first load until the ESP32 publishes an initial health value. This is resolved immediately after both ESP32s boot and connect.

5.3 MicroPython Limitations

MicroPython's time_pulse_us() function is used for NEC protocol decoding. On heavily loaded systems or during WiFi reconnection events, interrupt timing may be affected, potentially causing missed or misread IR frames.

The main loop is single-threaded. During MQTT safe_publish() reconnection retries, the button and IR receiver are not checked, which may cause a brief (~1 second) unresponsive period.



6. Known Issues and Solutions

Issue

Cause

Solution

ValueError: invalid pin on boot

GPIO 35/36/37 reserved on ESP32-S3

Use GPIO 9 for IR receiver

ESP32 freezes after MQTT connect

Phone hotspot client isolation

Use a router or laptop hotspot without client isolation

Dashboard shows 'Please add UI nodes'

Group field empty after JSON import

Manually create Tab and Group, assign all UI nodes

TypeError in Node-RED on startup

Both FlowFuse and classic dashboard installed

Uninstall @flowfuse/node-red-dashboard, keep only classic v3.6.6

Restart button does not reset dashboard gauges

Old retained messages persist on broker

Use function node to publish retained reset messages for all topics

Player cannot shoot (no 'Pew!' in REPL)

read_nec() blocking the main loop

Add guard: only call read_nec() if ir_rx.value() == 0

Health gauge shows 0 on dashboard load

Dashboard subscribed before ESP32 published

ESP32 publishes initial health with retain=True on boot





7. Quick Reference

7.1 MQTT Topics

Topic

Publisher

Subscriber

Retained

lasertag/player1/health

Player 1 ESP32

Node-RED

Yes

lasertag/player2/health

Player 2 ESP32

Node-RED

Yes

lasertag/player1/hit

Player 1 ESP32

Node-RED

Yes

lasertag/player2/hit

Player 2 ESP32

Node-RED

Yes

lasertag/game/status

Both ESP32s

Node-RED

Yes

lasertag/game/restart

Node-RED

Both ESP32s

No



7.2 Key Configuration Variables (firmware)

Variable

Default

Description

PLAYER_ID

0x01

0x01 for Player 1, 0x02 for Player 2

BROKER_IP

YOUR_LOCAL_IP

IP address of machine running Mosquitto

MAX_HITS

6

Hits required to eliminate a player

COOLDOWN_MS

500

Minimum milliseconds between shots

PING_INTERVAL

10000

MQTT keepalive ping interval in milliseconds





End of Instruction Manual
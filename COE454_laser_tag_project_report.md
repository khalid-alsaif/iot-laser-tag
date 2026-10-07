# COE454_laser_tag_project_report

IoT Laser Tag: A Real-Time Multiplayer Game with MQTT and Edge Computing

Saud Alsaleem and Khalid Alsaif

King Fahd University of Petroleum and Minerals

Computer Engineering Department COE 454: Internet of Things – Term 252





Abstract— This report presents the design and implementation of an IoT-based laser tag system built using two ESP32-S3 microcontrollers communicating via infrared (IR) signals encoded with the NEC protocol. The system features real-time health tracking using PWM-controlled LEDs, game state management published over MQTT to a Mosquitto broker, and a live Node-RED dashboard for spectators. The project demonstrates a complete IoT pipeline encompassing sensing (IR receiver), actuation (LEDs and IR transmitter), edge computing (local game logic on the ESP32), and cloud-layer visualization (Node-RED dashboard). Performance evaluation covers MQTT publish latency, IR detection reliability, and protocol overhead analysis. The system successfully supports two-player real-time gameplay with dashboard-initiated game restarts via bidirectional MQTT communication.



Introduction

The Internet of Things (IoT) has expanded beyond traditional monitoring and automation applications into interactive, real-time systems that require low-latency communication between multiple distributed nodes. This project explores this domain through the implementation of a two-player IoT laser tag game, a system that demands reliable sensing, fast actuation, and coordinated state management across multiple devices.

Commercial laser tag systems are typically proprietary, expensive, and not designed for customization or integration with IoT platforms. Our solution provides an open, cost-effective alternative built entirely from commodity hardware: ESP32-S3 development kits, IR transmitter and receiver modules, LEDs, and push buttons. Despite the name “laser tag,” commercial systems actually use infrared communication rather than lasers, as IR is safe for human exposure and supports data encoding. Our system follows the same principle, using the NEC infrared protocol for hit detection, MQTT for game state communication, and a Node-RED dashboard for real-time visualization and game control.

The primary advantage of this approach is the clear separation between edge and cloud computing layers. All time-critical operations, including IR encoding and decoding, hit detection, health tracking, and LED actuation, execute locally on the ESP32 without network dependency. The MQTT layer handles non-time-critical but important tasks such as publishing game events to the dashboard and receiving game control commands like restart signals. This architecture ensures gameplay remains responsive even under network variability.

The project satisfies all COE 454 course requirements: it employs two MCUs (one per player), implements two complete control cycles (hit detection with health reduction, and game-over detection with winner announcement), uses MQTT as the mandatory protocol, and provides a descriptive data analysis dashboard showing live health gauges, hit logs, game status, and a restart control button.

System Design 

The IoT Laser Tag system is designed as a distributed architecture where two ESP32-S3 microcontrollers serve as edge devices, a Mosquitto MQTT broker handles message routing, and a Node-RED instance provides the visualization and control dashboard. The following subsections detail each architectural layer and the technologies employed.

System Architecture

Each player’s vest consists of an ESP32-S3-DevKitC board connected to an IR transmitter module, an IR receiver module, three LEDs for health display, and a push button for firing. The IR transmitter and receiver are pre-built modules with onboard resistors and circuitry, simplifying wiring to three pins each (VCC, GND, and DATA/OUT). The hardware components per player are: one ESP32-S3-DevKitC (main MCU), one IR transmitter module (38 kHz, DATA pin connected to GPIO 18), one IR receiver module (TSOP-based, OUT pin connected to GPIO 9), three red LEDs with 220Ω resistors (connected to GPIO 13, 12, and 11), one push button (connected to GPIO 2 with internal pull-up resistor), and one 18650 Li-Ion battery with TP4056 charging module for portable power.

The overall system architecture is as follows. Both ESP32 devices communicate with each other via point-to-point IR signals for hit detection. Simultaneously, both devices connect over WiFi to a Mosquitto MQTT broker running on a separate machine on the local network. The Node-RED dashboard subscribes to MQTT topics to display live game data, and can also publish restart commands back through the broker to both ESP32 devices. The following graph represents this architecture:







Network Architecture

The network architecture consists of two layers. The physical game layer uses point-to-point infrared communication between players. The IR transmitter emits a 38 kHz modulated NEC-encoded signal carrying a 32-bit frame that includes the shooter’s player ID (8-bit address), an inverted copy of the address for error checking, a command byte indicating the action (shoot), and the inverted command byte. The IR receiver module demodulates this signal, and the read_nec() function measures pulse timings to decode each bit: a short silence (~565 µs) after the 560 µs carrier burst represents a 0, while a long silence (~1690 µs) represents a 1.

The telemetry layer uses WiFi (802.11) to connect both ESP32-S3 devices to a local network. Each ESP32 publishes game events to a Mosquitto MQTT broker running on a separate machine (IP: YOUR_LOCAL_IP, port 1883). The MQTT topics are structured hierarchically: lasertag/player{id}/health for remaining health points, lasertag/player{id}/hit for hit event descriptions, lasertag/game/status for game state announcements, and lasertag/game/restart for receiving restart commands from the dashboard. Node-RED subscribes to all topics under lasertag/# and renders the data on a web-based dashboard.

The following sequence diagram illustrates the data flow for a typical hit event and for a restart command:



Computing Architecture

The computing architecture follows a two-tier edge-cloud model. At the edge layer, each ESP32-S3 running MicroPython handles all time-critical game logic locally. This includes NEC protocol encoding and decoding using carrier_burst() for 38 kHz PWM generation and read_nec() for pulse-timing-based decoding, hit validation by checking that the received player ID differs from the local player’s ID to prevent self-hits from reflected signals, health state management using a hit counter (0 to 6) and an alive boolean flag, PWM-based LED brightness control providing six progressive levels of visual feedback (off, half brightness, full brightness across three LEDs), button input handling with a 500 ms cooldown to prevent shot spamming, and MQTT event publishing with automatic reconnection on failure via a safe_publish() wrapper function.

At the cloud layer, the Mosquitto MQTT broker and Node-RED dashboard run on a separate machine on the local network. The broker routes all messages between the ESP32 devices and the dashboard. Node-RED subscribes to all lasertag/# topics and renders live health gauges, hit logs, and game status on a web-based UI accessible at http://<broker-ip>:1880/ui. The dashboard also publishes restart commands back to the ESP32 devices via the broker, demonstrating bidirectional cloud-to-edge communication. The Mosquitto MQTT broker is hosted on a server machine and started using the following command:

.\mosquitto.exe -c .\mosquitto.conf -v

The broker listens on the IP address of the hosting machine and manages message exchange between the ESP32 edge devices and the game dashboard. The MQTT communication architecture is based on a publish/subscribe model, where ESP32 devices publish game events and the dashboard server subscribes to the corresponding topics.



For a two-player laser tag system, the MQTT broker uses the following topics:

lasertag/player0x01/health 

Publisher: Player 1 ESP32 

Subscriber: Server dashboard 

lasertag/player0x02/health 

Publisher: Player 2 ESP32 

Subscriber: Server dashboard 

lasertag/player0x01/hit 

Publisher: Player 1 ESP32 

Subscriber: Server dashboard 

lasertag/player0x02/hit 

Publisher: Player 2 ESP32 

Subscriber: Server dashboard 

lasertag/game/status 

Publishers: Player 1 ESP32 and Player 2 ESP32 

Subscriber: Server dashboard 

lasertag/game/restart 

Publisher: Server dashboard 

Subscribers: Player 1 ESP32 and Player 2 ESP32 

The ESP32 edge devices are programmed using MicroPython and communicate with the MQTT broker through the umqtt.simple library. Messages are published to the broker using the safe_publish(topic, message) function, which provides basic error handling and reconnection support. Incoming MQTT messages are received and processed using the check_msg() method, enabling the ESP32 devices to react to game events such as restart commands or player status updates.



The following figure shows the Mosquitto MQTT broker running on the server machine. The broker displays all published MQTT messages and prints game events in real time.















Technologies and Protocols

The project employs the following technologies and protocols. The microcontroller platform is the ESP32-S3-DevKitC running MicroPython firmware, chosen for its built-in WiFi, adequate GPIO count, and PWM support. The physical communication layer uses the NEC infrared protocol at 38 kHz carrier frequency, encoding a 32-bit frame consisting of an 8-bit address, its bitwise inverse, an 8-bit command, and its bitwise inverse. This built-in redundancy provides error detection: the receiver verifies that each byte and its inverse sum to 0xFF before accepting the frame. The networking protocol is MQTT v3.1.1 running over TCP on port 1883 via the umqtt.simple MicroPython library. The broker is Eclipse Mosquitto 2.1.2 configured with listener 1883 and allow_anonymous true to permit connections without credentials. The dashboard is built on Node-RED v4.1.8 using the node-red-dashboard v3.6.6 plugin, which provides gauge, text, and button widgets rendered in a web UI. The programming languages used are MicroPython for the ESP32 firmware and JavaScript for Node-RED function nodes.

Node-RED Dashboard Implementation

The Node-RED dashboard serves as the spectator and control interface for the laser tag system. It was built using Node-RED v4.1.8 with the classic node-red-dashboard v3.6.6 plugin. The dashboard is organized under a single tab named “Laser Tag” containing a group named “Game” that holds all UI widgets.

The flow consists of five MQTT input nodes subscribing to the Mosquitto broker at YOUR_LOCAL_IP:1883. Two nodes subscribe to lasertag/player1/health and lasertag/player2/health respectively. Each feeds into a function node labeled “To Number” that converts the incoming string payload to a numeric value using msg.payload = Number(msg.payload), which is necessary because MQTT payloads are always strings but the gauge widget requires numeric input. The output of each function node feeds into a gauge widget. The gauges display health on a scale from 0 to 6, with color transitions from green (full health) through yellow (moderate) to red (critical). Two additional MQTT input nodes subscribe to the hit topics (lasertag/player1/hit and lasertag/player2/hit) and display the most recent hit event in text widgets labeled “Player 1 Last Hit” and “Player 2 Last Hit.” A fifth MQTT input node subscribes to lasertag/game/status and displays game state announcements such as “Player 1 online” or “Player 1 DEAD – Player 2 wins!” in a text widget labeled “Game Status.”

The dashboard also includes a “Restart Game” button that allows a spectator or game operator to reset the match from the dashboard. Initially, the button was connected directly to an MQTT output node publishing to lasertag/game/restart. However, this approach only triggered the ESP32 callback to reset health locally; the dashboard gauges and text fields retained their old values because the broker still held the previous retained messages. To solve this, a function node was added between the restart button and the MQTT output node. This function node generates an array of six MQTT messages that collectively reset all game state: a restart command to lasertag/game/restart, both players’ health reset to 6 with the retain flag set to true, both hit logs cleared to “-” with retain, and a new game status message “Game restarted – both players ready” with retain. The use of retained messages ensures that the dashboard always displays the most current game state, even after a page refresh.

The following graph shows the Node-RED dashboard logic flow:











Performance Evaluation

The system was evaluated across several dimensions to assess its real-time performance and reliability.

IR Communication Reliability: The NEC protocol provided reliable hit detection at distances up to approximately 2–5 meters when the transmitter and receiver were pointed directly at each other. The 38 kHz modulation effectively filtered ambient IR noise. The built-in error checking via inverted address and command bytes in the 32-bit NEC frame ensured that corrupted signals were discarded rather than registering as false hits. The IR modules used in this project are pre-built PCBs with onboard resistors and TSOP receivers, which simplified wiring and provided consistent modulation quality.

MQTT Publish Latency: The time between a hit being detected on the ESP32 and the corresponding MQTT message arriving at the broker was observed to be consistently under 50 ms on the local network. The dashboard gauge update was perceived as near-instantaneous from the spectator’s perspective. The safe_publish() wrapper function ensures that if a publish fails due to a dropped connection, the system automatically reconnects and retries, preventing lost events.

Protocol Overhead: Each MQTT PUBLISH message for a health update carries approximately 40–60 bytes including the fixed header, variable header with the topic name string, and a 1–2 byte payload (the health value as a string). This is lightweight compared to HTTP-based alternatives. The NEC IR frame is exactly 32 bits (4 bytes) of useful data, but the total physical transmission time including the 9 ms leader pulse, 4.5 ms space, 32 data bits (each with a 560 µs burst plus variable-length space), and stop bit is approximately 67.5 ms. This constrains the maximum theoretical firing rate, which is further limited by the 500 ms software cooldown.

Dashboard Responsiveness: The Node-RED dashboard displayed health gauge updates within approximately 100–200 ms of the MQTT message being published by the ESP32. The restart button’s effect was observed on both ESP32 devices within 1 second of being pressed, including the time for the function node to generate all six reset messages, publish them through the broker, and for the ESP32s to process the incoming restart command via client.check_msg() in the main loop.

Problems Faced

Several significant problems were encountered during development, each requiring targeted troubleshooting.

GPIO 35 Invalid on ESP32-S3: The initial wiring plan used GPIO 35 for the IR receiver input. When the MicroPython code attempted to initialize this pin, it raised a ValueError: invalid pin. Investigation revealed that on the ESP32-S3-DevKitC, GPIOs 35, 36, and 37 are internally connected to the PSRAM/flash interface and are not available as general-purpose I/O on the development board headers. The solution was to reassign the IR receiver to GPIO 9, a valid and accessible input pin on this board variant.

Phone Hotspot Client Isolation: When both ESP32 devices were connected to a mobile phone hotspot along with the laptop running Mosquitto, the second player’s ESP32 would freeze after attempting to connect to the MQTT broker. The root cause was client isolation, a security feature on most mobile hotspots that prevents connected devices from communicating with each other directly. This meant the ESP32 could reach the internet but not the laptop’s local IP address. The solution was to run Mosquitto on a separate machine connected to a network without client isolation, ensuring all devices could reach the broker.

Node-RED FlowFuse Dashboard Conflict: The @flowfuse/node-red-dashboard plugin (the newer, actively maintained dashboard) was initially installed alongside the classic node-red-dashboard v3.6.6. Having both plugins installed simultaneously caused a TypeError: Cannot read properties of null (reading ‘on’) at runtime, which prevented all dashboard widgets from rendering. The error originated in the FlowFuse plugin’s UIBaseNode constructor. The solution was to uninstall the @flowfuse/node-red-dashboard entirely and use only the classic node-red-dashboard, which resolved the conflict immediately.

Dashboard Group Configuration After JSON Import: After importing the Node-RED flow from a JSON configuration, the dashboard displayed “Welcome to the Node-RED Dashboard – Please add some UI nodes to your flow and redeploy” despite all nodes being visually present and connected on the canvas. The issue was that the imported gauge and text nodes had empty or invalid Group fields, marked with orange triangle warnings showing “Invalid properties: group.” The fix required manually creating a Tab (“Laser Tag”) and Group (“Game”) in the dashboard configuration, then opening each UI widget node individually and assigning it to the newly created group.

Restart Button Not Resetting Dashboard State: The initial restart implementation connected the dashboard button directly to an MQTT output node publishing “restart” to lasertag/game/restart. While this successfully triggered the ESP32 on_message callback to reset health and LEDs, the dashboard gauges and text fields did not update because the broker still held the old retained values for health and hit topics. The solution was to insert a function node that generates an array of six MQTT messages with retain flags, resetting all topics simultaneously: the restart command, both players’ health to 6, both hit logs to “-”, and the game status to “Game restarted – both players ready.”

Blocking read_nec() Function: The read_nec() function uses MicroPython’s time_pulse_us() with a 100,000 µs (100 ms) timeout to wait for the start of an NEC frame. During this blocking wait, the main loop could not check the button state, causing one player to appear unable to shoot. The fix was to add a guard condition checking ir_rx.value() == 0 before invoking read_nec(). Since the TSOP receiver output goes LOW when an IR signal is detected, this check ensures the decoding function is only called when a signal is actually present, allowing the button check to run freely in all other iterations of the loop.

Team Structure

The project was completed by a team of two students with the following division of responsibilities.

Saud Alsaleem was responsible for the Node-RED dashboard implementation, including the installation and configuration of Node-RED and the dashboard plugin, design and implementation of the flow with MQTT input nodes, function nodes for data type conversion, gauge and text widgets for real-time game state display, and the restart game button with its associated function node logic for publishing retained reset messages across all game topics. Saud also contributed to the shared ESP32 MicroPython codebase, including the game logic, LED health display system, and MQTT integration.

Khalid Alsaif was responsible for the Mosquitto MQTT broker setup and configuration, including installation, network configuration, and ensuring reliable connectivity between all system components. Khalid also contributed to the shared ESP32 code development, including the game logic, IR transmitter and receiver setup and logic, and MQTT integration.



 



Conclusions

This project successfully demonstrated the design and implementation of an IoT-based laser tag system that integrates sensing, actuation, edge computing, and cloud-based visualization. The system achieves reliable two-player gameplay using NEC-encoded infrared communication for hit detection, PWM-controlled LEDs for progressive health visualization, and MQTT for real-time telemetry to a Node-RED dashboard.

Key achievements include a complete edge-cloud IoT pipeline with clear separation of concerns, where all game-critical logic runs at the edge without network dependency. The bidirectional MQTT communication enables dashboard-initiated game control via retained messages. The custom NEC protocol implementation in MicroPython provides reliable player identification with built-in error detection. The Node-RED dashboard offers a functional real-time spectator interface with health gauges, hit logs, game status, and restart functionality.

Future improvements could include adding an OLED display per player to show ammo count and game timer locally, implementing an ammunition and reload system for additional strategic depth, supporting team-based gameplay with four or more ESP32 devices, adding a fog computing layer using a third ESP32 as a local MQTT broker for reduced latency, and implementing CoAP alongside MQTT for game control commands to explore multi-protocol IoT architectures.




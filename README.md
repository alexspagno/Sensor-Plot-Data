# Sensor-Plot-Data
Sensor Plot Data is a Python GUI application built with Tkinter, Matplotlib, and PySerial, designed to plot and record real-time serial data from microcontrollers like Arduino, ESP32. It supports 5 simultaneous data channels, real-time configuration, CSV recording/loading, and advanced multi-axis plotting.

# Features
- Live configuration Y-axis with labels, units, and  ranges
- JSON config saving/loading
- Live serial plotting 20Hz
- CSV recording and playback
- Scroll slider for navigating data during playback
- Live configuration forscaling, labels, and more

# Requirements
- Python 3.x
- pyserial
- matplotlib
- tkinter

#  How to Use

LIVE:
- Connect your device like an Arduino or ESP32
- The device must send exactly 5 comma-separated numeric values (like: 25.1, 70.0, 0.98, 123, 450) with a fixed interval of 50 milliseconds
- Launch the application
- Configure serial port
- Click “Connect” to begin live plotting
- Customize each axis and Number of points to display live
- Click “Save Config” to store your settings to config.json

RECORDING AND PLAYBACK:
- Click “Record” to begin saving incoming data
- Click “Stop” to end recording and save as .CSV
- Click “Open CSV” to load a file and review it with the slider




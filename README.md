# Home assistant Delonghi integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

![Company logo](https://brands.home-assistant.io/delonghi_primadonna/logo.png)

## Known issues

* Delonghi device reports one status at once if you remove water tank first and than remove coffeecake container you got only one warning about the water
* Delonghi device supports only one connection. You could not connect to device using the native application if you use this integration.
* Delonghi device may not handle customer disconnection. Your device may die but dlonghi may think it`s still connected.

## Component to integrate Delonghi coffee machine into the Home Assistant

This component establishes persistent Bluetooth connection to send commands to cafe machine. If any parallel connection will be set the integration will not work.
### Events

This integration triggers events in case of device state is changed.

The event looks like following:

```
{
   'data' : "b'd0 12 75 0f 01 05 00 00 00 07 00 00 00 00 00 00 00 9d 61'"
   'type' : 'status'
   'description' : 'DeviceOK'
}
```
There is only two event type available status and process. The list of available events can be found [here](./custom_components/delonghi_primadonna/device.py#L69)

## Installation

Install using HACS.

Or manually copy all files from this repository in custom_components/delonghi_primadonna to your <config directory>/custom_components/delonghi_primadonna/ directory.

## Configuration

* Find the device MAC address using BLE scanner or smartphone
* Open the integration page
* Click add integration
* Enter "Delonghi"
* Select "Delonghi Primadonna" integration
* Enter the name and the MAC address

![Charts](./images/image.png)


## Compartible devices

* Delonghi Primadonna
* Please add...
# Buses on Moscow map

The web application shows the movement of buses on a map of Moscow.

The Trio websocket library is used as the basis for the backend.

<img src="screenshots/buses.gif">

# How to install

- Download the repository and open the folder with project

- Install requirements libraries and packages:
```bash
pip3 install -r requirements.txt
```

# How to run
- Open on browser web page `index.html`
- Run script `server.py` in shell
- Run script `fake_bus.py` in shell to generate fake buses on the map


## Settings

At the bottom right of the page, you can enable debug logging mode and specify a non-standard web socket address.

<img src="screenshots/settings.png">

The settings are saved in the Local Storage of the browser and do not disappear after refreshing the page. To reset the settings, delete keys from Local Storage using Chrome Dev Tools -> Application tab -> Local Storage.

If something doesn't work as expected, then start by enabling debug logging mode.

## Data format

The frontend expects to receive a JSON message from the server with a list of buses:

```js
{
  "msgType": "Buses",
  "buses": [
    {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"},
    {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670к"},
  ]
}
```


Those buses that were not included in the `buses` list of the last message from the server will be removed from the map.

The frontend tracks the user's movement on the map and sends new window coordinates to the server:

```js
{
  "msgType": "newBounds",
  "data": {
    "east_lng": 37.65563964843751,
    "north_lat": 55.77367652953477,
    "south_lat": 55.72628839374007,
    "west_lng": 37.54440307617188,
  },
}
```



## Used js libraries

- [Leaflet](https://leafletjs.com/) — map rendering
- [loglevel](https://www.npmjs.com/package/loglevel) - for logging

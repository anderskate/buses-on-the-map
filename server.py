import json

import trio
from loguru import logger
from trio_websocket import serve_websocket, open_websocket_url, ConnectionClosed
from sys import stderr

buses = {}
bounds = {}


def is_inside(bounds, lat, lng):
    """"""
    if not bounds:
        return True

    window_coordinates = bounds['data']
    south_lat = window_coordinates['south_lat']
    north_lat = window_coordinates['north_lat']
    west_lng = window_coordinates['west_lng']
    east_lng = window_coordinates['east_lng']

    if south_lat <= lat <= north_lat and west_lng <= lng <= east_lng:
        return True
    return False


async def get_buses_info(request):
    global buses
    ws = await request.accept()
    while True:
        try:
            bus_info = await ws.get_message()
            formatted_bus_info = json.loads(bus_info)
            buses[formatted_bus_info['busId']] = formatted_bus_info
            # await trio.sleep(0.1)
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    global buses

    ws = await request.accept()
    while True:
        try:
            message = {
                "msgType": "Buses",
                "buses": [
                    bus for bus in buses.values()
                    if is_inside(bounds, bus['lat'], bus['lng'])
                ]
            }

            buses_count = len(message['buses'])
            logger.info(f'{buses_count} buses inside bounds')

            await ws.send_message(json.dumps(message))
            await listen_browser(ws)
            await trio.sleep(0.1)
        except ConnectionClosed:
            break


async def listen_browser(ws, wait_msg_timeout=0.1):
    """"""
    global bounds
    try:
        with trio.fail_after(wait_msg_timeout):
            browser_coordinates = await ws.get_message()
            bounds = json.loads(browser_coordinates)
        logger.info(json.loads(browser_coordinates))
    except ConnectionClosed:
        pass
    except trio.TooSlowError:
        pass


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket, get_buses_info,
            '127.0.0.1', 8080, None,
        )
        nursery.start_soon(
            serve_websocket, talk_to_browser,
            '127.0.0.1', 8000, None,
        )

trio.run(main)

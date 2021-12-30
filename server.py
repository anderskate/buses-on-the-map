import json
from dataclasses import dataclass, asdict
from typing import Optional

import trio
from loguru import logger
from trio_websocket import serve_websocket, open_websocket_url, ConnectionClosed
from sys import stderr


@dataclass
class Bus:
    """Representation info about specific bus at time."""
    busId: str
    lat: float
    lng: float
    route: str


@dataclass
class WindowBounds:
    """Representation coordinates browser window at time."""
    south_lat: float
    north_lat: float
    west_lng: float
    east_lng: float

    def is_inside(self, lat, lng):
        """"""
        if (
            self.south_lat <= lat <= self.north_lat
            and self.west_lng <= lng <= self.east_lng
        ):
            return True
        return False


buses: {str: Bus} = {}
bounds: WindowBounds = Optional[None]


async def get_buses_info(request):
    global buses
    ws = await request.accept()
    while True:
        try:
            bus_info = await ws.get_message()
            formatted_bus_info = json.loads(bus_info)
            bus = Bus(**formatted_bus_info)
            buses[bus.busId] = bus

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
                    asdict(bus) for bus in buses.values()
                    if bounds.is_inside(bus.lat, bus.lng)
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
            data_from_browser = await ws.get_message()
            formatted_browser_data = json.loads(data_from_browser).get('data')
            bounds = WindowBounds(**formatted_browser_data)

        logger.info(formatted_browser_data)
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

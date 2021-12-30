import json
from dataclasses import dataclass, asdict
from contextlib import suppress
from functools import partial

import trio
import asyncclick as click
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
    south_lat: float = None
    north_lat: float = None
    west_lng: float = None
    east_lng: float = None

    def is_inside(self, lat, lng):
        """"""
        if (
            self.south_lat <= lat <= self.north_lat
            and self.west_lng <= lng <= self.east_lng
        ):
            return True
        return False

    def update(self, south_lat, north_lat, west_lng, east_lng):
        """"""
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng


class ServerResponseException(Exception):
    pass


@dataclass
class BrowserMsg:
    """"""
    msgType: str
    data: dict

    @classmethod
    def validate(cls, msg):
        try:
            converted_msg = json.loads(msg)
        except json.decoder.JSONDecodeError:
            raise ServerResponseException('Requires valid JSON')

        msg_type = converted_msg.get('msgType')
        if not msg_type:
            raise ServerResponseException('Requires msgType specified')

        return converted_msg

    @classmethod
    def get_browser_msg_from_json(cls, msg):
        validated_msg = cls.validate(msg)
        return cls(**validated_msg)


buses: {str: Bus} = {}


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


async def talk_to_browser(request, bounds):
    global buses

    ws = await request.accept()
    while True:
        try:

            # When listening to data from the browser,
            # the 'bounds' object can change if the coordinates
            # of the open window in the browser have changed.
            await listen_browser(ws, bounds)

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
            await trio.sleep(0.1)
        except ConnectionClosed:
            break


async def listen_browser(ws, bounds, wait_msg_timeout=0.1):
    """"""
    try:
        with trio.fail_after(wait_msg_timeout):
            msg_from_browser = await ws.get_message()

        try:
            browser_msg = BrowserMsg.get_browser_msg_from_json(
                msg_from_browser
            )
        except ServerResponseException as error:
            error_response = {
                "msgType": "Errors",
                "errors": [str(error)]
            }
            await ws.send_message(json.dumps(error_response))
            return

        if browser_msg.data:
            bounds.update(**browser_msg.data)
        logger.info(browser_msg)
    except ConnectionClosed:
        pass
    except trio.TooSlowError:
        pass


@click.command()
@click.option(
    "--bus_port", default=8080,
    help="Port for bus imitator.",
)
@click.option(
    "--browser_port", default=8000,
    help="Port for browser."
)
@click.option(
    "--host", default='127.0.0.1',
    help="Server host."
)
@click.option(
    "--v", default='',
    help="Logging settings."
)
async def main(**kwargs):
    bus_port = kwargs.get('bus_port')
    browser_port = kwargs.get('browser_port')
    server_host = kwargs.get('host')

    bounds = WindowBounds()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket, get_buses_info,
            server_host, bus_port, None,
        )
        nursery.start_soon(
            serve_websocket, partial(talk_to_browser, bounds=bounds),
            server_host, browser_port, None,
        )


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main(_anyio_backend="trio")

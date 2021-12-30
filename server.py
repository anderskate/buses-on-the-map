import json
from dataclasses import asdict
from contextlib import suppress
from functools import partial

import trio
import asyncclick as click
from loguru import logger
from trio_websocket import (
    serve_websocket, ConnectionClosed,
    WebSocketConnection, WebSocketRequest,
)

from entities import Bus, WindowBounds, BrowserMsg
from exceptions import ServerResponseException


async def get_buses_info(request: WebSocketRequest, buses: {str: Bus}):
    """Get buses information with current coordinates."""
    ws = await request.accept()
    while True:
        try:
            bus_info = await ws.get_message()
            try:
                bus = Bus.get_bus_from_json(bus_info)
            except ServerResponseException as error:
                error_response = json.dumps(
                    {"msgType": "Errors", "errors": [str(error)]}
                )
                await ws.send_message(error_response)
                continue

            # The buses variable is constantly changing,
            # as the server constantly receives new bus coordinates.
            buses[bus.busId] = bus

        except ConnectionClosed:
            break


async def talk_to_browser(
    request: WebSocketRequest, bounds: WindowBounds, buses: {str: Bus}
):
    """Tell the browser the coordinates of the current buses."""
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
        except ConnectionClosed:
            break


async def listen_browser(
    ws: WebSocketConnection, bounds: WindowBounds, wait_msg_timeout=0.1
):
    """Listen messages getting from browser.

    If the message is not received within 'wait_msg_timeout',
    then the wait is interrupted.
    """
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
async def main(**kwargs):
    """Run server."""
    bus_port = kwargs.get('bus_port')
    browser_port = kwargs.get('browser_port')
    server_host = kwargs.get('host')

    bounds = WindowBounds()
    buses = {}
    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket,
            partial(get_buses_info, buses=buses),
            server_host, bus_port, None,
        )
        nursery.start_soon(
            serve_websocket,
            partial(talk_to_browser, bounds=bounds, buses=buses),
            server_host, browser_port, None,
        )


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main(_anyio_backend="trio")

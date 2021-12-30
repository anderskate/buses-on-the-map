import json
import random
import time
import os
from itertools import cycle, islice
from contextlib import suppress
from functools import wraps

import trio
import asyncclick as click
from loguru import logger
from trio import MemoryReceiveChannel, MemorySendChannel
from trio_websocket import (
    open_websocket_url, ConnectionClosed, ConnectionRejected,
)


def relaunch_on_disconnect(async_function, timeout=3):
    """Decorator for network reconnection retries with timeout."""
    @wraps(async_function)
    async def wrapper(*args, **kwargs):
        while True:
            try:
                await async_function(*args, **kwargs)
            except (ConnectionRejected, ConnectionClosed):
                logger.warning(f'Try to connect again after {timeout} sec.')
                time.sleep(timeout)
    return wrapper


def load_routes(directory_path: str) -> dict:
    """Get info with coordinates for the specific route."""
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


def generate_bus_id(route_id: str, bus_index: int) -> str:
    """Generate id for specific bus with specific route."""
    return f"{route_id}-{bus_index}"


def get_current_coordinates(route: dict) -> list:
    """Get the coordinates of a bus of a specific route.

    :return For example: [55.634150565692, 37.619708527282]
    """
    coordinates = route.get('coordinates')
    current_coordinates = islice(
        coordinates, random.randint(0, len(coordinates)), None
    )
    while True:
        try:
            yield next(current_coordinates)
        except StopIteration:
            current_coordinates = cycle(coordinates)
            yield next(current_coordinates)


async def run_bus(
    bus_id: str, index: int, route: dict,
    send_channel: MemorySendChannel, refresh_timeout: float
):
    """Start a bus on a specific route, and from a specific starting point."""
    for coordinates in get_current_coordinates(route):
        message = {
            "busId": generate_bus_id(bus_id, index),
            "lat": coordinates[0],
            "lng": coordinates[1],
            "route": bus_id
        }
        await send_channel.send(message)
        await trio.sleep(refresh_timeout)


@relaunch_on_disconnect
async def send_updates(server_url: str, receive_channel: MemoryReceiveChannel):
    """Send updated coordinates of buses to the server."""
    async with open_websocket_url(server_url) as ws:
        async for message in receive_channel:
            await ws.send_message(json.dumps(message))


@click.command()
@click.option(
    "--routes_number", default=100,
    help="Number of busses routes.",
)
@click.option(
    "--buses_per_route", default=10,
    help="The number of buses on each route."
)
@click.option(
    "--server", default='ws://127.0.0.1:8080',
    help="Server address."
)
@click.option(
    "--websockets_number", default=5,
    help="The number of websockets."
)
@click.option(
    "--emulator_id", default='default_emulator',
    help="Prefix to busId in case of running "
         "multiple instances of the simulator."
)
@click.option(
    "--refresh_timeout", default=0.3,
    help="Delay in updating server coordinates."
)
@click.option(
    "--routes_path", default='routes',
    help="Directory path with routes data."
)
async def main(**kwargs):
    """Generate fake buses with coordinates and send it to server."""
    routes_number = kwargs.get('routes_number')
    buses_per_route = kwargs.get('buses_per_route')
    server_url = kwargs.get('server')
    websockets_number = kwargs.get('websockets_number')
    refresh_timeout = kwargs.get('refresh_timeout')
    routes_path = kwargs.get('routes_path')

    async with trio.open_nursery() as nursery:
        channels = [
            trio.open_memory_channel(0) for _ in range(websockets_number)
        ]
        for _, receive_channel in channels:
            nursery.start_soon(
                send_updates, server_url,
                receive_channel,
            )
        for route in islice(load_routes(routes_path), routes_number):

            for index in range(buses_per_route):
                send_channel, _ = random.choice(channels)
                bus_id = route.get('name')

                nursery.start_soon(
                    run_bus, bus_id, index,
                    route, send_channel, refresh_timeout,
                )

if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main(_anyio_backend="trio")

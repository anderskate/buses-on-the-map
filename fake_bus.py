import json
import random
import os
from itertools import cycle, islice

import trio
from trio_websocket import open_websocket_url


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


def generate_bus_id(route_id, bus_index):
    return f"{route_id}-{bus_index}"


def get_current_coordinates(route):
    """"""
    coordinates = route.get('coordinates')
    current_coordinates = islice(coordinates, random.randint(0, len(route) - 1), None)
    while True:
        try:
            yield next(current_coordinates)
        except StopIteration:
            current_coordinates = cycle(coordinates)
            yield next(current_coordinates)


async def run_bus(bus_id, index, route, send_channel):
    """"""
    for coordinates in get_current_coordinates(route):

        message = {
            "busId": generate_bus_id(bus_id, index),
            "lat": coordinates[0],
            "lng": coordinates[1],
            "route": bus_id
        }
        await send_channel.send(message)
        await trio.sleep(0.1)


async def send_updates(server_address, receive_channel):
    """"""
    async with open_websocket_url(server_address) as ws:
        async for message in receive_channel:
            await ws.send_message(json.dumps(message))


async def main(max_sockets=5, max_routes=350):
    async with trio.open_nursery() as nursery:
        bus_copies = 5

        channels = [trio.open_memory_channel(0) for _ in range(max_sockets)]
        for _, receive_channel in channels:
            nursery.start_soon(
                send_updates, 'ws://127.0.0.1:8080',
                receive_channel,
            )

        for route in islice(load_routes(), max_routes):

            for index in range(bus_copies):
                send_channel, _ = random.choice(channels)
                bus_id = route.get('name')

                nursery.start_soon(
                    run_bus, bus_id, index,
                    route, send_channel,
                )

trio.run(main)

import json
import random
import os
from itertools import cycle, islice

import trio
from sys import stderr
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
    current_route = islice(route, random.randint(0, len(route) - 1), None)
    while True:
        try:
            yield next(current_route)
        except StopIteration:
            current_route = cycle(route)
            yield next(current_route)


async def run_bus(url, bus_id, index, route):
    try:
        async with open_websocket_url(url) as ws:
            for coordinates in get_current_coordinates(route):
                message = {
                    "busId": generate_bus_id(bus_id, index),
                    "lat": coordinates[0],
                    "lng": coordinates[1],
                    "route": bus_id
                }

                await ws.send_message(json.dumps(message))
                await trio.sleep(0.1)

    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


async def main():
    async with trio.open_nursery() as nursery:
        count = 0
        bus_copies = 5

        for route in load_routes():
            route_coordinates = route.get('coordinates')

            bus_routes = [route_coordinates for _ in range(bus_copies)]
            for index, bus_route in enumerate(bus_routes):
                bus_id = route.get('name')

                nursery.start_soon(
                    run_bus, 'ws://127.0.0.1:8080',
                    bus_id, index, bus_route
                )

            # TODO Delete after tests. On mac OS limit - 255 incoming connections
            count += 1
            if count > 30:
                break


trio.run(main)

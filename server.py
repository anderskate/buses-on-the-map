import json

import trio
from trio_websocket import serve_websocket, open_websocket_url, ConnectionClosed
from sys import stderr

buses = {}


async def recipient_server(request):
    global buses
    ws = await request.accept()
    while True:
        try:
            bus_info = await ws.get_message()
            formatted_bus_info = json.loads(bus_info)
            buses[formatted_bus_info['busId']] = formatted_bus_info
            # print(buses)
            await trio.sleep(0.1)
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    global buses

    ws = await request.accept()
    while True:
        try:
            message = {
                "msgType": "Buses",
                "buses": list(buses.values())
            }
            print(message)
            await ws.send_message(json.dumps(message))
            await trio.sleep(0.1)
        except ConnectionClosed:
            break


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket, recipient_server,
            '127.0.0.1', 8080, None,
        )
        nursery.start_soon(
            serve_websocket, talk_to_browser,
            '127.0.0.1', 8000, None,
        )

trio.run(main)

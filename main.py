import json
import trio
from trio_websocket import serve_websocket, ConnectionClosed


async def send_message(ws):
    """"""
    # message = {
    #   "msgType": "Buses",
    #   "buses": [
    #     {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"},
    #     {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670к"},
    #   ]
    # }
    async with await trio.open_file("156.json") as f:
        file_data = await f.read()
        formatted_data = json.loads(file_data)
        coordinates = formatted_data['coordinates']
    for cord in coordinates:
        message = {
          "msgType": "Buses",
          "buses": [
            {"busId": "c790сс", "lat": cord[0], "lng": cord[1], "route": "156"},
          ]
        }
        await ws.send_message(json.dumps(message))
        await trio.sleep(3)


async def echo_server(request):
    ws = await request.accept()
    while True:
        try:
            # message = await ws.get_message()
            await send_message(ws)
        except ConnectionClosed:
            break


async def main():
    await serve_websocket(echo_server, '127.0.0.1', 8000, ssl_context=None)

trio.run(main)

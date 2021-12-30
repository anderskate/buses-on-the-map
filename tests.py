import json

import pytest
from trio_websocket import open_websocket_url


URL_FOR_BROWSER = 'ws://127.0.0.1:8000'
URL_FOR_BUSES = 'ws://127.0.0.1:8080'


@pytest.mark.trio
async def test_incorrect_json_msg_from_browser():
    """Test that if there is an incorrect json format in message
    for the server from the browser, an error response is displayed.
    """
    incorrect_json_msg = 'hello world!'
    async with open_websocket_url(URL_FOR_BROWSER) as ws:
        await ws.send_message(incorrect_json_msg)
        response_message = await ws.get_message()

    correct_response_msg = {
        "msgType": "Errors",
        "errors": ["Requires valid JSON"]
    }
    assert response_message == json.dumps(correct_response_msg)


@pytest.mark.trio
async def test_json_msg_without_msg_type_from_browser():
    """Test that if there is not 'msgType' field in message
    for the server from the browser, an error response is displayed."""
    msg_without_type = json.dumps(
        {"data": {}}
    )
    async with open_websocket_url(URL_FOR_BROWSER) as ws:
        await ws.send_message(msg_without_type)
        response_message = await ws.get_message()

    correct_response_msg = {
        "msgType": "Errors",
        "errors": ["Requires msgType specified"]
    }
    assert response_message == json.dumps(correct_response_msg)


@pytest.mark.trio
async def test_incorrect_json_msg_from_bus():
    """Test that if there is an incorrect json format in message
    for the server from bus, an error response is displayed.
    """
    incorrect_json_msg = 'hello world!'
    async with open_websocket_url(URL_FOR_BUSES) as ws:
        await ws.send_message(incorrect_json_msg)
        response_message = await ws.get_message()

    correct_response_msg = {
        "msgType": "Errors",
        "errors": ["Requires valid JSON"]
    }
    assert response_message == json.dumps(correct_response_msg)


@pytest.mark.trio
async def test_json_msg_without_busid_from_bus():
    """Test that if there is not 'busId' field in message
    for the server from bus, an error response is displayed."""
    msg_without_id = json.dumps(
        {"lat": 55.610089744936, "lng": 37.609123834818, "route": "683"}
    )
    async with open_websocket_url(URL_FOR_BUSES) as ws:
        await ws.send_message(msg_without_id)
        response_message = await ws.get_message()

    correct_response_msg = {
        "msgType": "Errors",
        "errors": ["Requires busId specified"]
    }
    assert response_message == json.dumps(correct_response_msg)

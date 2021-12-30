import json
from dataclasses import dataclass

from exceptions import ServerResponseException


@dataclass
class Bus:
    """Representation info about specific bus at time."""
    busId: str
    lat: float
    lng: float
    route: str

    @classmethod
    def validate(cls, json_data: str) -> dict:
        """Validate json data.

        If data is valid, return it with python dict format.
        """
        try:
            converted_msg = json.loads(json_data)
        except json.decoder.JSONDecodeError:
            raise ServerResponseException('Requires valid JSON')

        msg_type = converted_msg.get('busId')
        if not msg_type:
            raise ServerResponseException('Requires busId specified')

        return converted_msg

    @classmethod
    def get_bus_from_json(cls, json_msg: str) -> 'Bus':
        """Get json bus data and represent it to 'Bus' object."""
        validated_msg = cls.validate(json_msg)
        return cls(**validated_msg)


@dataclass
class WindowBounds:
    """Representation coordinates browser window at time."""
    south_lat: float = None
    north_lat: float = None
    west_lng: float = None
    east_lng: float = None

    def is_inside(self, lat: float, lng: float) -> bool:
        """Check that specific coordinates in bounds."""
        if (
            self.south_lat <= lat <= self.north_lat
            and self.west_lng <= lng <= self.east_lng
        ):
            return True
        return False

    def update(
        self, south_lat: float, north_lat: float,
        west_lng: float, east_lng: float
    ):
        """Update coordinates values."""
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng


@dataclass
class BrowserMsg:
    """Representation message from browser."""
    msgType: str
    data: dict

    @classmethod
    def validate(cls, msg: str) -> dict:
        """Validate json msg.

        If msg is valid, return it with python dict format.
        """
        try:
            converted_msg = json.loads(msg)
        except json.decoder.JSONDecodeError:
            raise ServerResponseException('Requires valid JSON')

        msg_type = converted_msg.get('msgType')
        if not msg_type:
            raise ServerResponseException('Requires msgType specified')

        return converted_msg

    @classmethod
    def get_browser_msg_from_json(cls, msg) -> 'BrowserMsg':
        """Get json msg and represent it to 'BrowserMsg' object."""
        validated_msg = cls.validate(msg)
        return cls(**validated_msg)

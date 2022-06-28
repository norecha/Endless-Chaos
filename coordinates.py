from dataclasses import dataclass


@dataclass
class Coordinate:
    x: int
    y: int


SWITCH_CHARACTERS = Coordinate(523, 680)
CHARACTERS = [
    Coordinate(750, 440),
    Coordinate(950, 440),
    Coordinate(1150, 440),
    Coordinate(750, 530),
    Coordinate(950, 530),
    Coordinate(1150, 530),
]
CONNECT = Coordinate(1000, 680)
CONNECT_CONFIRM = Coordinate(920, 590)

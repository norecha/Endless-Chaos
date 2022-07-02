from dataclasses import dataclass
from typing import Any, Optional

import pyautogui
from PIL import Image

import utils


@dataclass
class Ability:
    def __init__(
            self,
            ability_type: str,
            key: str,
            image: Any,
            cast: bool,
            cast_time: int,
            hold: bool,
            hold_time: int,
            directional: bool = False,
            esoteric: bool = False,
            cooldown: Optional[int] = None,
            last_used: int = 0,
    ):
        self.ability_type = ability_type
        self.key = key
        self.image = image
        self.cast = cast
        self.cast_time = cast_time
        self.hold = hold
        self.hold_time = hold_time
        self.directional = directional
        self.esoteric = esoteric
        self.cooldown = cooldown
        self.last_used = last_used

    @staticmethod
    def load_from_config(ability_config, client_util: utils.ClientUtil):
        if 'image_path' in ability_config:
            image = Image.open(ability_config['image_path'])
        else:
            left = ability_config['position']['left']
            top = ability_config['position']['top']
            width = ability_config['position']['width']
            height = ability_config['position']['height']
            image = client_util.screenshot(region=(left, top, width, height))
        return Ability(
            ability_type=ability_config['abilityType'],
            key=ability_config['key'],
            image=image,
            cast=ability_config['cast'],
            cast_time=ability_config['castTime'],
            hold=ability_config['hold'],
            hold_time=ability_config['holdTime'],
            directional=ability_config['directional'],
            esoteric=ability_config.get("esoteric", False),
            cooldown=ability_config.get("cooldown", False),
            last_used=0,
        )

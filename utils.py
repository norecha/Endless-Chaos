import random
import time
from typing import Tuple, Optional

import pyautogui
import pygetwindow
import pyscreeze
import win32gui
from absl import logging

from config import config

_GAME_RESOLUTION = (1920, 1080)


class ClientUtil:
    def __init__(self):
        x, y = _get_window_relative()
        self.client_x, self.client_y = x, y

    def _client_to_screen(self, x: int, y: int) -> Tuple[int, int]:
        return x + self.client_x, y + self.client_y

    def _screen_to_client_point(self, point: pyscreeze.Point) -> Optional[Tuple[int, int]]:
        if point is None:
            return None
        else:
            return point.x - self.client_x, point.y - self.client_y

    def _screen_to_client_box(self, box: pyscreeze.Box) -> Optional[Tuple[int, int, int, int]]:
        if box is None:
            return None
        else:
            return box.left - self.client_x, box.top - self.client_y, box.width, box.height

    def _convert_to_client_region(self, kwargs):
        if 'region' in kwargs and kwargs['region'] is not None:
            kwargs['region'] = (
                self.client_x + kwargs['region'][0], self.client_y + kwargs['region'][1],
                kwargs['region'][2], kwargs['region'][3],
            )
        else:
            kwargs['region'] = (
                self.client_x, self.client_y,
                _GAME_RESOLUTION[0], _GAME_RESOLUTION[1]
            )

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button='primary'):
        if x is not None and y is not None:
            x, y = self._client_to_screen(x, y)
        pyautogui.click(x=x, y=y, button=button)

    def mouse_down(self, x: Optional[int] = None, y: Optional[int] = None, button='primary'):
        if x is not None and y is not None:
            x, y = self._client_to_screen(x, y)
        pyautogui.mouseDown(x=x, y=y, button=button)

    def move_and_click(self, x: int, y: int, *, wait: int = 0):
        _move_and_click(*self._client_to_screen(x, y), wait=wait)

    def move_to(self, x: int, y: int):
        pyautogui.moveTo(*self._client_to_screen(x, y))

    def locate_on_screen(self, image, **kwargs) -> Optional[pyscreeze.Box]:
        self._convert_to_client_region(kwargs)
        return self._screen_to_client_box(pyautogui.locateOnScreen(image, **kwargs))

    def locate_center_on_screen(self, image, **kwargs) -> Optional[pyscreeze.Point]:
        self._convert_to_client_region(kwargs)
        return self._screen_to_client_point(pyautogui.locateCenterOnScreen(image, **kwargs))

    def screenshot(self, **kwargs):
        self._convert_to_client_region(kwargs)
        return pyautogui.screenshot(**kwargs)

    def pixel(self, x, y):
        x, y = self._client_to_screen(x, y)
        return pyautogui.pixel(x, y)

    def wait_loading_finish(self):
        while True:
            im = self.screenshot(region=(1652, 168, 240, 210))
            r, g, b = im.getpixel((1772 - 1652, 272 - 168))
            if r != 0 and g != 0 and b != 0:
                sleep(500, 800)
                break
            sleep(500, 800)
        sleep(1000)

    def wait_and_click_ok(self):
        return self._wait_and_click('./screenshots/ok.png', 0.75)

    def wait_and_click_leave(self):
        return self._wait_and_click(
            './screenshots/leave.png', 0.7, True, config["regions"]["leaveMenu"])

    def _wait_and_click(self, button_path, confidence, grayscale=False, region=None):
        while True:
            button = self.locate_center_on_screen(
                button_path,
                grayscale=grayscale,
                confidence=confidence,
                region=region,
            )
            if button is not None:
                x, y = button
                self.move_to(x=x, y=y)
                sleep(500, 600)
                self.click()
                sleep(150, 200)
                break
            sleep(500, 600)


def _get_window_relative() -> Tuple[int, int]:
    logging.info('Calculating window coordinates')
    windows = pygetwindow.getWindowsWithTitle('LOST ARK')
    if not windows:
        logging.error('LOST ARK window is not found')
        exit(1)
    window = windows[0]
    h_wnd = window._hWnd
    x, y = win32gui.ClientToScreen(h_wnd, (0, 0))
    window.activate()
    return x, y


def press(button, wait=0):
    pyautogui.press(button)
    if wait > 0:
        sleep(wait)


def _move_and_click(x: int, y: int, *, wait: int = 0):
    pyautogui.moveTo(x=x, y=y)
    sleep(200)
    pyautogui.click()
    if wait > 0:
        sleep(wait)


def sleep(minimum, maximum=None):
    if maximum is None:
        maximum = int(minimum * 1.15)
    time.sleep(random.randint(minimum, maximum) / 1000.0)


def key_down(*args, **kwargs):
    pyautogui.keyDown(*args, **kwargs)


def key_up(*args, **kwargs):
    pyautogui.keyUp(*args, **kwargs)

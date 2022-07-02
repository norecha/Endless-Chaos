import random
import time

import pyautogui
import pygetwindow
import win32con
import win32gui

from config import config


def move_window():
    print('Moving window')
    windows = pygetwindow.getWindowsWithTitle('LOST ARK')
    if not windows:
        print('LOST ARK window is not found')
        exit(1)
    window = windows[0]
    h_wnd = window._hWnd
    existing_style = win32gui.GetWindowLong(h_wnd, win32con.GWL_STYLE)
    # remove borders
    new_style = existing_style & ~win32con.WS_CAPTION
    win32gui.SetWindowLong(h_wnd, win32con.GWL_STYLE, new_style)
    win32gui.UpdateWindow(h_wnd)
    win32gui.MoveWindow(h_wnd, 0, 0, 1920, 1080, 0)
    window.activate()


def press(button, wait=0):
    pyautogui.press(button)
    if wait > 0:
        sleep(wait)


def click(coordinate, wait=0):
    pyautogui.moveTo(x=coordinate.x, y=coordinate.y)
    sleep(200)
    pyautogui.click()
    if wait > 0:
        sleep(wait)


def sleep(minimum, maximum=None):
    if maximum is None:
        maximum = int(minimum * 1.15)
    time.sleep(random.randint(minimum, maximum) / 1000.0)


def wait_loading_finish():
    while True:
        im = pyautogui.screenshot(region=(1652, 168, 240, 210))
        r, g, b = im.getpixel((1772 - 1652, 272 - 168))
        if r != 0 and g != 0 and b != 0:
            sleep(500, 800)
            break
        sleep(500, 800)
    sleep(1000)


def wait_and_click_ok():
    return _wait_and_click('./screenshots/ok.png', 0.75)


def wait_and_click_leave():
    return _wait_and_click(
        './screenshots/leave.png', 0.7, True, config["regions"]["leaveMenu"])


def _wait_and_click(button_path, confidence, grayscale=False, region=None):
    while True:
        button = pyautogui.locateCenterOnScreen(
            button_path,
            grayscale=grayscale,
            confidence=confidence,
            region=region,
        )
        if button is not None:
            x, y = button
            pyautogui.moveTo(x=x, y=y)
            sleep(500, 600)
            pyautogui.click()
            sleep(150, 200)
            break
        sleep(500, 600)

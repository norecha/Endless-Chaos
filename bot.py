import json
from functools import cache
from typing import Dict, List, Optional

from absl import app
from absl import flags

import coordinates
import utils
from ability import Ability

from config import config
import pyautogui
import time
import random
import math

FLAGS = flags.FLAGS
flags.DEFINE_enum('mode', 'infinite_chaos', ['daily', 'infinite_chaos'], 'Mode')
flags.DEFINE_integer('chars', 1, '# of chars for daily mode', lower_bound=1)
flags.DEFINE_integer('starting_char', 0, 'starting char', lower_bound=0)

newStates = {
    "status": "inCity",
    "abilityScreenshots": [],
    "clearCount": 0,
    "fullClearCount": 0,
    "moveToX": config["screenCenterX"],
    "moveToY": config["screenCenterY"],
    "botStartTime": None,
    "instanceStartTime": None,
    "deathCount": 0,
    "healthPotCount": 0,
    "timeoutCount": 0,
    "goldPortalCount": 0,
    "purplePortalCount": 0,
    "badRunCount": 0,
    "minTime": config["timeLimit"],
    "maxTime": -1,
}
states = newStates.copy()


def load_config(char: int) -> Dict:
    with open(f'character_configs/{char}.json') as f:
        return json.load(f)


def load_abilities(char_config: Dict) -> List[Ability] :
    abilities = []
    for ability_config in char_config['abilities']:
        if not ability_config['abilityType'] == 'normal':
            continue
        ability = Ability.load_from_config(ability_config)
        abilities.append(ability)
    return abilities


def switch_to_char(char):
    print(f'Switching to {char=}')
    utils.press('ESC', 1500)
    utils.click(coordinates.SWITCH_CHARACTERS, 1000)
    utils.click(coordinates.CHARACTERS[char], 1000)
    utils.click(coordinates.CONNECT, 1000)
    utils.click(coordinates.CONNECT_CONFIRM)
    utils.sleep(30000)
    utils.wait_loading_finish()


def daily(chars, starting_char=0):
    global states
    for char in range(starting_char, starting_char + chars):
        print(f'Starting daily for {char=}')
        states = newStates.copy()
        # switch to char
        if char != starting_char:
            switch_to_char(char)
        infinite_chaos(char, limit=1)
        utils.wait_loading_finish()
    print(f'Done with dailies')


def infinite_chaos(char, limit=None):
    print(f"Endless Chaos started {char=} {limit=}...")
    char_config = load_config(char)
    # save bot start time
    states["botStartTime"] = int(time.time_ns() / 1000000)
    abilities = None
    while True:
        if states["clearCount"] >= limit:
            print('Hit chaos limit')
            return
        if states["status"] == "inCity":
            # states = newStates
            states["abilityScreenshots"] = []
            # save instance start time
            states["instanceStartTime"] = int(time.time_ns() / 1000000)

            enterChaos()
            if checkTimeout():
                quitChaos()
                continue

        elif states["status"] == "floor1":
            print("floor1")
            pyautogui.moveTo(x=config["screenCenterX"], y=config["screenCenterY"])
            sleep(200, 300)
            # wait for loading
            waitForLoading()
            if checkTimeout():
                quitChaos()
                continue
            sleep(1000, 1200)
            print("floor1 loaded")

            # saving clean abilities icons
            if abilities is None:
                abilities = load_abilities(char_config)

            # check repair
            if config["autoRepair"]:
                doRepair()

            if char_config['class'] == 'Berserker':
                utils.press(config['specialty1'])

            # do floor one
            doFloor1(abilities)
        elif states["status"] == "floor2":
            print("floor2")
            pyautogui.moveTo(x=config["screenCenterX"], y=config["screenCenterY"])
            sleep(200, 300)
            # wait for loading
            waitForLoading()
            if checkTimeout():
                quitChaos()
                continue
            print("floor2 loaded")
            # do floor two
            doFloor2(abilities)
        elif states["status"] == "floor3":
            print("floor3")
            pyautogui.moveTo(x=config["screenCenterX"], y=config["screenCenterY"])
            sleep(200, 300)
            # wait for loading
            waitForLoading()
            if checkTimeout():
                quitChaos()
                continue
            print("floor3 loaded")
            # do floor 3
            # trigger start floor 3
            pyautogui.moveTo(x=1045, y=450)
            sleep(100, 120)
            pyautogui.click(button=config["move"])
            sleep(500, 600)
            doFloor3Portal(abilities)
            if checkTimeout() or config["floor3"] == False:
                quitChaos()
                continue
            doFloor3(abilities, limit)


def enterChaos():
    rightClick = "right"
    if config["move"] == "right":
        rightClick = "left"

    pyautogui.moveTo(x=config["screenCenterX"], y=config["screenCenterY"])
    sleep(200, 300)
    pyautogui.click(button=rightClick)
    sleep(200, 300)

    if config["shortcutEnterChaos"] == True:
        utils.wait_loading_finish()
        sleep(600, 800)
        while True:
            pyautogui.keyDown("alt")
            sleep(600, 800)
            pyautogui.press("q")
            sleep(300, 400)
            pyautogui.keyUp("alt")
            sleep(300, 400)
            pyautogui.moveTo(886, 346)
            sleep(600, 800)
            pyautogui.click(button="left")
            sleep(600, 800)

            enterButton = pyautogui.locateCenterOnScreen(
                "./screenshots/enterButton.png", confidence=0.75
            )
            if enterButton != None:
                x, y = enterButton
                pyautogui.moveTo(x=x, y=y)
                sleep(600, 800)
                pyautogui.click(x=x, y=y, button="left")
                break
            else:
                if checkTimeout():
                    # quitChaos()
                    return
                pyautogui.moveTo(886, 346)
                sleep(600, 800)
                pyautogui.click(button="left")
                sleep(600, 800)
    else:
        while True:
            enterHand = pyautogui.locateOnScreen("./screenshots/enterChaos.png")
            if enterHand != None:
                print("entering chaos...")
                pyautogui.press(config["interact"])
                break
            sleep(500, 800)
    sleep(600, 800)
    while True:
        acceptButton = pyautogui.locateCenterOnScreen(
            "./screenshots/acceptButton.png", confidence=0.75
        )
        if acceptButton != None:
            x, y = acceptButton
            pyautogui.moveTo(x=x, y=y)
            sleep(600, 800)
            pyautogui.click(x=x, y=y, button="left")
            break
        sleep(500, 800)
    states["status"] = "floor1"
    return


def doFloor1(abilities: List[Ability]):
    # trigger start floor 1
    # pyautogui.moveTo(x=845, y=600)
    pyautogui.moveTo(x=530, y=680)
    sleep(400, 500)
    pyautogui.click(button=config["move"])

    # delayed start for better aoe abiltiy usage at floor1 beginning
    if config["delayedStart"] != None:
        sleep(config["delayedStart"] - 100, config["delayedStart"] + 100)

    # # move to a side
    # pyautogui.press(config["blink"])
    # sleep(400, 500)

    # pyautogui.mouseDown(random.randint(800, 1120), random.randint(540, 580), button=config['move'])
    # sleep(2000,2200)
    # pyautogui.click(x=960, y=530, button=config['move'])

    # smash available abilities
    useAbilities(abilities)

    # bad run quit
    if checkTimeout():
        quitChaos()
        return

    print("floor 1 cleared")
    calculateMinimapRelative(states["moveToX"], states["moveToY"])
    enterPortal()
    if checkTimeout():
        quitChaos()
        return
    states["status"] = "floor2"
    return


def doFloor2(abilities: List[Ability]):
    pyautogui.mouseDown(x=1150, y=500, button=config["move"])
    sleep(800, 900)
    pyautogui.mouseDown(x=960, y=200, button=config["move"])
    sleep(800, 900)
    pyautogui.click(x=945, y=550, button=config["move"])

    useAbilities(abilities)

    # bad run quit
    if checkTimeout():
        quitChaos()
        return

    print("floor 2 cleared")
    calculateMinimapRelative(states["moveToX"], states["moveToY"])
    enterPortal()
    if checkTimeout():
        quitChaos()
        return
    states["status"] = "floor3"

    return


def doFloor3Portal(abilities: List[Ability]):
    bossBar = None
    goldMob = False
    normalMob = False
    for i in range(0, 10):
        goldMob = checkFloor3GoldMob()
        normalMob = check_red_mob()
        bossBar = pyautogui.locateOnScreen("./screenshots/bossBar.png", confidence=0.7)
        if normalMob == True:
            return
        if goldMob == True or bossBar != None:
            break
        sleep(500, 550)

    if goldMob == False and bossBar == None and config["floor3"] == False:
        return

    if bossBar != None:
        print("purple boss bar located")
        states["purplePortalCount"] = states["purplePortalCount"] + 1
        pyautogui.press(config["awakening"])
        useAbilities(abilities)
        print("special portal cleared")
        calculateMinimapRelative(states["moveToX"], states["moveToY"])
        if config["floor3"] == False:
            return
        enterPortal()
        sleep(800, 900)
    elif normalMob == True:
        return
    elif goldMob == True:
        print("gold mob located")
        states["goldPortalCount"] = states["goldPortalCount"] + 1
        useAbilities(abilities)
        print("special portal cleared")
        calculateMinimapRelative(states["moveToX"], states["moveToY"])
        if config["floor3"] == False:
            return
        enterPortal()
        sleep(800, 900)
    else:
        # hacky quit
        states["instanceStartTime"] == -1
        return

    # bad run quit
    if checkTimeout():
        return


def doFloor3(abilities: List[Ability], limit: Optional[int] = None):
    waitForLoading()
    print("real floor 3 loaded")

    if checkTimeout():
        quitChaos()
        return

    useAbilities(abilities)

    # bad run quit
    if checkTimeout():
        quitChaos()
        return

    # # FIXME: this is a fkin weird situation 紫门boss没判断出3楼而是还是走的2楼状态，但是这里注释掉不管只是会超时不会卡
    # if checkPortal():
    #     calculateMinimapRelative(states["moveToX"], states["moveToY"])
    #     enterPortal()
    #     if checkTimeout():
    #         quitChaos()
    #         return
    #     useAbilities()

    # # bad run quit
    # if checkTimeout():
    #     quitChaos()
    #     return

    print("Chaos Dungeon Full cleared")
    restartChaos(limit)


def quitChaos():
    # quit
    print("quitting")
    clearOk = pyautogui.locateCenterOnScreen(
        "./screenshots/clearOk.png", confidence=0.75
    )
    if clearOk != None:
        x, y = clearOk
        pyautogui.moveTo(x=x, y=y)
        sleep(600, 800)
        pyautogui.click(x=x, y=y, button="left")
        sleep(200, 300)
        pyautogui.moveTo(x=x, y=y)
        sleep(200, 300)
        pyautogui.click(x=x, y=y, button="left")
    sleep(500, 600)
    utils.wait_and_click_leave()
    sleep(500, 600)
    utils.wait_and_click_ok()
    utils.sleep(1500)
    states["status"] = "inCity"
    states["clearCount"] = states["clearCount"] + 1
    printResult()

    return


def restartChaos(limit=None):
    states["fullClearCount"] = states["fullClearCount"] + 1
    states["clearCount"] = states["clearCount"] + 1
    printResult()
    if states["clearCount"] >= limit:
        quitChaos()
        return

    sleep(1200, 1400)
    # states["abilityScreenshots"] = []
    states["instanceStartTime"] = int(time.time_ns() / 1000000)

    while True:
        selectLevelButton = pyautogui.locateCenterOnScreen(
            "./screenshots/selectLevel.png",
            grayscale=True,
            confidence=0.7,
            region=config["regions"]["leaveMenu"],
        )
        if selectLevelButton != None:
            x, y = selectLevelButton

            pyautogui.moveTo(x=x, y=y)
            sleep(500, 600)
            pyautogui.click(button="left")
            sleep(150, 200)
            break
        sleep(500, 600)
    sleep(500, 600)
    while True:
        enterButton = pyautogui.locateCenterOnScreen(
            "./screenshots/enterButton.png", confidence=0.75
        )
        if enterButton != None:
            x, y = enterButton
            pyautogui.moveTo(x=x, y=y)
            sleep(600, 800)
            pyautogui.click(x=x, y=y, button="left")
            break
        sleep(500, 600)
    sleep(500, 600)
    while True:
        acceptButton = pyautogui.locateCenterOnScreen(
            "./screenshots/acceptButton.png", confidence=0.75
        )
        if acceptButton != None:
            x, y = acceptButton
            pyautogui.moveTo(x=x, y=y)
            sleep(600, 800)
            pyautogui.click(x=x, y=y, button="left")
            break
        sleep(500, 800)
    sleep(2000, 2200)
    states["status"] = "floor1"
    return


def printResult():
    lastRun = (int(time.time_ns() / 1000000) - states["instanceStartTime"]) / 1000
    avgTime = int(
        ((int(time.time_ns() / 1000000) - states["botStartTime"]) / 1000)
        / states["clearCount"]
    )
    if states["instanceStartTime"] != -1:
        states["minTime"] = int(min(lastRun, states["minTime"]))
        states["maxTime"] = int(max(lastRun, states["maxTime"]))
    print(
        "Total runs completed: {}, full clears: {}, total death: {}, half runs: {}, timeout runs: {}, ".format(
            states["clearCount"],
            states["fullClearCount"],
            states["deathCount"],
            states["badRunCount"],
            states["timeoutCount"],
        )
    )
    print(
        "Average time: {}, fastest time: {}, slowest time: {}".format(
            avgTime,
            states["minTime"],
            states["maxTime"],
        )
    )
    print(
        "gold portal count: {}, purple portal count: {}".format(
            states["goldPortalCount"], states["purplePortalCount"]
        )
    )


def useAbilities(abilities: List[Ability]):
    while True:
        diedCheck()
        healthCheck()
        if checkTimeout():
            return

        # check elite and mobs
        if states["status"] == "floor2" and checkFloor2Elite():
            calculateMinimapRelative(states["moveToX"], states["moveToY"])
            moveToMinimapRelative(states["moveToX"], states["moveToY"], 750, 850, False)
        elif states["status"] == "floor2" and check_red_mob():
            calculateMinimapRelative(states["moveToX"], states["moveToY"])
            moveToMinimapRelative(states["moveToX"], states["moveToY"], 400, 500, False)
        elif states["status"] == "floor3" and checkFloor2Elite():
            calculateMinimapRelative(states["moveToX"], states["moveToY"])
            moveToMinimapRelative(states["moveToX"], states["moveToY"], 200, 300, False)
            if config["useAwakening"]:
                print('using awakening')
                pyautogui.press(config["awakening"])

        # cast sequence
        for ability in abilities:
            if states["status"] == "floor3" and checkChaosFinish():
                return
            diedCheck()
            healthCheck()

            # check portal
            if states["status"] == "floor3" and checkPortal():
                pyautogui.click(
                    x=config["screenCenterX"],
                    y=config["screenCenterY"],
                    button=config["move"],
                )
                sleep(100, 150)
                checkPortal()
                return
            elif states["status"] == "floor2" and checkPortal():
                pyautogui.click(
                    x=config["screenCenterX"],
                    y=config["screenCenterY"],
                    button=config["move"],
                )
                sleep(100, 150)
                checkPortal()
                return
            elif states["status"] == "floor1" and checkPortal():
                pyautogui.click(
                    x=config["screenCenterX"],
                    y=config["screenCenterY"],
                    button=config["move"],
                )
                sleep(100, 150)
                checkPortal()
                return

            # click rift core
            if states["status"] == "floor3":
                clickTower()

            # check high-priority mobs
            if states["status"] == "floor2" and checkFloor2Boss():
                calculateMinimapRelative(states["moveToX"], states["moveToY"])
                moveToMinimapRelative(
                    states["moveToX"], states["moveToY"], 950, 1050, True
                )
                fightFloor2Boss()
            elif states["status"] == "floor3" and checkFloor3GoldMob():
                calculateMinimapRelative(states["moveToX"], states["moveToY"])
                moveToMinimapRelative(
                    states["moveToX"], states["moveToY"], 500, 600, False
                )
            elif states["status"] == "floor3" and checkFloor3Tower():
                if not checkFloor2Elite() and not check_red_mob():
                    randomMove()
                    checkFloor3Tower()
                calculateMinimapRelative(states["moveToX"], states["moveToY"])
                moveToMinimapRelative(
                    states["moveToX"], states["moveToY"], 1200, 1300, True
                )
                # pyautogui.press("x")
                sleep(200, 220)
                clickTower()
            elif states["status"] == "floor3" and check_red_mob():
                calculateMinimapRelative(states["moveToX"], states["moveToY"])
                moveToMinimapRelative(
                    states["moveToX"], states["moveToY"], 200, 300, False
                )
                # pyautogui.press(config["awakening"])
            elif states["status"] == "floor3" and checkFloor2Boss():
                calculateMinimapRelative(states["moveToX"], states["moveToY"])
                moveToMinimapRelative(
                    states["moveToX"], states["moveToY"], 800, 900, True
                )

            # cast spells
            checkCDandCast(ability)

        # 防止卡先试试这样
        if states["status"] == "floor3" and not checkFloor2Elite():
            randomMove()


def checkCDandCast(ability: Ability):
    now_ms = int(time.time_ns() / 1000000)
    if pyautogui.locateOnScreen(
        ability.image, region=config["regions"]["abilities"]
    ):
        if ability.directional:
            pyautogui.moveTo(x=states["moveToX"], y=states["moveToY"])
        else:
            pyautogui.moveTo(x=config["screenCenterX"], y=config["screenCenterY"])

        if ability.cast:
            start_ms = int(time.time_ns() / 1000000)
            now_ms = int(time.time_ns() / 1000000)
            # spam until cast time before checking cd, to prevent 击倒后情况
            while now_ms - start_ms < ability.cast_time:
                pyautogui.press(ability.key)
                now_ms = int(time.time_ns() / 1000000)
            # while pyautogui.locateOnScreen(
            #     ability["image"], region=config["regions"]["abilities"]
            # ):
            #     pyautogui.press(ability["key"])
        elif ability.hold:
            start_ms = int(time.time_ns() / 1000000)
            now_ms = int(time.time_ns() / 1000000)
            pyautogui.keyDown(ability.key)
            while now_ms - start_ms < ability.hold_time:
                pyautogui.keyDown(ability.key)
                now_ms = int(time.time_ns() / 1000000)
            # while pyautogui.locateOnScreen(
            #     ability["image"], region=config["regions"]["abilities"]
            # ):
            #     pyautogui.keyDown(ability["key"])
            pyautogui.keyUp(ability.key)
        else:
            # 瞬发 ability
            pyautogui.press(ability.key)
            while pyautogui.locateOnScreen(
                ability.image, region=config["regions"]["abilities"]
            ):
                pyautogui.press(ability.key)
        ability.last_used = now_ms
        sleep(200, 320)


def checkPortal():
    # check portal image
    portal = pyautogui.locateCenterOnScreen(
        "./screenshots/portal.png", region=config["regions"]["minimap"], confidence=0.7
    )
    if portal != None:
        x, y = portal
        states["moveToX"] = x
        states["moveToY"] = y
        print("portal image x: {} y: {}".format(states["moveToX"], states["moveToY"]))
        return True

    # # only check with portal image on floor 2
    # if states["status"] == "floor2":
    #     return False

    for r, g, b, rel_x, rel_y in spiral_search():
        if (r in range(75, 85) and g in range(140, 150) and b in range(250, 255)) or (
            r in range(120, 130) and g in range(210, 220) and b in range(250, 255)
        ):
            left, top, _w, _h = config["regions"]["minimap"]
            states["moveToX"] = left + rel_x
            states["moveToY"] = top + rel_y
            print(
                "portal pixel x: {} y: {}, r: {} g: {} b: {}".format(
                    states["moveToX"], states["moveToY"], r, g, b
                )
            )
            return True
    return False


def checkFloor2Elite():
    for r, g, b, rel_x, rel_y in spiral_search():
        if (r in range(200, 215)) and (g in range(125, 150)) and (b in range(30, 60)):
            left, top, _w, _h = config["regions"]["minimap"]
            states["moveToX"] = left + rel_x
            states["moveToY"] = top + rel_y
            print(
                "elite x: {} y: {}, r: {} g: {} b: {}".format(
                    states["moveToX"], states["moveToY"], r, g, b
                )
            )
            return True
    return False


def check_red_mob() -> bool:
    for r, g, b, rel_x, rel_y in spiral_search():
        if (r in range(200, 255)) and (g in range(10, 40)) and (b in range(10, 40)):
            left, top, _w, _h = config["regions"]["minimap"]
            states["moveToX"] = left + rel_x
            states["moveToY"] = top + rel_y
            print(
                "red mob x: {} y: {}, r: {} g: {} b: {}".format(
                    states["moveToX"], states["moveToY"], r, g, b
                )
            )
            return True
    return False


def checkFloor3GoldMob():
    for r, g, b, rel_x, rel_y in spiral_search():
        if r == 255 and g == 188 and b == 30:
            left, top, _w, _h = config["regions"]["minimap"]
            states["moveToX"] = left + rel_x
            states["moveToY"] = top + rel_y
            print(
                "gold x: {} y: {}, r: {} g: {} b: {}".format(
                    states["moveToX"], states["moveToY"], r, g, b
                )
            )
            return True
    return False


def checkFloor2Boss():
    fightFloor2Boss()
    bossLocation = pyautogui.locateCenterOnScreen(
        "./screenshots/boss.png", confidence=0.65
    )
    if bossLocation != None:
        bossLocation = tuple(bossLocation)
        left, top = bossLocation
        states["moveToX"] = left
        states["moveToY"] = top
        print("boss x: {} y: {}".format(states["moveToX"], states["moveToY"]))
        return True
    return False


# def checkFloor2Boss():
#     sleep(100, 200)
#     fightFloor2Boss()
#     minimap = pyautogui.screenshot(region=config["regions"]["minimap"])  # Top Right
#     width, height = minimap.size
#     order = spiralSearch(width, height, math.floor(width / 2), math.floor(height / 2))
#     for entry in order:
#         if entry[1] >= width or entry[0] >= height:
#             continue
#         r, g, b = minimap.getpixel((entry[1], entry[0]))
#         if (
#             (r in range(153, 173)) and (g in range(25, 35)) and (b in range(25, 35))
#         ):  # r == 199 and g == 28 and b == 30
#             left, top, _w, _h = config["regions"]["minimap"]
#             states["moveToX"] = left + entry[1]
#             states["moveToY"] = top + entry[0]
#             print(
#                 "Boss x: {} y: {}, r: {} g: {} b: {}".format(
#                     states["moveToX"], states["moveToY"], r, g, b
#                 )
#             )
#             return True


def clickTower():
    riftCore1 = pyautogui.locateCenterOnScreen(
        "./screenshots/riftcore1.png", confidence=0.6
    )
    riftCore2 = pyautogui.locateCenterOnScreen(
        "./screenshots/riftcore2.png", confidence=0.6
    )
    if riftCore1 != None:
        x, y = riftCore1
        if y > 650 or x < 400 or x > 1500:
            return
        states["moveToX"] = x
        states["moveToY"] = y + 190
        pyautogui.click(x=states["moveToX"], y=states["moveToY"], button=config["move"])
        print("clicked rift core")
        sleep(100, 120)
        pyautogui.press(config["meleeAttack"])
        sleep(900, 960)
        pyautogui.press(config["meleeAttack"])
    elif riftCore2 != None:
        x, y = riftCore2
        if y > 650 or x < 400 or x > 1500:
            return
        states["moveToX"] = x
        states["moveToY"] = y + 190
        pyautogui.click(x=states["moveToX"], y=states["moveToY"], button=config["move"])
        print("clicked rift core")
        sleep(100, 120)
        pyautogui.press(config["meleeAttack"])
        sleep(900, 960)
        pyautogui.press(config["meleeAttack"])


def checkFloor3Tower():
    tower = pyautogui.locateCenterOnScreen(
        "./screenshots/tower.png", region=config["regions"]["minimap"], confidence=0.7
    )
    if tower != None:
        x, y = tower
        states["moveToX"] = x
        states["moveToY"] = y - 1
        print("tower image x: {} y: {}".format(states["moveToX"], states["moveToY"]))
        return True

    for r, g, b, rel_x, rel_y in spiral_search():
        if (
            (r == 242 and g == 63 and b == 68)
            or (r == 162 and g == 162 and b == 162)
            or (r == 126 and g == 97 and b == 103)
        ):
            left, top, _w, _h = config["regions"]["minimap"]
            states["moveToX"] = left + rel_x
            states["moveToY"] = top + rel_y
            # pos offset
            if r == 126 and g == 97 and b == 103:
                states["moveToY"] = states["moveToY"] + 7
            elif r == 162 and g == 162 and b == 162:
                states["moveToY"] = states["moveToY"] - 13
            print(
                "tower pixel pos x: {} y: {}, r: {} g: {} b: {}".format(
                    states["moveToX"], states["moveToY"], r, g, b
                )
            )
            return True

    return False


def checkChaosFinish():
    clearOk = pyautogui.locateCenterOnScreen(
        "./screenshots/clearOk.png", confidence=0.75
    )
    if clearOk != None:
        x, y = clearOk
        pyautogui.moveTo(x=x, y=y)
        sleep(600, 800)
        pyautogui.click(x=x, y=y, button="left")
        sleep(200, 300)
        pyautogui.moveTo(x=x, y=y)
        sleep(200, 300)
        pyautogui.click(x=x, y=y, button="left")
        return True
    return False


def fightFloor2Boss():
    if pyautogui.locateOnScreen("./screenshots/bossBar.png", confidence=0.7):
        print("boss bar located")
        pyautogui.press(config["awakening"])


def calculateMinimapRelative(x, y):
    selfLeft = config["minimapCenterX"]
    selfTop = config["minimapCenterY"]
    if abs(selfLeft - x) <= 3 and abs(selfTop - y) <= 3:
        states["moveToX"] = config["screenCenterX"]
        states["moveToY"] = config["screenCenterY"]
        return

    x = x - selfLeft
    y = y - selfTop
    # print("relative to center pos x: {} y: {}".format(x, y))

    dist = 200
    if y < 0:
        dist = -dist

    if x == 0:
        if y < 0:
            newY = y - abs(dist)
        else:
            newY = y + abs(dist)
        # print("relative to center pos newX: 0 newY: {}".format(int(newY)))
        states["moveToX"] = 0 + config["screenCenterX"]
        states["moveToY"] = int(newY) + config["screenCenterY"]
        return
    if y == 0:
        if x < 0:
            newX = x - abs(dist)
        else:
            newX = x + abs(dist)
        # print("relative to center pos newX: {} newY: 0".format(int(newX)))
        states["moveToX"] = int(newX) + config["screenCenterX"]
        states["moveToY"] = 0 + config["screenCenterY"]
        return

    k = y / x
    # newX = x + dist
    newY = y + dist
    # newY = k * (newX - x) + y
    newX = (newY - y) / k + x

    # print("before confining newX: {} newY: {}".format(int(newX), int(newY)))
    if newX < 0 and abs(newX) > config["clickableAreaX"]:
        newX = -config["clickableAreaX"]
        if newY < 0:
            newY = newY + abs(dist) * 0.25
        else:
            newY = newY - abs(dist) * 0.25
    elif newX > 0 and abs(newX) > config["clickableAreaX"]:
        newX = config["clickableAreaX"]
        if newY < 0:
            newY = newY + abs(dist) * 0.25
        else:
            newY = newY - abs(dist) * 0.25

    if newY < 0 and abs(newY) > config["clickableAreaY"]:
        newY = -config["clickableAreaY"]
        if newX < 0:
            newX = newX + abs(dist) * 0.7
        else:
            newX = newX - abs(dist) * 0.7
    elif newY > 0 and abs(newY) > config["clickableAreaY"]:
        newY = config["clickableAreaY"]
        if newX < 0:
            newX = newX + abs(dist) * 0.7
        else:
            newX = newX - abs(dist) * 0.7

    # print(
    #     "after confining relative to center pos newX: {} newY: {}".format(
    #         int(newX), int(newY)
    #     )
    # )
    states["moveToX"] = int(newX) + config["screenCenterX"]
    states["moveToY"] = int(newY) + config["screenCenterY"]
    return


def moveToMinimapRelative(x, y, timeMin, timeMax, blink):
    # move one step to direction
    if (
        states["moveToX"] == config["screenCenterX"]
        and states["moveToY"] == config["screenCenterY"]
    ):
        return
    print("moving to pos x: {} y: {}".format(states["moveToX"], states["moveToY"]))

    # count = 0
    # turn = True
    # deflect = 60

    # moving in a straight line
    pyautogui.click(x=x, y=y, button=config["move"])
    sleep(int(timeMin / 2), int(timeMax / 2))

    # moving in a straight line
    pyautogui.click(x=x, y=y, button=config["move"])
    sleep(int(timeMin / 2), int(timeMax / 2))
    # sleep(timeMin, timeMax)

    # optional blink here
    if blink:
        pyautogui.press(config["blink"])
        sleep(100, 150)

    return

    # # snake moving
    # while count < 3:
    #     if x > 960 and y < 540:
    #         if turn:
    #             x = x - deflect* 2.5
    #             y = y - deflect
    #         else:
    #             x = x + deflect* 2.5
    #             y = y + deflect
    #     elif x > 960 and y > 540:
    #         if turn:
    #             x = x + deflect* 2.5
    #             y = y - deflect
    #         else:
    #             x = x - deflect * 2.5
    #             y = y + deflect
    #     elif x < 960 and y > 540:
    #         if turn:
    #             x = x + deflect* 2.5
    #             y = y + deflect
    #         else:
    #             x = x - deflect* 2.5
    #             y = y - deflect
    #     elif x < 960 and y < 540:
    #         if turn:
    #             x = x - deflect* 2.5
    #             y = y + deflect
    #         else:
    #             x = x + deflect* 2.5
    #             y = y - deflect
    #     pyautogui.mouseDown(x=x, y=y, button=config['move'])
    #     sleep(math.floor(timeMin / 3), math.floor(timeMax / 3))
    #     turn = not turn
    #     count = count + 1


def randomMove():
    x = random.randint(
        config["screenCenterX"] - config["clickableAreaX"],
        config["screenCenterX"] + config["clickableAreaX"],
    )
    y = random.randint(
        config["screenCenterY"] - config["clickableAreaY"],
        config["screenCenterY"] + config["clickableAreaY"],
    )

    print("random move to x: {} y: {}".format(x, y))
    pyautogui.click(x=x, y=y, button=config["move"])
    sleep(200, 250)
    pyautogui.click(x=x, y=y, button=config["move"])
    sleep(200, 250)
    # pyautogui.click(
    #     x=config["screenCenterX"], y=config["screenCenterY"], button=config["move"]
    # )


def enterPortal():
    # repeatedly move and press g until black screen
    sleep(1100, 1200)
    print("moving to portal x: {} y: {}".format(states["moveToX"], states["moveToY"]))
    enterTime = int(time.time_ns() / 1000000)
    portal_try = enterTime
    while True:
        im = pyautogui.screenshot(region=(1652, 168, 240, 210))
        r, g, b = im.getpixel((1772 - 1652, 272 - 168))
        if r == 0 and g == 0 and b == 0:
            return

        nowTime = int(time.time_ns() / 1000000)
        if nowTime - enterTime > 30000:
            # FIXME:
            states["instanceStartTime"] = -1
            return
        if nowTime - portal_try > 6000:
            print('Trying to find portal again')
            checkPortal()
            calculateMinimapRelative(states["moveToX"], states["moveToY"])
            portal_try = nowTime

        if (states["moveToX"] == config["screenCenterX"] and
                states["moveToY"] == config["screenCenterY"]):
            pyautogui.press(config["interact"])
            sleep(100, 120)
        else:
            pyautogui.press(config["interact"])
            pyautogui.click(
                x=states["moveToX"], y=states["moveToY"], button=config["move"]
            )
            sleep(50, 60)
            pyautogui.press(config["interact"])
            pyautogui.click(
                x=states["moveToX"], y=states["moveToY"], button=config["move"]
            )
            sleep(50, 60)
            pyautogui.press(config["interact"])


# def enterPortal():
#     # repeatedly move and press g until black screen
#     print("moving to portal x: {} y: {}".format(states["moveToX"], states["moveToY"]))
#     turn = True
#     deflect = 80
#     while True:
#         im = pyautogui.screenshot(region=(1652, 168, 240, 210))
#         r, g, b = im.getpixel((1772 - 1652, 272 - 168))
#         if r == 0 and g == 0 and b == 0:
#             return

#         x = states["moveToX"]
#         y = states["moveToY"]
#         if x > 960 and y < 540:
#             if turn:
#                 x = x - deflect * 2.5
#                 y = y - deflect
#             else:
#                 x = x + deflect * 2.5
#                 y = y + deflect
#         elif x > 960 and y > 540:
#             if turn:
#                 x = x + deflect * 2.5
#                 y = y - deflect
#             else:
#                 x = x - deflect * 2.5
#                 y = y + deflect
#         elif x < 960 and y > 540:
#             if turn:
#                 x = x + deflect * 2.5
#                 y = y + deflect
#             else:
#                 x = x - deflect * 2.5
#                 y = y - deflect
#         elif x < 960 and y < 540:
#             if turn:
#                 x = x - deflect * 2.5
#                 y = y + deflect
#             else:
#                 x = x + deflect * 2.5
#                 y = y - deflect
#         # print('movex: {} movey: {} x:{} y: {} turn: {}'.format(states['moveToX'], states['moveToY'], x,y,turn))
#         count = 0
#         while count < 5:
#             pyautogui.press(config["interact"])
#             im = pyautogui.screenshot(region=(1652, 168, 240, 210))
#             r, g, b = im.getpixel((1772 - 1652, 272 - 168))
#             if r == 0 and g == 0 and b == 0:
#                 return

#             if (
#                 states["moveToX"] == config["screenCenterX"]
#                 and states["moveToY"] == config["screenCenterY"]
#             ):
#                 pyautogui.press(config["interact"])
#                 sleep(100, 120)
#             else:
#                 pyautogui.click(x=x, y=y, button=config["move"])
#                 sleep(50, 60)
#                 pyautogui.press(config["interact"])
#                 count = count + 1
#             turn = not turn
#     return


def waitForLoading():
    print("loading")
    while True:
        leaveButton = pyautogui.locateOnScreen(
            "./screenshots/leave.png",
            grayscale=True,
            confidence=0.7,
            region=config["regions"]["leaveMenu"],
        )
        if leaveButton != None:
            return
        sleep(150, 200)
        if checkTimeout():
            return


def diedCheck():  # get information about wait a few second to revive
    if pyautogui.locateOnScreen(
        "./screenshots/died.png", grayscale=True, confidence=0.9
    ):
        states["deathCount"] = states["deathCount"] + 1
        sleep(5000, 5500)
        while (
            pyautogui.locateOnScreen("./screenshots/resReady.png", confidence=0.7)
            != None
        ):
            pyautogui.moveTo(1275, 454)
            sleep(600, 800)
            pyautogui.click(1275, 454, button="left")
            sleep(600, 800)
            pyautogui.moveTo(config["screenCenterX"], config["screenCenterY"])
    return


def doRepair():
    # Check if repair needed
    if states["deathCount"] % 5 == 0 or pyautogui.locateOnScreen(
        "./screenshots/repair.png",
        grayscale=True,
        confidence=0.5,
        region=(1500, 134, 100, 100),
    ):
        print('Repairing')
        sleep(800, 900)
        pyautogui.press("f1")
        sleep(800, 900)
        pyautogui.moveTo(1182, 654)
        sleep(800, 900)
        pyautogui.click(1182, 654, button="left")
        sleep(800, 900)
        pyautogui.moveTo(1068, 644)
        sleep(800, 900)
        pyautogui.click(1068, 644, button="left")
        sleep(800, 900)
        pyautogui.press("esc")
        sleep(800, 900)
        pyautogui.press("esc")
        sleep(800, 900)


def healthCheck():
    x = int(
        config["healthCheckX"]
        + (870 - config["healthCheckX"]) * config["healthPotAtPercent"]
    )
    y = config["healthCheckY"]
    r, g, b = pyautogui.pixel(x, y)
    # print(x, r, g, b)
    if r < 70 and config["useHealthPot"]:
        leaveButton = pyautogui.locateCenterOnScreen(
            "./screenshots/leave.png",
            grayscale=True,
            confidence=0.7,
            region=config["regions"]["leaveMenu"],
        )
        if leaveButton == None:
            return
        pyautogui.press(config["healthPot"])
        states["healthPotCount"] = states["healthPotCount"] + 1
        return
    return


def sleep(min, max):
    time.sleep(random.randint(min, max) / 1000.0)


def spiral_search():
    minimap = pyautogui.screenshot(region=config["regions"]["minimap"])  # Top Right
    width, height = minimap.size
    coords = spiralSearch(width, height, math.floor(width / 2), math.floor(height / 2))
    for coord in coords:
        r, g, b = minimap.getpixel(coord)
        yield r, g, b, coord[0], coord[1]


@cache
def spiralSearch(rows, cols, rStart, cStart):
    ans = []  # 可以通过长度来退出返回
    end = rows * cols  # 边界扩张
    i = i1 = i2 = rStart
    # 分别是当前点,上下边界的上边界，下边界
    j = j1 = j2 = cStart  # 当前，左、右边界
    while True:
        j2 += 1
        while j < j2:
            if 0 <= j < cols and 0 <= i:  # i刚减完
                ans.append((i, j))
            j += 1
            if 0 > i:  # i超过了，跳过优化
                j = j2  # 没有答案可添加
        i2 += 1
        while i < i2:
            if 0 <= i < rows and j < cols:
                ans.append((i, j))
            i += 1
            if j >= cols:
                i = i2
        j1 -= 1
        while j > j1:
            if 0 <= j < cols and i < rows:
                ans.append((i, j))
            j -= 1
            if i >= rows:
                j = j1
        i1 -= 1
        while i > i1:
            if 0 <= i < rows and 0 <= j:
                ans.append((i, j))
            i -= 1
            if 0 > j:
                i = i1
        if len(ans) == end:
            return ans


def checkTimeout():
    currentTime = int(time.time_ns() / 1000000)
    # hacky way of quitting
    if states["instanceStartTime"] == -1:
        print("hacky timeout")
        # timeout = pyautogui.screenshot()
        # timeout.save("./timeout/weird" + str(currentTime) + ".png")
        states["badRunCount"] = states["badRunCount"] + 1
        return True
    if currentTime - states["instanceStartTime"] > config["timeLimit"]:
        print("timeout triggered")
        # timeout = pyautogui.screenshot()
        # timeout.save("./timeout/overtime" + str(currentTime) + ".png")
        states["timeoutCount"] = states["timeoutCount"] + 1
        return True
    return False


def main(_argv):
    utils.move_window()
    if FLAGS.mode == 'infinite_chaos':
        infinite_chaos(FLAGS.starting_char)
    elif FLAGS.mode == 'daily':
        daily(FLAGS.chars, FLAGS.starting_char)


if __name__ == "__main__":
    app.run(main)

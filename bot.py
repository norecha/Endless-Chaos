from dataclasses import dataclass
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
flags.DEFINE_integer('starting_char', 1, 'starting char', lower_bound=1)

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
client_util = utils.ClientUtil()


def load_config(char: int) -> Dict:
    with open(f'character_configs/{char}.json') as f:
        return json.load(f)


def load_abilities(char_config: Dict) -> List[Ability]:
    abilities = []
    for ability_config in char_config['abilities']:
        if not ability_config['abilityType'] == 'normal':
            continue
        ability = Ability.load_from_config(ability_config, client_util)
        abilities.append(ability)
    return abilities


def switch_to_char(char):
    print(f'Switching to {char=}')
    utils.press('ESC', 1500)
    client_util.move_and_click(*coordinates.SWITCH_CHARACTERS, wait=1000)
    client_util.move_and_click(*coordinates.CHARACTERS[char - 1], wait=1000)
    client_util.move_and_click(*coordinates.CONNECT, wait=1000)
    client_util.move_and_click(*coordinates.CONNECT_CONFIRM)
    utils.sleep(30000)
    client_util.wait_loading_finish()


def daily(chars, starting_char):
    global states
    for char in range(starting_char, starting_char + chars):
        print(f'Starting daily for {char=}')
        states = newStates.copy()
        # switch to char
        if char != starting_char:
            switch_to_char(char)
        infinite_chaos(char, limit=2)
        client_util.wait_loading_finish()
    print(f'Done with dailies')


def infinite_chaos(char, limit: Optional[int] = None):
    print(f"Endless Chaos started {char=} {limit=}...")
    char_config = load_config(char)
    # save bot start time
    states["botStartTime"] = int(time.time_ns() / 1000000)
    abilities = None
    while True:
        if limit and states["clearCount"] >= limit:
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
            client_util.move_to(x=config["screenCenterX"], y=config["screenCenterY"])
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
            doRepair()

            if char_config['class'] == 'Berserker':
                utils.press(config['specialty1'])

            # do floor one
            doFloor1(abilities)
        elif states["status"] == "floor2":
            print("floor2")
            client_util.move_to(x=config["screenCenterX"], y=config["screenCenterY"])
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
            client_util.move_to(x=config["screenCenterX"], y=config["screenCenterY"])
            sleep(200, 300)
            # wait for loading
            waitForLoading()
            if checkTimeout():
                quitChaos()
                continue
            print("floor3 loaded")
            # do floor 3
            # trigger start floor 3
            client_util.move_to(x=1045, y=450)
            sleep(100, 120)
            client_util.click(button=config["move"])
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

    client_util.move_to(x=config["screenCenterX"], y=config["screenCenterY"])
    sleep(200, 300)
    client_util.click(button=rightClick)
    sleep(200, 300)

    if config["shortcutEnterChaos"] == True:
        client_util.wait_loading_finish()
        sleep(600, 800)
        while True:
            pyautogui.keyDown("alt")
            sleep(600, 800)
            utils.press("q")
            sleep(300, 400)
            pyautogui.keyUp("alt")
            sleep(300, 400)
            client_util.move_to(886, 346)
            sleep(600, 800)
            client_util.click(button="left")
            sleep(600, 800)

            enterButton = client_util.locate_center_on_screen(
                "./screenshots/enterButton.png", confidence=0.75
            )
            if enterButton != None:
                x, y = enterButton
                client_util.move_to(x=x, y=y)
                sleep(600, 800)
                client_util.click(x=x, y=y, button="left")
                break
            else:
                if checkTimeout():
                    # quitChaos()
                    return
                client_util.move_to(886, 346)
                sleep(600, 800)
                client_util.click(button="left")
                sleep(600, 800)
    else:
        while True:
            enterHand = client_util.locate_on_screen("./screenshots/enterChaos.png")
            if enterHand != None:
                print("entering chaos...")
                utils.press(config["interact"])
                break
            sleep(500, 800)
    sleep(600, 800)
    while True:
        acceptButton = client_util.locate_center_on_screen(
            "./screenshots/acceptButton.png", confidence=0.75
        )
        if acceptButton != None:
            x, y = acceptButton
            client_util.move_to(x=x, y=y)
            sleep(600, 800)
            client_util.click(x=x, y=y, button="left")
            break
        sleep(500, 800)
    states["status"] = "floor1"
    return


def doFloor1(abilities: List[Ability]):
    # trigger start floor 1
    # mouse_util.move_to(x=845, y=600)
    client_util.move_to(x=530, y=680)
    sleep(400, 500)
    client_util.click(button=config["move"])

    # delayed start for better aoe abiltiy usage at floor1 beginning
    if config["delayedStart"] != None:
        sleep(config["delayedStart"] - 100, config["delayedStart"] + 100)

    # # move to a side
    # utils.press(config["blink"])
    # sleep(400, 500)

    # mouse_util.mouse_down(random.randint(800, 1120), random.randint(540, 580), button=config['move'])
    # sleep(2000,2200)
    # mouse_util.click(x=960, y=530, button=config['move'])

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
    client_util.mouse_down(x=1150, y=500, button=config["move"])
    sleep(800, 900)
    client_util.mouse_down(x=960, y=200, button=config["move"])
    sleep(800, 900)
    client_util.click(x=945, y=550, button=config["move"])

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
    print('Identifying floor 3 portal')
    bossBar = None
    goldMob = False
    normalMob = False
    for i in range(0, 10):
        goldMob = checkFloor3GoldMob()
        normalMob = check_red_mob()
        bossBar = client_util.locate_on_screen("./screenshots/bossBar.png", confidence=0.7)
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
        utils.press(config["awakening"])
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

    useAbilities(abilities, check_portal=False)

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
    clearOk = client_util.locate_center_on_screen(
        "./screenshots/clearOk.png", confidence=0.75
    )
    if clearOk != None:
        x, y = clearOk
        client_util.move_to(x=x, y=y)
        sleep(600, 800)
        client_util.click(x=x, y=y, button="left")
        sleep(200, 300)
        client_util.move_to(x=x, y=y)
        sleep(200, 300)
        client_util.click(x=x, y=y, button="left")
    sleep(500, 600)
    client_util.wait_and_click_leave()
    sleep(500, 600)
    client_util.wait_and_click_ok()
    utils.sleep(1500)
    states["status"] = "inCity"
    states["clearCount"] = states["clearCount"] + 1
    printResult()

    return


def restartChaos(limit: Optional[int] = None):
    states["fullClearCount"] = states["fullClearCount"] + 1
    states["clearCount"] = states["clearCount"] + 1
    printResult()
    if limit and states["clearCount"] >= limit:
        quitChaos()
        return

    sleep(1200, 1400)
    # states["abilityScreenshots"] = []
    states["instanceStartTime"] = int(time.time_ns() / 1000000)

    while True:
        selectLevelButton = client_util.locate_center_on_screen(
            "./screenshots/selectLevel.png",
            grayscale=True,
            confidence=0.7,
            region=config["regions"]["leaveMenu"],
        )
        if selectLevelButton != None:
            x, y = selectLevelButton

            client_util.move_to(x=x, y=y)
            sleep(500, 600)
            client_util.click(button="left")
            sleep(150, 200)
            break
        sleep(500, 600)
    sleep(500, 600)
    while True:
        enterButton = client_util.locate_center_on_screen(
            "./screenshots/enterButton.png", confidence=0.75
        )
        if enterButton != None:
            x, y = enterButton
            client_util.move_to(x=x, y=y)
            sleep(600, 800)
            client_util.click(x=x, y=y, button="left")
            break
        sleep(500, 600)
    sleep(500, 600)
    while True:
        acceptButton = client_util.locate_center_on_screen(
            "./screenshots/acceptButton.png", confidence=0.75
        )
        if acceptButton != None:
            x, y = acceptButton
            client_util.move_to(x=x, y=y)
            sleep(600, 800)
            client_util.click(x=x, y=y, button="left")
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


@dataclass
class SpiralResult:
    found: bool
    r: int = 0
    g: int = 0
    b: int = 0
    rel_x: int = 0
    rel_y: int = 0


def check_spiral_predicates(predicates) -> List[SpiralResult]:
    result = [SpiralResult(False) for _ in predicates]
    for r, g, b, rel_x, rel_y in spiral_search():
        for i, predicate in enumerate(predicates):
            if not result[i].found and predicate(r, g, b):
                result[i] = SpiralResult(True, r, g, b, rel_x, rel_y)
    return result


def useAbilities(abilities: List[Ability], check_portal: Optional[bool] = True):
    while True:
        diedCheck()
        healthCheck()
        if checkTimeout():
            return

        # check elite and mobs
        if states["status"] == "floor1" and check_red_mob():
            calculateMinimapRelative(states["moveToX"], states["moveToY"])
            moveToMinimapRelative(states["moveToX"], states["moveToY"], 200, 300, False)
        elif states["status"] == "floor2" and checkFloor2Elite():
            calculateMinimapRelative(states["moveToX"], states["moveToY"])
            moveToMinimapRelative(states["moveToX"], states["moveToY"], 750, 850, False)
        elif states["status"] == "floor2" and check_red_mob():
            calculateMinimapRelative(states["moveToX"], states["moveToY"])
            moveToMinimapRelative(states["moveToX"], states["moveToY"], 400, 500, False)
        elif states["status"] == "floor3" and checkChaosFinish():
            return
        elif states["status"] == "floor3" and checkFloor2Elite():
            calculateMinimapRelative(states["moveToX"], states["moveToY"])
            moveToMinimapRelative(states["moveToX"], states["moveToY"], 200, 300, False)
            if config["useAwakening"]:
                print('using awakening')
                utils.press(config["awakening"])

        # cast sequence
        for ability_index, ability in enumerate(abilities):
            diedCheck()
            healthCheck()

            # check portal
            if check_portal and ability_index % 2 == 0 and states["status"] in ("floor1", "floor2", "floor3") and checkPortal():
                client_util.click(
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
            # floor3 checks take long time, don't do it after every ability
            elif states["status"] == "floor3" and ability_index % 3 == 0:
                # check all pixels in one spiral
                gold, red, tower, elite = check_spiral_predicates(
                    [is_gold_mob, is_red_mob, is_tower_pixel, is_elite_mob])
                if gold.found:
                    left, top, _w, _h = config["regions"]["minimap"]
                    states["moveToX"] = left + gold.rel_x
                    states["moveToY"] = top + gold.rel_y
                    print(
                        "gold x: {} y: {}, r: {} g: {} b: {}".format(
                            states["moveToX"], states["moveToY"], gold.r, gold.g, gold.b
                        )
                    )
                    calculateMinimapRelative(states["moveToX"], states["moveToY"])
                    moveToMinimapRelative(
                        states["moveToX"], states["moveToY"], 500, 600, False
                    )
                elif checkFloor3Tower(tower):
                    if not elite.found and not red.found:
                        randomMove()
                        tower, = check_spiral_predicates([is_tower_pixel])
                        checkFloor3Tower(tower)
                    calculateMinimapRelative(states["moveToX"], states["moveToY"])
                    moveToMinimapRelative(
                        states["moveToX"], states["moveToY"], 1200, 1300, True
                    )
                    # utils.press("x")
                    sleep(200, 220)
                    clickTower()
                elif red.found:
                    left, top, _w, _h = config["regions"]["minimap"]
                    states["moveToX"] = left + red.rel_x
                    states["moveToY"] = top + red.rel_y
                    print(
                        "red mob x: {} y: {}, r: {} g: {} b: {}".format(
                            states["moveToX"], states["moveToY"], red.r, red.g, red.b
                        )
                    )
                    calculateMinimapRelative(states["moveToX"], states["moveToY"])
                    moveToMinimapRelative(
                        states["moveToX"], states["moveToY"], 200, 300, False
                    )
                elif checkFloor2Boss():
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
    if client_util.locate_on_screen(
        ability.image, region=config["regions"]["abilities"]
    ):
        if ability.directional:
            client_util.move_to(x=states["moveToX"], y=states["moveToY"])
        else:
            client_util.move_to(x=config["screenCenterX"], y=config["screenCenterY"])

        if ability.cast:
            start_ms = int(time.time_ns() / 1000000)
            now_ms = int(time.time_ns() / 1000000)
            # spam until cast time before checking cd, to prevent 击倒后情况
            while now_ms - start_ms < ability.cast_time:
                utils.press(ability.key)
                now_ms = int(time.time_ns() / 1000000)
            # while mouse_util.locate_on_screen(
            #     ability["image"], region=config["regions"]["abilities"]
            # ):
            #     utils.press(ability["key"])
        elif ability.hold:
            start_ms = int(time.time_ns() / 1000000)
            now_ms = int(time.time_ns() / 1000000)
            pyautogui.keyDown(ability.key)
            while now_ms - start_ms < ability.hold_time:
                pyautogui.keyDown(ability.key)
                now_ms = int(time.time_ns() / 1000000)
            # while mouse_util.locate_on_screen(
            #     ability["image"], region=config["regions"]["abilities"]
            # ):
            #     pyautogui.keyDown(ability["key"])
            pyautogui.keyUp(ability.key)
        else:
            # 瞬发 ability
            utils.press(ability.key)
            while client_util.locate_on_screen(
                ability.image, region=config["regions"]["abilities"]
            ):
                utils.press(ability.key)


def checkPortal():
    # check portal image
    portal = client_util.locate_center_on_screen(
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
        if (r in range(75, 86) and g in range(140, 151) and b in range(250, 256)) or (
            r in range(120, 131) and g in range(210, 221) and b in range(250, 256)
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


def is_elite_mob(r, g, b):
    return r in range(200, 216) and g in range(125, 151) and b in range(30, 61)


def checkFloor2Elite():
    for r, g, b, rel_x, rel_y in spiral_search():
        if is_elite_mob(r, g, b):
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


def is_red_mob(r, g, b):
    return r in range(200, 256) and g in range(10, 41) and b in range(10, 41)


def check_red_mob() -> bool:
    for r, g, b, rel_x, rel_y in spiral_search():
        if is_red_mob(r, g, b):
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


def is_gold_mob(r, g, b):
    return r in range(240, 256) and g in range(180, 201) and b in range(0, 41)


def checkFloor3GoldMob():
    for r, g, b, rel_x, rel_y in spiral_search():
        if is_gold_mob(r, g, b):
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
    bossLocation = client_util.locate_center_on_screen(
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
#     minimap = mouse_util.screenshot(region=config["regions"]["minimap"])  # Top Right
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
    riftCore1 = client_util.locate_center_on_screen(
        "./screenshots/riftcore1.png", confidence=0.6
    )
    riftCore2 = client_util.locate_center_on_screen(
        "./screenshots/riftcore2.png", confidence=0.6
    )
    if riftCore1 != None:
        x, y = riftCore1
        if y > 650 or x < 400 or x > 1500:
            return
        states["moveToX"] = x
        states["moveToY"] = y + 190
        client_util.click(x=states["moveToX"], y=states["moveToY"], button=config["move"])
        print("clicked rift core")
        sleep(100, 120)
        utils.press(config["meleeAttack"])
        sleep(900, 960)
        utils.press(config["meleeAttack"])
    elif riftCore2 != None:
        x, y = riftCore2
        if y > 650 or x < 400 or x > 1500:
            return
        states["moveToX"] = x
        states["moveToY"] = y + 190
        client_util.click(x=states["moveToX"], y=states["moveToY"], button=config["move"])
        print("clicked rift core")
        sleep(100, 120)
        utils.press(config["meleeAttack"])
        sleep(900, 960)
        utils.press(config["meleeAttack"])


def is_tower_pixel(r, g, b):
    return ((r in range(240, 245) and r in range(60, 65) and r in range(65, 70)) or
            (r in range(160, 165) and g in range(160, 165) and b in range(160, 165)) or
            (r in range(125, 130) and g in range(95, 100) and b in range(100, 105)))


def checkFloor3Tower(tower_result: SpiralResult):
    tower = client_util.locate_center_on_screen(
        "./screenshots/tower.png", region=config["regions"]["minimap"], confidence=0.7
    )
    if tower != None:
        x, y = tower
        states["moveToX"] = x
        states["moveToY"] = y - 1
        print("tower image x: {} y: {}".format(states["moveToX"], states["moveToY"]))
        return True

    if tower_result.found:
        left, top, _w, _h = config["regions"]["minimap"]
        states["moveToX"] = left + tower_result.rel_x
        states["moveToY"] = top + tower_result.rel_y
        # pos offset
        if tower_result.r in range(125, 130) and tower_result.g in range(95, 100) and tower_result.b in range(100, 105):
            states["moveToY"] = states["moveToY"] + 7
        elif tower_result.r in range(160, 165) and tower_result.g in range(160, 165) and tower_result.b in range(160, 165):
            states["moveToY"] = states["moveToY"] - 13
        print(
            "tower pixel pos x: {} y: {}, r: {} g: {} b: {}".format(
                states["moveToX"], states["moveToY"], tower_result.r, tower_result.g, tower_result.b
            )
        )
        return True

    return False


def checkChaosFinish():
    clearOk = client_util.locate_center_on_screen(
        "./screenshots/clearOk.png", confidence=0.75
    )
    if clearOk != None:
        x, y = clearOk
        client_util.move_to(x=x, y=y)
        sleep(600, 800)
        client_util.click(x=x, y=y, button="left")
        sleep(200, 300)
        client_util.move_to(x=x, y=y)
        sleep(200, 300)
        client_util.click(x=x, y=y, button="left")
        return True
    return False


def fightFloor2Boss():
    if client_util.locate_on_screen("./screenshots/bossBar.png", confidence=0.7):
        print("boss bar located")
        utils.press(config["awakening"])


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
    if abs(newX) > config["clickableAreaX"]:
        delta = (abs(newX) > config["clickableAreaX"]) * k
        newX = -config["clickableAreaX"] if newX < 0 else config["clickableAreaX"]
        if newY < 0:
            newY = newY + delta
        else:
            newY = newY - delta

    if abs(newY) > config["clickableAreaY"]:
        delta = (abs(newY) - config["clickableAreaY"]) / k
        newY = -config["clickableAreaY"] if newY < 0 else config["clickableAreaY"]
        if newX < 0:
            newX = newX + delta
        else:
            newX = newX - delta

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
    client_util.click(x=x, y=y, button=config["move"])
    sleep(int(timeMin / 2), int(timeMax / 2))

    # moving in a straight line
    client_util.click(x=x, y=y, button=config["move"])
    sleep(int(timeMin / 2), int(timeMax / 2))
    # sleep(timeMin, timeMax)

    # optional blink here
    if blink:
        utils.press(config["blink"])
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
    #     mouse_util.mouse_down(x=x, y=y, button=config['move'])
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
    client_util.click(x=x, y=y, button=config["move"])
    sleep(200, 250)
    client_util.click(x=x, y=y, button=config["move"])
    sleep(200, 250)
    # mouse_util.click(
    #     x=config["screenCenterX"], y=config["screenCenterY"], button=config["move"]
    # )


def enterPortal():
    # repeatedly move and press g until black screen
    sleep(1100, 1200)
    print("moving to portal x: {} y: {}".format(states["moveToX"], states["moveToY"]))
    enterTime = int(time.time_ns() / 1000000)
    portal_try = enterTime
    while True:
        im = client_util.screenshot(region=(1652, 168, 240, 210))
        r, g, b = im.getpixel((1772 - 1652, 272 - 168))
        if r == 0 and g == 0 and b == 0:
            return

        nowTime = int(time.time_ns() / 1000000)
        if nowTime - enterTime > 30000:
            # FIXME:
            states["instanceStartTime"] = -1
            return
        if nowTime - portal_try > 4500:
            print('Trying to find portal again')
            checkPortal()
            calculateMinimapRelative(states["moveToX"], states["moveToY"])
            print("moving to portal x: {} y: {}".format(states["moveToX"], states["moveToY"]))
            portal_try = nowTime

        if (states["moveToX"] == config["screenCenterX"] and
                states["moveToY"] == config["screenCenterY"]):
            utils.press(config["interact"])
            sleep(100, 120)
        else:
            utils.press(config["interact"])
            client_util.click(
                x=states["moveToX"], y=states["moveToY"], button=config["move"]
            )
            sleep(50, 60)
            utils.press(config["interact"])
            client_util.click(
                x=states["moveToX"], y=states["moveToY"], button=config["move"]
            )
            sleep(50, 60)
            utils.press(config["interact"])


# def enterPortal():
#     # repeatedly move and press g until black screen
#     print("moving to portal x: {} y: {}".format(states["moveToX"], states["moveToY"]))
#     turn = True
#     deflect = 80
#     while True:
#         im = mouse_util.screenshot(region=(1652, 168, 240, 210))
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
#             utils.press(config["interact"])
#             im = mouse_util.screenshot(region=(1652, 168, 240, 210))
#             r, g, b = im.getpixel((1772 - 1652, 272 - 168))
#             if r == 0 and g == 0 and b == 0:
#                 return

#             if (
#                 states["moveToX"] == config["screenCenterX"]
#                 and states["moveToY"] == config["screenCenterY"]
#             ):
#                 utils.press(config["interact"])
#                 sleep(100, 120)
#             else:
#                 mouse_util.click(x=x, y=y, button=config["move"])
#                 sleep(50, 60)
#                 utils.press(config["interact"])
#                 count = count + 1
#             turn = not turn
#     return


def waitForLoading():
    print("loading")
    while True:
        leaveButton = client_util.locate_on_screen(
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
    if client_util.locate_on_screen(
        "./screenshots/died.png", grayscale=True, confidence=0.9
    ):
        states["deathCount"] = states["deathCount"] + 1
        sleep(5000, 5500)
        while (
                client_util.locate_on_screen("./screenshots/resReady.png", confidence=0.7)
                != None
        ):
            client_util.move_to(1275, 454)
            sleep(600, 800)
            client_util.click(1275, 454, button="left")
            sleep(600, 800)
            client_util.move_to(config["screenCenterX"], config["screenCenterY"])
    return


def doRepair():
    if not config["autoRepair"]:
        return

    # Check if repair needed
    if states["deathCount"] % 4 == 1 or states["clearCount"] % 4 == 1 or client_util.locate_on_screen(
        "./screenshots/repair.png",
        grayscale=True,
        confidence=0.5,
        region=(1500, 134, 100, 100),
    ):
        print('Repairing')
        sleep(800, 900)
        utils.press("f1")
        sleep(800, 900)
        client_util.move_to(1182, 654)
        sleep(800, 900)
        client_util.click(1182, 654, button="left")
        sleep(800, 900)
        client_util.move_to(1068, 644)
        sleep(800, 900)
        client_util.click(1068, 644, button="left")
        sleep(800, 900)
        utils.press("esc")
        sleep(800, 900)
        utils.press("esc")
        sleep(800, 900)


def healthCheck():
    x = int(
        config["healthCheckX"]
        + (870 - config["healthCheckX"]) * config["healthPotAtPercent"]
    )
    y = config["healthCheckY"]
    r, g, b = client_util.pixel(x, y)
    # print(x, r, g, b)
    if r < 70 and config["useHealthPot"]:
        leaveButton = client_util.locate_center_on_screen(
            "./screenshots/leave.png",
            grayscale=True,
            confidence=0.7,
            region=config["regions"]["leaveMenu"],
        )
        if leaveButton == None:
            return
        utils.press(config["healthPot"])
        states["healthPotCount"] = states["healthPotCount"] + 1
        return
    return


def sleep(min, max):
    time.sleep(random.randint(min, max) / 1000.0)


def spiral_search():
    minimap = client_util.screenshot(region=config["regions"]["minimap"])  # Top Right
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
        # timeout = mouse_util.screenshot()
        # timeout.save("./timeout/weird" + str(currentTime) + ".png")
        states["badRunCount"] = states["badRunCount"] + 1
        return True
    if currentTime - states["instanceStartTime"] > config["timeLimit"]:
        print("timeout triggered")
        # timeout = mouse_util.screenshot()
        # timeout.save("./timeout/overtime" + str(currentTime) + ".png")
        states["timeoutCount"] = states["timeoutCount"] + 1
        return True
    return False


def main(_argv):
    if FLAGS.mode == 'infinite_chaos':
        infinite_chaos(FLAGS.starting_char)
    elif FLAGS.mode == 'daily':
        daily(FLAGS.chars, FLAGS.starting_char)


if __name__ == "__main__":
    app.run(main)

from collections import namedtuple
from dataclasses import dataclass
import json
from functools import cache
import logging as py_logging
import math
import os
import random
import time
from typing import Dict, List, Optional

from absl import app
from absl import flags
from absl import logging

import coordinates
import utils
from ability import Ability
from config import config

FLAGS = flags.FLAGS
flags.DEFINE_integer('limit', None, 'optional chaos limit per char', lower_bound=1)
flags.DEFINE_integer('chars', 1, '# of chars for daily mode', lower_bound=1)
flags.DEFINE_integer('starting_char', 1, 'starting char', lower_bound=1)
flags.DEFINE_bool('shutdown', False, 'shutdown pc when done')
flags.DEFINE_bool('kill', False, 'kill lostark when done')

MinimapCoord = namedtuple("MinimapCoord", "x y")
ScreenCoord = namedtuple("ScreenCoord", "x y")

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
client_util: Optional[utils.ClientUtil] = None


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
    logging.info(f'Switching to {char=}')
    utils.press('ESC', 2500)
    client_util.move_and_click(*coordinates.SWITCH_CHARACTERS, wait=4000)
    client_util.move_and_click(*coordinates.CHARACTERS[char - 1], wait=2000)
    client_util.move_and_click(*coordinates.CHARACTERS[char - 1], wait=2000)
    client_util.move_and_click(*coordinates.CONNECT, wait=2000)
    client_util.move_and_click(*coordinates.CONNECT, wait=2000)
    client_util.move_and_click(*coordinates.CONNECT_CONFIRM, wait=2000)
    utils.sleep(30000)
    client_util.wait_loading_finish()


def daily(chars, starting_char, limit: Optional[int] = None):
    global states
    daily_states = []
    for char in range(starting_char, starting_char + chars):
        logging.info(f'Starting daily for {char=}')
        states = newStates.copy()
        # switch to char
        if char != starting_char:
            switch_to_char(char)
        infinite_chaos(char, limit=limit)
        client_util.wait_loading_finish()
        daily_states.append(states)
    logging.info(f'Done with dailies')
    for i, state in enumerate(daily_states):
        logging.info(f'Character {i + starting_char}:')
        printResult(state)
        logging.info('----------------------------')


def infinite_chaos(char, limit: Optional[int] = None):
    logging.info(f"Endless Chaos started {char=} {limit=}...")
    char_config = load_config(char)
    logging.info(f"On class {char_config['class']}")
    # save bot start time
    states["botStartTime"] = int(time.time_ns() / 1000000)
    abilities = None
    while True:
        if limit is not None and states["clearCount"] >= limit:
            logging.info('Hit chaos limit')
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
            logging.info("floor1")
            client_util.move_to(x=config["screenCenterX"], y=config["screenCenterY"])
            sleep(200, 300)
            # wait for loading
            waitForLoading()
            if checkTimeout():
                quitChaos()
                continue
            sleep(1000, 1200)
            logging.info("floor1 loaded")

            # saving clean abilities icons
            if abilities is None:
                abilities = load_abilities(char_config)

            # check repair
            doRepair()

            # do floor one
            doFloor1(abilities, char_config)
        elif states["status"] == "floor2":
            logging.info("floor2")
            client_util.move_to(x=config["screenCenterX"], y=config["screenCenterY"])
            sleep(200, 300)
            # wait for loading
            waitForLoading()
            if checkTimeout():
                quitChaos()
                continue
            logging.info("floor2 loaded")
            # do floor two
            doFloor2(abilities, char_config)
        elif states["status"] == "floor3":
            logging.info("floor3")
            client_util.move_to(x=config["screenCenterX"], y=config["screenCenterY"])
            sleep(200, 300)
            # wait for loading
            waitForLoading()
            if checkTimeout():
                quitChaos()
                continue
            logging.info("floor3 loaded")
            # do floor 3
            # trigger start floor 3
            client_util.move_to(x=1045, y=450)
            sleep(100, 120)
            client_util.click(button=config["move"])
            sleep(500, 600)
            doFloor3Portal(abilities, char_config)
            if checkTimeout() or not config["floor3"]:
                quitChaos()
                continue
            doFloor3(abilities, char_config, limit)


def enterChaos():
    logging.info('Entering chaos')
    rightClick = "right"
    if config["move"] == "right":
        rightClick = "left"

    client_util.move_to(x=config["screenCenterX"], y=config["screenCenterY"])
    sleep(200, 300)
    client_util.click(button=rightClick)
    sleep(200, 300)

    if config["shortcutEnterChaos"]:
        client_util.wait_loading_finish()
        sleep(600, 800)
        while True:
            logging.info('Pressing alt-q')
            utils.key_down("alt")
            sleep(600, 800)
            utils.press("q")
            sleep(300, 400)
            utils.key_up("alt")
            sleep(300, 400)
            client_util.move_to(886, 346)
            sleep(600, 800)
            client_util.click(button="left")
            sleep(600, 800)

            enterButton = client_util.locate_center_on_screen(
                "./screenshots/enterButton.png", confidence=0.75
            )
            if enterButton is not None:
                x, y = enterButton
                client_util.move_to(x=x, y=y)
                sleep(600, 800)
                client_util.click(x=x, y=y, button="left")
                break
            else:
                if checkTimeout():
                    logging.info('Entering chaos timeout')
                    return
                client_util.move_to(886, 346)
                sleep(600, 800)
                client_util.click(button="left")
                sleep(600, 800)
    else:
        while True:
            enterHand = client_util.locate_on_screen("./screenshots/enterChaos.png")
            if enterHand is not None:
                logging.info("entering chaos...")
                utils.press(config["interact"])
                break
            sleep(500, 800)
    sleep(600, 800)
    while True:
        acceptButton = client_util.locate_center_on_screen(
            "./screenshots/acceptButton.png", confidence=0.75
        )
        if acceptButton is not None:
            x, y = acceptButton
            client_util.move_to(x=x, y=y)
            sleep(600, 800)
            client_util.click(x=x, y=y, button="left")
            break
        sleep(500, 800)
    states["status"] = "floor1"
    return


def doFloor1(abilities: List[Ability], char_config: Dict):
    # trigger start floor 1
    # mouse_util.move_to(x=845, y=600)
    client_util.move_to(x=530, y=680)
    sleep(400, 500)
    client_util.click(button=config["move"])

    # delayed start for better aoe abiltiy usage at floor1 beginning
    if config["delayedStart"] is not None:
        sleep(config["delayedStart"] - 100, config["delayedStart"] + 100)

    # # move to a side
    # utils.press(config["blink"])
    # sleep(400, 500)

    # mouse_util.mouse_down(random.randint(800, 1120), random.randint(540, 580), button=config['move'])
    # sleep(2000,2200)
    # mouse_util.click(x=960, y=530, button=config['move'])

    # smash available abilities
    portal_minimap_coord = useAbilities(abilities, char_config)

    # bad run quit
    if checkTimeout():
        quitChaos()
        return

    logging.info("floor 1 cleared")
    portal_coord = convert_minimap_to_screen(portal_minimap_coord, dist=100)
    enterPortal(portal_coord)
    if checkTimeout():
        quitChaos()
        return
    states["status"] = "floor2"
    return


def doFloor2(abilities: List[Ability], char_config: Dict):
    client_util.mouse_down(x=1150, y=500, button=config["move"])
    sleep(800, 900)
    client_util.mouse_down(x=960, y=200, button=config["move"])
    sleep(800, 900)
    client_util.click(x=945, y=550, button=config["move"])

    portal_minimap_coord = useAbilities(abilities, char_config)

    # bad run quit
    if checkTimeout():
        quitChaos()
        return

    logging.info("floor 2 cleared")
    portal_coord = convert_minimap_to_screen(portal_minimap_coord, dist=100)
    enterPortal(portal_coord)
    if checkTimeout():
        quitChaos()
        return
    states["status"] = "floor3"

    return


def doFloor3Portal(abilities: List[Ability], char_config: Dict):
    logging.info('Identifying floor 3 portal')
    bossBar = None
    goldMob = False
    normal_mob = False
    for i in range(0, 10):
        goldMob = checkFloor3GoldMob()
        normal_mob = check_red_mob()
        bossBar = client_util.locate_on_screen("./screenshots/bossBar.png", confidence=0.7)
        if normal_mob:
            return
        if goldMob or bossBar is not None:
            break
        sleep(500, 550)

    if not goldMob and bossBar is None and not config["floor3"]:
        return

    if bossBar is not None:
        logging.info("purple boss bar located")
        states["purplePortalCount"] = states["purplePortalCount"] + 1
        utils.press(config["awakening"])
        portal_minimap_coord = useAbilities(abilities, char_config)

        # bad run quit
        if checkTimeout():
            logging.info("special portal timeout")
            quitChaos()
            return

        logging.info("special portal cleared")
        portal_coord = convert_minimap_to_screen(portal_minimap_coord, dist=100)
        if not config["floor3"]:
            return
        enterPortal(portal_coord)
        sleep(800, 900)
    elif normal_mob:
        return
    elif goldMob:
        logging.info("gold mob located")
        states["goldPortalCount"] = states["goldPortalCount"] + 1
        portal_minimap_coord = useAbilities(abilities, char_config)

        # bad run quit
        if checkTimeout():
            logging.info("gold portal timeout")
            quitChaos()
            return

        logging.info("special portal cleared")
        portal_coord = convert_minimap_to_screen(portal_minimap_coord, dist=100)
        if not config["floor3"]:
            return
        enterPortal(portal_coord)
        sleep(800, 900)
    else:
        # hacky quit
        states["instanceStartTime"] = -1
        return

    # bad run quit
    if checkTimeout():
        return


def doFloor3(abilities: List[Ability], char_config: Dict, limit: Optional[int] = None):
    waitForLoading()
    logging.info("real floor 3 loaded")

    if checkTimeout():
        quitChaos()
        return

    useAbilities(abilities, char_config, check_portal=False)

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

    logging.info("Chaos Dungeon Full cleared")
    restartChaos(limit)


def quitChaos():
    # quit
    logging.info("quitting")
    clearOk = client_util.locate_center_on_screen(
        "./screenshots/clearOk.png", confidence=0.75
    )
    if clearOk is not None:
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
    printResult(states)

    return


def restartChaos(limit: Optional[int] = None):
    states["fullClearCount"] = states["fullClearCount"] + 1
    states["clearCount"] = states["clearCount"] + 1
    printResult(states)
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
        if selectLevelButton is not None:
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
        if enterButton is not None:
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
        if acceptButton is not None:
            x, y = acceptButton
            client_util.move_to(x=x, y=y)
            sleep(600, 800)
            client_util.click(x=x, y=y, button="left")
            break
        sleep(500, 800)
    sleep(2000, 2200)
    states["status"] = "floor1"
    return


def printResult(states):
    lastRun = (int(time.time_ns() / 1000000) - states["instanceStartTime"]) / 1000
    avgTime = int(
        ((int(time.time_ns() / 1000000) - states["botStartTime"]) / 1000)
        / states["clearCount"]
    )
    if states["instanceStartTime"] != -1:
        states["minTime"] = int(min(lastRun, states["minTime"]))
        states["maxTime"] = int(max(lastRun, states["maxTime"]))
    logging.info(
        "Total runs completed: {}, full clears: {}, total death: {}, half runs: {}, timeout runs: {}, ".format(
            states["clearCount"],
            states["fullClearCount"],
            states["deathCount"],
            states["badRunCount"],
            states["timeoutCount"],
        )
    )
    logging.info(
        "Average time: {}, fastest time: {}, slowest time: {}".format(
            avgTime,
            states["minTime"],
            states["maxTime"],
        )
    )
    logging.info(
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


def useAbilities(abilities: List[Ability],
                 char_config: Dict,
                 check_portal: Optional[bool] = True) -> Optional[MinimapCoord]:
    while True:
        diedCheck()
        healthCheck(char_config)
        if checkTimeout():
            return

        # check elite and mobs
        if states["status"] == "floor1" and (red_mob := check_red_mob()):
            move_to_minimap_coord(red_mob, 200, 300, False, char_config)
        elif states["status"] == "floor2" and (elite := check_elite()):
            move_to_minimap_coord(elite, 750, 850, False, char_config)
        elif states["status"] == "floor2" and (red_mob := check_red_mob()):
            move_to_minimap_coord(red_mob, 400, 500, False, char_config)
        elif states["status"] == "floor3" and checkChaosFinish():
            return
        elif states["status"] == "floor3" and (elite := check_elite()):
            move_to_minimap_coord(elite, 200, 300, False, char_config)
            if config["useAwakening"]:
                logging.info('using awakening')
                utils.press(config["awakening"])

        # cast sequence
        for ability_index, ability in enumerate(abilities):
            diedCheck()
            healthCheck(char_config)

            # check portal
            if (check_portal and
                ability_index % 2 == 0 and
                states["status"] in ("floor1", "floor2", "floor3") and
                    (portal_coords := checkPortal())):
                client_util.click(
                    x=config["screenCenterX"],
                    y=config["screenCenterY"],
                    button=config["move"],
                )
                sleep(100, 150)
                return checkPortal() or portal_coords

            # click rift core
            if states["status"] == "floor3":
                clickTower()

            # check high-priority mobs
            if states["status"] == "floor2" and (boss := checkFloor2Boss()):
                move_to_minimap_coord(boss, 950, 1050, True, char_config)
                fightFloor2Boss()
            # floor3 checks take long time, don't do it after every ability
            elif states["status"] == "floor3" and ability_index % 3 == 0:
                # check all pixels in one spiral
                gold, red, tower, elite = check_spiral_predicates(
                    [is_gold_mob, is_red_mob, is_tower_pixel, is_elite_mob])
                if gold.found:
                    left, top, _w, _h = config["regions"]["minimap"]
                    coord = MinimapCoord(left + gold.rel_x, top + gold.rel_y)
                    logging.info(
                        "gold {}, r: {} g: {} b: {}".format(coord, gold.r, gold.g, gold.b)
                    )
                    move_to_minimap_coord(coord, 500, 600, False, char_config)
                elif tower_coord := checkFloor3Tower(tower):
                    logging.info('Zooming to tower')
                    for i in range(3):
                        logging.info('Random moving to tower')
                        randomMove(tower_coord)
                        # search again since we moved
                        tower, = check_spiral_predicates([is_tower_pixel])
                        tower_coord = checkFloor3Tower(tower)
                        if tower_coord:
                            move_to_minimap_coord(tower_coord, 1200, 1300, True, char_config)
                            sleep(400, 420)
                            clickTower()
                        else:
                            logging.info('Lost the tower, try later')
                            break
                elif red.found:
                    left, top, _w, _h = config["regions"]["minimap"]
                    red_coord = MinimapCoord(left + red.rel_x, top + red.rel_y)
                    logging.info("red mob {}, r: {} g: {} b: {}".format(red_coord, red.r, red.g, red.b))
                    move_to_minimap_coord(red_coord, 200, 300, False, char_config)
                elif boss := checkFloor2Boss():
                    move_to_minimap_coord(boss, 800, 900, True, char_config)

            # cast spells
            checkCDandCast(ability)

        # 防止卡先试试这样
        if states["status"] == "floor3" and not check_elite():
            randomMove()


def checkCDandCast(ability: Ability):
    if client_util.locate_on_screen(
        ability.image, region=config["regions"]["abilities"], confidence=0.995
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
            utils.key_down(ability.key)
            while now_ms - start_ms < ability.hold_time:
                utils.key_down(ability.key)
                now_ms = int(time.time_ns() / 1000000)
            # while mouse_util.locate_on_screen(
            #     ability["image"], region=config["regions"]["abilities"]
            # ):
            #     utils.key_down(ability["key"])
            utils.key_up(ability.key)
        else:
            # 瞬发 ability
            utils.press(ability.key)
            while client_util.locate_on_screen(
                ability.image, region=config["regions"]["abilities"]
            ):
                utils.press(ability.key)


def checkPortal() -> Optional[MinimapCoord]:
    # check portal image
    portal = client_util.locate_center_on_screen(
        "./screenshots/portal.png", region=config["regions"]["minimap"], confidence=0.7
    )
    if portal is not None:
        x, y = portal
        coord = MinimapCoord(x, y)
        logging.info("portal image {}".format(coord))
        return coord

    for r, g, b, rel_x, rel_y in spiral_search():
        if (r in range(75, 86) and g in range(140, 151) and b in range(250, 256)) or (
            r in range(120, 131) and g in range(210, 221) and b in range(250, 256)
        ):
            left, top, _w, _h = config["regions"]["minimap"]
            coord = MinimapCoord(left + rel_x, top + rel_y)
            logging.info("portal pixel {}, r: {} g: {} b: {}".format(coord, r, g, b))
            return coord
    return None


def is_elite_mob(r, g, b):
    return r in range(200, 216) and g in range(125, 151) and b in range(30, 61)


def check_elite() -> Optional[MinimapCoord]:
    for r, g, b, rel_x, rel_y in spiral_search():
        if is_elite_mob(r, g, b):
            left, top, _w, _h = config["regions"]["minimap"]
            coord = MinimapCoord(left + rel_x, top + rel_y)
            logging.info(
                "elite coord: {} r: {} g: {} b: {}".format(
                    coord, r, g, b
                )
            )
            return coord
    return None


def is_red_mob(r, g, b):
    return r in range(200, 256) and g in range(10, 41) and b in range(10, 41)


def check_red_mob() -> Optional[MinimapCoord]:
    for r, g, b, rel_x, rel_y in spiral_search():
        if is_red_mob(r, g, b):
            left, top, _w, _h = config["regions"]["minimap"]
            coord = MinimapCoord(left + rel_x, top + rel_y)
            logging.info(
                "red mob coord: {} r: {} g: {} b: {}".format(
                    coord, r, g, b
                )
            )
            return coord
    return None


def is_gold_mob(r, g, b):
    return r in range(240, 256) and g in range(180, 201) and b in range(0, 41)


def checkFloor3GoldMob():
    for r, g, b, rel_x, rel_y in spiral_search():
        if is_gold_mob(r, g, b):
            left, top, _w, _h = config["regions"]["minimap"]
            states["moveToX"] = left + rel_x
            states["moveToY"] = top + rel_y
            logging.info(
                "gold x: {} y: {}, r: {} g: {} b: {}".format(
                    states["moveToX"], states["moveToY"], r, g, b
                )
            )
            return True
    return False


def checkFloor2Boss() -> Optional[MinimapCoord]:
    fightFloor2Boss()
    bossLocation = client_util.locate_center_on_screen(
        "./screenshots/boss.png", confidence=0.65
    )
    if bossLocation is not None:
        bossLocation = tuple(bossLocation)
        left, top = bossLocation
        coord = MinimapCoord(left, top)
        logging.info("boss {}".format(coord))
        return coord
    return None


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
#             logging.info(
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
    if riftCore1 is not None:
        x, y = riftCore1
        if y > 650 or x < 400 or x > 1500:
            return
        states["moveToX"] = x
        states["moveToY"] = y + 190
        client_util.click(x=states["moveToX"], y=states["moveToY"], button=config["move"])
        logging.info("clicked rift core")
        sleep(100, 120)
        utils.press(config["meleeAttack"])
        sleep(300, 320)
        utils.press(config["meleeAttack"])
        sleep(900, 960)
        utils.press(config["meleeAttack"])
    elif riftCore2 is not None:
        x, y = riftCore2
        if y > 650 or x < 400 or x > 1500:
            return
        states["moveToX"] = x
        states["moveToY"] = y + 190
        client_util.click(x=states["moveToX"], y=states["moveToY"], button=config["move"])
        logging.info("clicked rift core")
        sleep(100, 120)
        utils.press(config["meleeAttack"])
        sleep(300, 320)
        utils.press(config["meleeAttack"])
        sleep(900, 960)
        utils.press(config["meleeAttack"])


def is_tower_pixel(r, g, b):
    return ((r in range(240, 245) and r in range(60, 65) and r in range(65, 70)) or
            (r in range(160, 165) and g in range(160, 165) and b in range(160, 165)) or
            (r in range(125, 130) and g in range(95, 100) and b in range(100, 105)))


def checkFloor3Tower(tower_result: SpiralResult) -> Optional[MinimapCoord]:
    tower = client_util.locate_center_on_screen(
        "./screenshots/tower.png", region=config["regions"]["minimap"], confidence=0.7
    )
    if tower is not None:
        x, y = tower
        coord = MinimapCoord(x, y - 1)
        logging.info("tower image {}".format(coord))
        return coord

    if tower_result.found:
        left, top, _w, _h = config["regions"]["minimap"]
        x = left + tower_result.rel_x
        y = top + tower_result.rel_y
        # pos offset
        if tower_result.r in range(125, 130) and tower_result.g in range(95, 100) and tower_result.b in range(100, 105):
            y += 7
        elif tower_result.r in range(160, 165) and tower_result.g in range(160, 165) and tower_result.b in range(160, 165):
            y -= 13
        coord = MinimapCoord(x, y)
        logging.info(
            "tower pixel pos {}, r: {} g: {} b: {}".format(
                coord, tower_result.r, tower_result.g, tower_result.b
            )
        )
        return coord

    return None


def checkChaosFinish() -> bool:
    clearOk = client_util.locate_center_on_screen(
        "./screenshots/clearOk.png", confidence=0.75
    )
    if clearOk is not None:
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
        logging.info("boss bar located")
        utils.press(config["awakening"])


def convert_minimap_to_screen(minimap: MinimapCoord, dist: int = 200) -> ScreenCoord:
    selfLeft = config["minimapCenterX"]
    selfTop = config["minimapCenterY"]
    x = minimap.x
    y = minimap.y
    if abs(selfLeft - x) <= 3 and abs(selfTop - y) <= 3:
        return ScreenCoord(config["screenCenterX"], config["screenCenterY"])

    x = x - selfLeft
    y = y - selfTop
    # logging.info("relative to center pos x: {} y: {}".format(x, y))

    if y < 0:
        dist = -dist

    if x == 0:
        if y < 0:
            newY = y - abs(dist)
        else:
            newY = y + abs(dist)
        return ScreenCoord(0 + config["screenCenterX"], int(newY) + config["screenCenterY"])
    if y == 0:
        if x < 0:
            newX = x - abs(dist)
        else:
            newX = x + abs(dist)
        return ScreenCoord(int(newX) + config["screenCenterX"], 0 + config["screenCenterY"])

    k = y / x
    # newX = x + dist
    newY = y + dist
    # newY = k * (newX - x) + y
    newX = (newY - y) / k + x

    # logging.info("before confining newX: {} newY: {}".format(int(newX), int(newY)))
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

    return ScreenCoord(int(newX) + config["screenCenterX"], int(newY) + config["screenCenterY"])


def move_to_minimap_coord(minimap_coord: MinimapCoord, time_min: int, time_max: int, blink: bool, char_config: Dict):
    screen_coord = convert_minimap_to_screen(minimap_coord)

    x = screen_coord.x
    y = screen_coord.y
    # move one step to direction
    if x == config["screenCenterX"] and y == config["screenCenterY"]:
        return
    logging.info("moving to pos x: {} y: {}".format(states["moveToX"], states["moveToY"]))

    # moving in a straight line
    client_util.click(x=x, y=y, button=config["move"])
    sleep(int(time_min / 2), int(time_max / 2))

    # moving in a straight line
    client_util.click(x=x, y=y, button=config["move"])
    sleep(int(time_min / 2), int(time_max / 2))
    # sleep(timeMin, timeMax)

    # optional blink here
    if blink and not is_gunlancer(char_config):
        utils.press(config["blink"])
        sleep(100, 150)


def randomMove(minimap_coord: Optional[MinimapCoord] = None) -> None:
    from_x = config["screenCenterX"] - config["clickableAreaX"]
    to_x = config["screenCenterX"] + config["clickableAreaX"]
    from_y = config["screenCenterY"] - config["clickableAreaY"]
    to_y = config["screenCenterY"] + config["clickableAreaY"]

    x = random.randint(from_x, to_x)
    if minimap_coord:
        # dont random move to same quadrant
        if (x < config["screenCenterX"]) == (minimap_coord.x < config["minimapCenterX"]):
            # if both have same signs, make sure y's have different signs
            if minimap_coord.y < config["minimapCenterY"]:
                from_y = config["screenCenterY"]
            else:
                to_y = config["screenCenterY"]

    y = random.randint(from_y, to_y)

    logging.info("random move to x: {} y: {}".format(x, y))
    client_util.click(x=x, y=y, button=config["move"])
    sleep(200, 250)
    client_util.click(x=x, y=y, button=config["move"])
    sleep(300, 350)
    # mouse_util.click(
    #     x=config["screenCenterX"], y=config["screenCenterY"], button=config["move"]
    # )


def enterPortal(portal_coord: ScreenCoord) -> None:
    # repeatedly move and press g until black screen
    sleep(1100, 1200)
    logging.info("moving to portal {}".format(portal_coord))
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
            logging.info('Trying to find portal again')
            if portal_minimap_coord := checkPortal():
                portal_coord = convert_minimap_to_screen(portal_minimap_coord, dist=100)
                logging.info("moving to portal {}".format(portal_coord))
            portal_try = nowTime

        if portal_coord.x == config["screenCenterX"] and portal_coord.y == config["screenCenterY"]:
            utils.press(config["interact"])
            sleep(100, 120)
        else:
            utils.press(config["interact"])
            client_util.click(x=portal_coord.x, y=portal_coord.y, button=config["move"])
            sleep(50, 60)
            utils.press(config["interact"])
            client_util.click(x=portal_coord.x, y=portal_coord.y, button=config["move"])
            sleep(50, 60)
            utils.press(config["interact"])


def waitForLoading():
    logging.info("loading")
    while True:
        leaveButton = client_util.locate_on_screen(
            "./screenshots/leave.png",
            grayscale=True,
            confidence=0.7,
            region=config["regions"]["leaveMenu"],
        )
        if leaveButton is not None:
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
        while client_util.locate_on_screen("./screenshots/resReady.png", confidence=0.7) is not None:
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
        logging.info('Repairing')
        sleep(800, 900)
        utils.press("f1")
        sleep(800, 900)
        client_util.move_to(1130, 660)
        sleep(800, 900)
        client_util.click(1130, 660, button="left")
        sleep(800, 900)
        client_util.move_to(1068, 644)
        sleep(800, 900)
        client_util.click(1068, 644, button="left")
        sleep(800, 900)
        utils.press("esc")
        sleep(800, 900)
        utils.press("esc")
        sleep(800, 900)


def is_berserker(char_config: Dict) -> bool:
    return char_config['class'] == 'Berserker'


def is_gunlancer(char_config: Dict) -> bool:
    return char_config['class'] == 'Gunlancer'


def healthCheck(char_config: Dict):
    if is_berserker(char_config):
        percent_check = 0.15
    else:
        percent_check = config["healthPotAtPercent"]
    x = int(
        config["healthCheckX"]
        + (870 - config["healthCheckX"]) * percent_check
    )
    y = config["healthCheckY"]
    r, g, b = client_util.pixel(x, y)
    # logging.info(x, r, g, b)
    if r < 70 and config["useHealthPot"]:
        leaveButton = client_util.locate_center_on_screen(
            "./screenshots/leave.png",
            grayscale=True,
            confidence=0.7,
            region=config["regions"]["leaveMenu"],
        )
        if leaveButton is None:
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
        logging.info("hacky timeout")
        # timeout = mouse_util.screenshot()
        # timeout.save("./timeout/weird" + str(currentTime) + ".png")
        states["badRunCount"] = states["badRunCount"] + 1
        return True
    if currentTime - states["instanceStartTime"] > config["timeLimit"]:
        logging.info("timeout triggered")
        # timeout = mouse_util.screenshot()
        # timeout.save("./timeout/overtime" + str(currentTime) + ".png")
        states["timeoutCount"] = states["timeoutCount"] + 1
        return True
    return False


def test_ability(char: int, ability: int):
    setup()
    char_config = load_config(char)
    abilities = load_abilities(char_config)
    checkCDandCast(abilities[ability])


def setup():
    global client_util
    file_handler = py_logging.FileHandler(filename='out.log', mode='w')
    file_handler.setFormatter(logging.PythonFormatter())
    logging.get_absl_logger().addHandler(file_handler)
    client_util = utils.ClientUtil()


def main(_argv):
    setup()
    daily(FLAGS.chars, FLAGS.starting_char, limit=FLAGS.limit)
    if FLAGS.shutdown:
        os.system('shutdown /s /t 10')
    elif FLAGS.kill:
        os.system("taskkill /im LOSTARK.exe")


if __name__ == "__main__":
    app.run(main)

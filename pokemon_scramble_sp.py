#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Erimus'
# 这个版本用的uiautomator
# https://github.com/openatx/uiautomator2
# 先要把模拟器下adb所在目录加入环境变量
# 确认下截图为720x1280（设置/分辨率/自定义）
# 使用极速模式 DirectX 颜色和其它模式会有所不同
# 先启动夜神模拟器，然后运行本程序。
# TODO 因为每日任务需要手动领一下，所以齿轮装满还未自动处理。

import uiautomator2
import subprocess
import re
from toolbox import set_log, FS, CSS, Timer, time, countdown, formatJSON, beep
from random import randint as rdm

# ═══════════════════════════════════════════════
d = im_pixel = ''
roundTm = Timer()
roundCount = 1
battleTm = Timer()  # 战斗计时 超过一定时间（遇到boss）出技能
otherCount = 0      # [其它]界面出现的次数

explore = 1         # 是否探索新关卡/0为自动重复进行指定关卡
stage = 1           # 默认选择第N个关卡

stageY = 680 + (100 * stage)
# ═══════════════════════════════════════════════


def get_device():
    process = subprocess.Popen('adb devices', shell=True, stdout=subprocess.PIPE)
    r = process.stdout.read()
    device = re.findall(r'127\.0\.0\.1:\d+', str(r))[0]
    print(f'device: {device}')

    global d
    d = uiautomator2.connect_adb_wifi(device)  # connect to device
    log.info(formatJSON(d.info))


def start_game(package_name, force=False):
    get_device()
    current = d.app_current().get('package')
    log.info(f'Current App: {current}')
    sess = d.session(package_name, attach=True)  # 未启动的话会启动
    if not sess.running() or force:
        log.info(f'Session Running: {sess.running()} | Force Restart: {force}')
        sess.restart()
        log.warning(f'Restart: {package_name}')
        countdown(120)


def screen_capture(save=0):
    global im_pixel
    tm = Timer()
    im = d.screenshot()
    im_pixel = im.load()
    # im.show()
    if save:
        im.save('screen_shot/sc.png')
    log.info(CSS(f'{"Screen capture took":-<25s} {tm.gap()}', 'lk'))


def check_point(pos, color, tolerance=20, showLog=0):  # 棋子取色精确范围
    r, g, b = color
    i = tolerance  # 近似范围
    src = im_pixel[tuple(pos)]
    if showLog:
        log.info(CSS(f'{pos} = {src}', 'lk'))
    return ((r - i < src[0] < r + i)
            and (g - i < src[1] < g + i)
            and (b - i < src[2] < b + i))


def check_match(*conditionList, tolerance=20, showLog=0):
    # 标准输入格式为(([x,y],[r,g,b]),...)
    if not isinstance(conditionList[0], tuple):  # 简化输入 [x,y],[r,g,b] 转换
        conditionList = [conditionList]
    for pos, color in conditionList:
        if not check_point(pos, color, tolerance=tolerance, showLog=showLog):
            return False
    return True


def click(x, y, info='', wait=0):
    if info:
        log.info(CSS(info))
    d.click(x, y)
    time.sleep(wait)


def debug():
    time.sleep(3)
    screen_capture(save=1)
    raise


# ═══════════════════════════════════════════════


class UI():

    def home(self):  # 等待出击
        return check_match(([100, 200], [38, 172, 207]),     # 选单
                           ([360, 1170], [40, 165, 211]),    # 冒险上的蓝色方块
                           ([360, 1182], [255, 255, 255]))  # 冒险上的白色区域

    def select_stage(self):  # 选择关卡
        return check_match(([666, 150], [243, 207, 10]),     # 右上角123
                           ([420, 1240], [251, 118, 146]))  # 返回按钮红色

    def stone(self):  # 矿石
        return check_match(([360, 130], [163, 245, 245]),    # 蓝框顶部
                           ([420, 1210], [251, 116, 146]))  # 返回按钮红色

    def battle(self):  # 战斗中
        return check_match(([55, 1140], [40, 165, 211]),   # 替换左耳尖
                           ([145, 1150], [40, 165, 211]),  # 替换右耳尖
                           ([360, 1236], [0, 160, 255]))  # 底部蓝色蓄力条


ui = UI()


# ═══════════════════════════════════════════════


def has_surprise():
    firstMarkPostion = (200, 260)  # 第一个感叹号左上角的位置
    xGap, yGap = 210, 240  # 间距
    size = (40, 40)  # 感叹号的大小
    searchRange = []
    for h in range(3):
        for v in range(2):
            searchRange.append({
                'startX': firstMarkPostion[0] + h * xGap,
                'startY': firstMarkPostion[1] + v * yGap,
                'endX': firstMarkPostion[0] + h * xGap + size[0],
                'endY': firstMarkPostion[1] + v * yGap + size[1],
            })
    # print(formatJSON(searchRange))
    for r in searchRange:
        for x in range(r['startX'], r['endX']):
            for y in range(r['startY'], r['endY']):
                if check_match([x, y], [241, 17, 71], tolerance=10, showLog=0):  # 找到红色
                    if check_match([x + 10, y], [255, 255, 255], tolerance=5, showLog=0):  # 找到右侧白色
                        log.info(CSS(f'Found Surprise Mark ❗ {x}|{y}', 'r'))
                        return x, y


def stone_page():
    loop_count = 0
    while True:
        loop_count += 1
        surprise = has_surprise()
        if surprise:  # 如果有完成的矿石
            sx, sy = surprise
            click(sx - 60, sy + 60, CSS('领取完成的矿石', 'y'), wait=3)
            click(360, 810, CSS('确认领取', 'y'), wait=5)
            while True:
                loop_count += 1
                screen_capture()
                if ui.stone() or loop_count > 100:
                    break
                click(360, 810, CSS('确认道具', 'y'), wait=3)
            log.info(CSS('矿石领取完成', 'g'))
            # 开发新的矿石
            newX = 360 if sx < 270 else 150  # 避开刚领取的矿石
            click(newX, 300, CSS('点击矿石', 'y'), wait=3)
            click(360, 800, CSS('开始加工', 'y'), wait=10)
            click(360, 1120, CSS('矿石界面 关闭', 'y'), wait=3)
        elif check_match(([360, 1055], [0, 146, 237])):  # 垃圾桶盖子
            click(360, 1055, CSS('矿石界面（有垃圾桶）', 'y'), wait=5)   # 点垃圾桶
            click(500, 700, CSS('确认丢弃', 'y'), wait=5)
        else:
            click(360, 1200, CSS('矿石界面 关闭', 'y'), wait=3)

        screen_capture()
        if ui.home():
            break

        if loop_count >= 100:
            raise


def stage_page():
    loop_count = 0
    while True:
        loop_count += 1
        # 探测 & 有羽毛
        if explore and check_match([540, 880], [49, 157, 207]):
            click(540, 880, '点击探测', wait=5)

        # 选择已有关卡
        elif check_match([460, 720], [247, 171, 77]):  # 出击按钮
            click(360, 720, '出击', wait=5)

        # 投放羽毛界面
        elif check_match([450, 960], [255, 255, 255]):
            rx, ry = rdm(80, 640), rdm(310, 870)  # 全地图范围
            # rx, ry = rdm(280, 480), rdm(800, 880)  # 指定地区
            click(rx, ry, f'搜索 {rx} {ry}', wait=5)

        # 选择关卡 这里颠倒顺序因为无判断条件
        else:
            click(320, stageY, f'选择关卡 {stage}', wait=3)

        # 确认进入战斗 退出本环节
        if ui.battle():  # 底部蓝色蓄力条
            global battleTm, roundCount
            log.info(CSS('战斗开始！', 'r'))
            battleTm = Timer()  # 开始战斗计时
            roundCount += 1
            break

        screen_capture()  # 更新截图
        if loop_count >= 100:
            raise


def send_pokemon():
    log.info('===== 进入宝可梦一览 =====')
    loop_count = 0
    send = 0
    screen_capture()  # 获取截图
    if check_match(([515, 175], [213, 231, 233]),           # 正三角左上白色
                   ([515, 195], [31, 145, 250])):  # 正三角左下蓝色
        click(530, 190, '倒序排列')
    while send < 2:
        loop_count += 1
        screen_capture()  # 获取截图
        if check_match(([360, 15], [130, 227, 247]),              # 精灵球背景
                       ([420, 1200], [250, 120, 150])):  # 底部的关闭
            click(210, 180, '选择100', wait=2)
        elif check_match([520, 1200], [89, 247, 146]):  # 赠送按钮
            click(360, 1200, '送往协会', wait=2)
        elif check_match([520, 750], [79, 242, 137]):  # 确定按钮
            click(520, 750, '确认', wait=5)
        elif check_match([400, 730], [84, 242, 141]):  # OK按钮
            click(360, 720, '回执', wait=2)
            send += 0.5  # 回执会收到两份
            log.info(f'已送出宝可梦 {CSS(int(send//1*100))}')
        elif check_match(([460, 700], [251, 132, 159])):  # 宝可梦已送完的情况
            click(360, 700, '未选择宝可梦', wait=2)
            log.info(f'宝可梦已送完')
            click(360, 310, '转到力量齿轮页面（唤出返回按钮）', wait=2)
            send += 99  # 退出
        if loop_count >= 100:
            raise

    # 关闭界面
    while True:
        screen_capture()  # 获取截图
        if check_match(([420, 1200], [247, 124, 151])):  # 红色返回按钮
            click(360, 1180, '退出宝可梦一览')
            return


# ═══════════════════════════════════════════════


def play_game():  # 寻找起点和终点坐标

    screen_capture()  # 获取截图

    global otherCount

    # 等待界面
    if ui.home():  # 冒险上的白色区域
        log.info(FS.rainbow("=" * 40))
        log.info(f'Round: {CSS(roundCount)} | Last used: {CSS(roundTm.gap())}')
        otherCount = 0
        click(360, 1120, CSS('等待界面 点击冒险按钮', 'g'), wait=3)

    # 关卡选择
    elif ui.select_stage():
        log.info(CSS('关卡选择'))
        stage_page()

    # 战斗中
    elif ui.battle():
        log.info(CSS(f'战斗中 {battleTm.total()}', 'r'))
        if float(battleTm.total()) > 40:  # 战斗超过一定时间，可能到达boss处。
            click(620, 1180)  # 技能
            click(320, 640)  # 最下面的关卡
        time.sleep(5)  # 按太快了影响走路速度

    # 矿石界面
    elif ui.stone():
        log.info(CSS('===== 进入矿石界面 =====', 'y'))
        stone_page()

    # 宝可梦过多
    elif check_match(([490, 715], [75, 244, 139]),  # 一览按钮
                     ([440, 820], [252, 116, 147])):  # 返回按钮
        log.warning('宝可梦过多')
        click(360, 710, '进入一览', wait=5)  # 确定丢弃
        send_pokemon()

    # 战斗结束
    else:
        otherCount += 1
        click(360, 1000, CSS(f'其它 {otherCount}', 'c'), wait=1)  # 需防止在关卡选择界面误点击

    if otherCount > 200:
        otherCount = 0
        raise


# ═══════════════════════════════════════════════


def main():

    package_name = 'jp.pokemon.pokemonscrambleSP'
    start_game(package_name)

    # screen_capture(save=1)  # 测试用截屏
    # print(d.app_current())
    # return

    while True:
        try:
            play_game()
        except Exception:
            # restart game
            try:
                start_game(package_name, force=True)
            except Exception as e:
                beep(1)
                raise e


# ═══════════════════════════════════════════════


if __name__ == '__main__':

    log = set_log(level='INFO')
    main()

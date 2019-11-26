#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Erimus'
'''
这个是adb版本，响应很慢，弃用。
'''
# 先要把模拟器下adb所在目录加入环境变量
# 确认下截图为720x1280（设置/分辨率/自定义）
# 使用极速模式 DirectX 颜色和其它模式会有所不同

import os
import sys
import subprocess
import time
from PIL import Image
from io import BytesIO
import logging as log
import re

# ═══════════════════════════════════════════════
log.basicConfig(level=log.INFO,
                format=('[%(asctime)s] %(message)s'),
                datefmt='%m-%d %H:%M:%S')
screenshot_way = 2
im_pixel = ''
adb = ''
w, h = 720, 1280
roundStart = time.time()
# ═══════════════════════════════════════════════


def check_screenshot_method():  # 检查获取截图的方式
    global screenshot_way
    if (screenshot_way < 0):
        log.info('暂不支持当前设备')
        sys.exit()
    binary_screenshot = pull_screenshot()
    try:
        Image.open(BytesIO(binary_screenshot)).load()  # 直接使用内存IO
        log.info('Capture Method: {}'.format(screenshot_way))
    except Exception:
        screenshot_way -= 1
        check_screenshot_method()


def pull_screenshot():  # 获取截图
    global screenshot_way
    if screenshot_way in [1, 2]:
        process = subprocess.Popen(
            f'{adb} shell screencap -p',  # png
            shell=True, stdout=subprocess.PIPE)
        screenshot = process.stdout.read()
        if screenshot_way == 2:
            binary_screenshot = screenshot.replace(b'\r\n', b'\n')
        else:
            binary_screenshot = screenshot.replace(b'\r\r\n', b'\n')
        return binary_screenshot
    elif screenshot_way == 0:
        os.system(f'{adb} shell screencap -p /sdcard/autojump.png')
        os.system(f'{adb} pull /sdcard/autojump.png .')


# ═══════════════════════════════════════════════


def click(x, y):
    os.system(f'{adb} shell input tap {x} {y}')


def check_match(pos, targetColor):  # 棋子取色精确范围
    r, g, b = targetColor
    i = 20  # 近似范围
    src = im_pixel[tuple(pos)]
    log.info(f'{pos} = {src}')
    return ((r - i < src[0] < r + i)
            and (g - i < src[1] < g + i)
            and (b - i < src[2] < b + i))


def check_status():  # 寻找起点和终点坐标
    start = time.time()
    # 获取截图
    global im_pixel
    binary_screenshot = pull_screenshot()
    # print(binary_screenshot)
    im = Image.open(BytesIO(binary_screenshot))
    im_pixel = im.load()
    # im.show()
    # im.save('sc.png')
    print(f'Screen capture used: {time.time()-start}')

    start = time.time()
    stageY = 680 + (100 * 3)  # 第N个关卡
    # 等待界面
    if (check_match([100, 200], [38, 172, 207])  # 选单
        and check_match([360, 1170], [40, 165, 211])  # 冒险上的蓝色方块
            and check_match([360, 1182], [255, 255, 255])):  # 冒险上的白色区域

        global roundStart
        log.info(f'{"="*30} {(time.time()-roundStart):.2f}')
        roundStart = time.time()
        log.info('等待界面')
        click(360, 1120)  # 按冒险按钮

    # 关卡选择
    elif (check_match([666, 150], [243, 207, 10])  # 右上角123
          and check_match([420, 1240], [251, 118, 146])):  # 返回按钮红色
        log.info('关卡选择')
        click(320, stageY)  # 最下面的关卡
        click(360, 720)  # 点出击

    # 出击
    elif (check_match([470, 710], [251, 213, 166])  # 出击按钮高光
            and check_match([470, 720], [247, 171, 77])):  # 出击按钮黄色
        log.info('出击')
        click(360, 720)  # 点出击

    # 战斗中
    elif (check_match([55, 1140], [40, 165, 211])  # 替换左耳尖
            and check_match([145, 1150], [40, 165, 211])  # 替换右耳尖
            and check_match([360, 1236], [0, 160, 255])):  # 底部蓝色横条
        log.info('战斗中')
        click(320, stageY)  # 最下面的关卡
        click(620, 1180)  # 技能

    # 矿石界面
    elif (check_match([420, 1200], [255, 187, 203])  # 返回按钮高光
            and check_match([420, 1210], [251, 116, 146])):  # 返回按钮红色
        if check_match([360, 1055], [0, 146, 237]):  # 垃圾桶盖子
            log.info('矿石界面（有垃圾桶）')
            click(360, 1055)  # 丢弃
            click(500, 700)  # 确定丢弃
        else:
            log.info('矿石界面')
            click(360, 1200)  # 关闭

    # 确认丢弃
    elif (check_match([300, 700], [251, 116, 146])  # 取消红色
            and check_match([420, 700], [77, 245, 135])):  # 确定绿色
        log.info('确认丢弃')
        click(500, 700)  # 确定丢弃

    # 宝可梦过多
    elif (check_match([490, 715], [75, 244, 139])  # 一览按钮
            and check_match([440, 820], [252, 116, 147])):  # 返回按钮
        log.info('宝可梦过多')
        # click(450, 890)  # 确定丢弃
        os.system('D:\\Music\\Ringtones\\1up.caf')
        raise

    # 战斗结束
    else:
        log.info('其它')
        click(320, stageY)  # 最下面的关卡
        click(320, stageY)  # 最下面的关卡
        click(320, stageY)  # 最下面的关卡
    print(f'Click used: {time.time()-start}')


# ═══════════════════════════════════════════════


def main():
    process = subprocess.Popen('adb devices', shell=True, stdout=subprocess.PIPE)
    r = process.stdout.read()
    device = re.findall(r'127\.0\.0\.1:\d+', str(r))[0]
    print(f'device: {device}')
    global adb
    adb = f'adb -s {device}'

    check_screenshot_method()  # 检查截图

    while True:
        check_status()
        # time.sleep(2)


# ═══════════════════════════════════════════════


if __name__ == '__main__':
    main()

from PIL import ImageGrab, Image
import random
import csv
import copy
import pandas as pd
import pyautogui
import collections
import cv2
import numpy as np
from itertools import product

random.seed(0)

HIGHT, WIDTH = 15, 23

# ! TODO
# スクショ範囲を実行時に指定
# 1マスのサイズと左上の初期位置を実行時に指定する
# durationを変更可能にする

# --init: オプションで各座標を取得していく
# argparseで諸々設定する

CELL_SIZE = 25
INIT_HIGHT, INIT_WIDTH = 146, 723

def get_color(r, g, b):

    # gray or blank
    if abs(r-g) < 3 and abs(r-b) < 3 and abs(g-b) < 3:
        if r >= 230 and g >= 230 and b >= 230:  return 'blank'
        elif r < 230 and g < 230 and b < 230:   return 'gray'

    # pink or purple
    if g < r and g < b:
        if g < 110:         return 'purple'
        elif g >= 110:      return 'pink'

    # red or yellow or
    # brown or orange
    if b < r and b <= g:
        # brown or orange
        if b < 10:
            if g < 110:     return 'brown'
            elif g >= 110:  return 'orange'
        elif b >= 10:
            if g < 120:     return 'red'
            elif g >= 120:  return 'yellow'
    
    # blue or green or cyan
    if r < b and r < g:
        # blue or green
        if r < 15:
            if b < 15:      return 'green'
            elif b >= 15:   return 'blue'
        elif r >= 15:       return 'cyan'

# 上下左右の一番近い色を取得
def get_udlr_colors(color_mat, row, col):

    udlr_colors = [None, None, None, None]
    uldr_coords = [[], [], [], []]
    
    # 上下左右に色があるかどうかみる．なければ文字列のNoneを入れる
    i = 1

    while (None in udlr_colors):
        # up
        if udlr_colors[0] == None:
            if row-i < 0:
                udlr_colors[0] = 'None'
            else:
                if color_mat[row-i][col] != 'blank':
                    udlr_colors[0] = color_mat[row-i][col]
                    uldr_coords[0] = [row-i, col]

        # down
        if udlr_colors[1] == None:
            if row+i >= HIGHT:
                udlr_colors[1] = 'None'
            else:
                if color_mat[row+i][col] != 'blank':
                    udlr_colors[1] = color_mat[row+i][col]
                    uldr_coords[1] = [row+i, col]

        # left
        if udlr_colors[2] == None:
            if col-i < 0:
                udlr_colors[2] = 'None'
            else:
                if color_mat[row][col-i] != 'blank':
                    udlr_colors[2] = color_mat[row][col-i]
                    uldr_coords[2] = [row, col-i]

        # right
        if udlr_colors[3] == None:
            if col+i >= WIDTH:
                udlr_colors[3] = 'None'
            else:
                if color_mat[row][col+i] != 'blank':
                    udlr_colors[3] = color_mat[row][col+i]
                    uldr_coords[3] = [row, col+i]

        i += 1

    return udlr_colors, uldr_coords

def solve(img):

    # Imageのサイズは（横幅，縦幅）
    im = img.resize((WIDTH, HIGHT), resample=Image.NONE)
    
    color_mat = [[0 for _ in range(WIDTH)] for _ in range(HIGHT)]
    solver_mat = [["" for _ in range(WIDTH)] for _ in range(HIGHT)]

    itr = 0

    # 色の情報を取得
    for i, j in product(range(HIGHT), range(WIDTH)):
        try:
            r, g, b, _ = im.getpixel((j, i))
        except:
            r, g, b = im.getpixel((j, i))

        color_mat[i][j] = get_color(r, g, b)

    for _ in range(3000):
        rand_row = random.randint(0, HIGHT-1)
        rand_col = random.randint(0, WIDTH-1)

        if color_mat[rand_row][rand_col] == 'blank':
            # 上下左右の色と座標を取得
            uldr_colors, uldr_coods = get_udlr_colors(color_mat, rand_row, rand_col)

            colors_count = collections.Counter(uldr_colors)
            most_common_color = colors_count.most_common(2)

            # 異なる色のペアが2つあるか判別
            if len(most_common_color) == 2:
                # None処理
                if most_common_color[0][0] == 'None':
                    most_common_color = most_common_color[1]
                elif most_common_color[1][0] == 'None':
                    most_common_color = most_common_color[0]
                else:
                    n_second_pair = most_common_color[1][1]
                    if n_second_pair < 2:
                        most_common_color = most_common_color[0]
            elif len(most_common_color) == 1:
                most_common_color = most_common_color[0]

            # 1ペアの場合
            if type(most_common_color[1]) == int:
                pair_idx = []
                if most_common_color[0] != 'None' and most_common_color[1] % 2 == 0:
                    pair_idx = [n for n, v in enumerate(uldr_colors) if v == most_common_color[0]]
            # 2ペアの場合
            else:
                pair_idx = []
                for mcc in most_common_color:
                    if mcc[0] != 'None' and mcc[1] % 2 == 0:
                        pair_idx.extend([n for n, v in enumerate(uldr_colors) if v == mcc[0]])
            
            if len(pair_idx) >= 2:
                # 既に押してある場所の時
                if solver_mat[rand_row][rand_col] != '':
                    t = solver_mat[rand_row][rand_col]
                    itr_str = f'{t},{itr}'
                    solver_mat[rand_row][rand_col] = itr_str
                else:
                    solver_mat[rand_row][rand_col] = itr

                for i in range(len(pair_idx)):
                    row, col = uldr_coods[pair_idx[i]]
                    color_mat[row][col] = 'blank'

                itr += 1

    n_blank = 0
    for i in range(HIGHT):
        n_blank += color_mat[i].count('blank')

    score = 200 - ((HIGHT*WIDTH) - n_blank)
    print(f'Score:{score}, Iter.: {itr}')

    return score, solver_mat, itr

def run(solver_result, itr):

    mouse_x, mouse_y = 0, 0
    # duration = 0.1

    for i in range(itr):
        for row, col in product(range(HIGHT), range(WIDTH)):
            if solver_result[row][col] != '':
                if type(solver_result[row][col]) == str:
                    itrs = solver_result[row][col].split(',')
                    for solres in itrs:
                        if int(solres) == i:
                            mouse_x = INIT_WIDTH + ((col)*CELL_SIZE)
                            mouse_y = INIT_HIGHT + (row*CELL_SIZE)
                            # pyautogui.click(mouse_x, mouse_y, duration=duration)
                            pyautogui.click(mouse_x, mouse_y)
                else:
                    if solver_result[row][col] == i:
                        mouse_x = INIT_WIDTH + (col*CELL_SIZE)
                        mouse_y = INIT_HIGHT + (row*CELL_SIZE)
                        # pyautogui.click(mouse_x, mouse_y, duration=duration)
                        pyautogui.click(mouse_x, mouse_y)

if __name__ == '__main__':

    # while True:
    #     mouse_pos = pyautogui.position()
    #     print(mouse_pos)

    # img = ImageGrab.grabclipboard()
    img = ImageGrab.grab((711, 133, 1284, 506))

    while True:
        score, solver_result, itr = solve(img)
        if score >= 200:

            run(solver_result, itr)

            # with open('color_mat.csv', 'w', newline='') as f:
            #     writer = csv.writer(f)
            #     writer.writerows(color_mat)

            break
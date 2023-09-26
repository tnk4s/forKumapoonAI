import random

import numpy as np
import json
import arcade
from pydantic import BaseModel, ConfigDict

from .shapes import Block, Flag, Cushion
from .constants import Constants as CONST


class Level(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    bg: tuple[int, int, int]
    obstacles: list[arcade.Sprite]
    cushions: list[arcade.Sprite]


class MapLoader:
    def __init__(self, path):
        self.levels = []
        self.flag = None
        self._load_map(path)

    def is_top(self, level: int) -> bool:
        return len(self.levels) - 1 == level

    def _load_map(self, path):
        with open(path, "r") as f:
            map_json = json.load(f)
        # self.levels += [Level(bg=(135, 206, 235), obstacles=[]) for _ in range(len(map_json))]
        for idx, map_data in map_json.items():
            self._add_level(int(idx), map_data)
            # for block in level["blocks"]:
            #     self.levels[idx].obstacles.append(Block(*block))

    def _add_level(self, idx, map_data):
        tile_width = CONST.TILE_WIDTH
        tile_height = CONST.TILE_HEIGHT
        level = Level(bg=(135, 206, 235), obstacles=[], cushions=[])
        for j, line in enumerate(map_data[::-1]):
            for i, c in enumerate(line):
                if c == 'G':
                    self.flag = Flag(i * tile_width, j * tile_height + CONST.HEIGHT * idx)

                # elif c == '*':
                #     block = Block(i * tile_width, j * tile_height + CONST.HEIGHT * idx)
                #     level.obstacles.append(block)

        rects = self._find_block_rect(map_data[::-1])
        for i, rect in enumerate(rects):
            from_x, from_y, to_x, to_y = rect
            x = from_x * tile_width
            y = from_y * tile_height + CONST.HEIGHT * idx
            width = (to_x - from_x) * tile_width
            height = (to_y - from_y) * tile_height
            print('rect', x, y, width, height, i, idx)
            block = Block(x, y, width, height, texturename=f'block{i}')
            level.obstacles.append(block)

        self.levels.append(level)

    def _find_end(self, i, j, data):
        # print(f'find from: ({i, j})')
        x_max = len(data[0])
        y_max = len(data)

        w, h = 0, 0
        for n in range(i, x_max):
            if data[j, n] == '*':
                w += 1
            else:
                break

        for m in range(j, y_max):
            if data[m, i] == '*':
                h += 1
            else:
                break

        # print(f'w, h: {w, h}')

        if w >= h:
            _x = i + w
            _y = self._get_horizontal_edge(i, j, data, w)
        else:
            _x = self._get_vertical_edge(i, j, data, h)
            _y = j + h

        # print(f'_x, _y: {_x, _y}')
        return (_x, _y)

    def _get_horizontal_edge(self, i, j, data, w):
        y = 0
        while j + y < 30:
            if all([c == '*' for c in data[j + y, i:i + w]]):
                y += 1
            else:
                break
        return j + y

    def _get_vertical_edge(self, i, j, data, h):
        x = 0
        while i + x < 30:
            if all([c == '*' for c in data[j:j + h, i + x]]):
                x += 1
            else:
                break
        return i + x

    def _find_block_rect(self, map_data):
        rects = []
        np_map = np.array([list(line) for line in map_data])
        self._rects = np.zeros((30, 30))
        for j, line in enumerate(np_map):
            for i, cell in enumerate(line):
                if self._rects[j][i] == 1:
                    continue

                if cell == '*':
                    _x, _y = self._find_end(i, j, np_map)
                    rects.append((i, j, _x, _y))
                    print(i, j, _x, _y)
                    for y in range(j, _y):
                        for x in range(i, _x):
                            self._rects[y, x] = 1

        return rects

from abc import ABC, abstractmethod
from typing import Tuple

import arcade
import random

from .player import Player


class Controller(ABC):
    @abstractmethod
    def update(self, player: Player, **kwargs) -> Tuple[bool, bool, bool]:
        return True, True, True


class RandomPlayer(Controller):
    def __init__(self) -> None:
        super().__init__()

    def update(self, player: Player, **kwargs) -> tuple[bool, bool, bool]:
        return tuple(random.choice([True, False]) for _ in range(3))


class Human(Controller):
    def __init__(self) -> None:
        super().__init__()

    def update(self, player: Player, **kwargs) -> Tuple[bool, bool, bool]:

        keys = list(kwargs['current'])
        if kwargs['key'] == arcade.key.LEFT:
            key_index = 0
        elif kwargs['key'] == arcade.key.RIGHT:
            key_index = 1
        elif kwargs['key'] == arcade.key.SPACE:
            key_index = 2
        else:
            return (False, False, False)
        keys[key_index] = kwargs['pressed']

        return tuple(keys)

class AiControll(Controller):
    def __init__(self) -> None:
        super().__init__()
        self.auto_action = {"LEFT":False, "RIGHT":False, "SPACE":False}
    
    def set_auto_action(self, l, r, s):#l,r,s bool
        self.auto_action["LEFT"] = l
        self.auto_action["RIGHT"] = r
        self.auto_action["SPACE"] = s

    def update(self, player: Player, **kwargs) -> Tuple[bool, bool, bool]:
        return (self.auto_action["LEFT"], self.auto_action["RIGHT"], self.auto_action["SPACE"])

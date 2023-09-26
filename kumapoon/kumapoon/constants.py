from dataclasses import dataclass


@dataclass(frozen=True)
class Constants:
    WIDTH = 600
    HEIGHT = 900
    TILE_WIDTH = 20
    TILE_HEIGHT = 30
    GRAVITY = 1500
    DAMPING = 1.0
    WALL_FRICTION = 0.7


@dataclass(frozen=True)
class PlayerConstants:
    DAMPING = 0.4
    FRICTION = 1.0
    MASS = 2.0
    RUN_SPEED = 500
    MAX_HORIZONTAL_SPEED = 450
    MAX_VERTICAL_SPEED = 1500
    MAX_JUMP_TIMER = 60
    MAX_JUMP_IMPULSE = 1800

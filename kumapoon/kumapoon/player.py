import arcade

from .constants import PlayerConstants as PLAYER


class Line:
    pass


class Player(arcade.Sprite):

    def __init__(self, filename="assets/images/kumapon.png"):
        super().__init__(filename=filename, hit_box_algorithm='Detailed')

        self.texture = self.textures[0]
        self.hit_box = self.texture.hit_box_points

        self.jump_timer = 0

        self.is_on_ground = False
        self.isLeftPressed = False
        self.isRightPressed = False
        self.isJumpPressed = False

        self.left_edge = min(self.hit_box, key=lambda x: x[0])[0]
        self.right_edge = max(self.hit_box, key=lambda x: x[0])[0]
        self.top_edge = min(self.hit_box, key=lambda x: x[1])[1]
        self.bottom_edge = max(self.hit_box, key=lambda x: x[1])[1]

    @property
    def top(self):
        return self.center_y - self.top_edge

    @property
    def bottom(self):
        return self.center_y - self.bottom_edge

    @property
    def left(self):
        return self.center_x + self.left_edge

    @property
    def right(self):
        return self.center_x + self.right_edge

    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        pass
        # is_on_ground = physics_engine.is_on_ground(self)

    def get_fx(self):
        if not self.is_on_ground:
            return 0

        if self.isJumpPressed:
            return 0
        else:
            if self.isRightPressed:
                fx = PLAYER.RUN_SPEED
            elif self.isLeftPressed:
                fx = -PLAYER.RUN_SPEED
            else:
                fx = 0
            return fx

    def update_jumptimer(self):
        if self.jump_timer < PLAYER.MAX_JUMP_TIMER:
            self.jump_timer += 1

    def is_moving_down(self):
        return self.vy < 0

    def is_moving_up(self):
        return self.vy > 0

    def is_moving_left(self):
        return self.vx > 0

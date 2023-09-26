import arcade


class BlockBase(arcade.Sprite):
    def __init__(self, x, y, width, height, filename=None):
        super().__init__(
            filename=filename,
            center_x=x + width // 2, center_y=y + height // 2
        )

    def __repr__(self):
        return f"{type(self)}({self.position})"


class Block(BlockBase):
    def __init__(
        self, x, y, width=20, height=30, color=(116, 80, 48),
        filename=None, texturename='block', gravity=1, fade=None
    ):
        super().__init__(x, y, width, height, filename)
        # arcade.draw_lrtb_rectangle_filled(x, x+width, y, y-height, color)
        self.gravity = gravity
        self.fade = fade
        self.texture = arcade.Texture.create_filled(texturename, (width, height), color)


class Cushion(BlockBase):
    def __init__(
        self, x, y, width=20, height=5, color=(0, 0, 0),
        filename=None, texturename='cushion'
    ):
        super().__init__(x, y, width, height, filename)
        self.texture = arcade.Texture.create_filled(texturename, (width, height), color)


class Flag(arcade.Sprite):
    def __init__(self, x, y, width=20, height=30, scale=0.2, filename='./assets/images/flag.png'):
        super().__init__(
            filename=filename, scale=scale,
            center_x=x + width // 2, center_y=y + height // 2
        )


# class Flag(BlockBase):
#     def __init__(self, x, y, width=20, height=30, filename='./assets/images/flag.png'):
#         # print(x, y)
#         super().__init__(x, y, width, height, filename, scale=0.2)

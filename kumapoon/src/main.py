import arcade

from kumapoon.constants import Constants as CONST
from kumapoon.constants import PlayerConstants as PLAYER
from kumapoon.controller import Controller, Human, RandomPlayer, AiControll
from kumapoon.maploader import MapLoader
from kumapoon.player import Player

import itertools

import gym

import threading


class Game(arcade.Window):
    def __init__(self, controller: Controller):
        super().__init__(CONST.WIDTH, CONST.HEIGHT, "Kumapoon")

        self.controller = controller
        self.scene: arcade.Scene | None = None
        self.player: arcade.Sprite | None = None
        self.obstacle_list: arcade.SpriteList | None = arcade.SpriteList()
        self.current_level = 0

        self.left_pressed: bool = False
        self.right_pressed: bool = False
        self.space_pressed: bool = False

        self.released: bool = False

        self.physics_engine: arcade.PymunkPhysicsEngine | None = None
        self.camera = None
        self.gui_camera = None

    def _setup(self):
        self.scene = arcade.Scene()
        self.camera = arcade.Camera(CONST.WIDTH, CONST.HEIGHT)
        self.gui_camera = arcade.Camera(CONST.WIDTH, CONST.HEIGHT)
        self.map = MapLoader("assets/data/map.json")
        self.scene.add_sprite('Flag', self.map.flag)

        self.player = Player()
        self.player.center_x = CONST.WIDTH // 2
        self.player.center_y = 100
        self.scene.add_sprite('Player', self.player)

        self.key_state = (False, False, False)
        for level in self.map.levels:
            self.obstacle_list.extend(level.obstacles)
        self.scene.add_sprite_list('Blocks', sprite_list=self.obstacle_list)

        arcade.set_background_color(self.map.levels[self.current_level].bg)

        gravity = (0, -CONST.GRAVITY)
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=CONST.DAMPING, gravity=gravity)
        self.physics_engine.add_sprite(
            self.player, friction=PLAYER.FRICTION, mass=PLAYER.MASS,
            moment=arcade.PymunkPhysicsEngine.MOMENT_INF, collision_type="player",
            max_horizontal_velocity=PLAYER.MAX_HORIZONTAL_SPEED,
            max_vertical_velocity=PLAYER.MAX_VERTICAL_SPEED
        )
        self.physics_engine.add_sprite_list(
            self.scene.get_sprite_list('Blocks'), friction=CONST.WALL_FRICTION,
            collision_type="wall", body_type=arcade.PymunkPhysicsEngine.STATIC
        )

        def _block_hit_hundler(player_sprite, block_sprite, _arbiter, _space, _data):
            if abs(_arbiter.normal[0]) > 0.8:
                #print(_arbiter.normal)
                impulse_x, impulse_y = _arbiter.total_impulse
                normal_x, normal_y = _arbiter.normal
                self.physics_engine.apply_impulse(
                    self.player, (impulse_x * abs(normal_x), impulse_y * abs(normal_y))
                )
                #print('bounce_side', _arbiter.total_impulse)

            if _arbiter.normal[1] > 0 and _arbiter.total_impulse[1] < 0:
                f_x, f_y = _arbiter.total_impulse
                self.physics_engine.apply_impulse(self.player, (-f_x * 0.6, f_y * 0.6))
                #print('bounce_down', _arbiter.total_impulse)

        self.physics_engine.add_collision_handler(
            'player', 'wall', post_handler=_block_hit_hundler
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.close_window()
            exit(0)

        self.key_state = self.controller.update(
            self.player, current=self.key_state, key=key, pressed=True
        )
        if key == arcade.key.SPACE:
            self.released = False

    def on_key_release(self, key, modifiers):
        self.key_state = self.controller.update(
            self.player, current=self.key_state, key=key, pressed=False
        )
        if key == arcade.key.SPACE:
            self.released = True

    def update_player(self):
        left, right, jump = self.key_state
        self.player.isLeftPressed = left
        self.player.isRightPressed = right
        self.player.isJumpPressed = jump

        is_on_ground = self.physics_engine.is_on_ground(self.player)
        force = (0, 0)

        #ジャンプできるように==========================================
        if jump == False and self.player.jump_timer != 0:
            self.released = True
        else:
            self.released = False
        #===========================================================

        if left and not right:
            force = (-PLAYER.RUN_SPEED, 0)
            self.physics_engine.set_friction(self.player, 0)
        elif right and not left:
            force = (PLAYER.RUN_SPEED, 0)
            self.physics_engine.set_friction(self.player, 0)
        elif (not left) and (not right):
            self.physics_engine.set_friction(self.player, 1.0)

        if is_on_ground and not jump:
            self.physics_engine.apply_force(self.player, force)
        else:
            self.physics_engine.set_friction(self.player, 1.0)

        if jump and is_on_ground:
            self.physics_engine.set_horizontal_velocity(self.player, 0)
            self.player.update_jumptimer()
        elif self.released and is_on_ground:
            jump_timer = min(self.player.jump_timer, PLAYER.MAX_JUMP_TIMER)
            force_y = 1000 + jump_timer * 30
            self.physics_engine.apply_impulse(self.player, (force[0], force_y))
            self.released = False
            self.player.jump_timer = 0

        self._edge_bounce()

    def _edge_bounce(self):
        player_object = self.physics_engine.get_physics_object(self.player)
        velocity_x = player_object.body.velocity[0]
        if self.player.right > CONST.WIDTH and velocity_x > 0:
            self.physics_engine.set_horizontal_velocity(self.player, -velocity_x)
        elif self.player.left < 0 and velocity_x < 0:
            self.physics_engine.set_horizontal_velocity(self.player, -velocity_x)

    def _switch_camera(self):
        if self.player.center_y > CONST.HEIGHT * (self.current_level + 1):
            if self.map.is_top(self.current_level):
                return
            self.current_level += 1
            self.camera.move_to((0, CONST.HEIGHT * self.current_level))

        elif self.player.center_y < CONST.HEIGHT * self.current_level:
            self.current_level -= 1
            self.camera.move_to((0, CONST.HEIGHT * self.current_level))

    def on_update(self, delta_time):
        self.update_player()
        self.physics_engine.step()

    def _check_clear(self):
        collide_flag = arcade.check_for_collision(
            self.player, self.map.flag
        )
        if collide_flag:
            self.cleared = True

    def _draw_jump_timer(self):
        power = int(255 * (self.player.jump_timer / PLAYER.MAX_JUMP_TIMER))
        arcade.draw_circle_filled(
            self.player.center_x, self.player.center_y,
            30 * (self.player.jump_timer / PLAYER.MAX_JUMP_TIMER) + 20,
            (power, 255 - power, 0)
        )

    def _draw_debug_text(self):
        arcade.draw_text(
            f"level: {self.current_level}", 10, CONST.HEIGHT - 30, arcade.color.BLACK, 20
        )
        arcade.draw_text(
            f"({self.player.center_x:.1f}, {self.player.center_y:.1f})",
            10, CONST.HEIGHT - 50, arcade.color.BLACK, 20
        )
        arcade.draw_text(
            f"on_ground: {self.physics_engine.is_on_ground(self.player)}",
            10, CONST.HEIGHT - 70, arcade.color.BLACK, 20
        )
        arcade.draw_text(
            f"jump_timer: {self.player.jump_timer}",
            10, CONST.HEIGHT - 90, arcade.color.BLACK, 20
        )
        arcade.draw_text(
            f"{self.physics_engine.get_physics_object(self.player).body.velocity}",
            10, CONST.HEIGHT - 110, arcade.color.BLACK, 20
        )
        arcade.draw_text(
            f"{self.player.left:.1f}, {self.player.right:.1f}",
            10, CONST.HEIGHT - 130, arcade.color.BLACK, 20
        )
        arcade.draw_text(
            f"{self.physics_engine.get_physics_object(self.player).shape.friction}",
            10, CONST.HEIGHT - 150, arcade.color.BLACK, 20
        )

    def on_draw(self):
        self.clear()
        self.camera.use()
        self._switch_camera()
        self._draw_jump_timer()
        self.scene.draw()
        # self.player.draw_hit_box()
        # self.obstacle_list.draw_hit_boxes()
        self.gui_camera.use()
        self._draw_debug_text()


class KumapoonGameEnv(gym.Env, Game):
    def __init__(self):
        super().__init__(AiControll())
        #super().__init__(RandomPlayer())
        #super().__init__(Human())
        self.FIELD_TYPES = [
            " ",
            "*",
            "G"
        ]
        self.a_map = AroundMap()
        self.update_counter = 0
        self.observation_data = {}#仮　一定frameおきにこちらに保存．Envはこちらを参照すべき?
        self.action_space = gym.spaces.Discrete(3)  # 左右跳　たぶん
        self.observation_space = gym.spaces.Box(    # 確実に違う 
            low = 0,#[0 for _ in range(4 + 30*30)],
            high = 2,#[2 for _ in range(4 + 30*30)]
            #shape = (1, 4 + 30*30)
        )
        self.reward_range = [-1., 100.]
        self.last_on_g_rw = 0.0

        #self.run_thread = threading.Thread(target=arcade.run)
        #self.reset()
    
    def reset(self):
        #print("ENV_RESET")
        self._setup()
        self.on_update(0.5)
        #self.run_thread.start()
        #arcade.run()#ゲームループは別で回しながらstep()で観測する感じ?

        #仮の観測データをセット
        self.set_observ()

        return self.observe()
    
    def step(self, action):
        for i in range(4):
            self.on_update(0.5)
        # 1ステップ進める処理を記述。戻り値は observation, reward, done(ゲーム終了したか), info(追加の情報の辞書)
        #action = (False, False, False)#仮
        #print("given action", action)
        l, r, s = (False, False, False)
        if action == 0:
            l = True
        elif action == 1:
            r = True
        else:
            s = True

        self.controller.set_auto_action(l, r, s)#AIの動きを入力
        #print("action ", self.update_counter, ":", l, r, s)

        #ここでstep()処理は時間をおくべき？

        observation = self.observe()
        reward = self.get_reward()
        self.done = self.is_done()
        return observation, reward, self.done, {}
    
    def render(self, mode):
        pass

    def close(self):
        pass

    def seed(self, seed=None):
        pass

    def get_reward(self):#報酬を考える
        pl, px, py = self.current_level, self.player.center_x, self.player.center_y
        rw = (10.0 * (py/CONST.HEIGHT * py/CONST.HEIGHT) ) + ((pl * pl) * 10.0) + (5 * (self.player.jump_timer / PLAYER.MAX_JUMP_TIMER) * (self.player.jump_timer / PLAYER.MAX_JUMP_TIMER))
        if self.physics_engine.is_on_ground(self.player):
            if rw > self.last_on_g_rw:
                self.last_on_g_rw = rw
                rw = rw * 2
            else:
                self.last_on_g_rw = rw
                rw = rw / 2
        if self.player.jump_timer == PLAYER.MAX_JUMP_TIMER:
            rw = -1.0
        
        return rw
    
    def observe(self):
        #とりあえず1*904の形に整形
        observation_l = []
        observation_l.append(self.observation_data["CurrentLv"])
        observation_l.append(self.observation_data["onGround"])
        observation_l.append(self.observation_data["CenterX"])
        observation_l.append(self.observation_data["CenterY"])
        observation_l.append(self.observation_data["JumpTimer"])
        for v in list(itertools.chain.from_iterable(self.observation_data["Around"])):
            observation_l.append(v)

        return observation_l
    
    def set_observ(self):
        self.observation_data = {}#初期化
        self.observation_data["CurrentLv"] = self.current_level
        self.observation_data["onGround"] = self.physics_engine.is_on_ground(self.player)
        self.observation_data["CenterX"] = self.player.center_x
        self.observation_data["CenterY"] = self.player.center_y
        self.observation_data["JumpTimer"] = self.player.jump_timer
        self.observation_data["Around"] = self.a_map.get_around(self.current_level, self.player.center_y)
    
    def is_done(self):
        #ゴールに接触したかを返したい
        return False

    def update_player(self):#特定のフレーム毎にobservationを保存する処理を追加．これで同期が取れる？
        #キーが押されなくても強制発動
        self.key_state = self.controller.update(
            self.player, current=self.key_state, key=arcade.key.SPACE, pressed=True
        )
        super().update_player()

        #self.update_counter += 1 #アプデ=フレームを数える
        #if self.update_counter % 4 == 0:#4フレーム毎に保存（仮）
        self.set_observ()

        #print("==observation_data==")
        #print(self.observation_data)


import json
class AroundMap:
    def __init__(self):
        self.path = "assets/data/map.json"
        self.joined_map = []
        self.FIELD_TYPES = [
            " ",
            "*",
            "G"
        ]
        self.goal_xy = (0.0, 0.0)

        with open(self.path, "r") as f:
            map_json = json.load(f)
        for idx, map_data in map_json.items():
            #print("idx", idx)
            #print("map_data", map_data)
            for l_md in reversed(map_data):
                self.joined_map.append(self._num_map(l_md))
                #if "G" in l_md:
                #    pass
        '''
        for l in reversed(self.joined_map):
            print(l)
        '''
        
    
    def _num_map(self, l_md):
        l_md_n = []
        for s in l_md:
            l_md_n.append(self.FIELD_TYPES.index(s))
        
        return l_md_n
    
    def get_around(self, level, y):
        around = []
        base_l = 30 * level
        m_y = int(30 * (y / CONST.HEIGHT))

        for i in range(30):
            if len(self.joined_map) > (i + m_y + base_l - 2):
                around.append(self.joined_map[i + m_y + base_l - 2])
            else:
                around.append([0 for _ in range(30)])
        '''
        for l in reversed(around):
            print(l)
        '''
        return around

import torch
import torch.nn as nn
import numpy as np
class AiDrive(Game):
    def __init__(self):
        super().__init__(AiControll())
        self.FIELD_TYPES = [
            " ",
            "*",
            "G"
        ]
        self.a_map = AroundMap()
        self.observation_data = {}

        self.my_brain = MyBrain()
        self.my_brain.model.load_state_dict(torch.load("./dqn_models/my_agent_v0.pth"))

    def _setup(self):
        super()._setup()
        #仮の観測データをセット
        self.set_observ()
    
    def update_player(self):
        observation = self.get_observation()
        action = self.decide_auto_action(observation)
        l, r, s = (False, False, False)
        if action == 0:
            l = True
        elif action == 1:
            r = True
        else:
            s = True

        self.controller.set_auto_action(l, r, s)#AIの動きを入力

        #キーが押されなくても強制発動
        self.key_state = self.controller.update(
            self.player, current=self.key_state, key=arcade.key.SPACE, pressed=True
        )
        super().update_player()

        self.set_observ()
    
    def set_observ(self):
        self.observation_data = {}#初期化
        self.observation_data["CurrentLv"] = self.current_level
        self.observation_data["onGround"] = self.physics_engine.is_on_ground(self.player)
        self.observation_data["CenterX"] = self.player.center_x
        self.observation_data["CenterY"] = self.player.center_y
        self.observation_data["JumpTimer"] = self.player.jump_timer
        self.observation_data["Around"] = self.a_map.get_around(self.current_level, self.player.center_y)

    def get_observation(self):
        #とりあえず1*904の形に整形
        observation_l = []
        observation_l.append(self.observation_data["CurrentLv"])
        observation_l.append(self.observation_data["onGround"])
        observation_l.append(self.observation_data["CenterX"])
        observation_l.append(self.observation_data["CenterY"])
        observation_l.append(self.observation_data["JumpTimer"])
        for v in list(itertools.chain.from_iterable(self.observation_data["Around"])):
            observation_l.append(v)

        return observation_l

    def decide_auto_action(self, observation):
        observation = torch.FloatTensor(observation)
        self.my_brain.eval()  # ネットワークを推論モードに切り替える
        with torch.no_grad():
            res = self.my_brain(observation)#.max(1)[1].view(1, 1)
            res = np.argmax(res)
            #print("decide_auto_action:", res)
        return res

class MyBrain(nn.Module):
    def __init__(self, num_states = 904+1, num_actions = 3):
        super().__init__()
        self.num_actions = num_actions

        # ニューラルネットワークを構築
        self.model = nn.Sequential()
        self.model.add_module('fc1', nn.Linear(num_states, 64))
        self.model.add_module('relu1', nn.ReLU())
        self.model.add_module('fc2', nn.Linear(64, 32))
        self.model.add_module('relu2', nn.ReLU())
        self.model.add_module('fc3', nn.Linear(32, num_actions))
    
    def forward(self, observation):
        return self.model(observation)

if __name__ == "__main__":
    #game = Game(Human())
    game = AiDrive()
    game._setup()
    arcade.run()

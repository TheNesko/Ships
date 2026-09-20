from random import randint

import pygame
from network import Network
from player import *
import pyperclip
from enum import Enum
from server import GameServer
from _thread import *
import time

from shared import Action


FPS_LIMIT = 60

WIDTH = 1200
HEIGHT = 700

SHIP_BOARD = (50, 150)
ATTACK_BOARD = (650, 150)

class Align(Enum):
    CENTER = 0
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4
    TOP_RIGHT = 5
    TOP_LEFT = 6
    BOTTOM_RIGHT = 7
    BOTTOM_LEFT = 8

    @staticmethod
    def get_pos(alignment, x, y, width, height):
        new_x, new_y = x, y
        match alignment:
            case Align.CENTER:
                new_x -= width/2
                new_y -= height/2
            case Align.RIGHT:
                new_x -= width
                new_y -= height/2
            case Align.LEFT:
                new_y -= height/2
            case Align.BOTTOM:
                new_x -= width/2
                new_y -= height
            case Align.TOP:
                new_x -= width/2
            case Align.TOP_RIGHT:
                new_x -= width
            case Align.BOTTOM_LEFT:
                new_y -= height
            case Align.BOTTOM_RIGHT:
                new_x -= width
                new_y -= height
        return new_x, new_y

def draw_text(
    screen,
    font,
    text:str,
    pos:list[float],
    color:tuple[int,int,int]=(0,0,0),
    alignment=Align.CENTER):
    x, y = pos.copy()
    width, height = font.size(text)
    text_obj = font.render(text, 0, color)
    x, y = Align.get_pos(alignment, x, y, width, height)
    screen.blit(text_obj, (x, y))
    return text_obj.get_size()

def point_in_rect(point_x, point_y, rect_x, rect_y, rect_width, rect_height):
    if point_x > rect_x and point_x < rect_x + rect_width:
        if point_y > rect_y and point_y < rect_y + rect_height:
            return True
    return False

class inputField:
    def __init__(self,
                font,
                pos:list[float],
                value="",
                preview="",
                width=200,
                height=50,
                centered=True,
                border_size = 5,
                border_radius = 0,
                text_color = (255,255,255),
                border_color = (40,40,40),
                bg_color = (0,0,0),
                font_size=32,
                bold=True) -> None:
        self.font = pygame.font.SysFont(font,size=font_size, bold=bold)
        self.value = value
        self.preview = preview
        self.pos = [pos[0]-width/2, pos[1]-height/2] if centered else pos
        self.width = width
        self.height = height
        self.centered = centered
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_size = border_size
        self.border_radius = border_radius
        self.text_color = text_color
        self.focused = False
        self._submit = False
        self._text_changed = False
        self.caret_speed = 10
        self._caret_tick = 0
        self._carret = False

    def update(self, events):
        self._text_changed = False
        self._submit = False
        self._caret_tick += 1
        if self._caret_tick%self.caret_speed == 0:
            self._carret = not self._carret
        if self.pressed(events): self.focused = not self.focused
        if self.focused == False: return
        ctrl_held = pygame.key.get_pressed()[pygame.K_LCTRL]
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c and ctrl_held: # COPY
                    pyperclip.copy(self.value)
                    continue
                if event.key == pygame.K_v and ctrl_held: # PASTE
                    self.value = pyperclip.paste()
                    continue
                if event.key == pygame.K_BACKSPACE: # REMOVE LAST
                    self.value = "" if ctrl_held else self.value[:-1]
                    self._text_changed = True
                    continue
                if event.key == pygame.K_RETURN: # SUBMIT TEXT
                    self._submit = True
                    continue
                pressed_key = event.unicode
                if pressed_key == "": continue
                self.value += pressed_key
                self._text_changed = True


    def submitted(self):
        return self._submit

    def pressed(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = event.pos
                    if point_in_rect(mouse_pos[0], mouse_pos[1], self.pos[0], self.pos[1], self.width, self.height):
                        return True
        return False

    def draw(self, screen):
        center_pos = self.pos.copy()
        text = self.value if self.value != "" or self.focused else self.preview

        pygame.draw.rect(
            screen,
            self.bg_color,
            pygame.Rect((center_pos[0], center_pos[1]), (self.width, self.height)),
            border_radius=self.border_radius
        )
        pygame.draw.rect(
            screen,
            self.border_color,
            pygame.Rect((center_pos[0], center_pos[1]), (self.width, self.height)),
            self.border_size,
            self.border_radius
        )

        text_pos = [center_pos[0]+self.width/2, center_pos[1]+self.height/2]
        text_size = draw_text(screen, self.font, text, text_pos, color=self.text_color)
        if self.focused and self._carret:
            caret_pos = [text_pos[0]+text_size[0]/2, text_pos[1]]
            draw_text(screen, self.font, "|", caret_pos, color=self.text_color)

class Button:
    def __init__(self,
                font,
                text,
                pos:list[float],
                width = 100,
                height = 50,
                centered = True,
                text_color = (255,255,255),
                bg_color = (0,0,0),
                border_color = (50,50,50),
                border_size = 5,
                border_radius = 0,
                font_size = 32,
                bold = True,
                auto_resize = False,
                margin = 10) -> None:
        self.font = pygame.font.SysFont(font,size=font_size, bold=bold)
        self.text = text
        self.pos = pos
        self.width = width
        self.height = height
        self.centered = centered
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_size = border_size
        self.border_radius = border_radius
        self.auto_resize = auto_resize
        self.margin = margin
        self._pressed = False

    def get_pos(self):
        pos = self.pos.copy()
        return [pos[0]-self.width/2, pos[1]-self.height/2] if self.centered else pos

    def pressed(self):
        return self._pressed

    def _is_pressed(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = event.pos
                    button_pos = self.get_pos()
                    if point_in_rect(mouse_pos[0], mouse_pos[1], button_pos[0], button_pos[1], self.width, self.height):
                        return True
        return False

    def update(self, events):
        self._pressed = False
        if self._is_pressed(events): self._pressed = True

    def draw(self, screen):
        center_offset = [self.width/2, self.height/2]
        pygame.draw.rect(
            screen,
            self.bg_color,
            pygame.Rect((self.pos[0]-center_offset[0], self.pos[1]-center_offset[1]), (self.width, self.height)),
            border_radius=self.border_radius
        )
        pygame.draw.rect(
            screen,
            self.border_color,
            pygame.Rect((self.pos[0]-center_offset[0], self.pos[1]-center_offset[1]), (self.width, self.height)),
            self.border_size,
            self.border_radius
        )

        size = draw_text(screen, self.font, self.text, self.pos, color=self.text_color)
        if self.auto_resize:
            margin = + self.border_size * 2 + self.margin
            self.width = size[0] + margin
            self.height = size[1] + margin

class Particle:

    CIRCLE = 0

    def __init__(self, lifetime = 0.0, x = 0, y = 0, color = (255,255,255)) -> None:
        self.x = x
        self.y = y
        self.lifetime = lifetime
        self.color = color
        self.gravity_x :float = 0.0
        self.gravity_y :float = 0.0
        self.velocity_x :float = 0.0
        self.velocity_y :float = 0.0

        self._time_passed :float = 0.0

    def update(self, dt:float):
        self._time_passed += dt
        self.velocity_x += self.gravity_x * dt
        self.velocity_y += self.gravity_y * dt
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), 10)

class ParticleEmitter:
    def __init__(self, x, y, lifetime, amount:int, emitting:bool = True, one_shot:bool = False, color = (255,255,255),
                init_velocity = [[-50, 50],[-50, 50]], gravity = [0.0, 98.0], explosivness:float = 0.0,
                lifetime_randomness:float = 1.0) -> None:
        self.x = x
        self.y = y
        self.lifetime = lifetime
        self.amount = amount
        self.emitting = emitting
        self.one_shot = one_shot
        self.color = color
        self.initial_velocity = init_velocity
        self.gravity = gravity
        self.explosivness = explosivness
        self.lifetime_randomness = lifetime_randomness


        self._time_passed : float = 0.0
        self.particles : list[Particle] = []
        self.emitted : int = 0

    def update(self, dt:float):
        # first update existing particles
        for particle in self.particles:
            particle.update(dt)
            if particle._time_passed >= particle.lifetime:
                self.particles.remove(particle)

        # if not emitting then skip rest
        if not self.emitting: return

        self._time_passed += dt
        if (self._time_passed/self.get_spawn_interval()) > self.emitted:
            if self.explosivness:
                for _ in range(int(self.amount * self.explosivness)):
                    self.spawn_particle()
            else:
                self.spawn_particle()

        if self.one_shot and self.emitted >= self.amount:
            self.emitting = False
            self.emitted = 0

    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)

    def start_emitting(self, x = None, y = None):
        if x: self.x = x
        if y: self.y = y
        self.emitting = True

    def spawn_particle(self):
        lifetime = self._get_lifetime()
        new_particle = Particle(lifetime, self.x, self.y)
        if type(self.color) is list:
            channels = []
            for channel in self.color:
                channels.append(randint(channel[0], channel[1]))

            new_particle.color = (channels[0], channels[1], channels[2])
        else:
            new_particle.color = self.color
        velocity_x = self.initial_velocity[0]
        velocity_y = self.initial_velocity[1]
        if type(velocity_x) is list:
            new_particle.velocity_x = randint(velocity_x[0], velocity_x[1])
        elif type(velocity_x) is float:
            new_particle.velocity_x = velocity_x
        if type(velocity_y) is list:
            new_particle.velocity_y = randint(velocity_y[0], velocity_y[1])
        elif type(velocity_y) is float:
            new_particle.velocity_y = velocity_y
        new_particle.gravity_x = self.gravity[0]
        new_particle.gravity_y = self.gravity[1]
        self.particles.append(new_particle)
        self.emitted += 1

    def get_emit_speed(self):
        return self.amount/self.lifetime

    def get_spawn_interval(self):
        return 1.0/self.get_emit_speed()

    def _get_lifetime(self):
        lifetime = self.lifetime
        rand_scale = 100
        lifetime_a = lifetime*rand_scale
        lifetime_b = (lifetime*self.lifetime_randomness)*rand_scale
        lifetime = randint(int(lifetime_a), int(lifetime_b))
        return lifetime/rand_scale

class Bomb:
    def __init__(self, board:Board, board_pos, x, y, emitter:ParticleEmitter) -> None:
        world_x, world_y = Board.to_world(x, y)
        world_x += Board.CELL_SIZE/2 + board_pos[0]
        world_y += Board.CELL_SIZE/2 + board_pos[1]
        self.attack_x = x
        self.attack_y = y
        self.x = world_x
        self.y = -100
        self.target_y = world_y
        self.emitter = emitter
        self.board = board
        self.finished = False

        self.start_dist = world_y - self.y

        self.velocity_y = self.start_dist
        self.gravity_y = 5000.0

    def update(self, dt:float):
        if self.finished: return

        self.velocity_y += self.gravity_y * dt
        self.y += self.velocity_y * dt
        self.y = min(self.target_y, self.y)

        if self.target_y - self.y <= 0:
            self.emitter.start_emitting(self.x, self.y)
            self.board.attack(self.attack_x, self.attack_y)
            self.finished = True
            return

    def draw(self, screen):
        curr_dist = self.target_y - self.y
        size = 30
        size +=  (size * 2)  / (self.start_dist/curr_dist)
        pygame.draw.polygon(
            screen,
            (0,255,0),
            [
                (self.x-size/2, self.y-size),
                (self.x+size/2, self.y-size),
                (self.x, self.y)
            ]
        )



class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.server = GameServer()
        self.server_thread = None
        self.n = Network()
        self.reply_thread = None
        self.p = Player()
        self.players_ready = 0
        self.reset_requests = 0
        self.match_started = False
        self.running = True
        self.done = False
        self.dt = 0.01

        self.fail_shot_emitter = ParticleEmitter(0, 0, 0.3, 24, color=[[0,20],[0,30],[200,255]], explosivness=1.0,
            init_velocity=[[-100, 100],[-100, -20]], lifetime_randomness=3.0, one_shot=True, gravity=[0.0, 150.0], emitting=False)
        self.correct_shot_emitter = ParticleEmitter(0, 0, 0.3, 24, color=[[196,255],[28,80],[20,20]], explosivness=1.0,
            init_velocity=[[-200, 200],[-200, 200]], lifetime_randomness=1.5, one_shot=True, gravity=[0.0, 0.0], emitting=False)
        self.emitters = [self.fail_shot_emitter, self.correct_shot_emitter]

        self.bombs :list[Bomb] = []

    def restart(self):
        self.p = Player()
        self.players_ready = 0
        self.reset_requests = 0
        self.match_started = False

    def spawn_bomb(self, board, board_pos, x, y, emitter):
        self.bombs.append(Bomb(board, board_pos, x, y, emitter))

    def manage_replies(self):
        while not self.done:
            try:
                reply = self.n.recv_data()
                print(reply)
                action = reply["action"]
                id = reply["client_id"]
                match action:
                    case Action.EXITED:
                        if self.n.id == id:
                            pass
                        else:
                            print("Player has left!")
                    case Action.JOINED:
                        self.p.attack_board = reply["attack_board"]
                        if self.n.id == id:
                            pass
                        else:
                            print("New player joined!")
                    case Action.ATTACK:
                        self.p.my_turn = reply["my_turn"] == self.n.id
                        result = reply["result"]
                        x = reply["x"]
                        y = reply["y"]
                        emitter = self.correct_shot_emitter if result else self.fail_shot_emitter
                        if self.n.id == id:
                            # self.p.attack_board.attack(x,y)
                            self.spawn_bomb(self.p.attack_board, ATTACK_BOARD, x, y, emitter)
                        else:
                            # self.p.ship_board.attack(x,y)
                            self.spawn_bomb(self.p.ship_board, SHIP_BOARD, x, y, emitter)
                            print(f"Other player attacked your ship at {x} {y}")
                    case Action.PLACE:
                        result = reply["result"]
                        x = reply["x"]
                        y = reply["y"]
                        if result == False: continue
                        if self.n.id == id:
                            self.p.ship_board.place_ship(x,y)
                        else:
                            self.p.attack_board.place_ship(x,y)
                            print(f"Other player placed a ship at {x}{y}")
                    case Action.REMOVE:
                        result = reply["result"]
                        x = reply["x"]
                        y = reply["y"]
                        if result == False: continue
                        if self.n.id == id:
                            self.p.ship_board.remove_ship(x,y)
                        else:
                            self.p.attack_board.remove_ship(x,y)
                            print(f"Other player removed ship from {x}{y}")
                    case Action.RESET:
                        self.reset_requests = reply["reset_requests"]
                        if self.n.id == id:
                            self.p.reset_request = reply["result"]
                        else:
                            pass
                        if reply["reset"]:
                            self.restart()
                    case Action.READY:
                        self.players_ready = reply["ready_player"]
                        self.match_started = reply["match_started"]
                        self.p.my_turn = reply["my_turn"] == self.n.id
                        if self.n.id == id:
                            self.p.ready = reply["result"]
                        else:
                            pass
            except TimeoutError:
                # print("No replies")
                pass
            except ConnectionError:
                print("Lost connection")
                break
        print("Reply thread closed")

    def redraw_screen(self, font):
        self.screen.fill((48, 58, 74)) #background

        self.p.ship_board.draw(self.screen, SHIP_BOARD, font, (11,79,189))
        self.p.attack_board.draw(self.screen, ATTACK_BOARD, font, (85,145,242), True)

        x_offset = WIDTH/4
        text = "Prepare"
        turn_text = ""
        if self.players_ready > 0:
            text = f"Ready: {self.players_ready}/2"
        if self.match_started:
            text = "Battle"
            turn_text = "Your Turn" if self.p.my_turn else "Wait"

            # display count of enemy ships only in battle
            width, height = draw_text(self.screen, font, "Enemy ships", [WIDTH-x_offset, 25], (255,255,255), alignment=Align.TOP_RIGHT)
            enemy_ships_left = self.p.attack_board.ship_amount - self.p.attack_board.destroyed
            enemy_ships_text = f"{self.p.attack_board.ship_amount}/{enemy_ships_left}"
            draw_text(self.screen, font, enemy_ships_text, [WIDTH-x_offset-width/2, 25+height], (255,255,255), alignment=Align.TOP)

        # display count of your ships
        width, height = draw_text(self.screen, font, "Your ships", [x_offset, 25], (255,255,255), alignment=Align.TOP_LEFT)
        your_ships_left = self.p.ship_board.ship_amount - self.p.ship_board.destroyed
        your_ships = f"{self.p.ship_board.ship_amount}/{your_ships_left}"
        draw_text(self.screen, font, your_ships, [x_offset+width/2, 25+height], (255,255,255), alignment=Align.TOP)

        text_size = font.size(text)
        ready_text = font.render(text, 0, (255,255,255))
        self.screen.blit(ready_text, (WIDTH/2-text_size[0]/2, 25))

        turn_text_size = font.size(turn_text)
        turn_text_obj = font.render(turn_text, 0, (255,0,0) if self.p.my_turn else (255,255,255))
        self.screen.blit(turn_text_obj, (WIDTH/2-turn_text_size[0]/2, 25+text_size[1]))

        for bomb in self.bombs:
            bomb.draw(self.screen)
        for emitter in self.emitters:
            emitter.draw(self.screen)

        reset_text = ""
        if self.reset_requests > 0:
            reset_text = f"Reset {self.reset_requests}/2 "
            reset_text += " press [R]" if self.p.reset_request == False else ""
        draw_text(self.screen, font, reset_text, [0, 0], (255, 0, 0), Align.TOP_LEFT)


        if self.match_started:
            if self.p.ship_board.ship_amount == self.p.ship_board.destroyed:
                draw_text(self.screen, font, "YOU LOST", [WIDTH/2, HEIGHT/2], (255,0,0))
            elif self.p.attack_board.ship_amount == self.p.attack_board.destroyed:
                draw_text(self.screen, font, "YOU WON", [WIDTH/2, HEIGHT/2], (0,255,0))

        if self.n.connected == False:
            font_list = pygame.font.get_fonts()
            new_font = pygame.font.SysFont(font_list[1],size=32, bold=True)
            draw_text(self.screen, new_font, "Not connected", [0, 0], (255,0,0), Align.TOP_LEFT)

        pygame.display.flip()

    def main_menu(self):
        font_list = pygame.font.get_fonts()
        font = pygame.font.SysFont(font_list[0],size=32, bold=True)

        ip_input = inputField(font_list[0], value="127.0.0.1:5555",preview="Enter address : port", pos=[WIDTH/2, HEIGHT/2], width=250, font_size=24)
        join_button = Button(font_list[0], "Join", [WIDTH/2, HEIGHT/2+ip_input.height+10],font_size=24)
        host_button = Button(font_list[0], "Host", [WIDTH/2, join_button.pos[1]+join_button.height+10],font_size=24)

        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    return False

            ip_input.update(events)
            join_button.update(events)
            host_button.update(events)

            if ip_input.submitted() or join_button.pressed():
                try:
                    user_input = ip_input.value.split(":")
                    if len(user_input) == 2:
                        print(f"connecting to {user_input}")
                        self.n.set_address(user_input[0], int(user_input[1]))
                        time.sleep(0.1)
                        print("Joining")
                        self.n.connect()
                        time.sleep(0.1)
                        return True
                except Exception as e:
                    print(e)

            if host_button.pressed():
                host_button.text = "Wait..."
                user_input = ip_input.value.split(":")
                if len(user_input) == 2:
                    print("Hosting")
                    self.server = GameServer()
                    self.server_thread = start_new_thread(self.server.start_server, (user_input[0], int(user_input[1])))
                    timeout = 0.0
                    while not self.server.started or timeout < 2.0:
                        time.sleep(1/FPS_LIMIT)
                        timeout += 1/FPS_LIMIT

                    if self.server.started:
                        timeout = 0.0
                        print(f" server started {self.server.started}")
                    else:
                        print("Failed to start server")
                        break
                    while timeout < 0.5 and self.server.started:
                        time.sleep(1/FPS_LIMIT)
                        timeout += 1/FPS_LIMIT
                        host_button.text = "Joining"
                    self.n.set_address(self.server.server_ip, self.server.server_port)
                    time.sleep(0.1)
                    print("Joining")
                    self.n.connect()
                    time.sleep(0.1)
                    return True
                host_button.text = "Host"

            self.screen.fill((30,30,30))

            draw_text(self.screen, font, "SERVER IP", [WIDTH/2, HEIGHT/2-50], (255,255,255))
            ip_input.draw(self.screen)
            join_button.draw(self.screen)
            host_button.draw(self.screen)

            pygame.display.flip()
            self.dt = self.clock.tick(FPS_LIMIT) / 1000

    def main(self):
        font_list = pygame.font.get_fonts()
        font = pygame.font.SysFont(font_list[0],size=32, bold=True)
        self.reply_thread = start_new_thread(self.manage_replies, ())

        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                    self.running = False
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        self.n.disconnect()
                        self.restart()
                        return
                    if event.key == pygame.K_SPACE:
                        self.n.send(Action.READY)

                    if event.key == pygame.K_r:
                        self.n.send(Action.RESET)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if self.match_started:
                        attack_board_x, attack_board_y = Board.to_grid(mouse_x-ATTACK_BOARD[0], mouse_y-ATTACK_BOARD[1])
                        if event.button == 1 and self.p.my_turn:
                            self.n.send(Action.ATTACK, [attack_board_x, attack_board_y])

            mouse_buttons = pygame.mouse.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            ship_board_x, ship_board_y = Board.to_grid(mouse_pos[0]-SHIP_BOARD[0], mouse_pos[1]-SHIP_BOARD[1])
            if mouse_buttons[0] and not self.match_started:
                self.n.send(Action.PLACE,[ship_board_x, ship_board_y])
            if mouse_buttons[2] and not self.match_started:
                self.n.send(Action.REMOVE,[ship_board_x, ship_board_y])

            for bomb in self.bombs:
                bomb.update(self.dt)
                if bomb.finished:
                    self.bombs.remove(bomb)
            for emitter in self.emitters:
                emitter.update(self.dt)


            self.redraw_screen(font)
            self.dt = self.clock.tick(FPS_LIMIT) / 1000

if __name__ == "__main__":
    game = Game()
    while game.running:
        if game.main_menu():
            game.main()
        if game.server.started:
            game.server.stop_server()
    pygame.quit()

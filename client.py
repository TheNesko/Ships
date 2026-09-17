from random import randint

import pygame
from network import Network
from player import *

WIDTH = 1200
HEIGHT = 700

SHIP_BOARD = (50, 150)
ATTACK_BOARD = (650, 150)

class Game:
    def __init__(self) -> None:
        self.n = Network()
        self.p = self.n.get_p()
        self.p2 = self.n.send(self.p)
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

    def redraw_screen(self, font):
        self.screen.fill((48, 58, 74)) #background

        self.p.ship_board.draw(self.screen, SHIP_BOARD, font, (11,79,189))
        self.p.attack_board.draw(self.screen, ATTACK_BOARD, font, (85,145,242), True)

        text = "Prepare"
        if self.p.ready or self.p2.ready:
            text = "Ready: 1/2"
        if self.players_ready():
            text = "Battle"
        text_size = font.size(text)
        ready_text = font.render(text, 0, (255,255,255))
        self.screen.blit(ready_text, (WIDTH/2-text_size[0]/2, 25))

        pygame.display.flip()

    def players_ready(self):
        return (self.p.ready == True and self.p2.ready == True)

    def toggle_ready(self):
        if self.players_ready(): return False
        self.p.ready = not self.p.ready

    def main(self):
        done = False
        font_list = pygame.font.get_fonts()
        font = pygame.font.SysFont(font_list[0],size=32, bold=True)

        while not done:
            self.p2 = self.n.send(self.p)
            self.p.ship_board = Board.merge(self.p2.attack_board, self.p.ship_board)
            self.p.attack_board = Board.merge(self.p.attack_board, self.p2.ship_board)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        self.toggle_ready()
                if event.type == pygame.MOUSEBUTTONUP:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if self.players_ready():
                        attack_board_x, attack_board_y = Board.to_grid(mouse_x-ATTACK_BOARD[0], mouse_y-ATTACK_BOARD[1])
                        if event.button == 1:
                            self.p.take_a_shot(attack_board_x, attack_board_y)
                    else:
                        ship_board_x, ship_board_y = Board.to_grid(mouse_x-SHIP_BOARD[0], mouse_y-SHIP_BOARD[1])
                        if event.button == 1:
                            self.p.place_ship(ship_board_x, ship_board_y)
                        if event.button == 3:
                            self.p.remove_ship(ship_board_x, ship_board_y)

            self.redraw_screen(font)
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.main()

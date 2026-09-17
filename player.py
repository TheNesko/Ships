import pygame

class Player:
    def __init__(self) -> None:
        self.ship_board = Board()
        self.attack_board = Board()
        self.ready = False

    def place_ship(self, x, y):
        if not self.ship_board.in_grid(x, y): return False
        if not self.ship_board.can_place(x, y): return False
        if self.ship_board.grid[x][y] == Board.SHIP_ID: return False
        self.ship_board.grid[x][y] = Board.SHIP_ID
        return True

    def remove_ship(self, x, y):
        if not self.ship_board.in_grid(x, y): return False
        if self.ship_board.grid[x][y] != Board.SHIP_ID: return False
        self.ship_board.grid[x][y] = Board.EMPTY
        return True

    def take_a_shot(self, x, y):
        if not self.attack_board.in_grid(x, y): return False
        if self.attack_board.grid[x][y] in [Board.CORRECT_SHOT, Board.FAILED_SHOT]: return False
        if self.attack_board.grid[x][y] == Board.SHIP_ID:
            self.attack_board.grid[x][y] = Board.CORRECT_SHOT
            print("Correct")
            if self.attack_board.is_destoyed(x, y):
                self.attack_board.surround_ship(x,y)
                print("Destroyed")
            return True
        self.attack_board.grid[x][y] = Board.FAILED_SHOT
        print("MISS!")
        return True


class Board:

    SIZE = 10
    CELL_SIZE = 50

    EMPTY = 0
    SHIP_ID = 1
    FAILED_SHOT = 2
    CORRECT_SHOT = -1

    NUMERIC = ["1","2","3","4","5","6","7","8","9","10"]
    ALPHABET = ["A","B","C","D","E","F","G","H","I","J"]


    def __init__(self) -> None:
        self.grid = []
        for x in range(Board.SIZE):
            self.grid.append([])
            for y in range(Board.SIZE):
                self.grid[x].append(0)

    @staticmethod
    def to_grid(x,y):
        return x//Board.CELL_SIZE, y//Board.CELL_SIZE

    @staticmethod
    def merge(attack_board, ship_board):
        for x in range(Board.SIZE):
            for y in range(Board.SIZE):
                attack = attack_board.grid[x][y]
                if attack in [Board.FAILED_SHOT, Board.CORRECT_SHOT]:
                    ship_board.grid[x][y] = attack
        return ship_board

    def in_grid(self, x,y):
        if x < 0 or x > Board.SIZE-1: return False
        if y < 0 or y > Board.SIZE-1: return False
        return True

    def can_place(self, x, y):
        horizontal = 0
        vertical = 0
        invalid = [(-1,-1), (1,1), (1,-1), (-1,1)]
        valid = [(1,0), (-1,0), (0,1), (0,-1)]
        for i, j in invalid:
            if not self.in_grid(x+i, y+j): continue
            if self.grid[x+i][y+j] in [Board.SHIP_ID, Board.CORRECT_SHOT]:
                return False

        for i, j in valid:
            if not self.in_grid(x+i, y+j): continue
            if self.grid[x+i][y+j] in [Board.SHIP_ID, Board.CORRECT_SHOT]:
                if i != 0:
                    horizontal += 1
                if j != 0:
                    vertical += 1

        return not (horizontal > 0 and vertical > 0)

    def is_destoyed(self, x, y):
        points = self.get_ship_points(x, y)
        for ship in points:
            if self.grid[ship[0]][ship[1]] == Board.SHIP_ID: return False
        return True

    def surround_ship(self, x, y):
        points = self.get_ship_points(x, y)
        cells = [(-1,-1), (1,1), (1,-1), (-1,1), (1,0), (-1,0), (0,1), (0,-1)]
        for ship in points:
            for cell in cells:
                next = (ship[0]+cell[0], ship[1]+cell[1])
                if not self.in_grid(next[0], next[1]): continue
                if self.grid[next[0]][next[1]] == Board.EMPTY:
                    self.grid[next[0]][next[1]] = Board.FAILED_SHOT

    def get_ship_points(self, x, y):
        points = [(x,y)]
        to_check = [(x,y)]
        neighboars = [(1,0), (-1,0), (0,1), (0,-1)]
        while len(to_check) > 0:
            ship = to_check[0]
            for i, j in neighboars:
                next = (ship[0]+i, ship[1]+j)
                if not self.in_grid(next[0], next[1]): continue
                if self.grid[next[0]][next[1]] in [Board.SHIP_ID, Board.CORRECT_SHOT]:
                    if next in points: continue
                    points.append(next)
                    to_check.append(next)
            to_check.remove(ship)
        return points


    def _draw_ship(self, screen, x, y):
        pygame.draw.rect(
            screen,
            (255,0,255),
            pygame.Rect(
                x,
                y,
                Board.CELL_SIZE,
                Board.CELL_SIZE
            )
        )


    def draw(self, screen, pos, font, color=(0,0,255), fog=False):
        pygame.draw.rect(
            screen,
            color,
            pygame.Rect(
                pos[0],
                pos[1],
                Board.CELL_SIZE * Board.SIZE,
                Board.CELL_SIZE * Board.SIZE)
        )
        # Draw grid lines and Numbers
        for x in range(Board.SIZE):
            x_pos = x * Board.CELL_SIZE
            lines_y = x_pos + pos[1]
            x_pos += pos[0]
            pygame.draw.line(screen, (0,0,0), (x_pos, pos[1]), (x_pos, pos[1]+Board.CELL_SIZE*Board.SIZE))
            pygame.draw.line(screen, (0,0,0), (pos[0], lines_y), (pos[0]+Board.CELL_SIZE*Board.SIZE, lines_y))
        last_y = Board.SIZE * Board.CELL_SIZE + pos[1]
        last_x = Board.SIZE * Board.CELL_SIZE + pos[0]
        pygame.draw.line(screen, (0,0,0), (last_x, pos[1]), (last_x, pos[1]+Board.CELL_SIZE*Board.SIZE))
        pygame.draw.line(screen, (0,0,0), (pos[0], last_y), (pos[0]+Board.CELL_SIZE*Board.SIZE, last_y))

        #Draw numbers/letters
        for x in range(Board.SIZE):
            x_pos = x * Board.CELL_SIZE
            x_pos += pos[0]
            number = Board.NUMERIC[x]
            number_size = font.size(number)
            number_offset_x = Board.CELL_SIZE/2-number_size[0]/2
            number_text = font.render(number,0,(0,0,0))
            screen.blit(number_text,(x_pos+number_offset_x, pos[1]-number_size[1]))

            y_pos = x * Board.CELL_SIZE
            y_pos += pos[1]
            letter = Board.ALPHABET[x]
            letter_size = font.size(letter)
            letter_offset_y = Board.CELL_SIZE/2-letter_size[1]/2
            letter_text = font.render(letter,0,(0,0,0))
            screen.blit(letter_text,(pos[0]-letter_size[0], y_pos+letter_offset_y))

        # Draw ships and shots
        for x in range(Board.SIZE):
            x_pos = x * Board.CELL_SIZE
            x_pos += pos[0]
            for y in range(Board.SIZE):
                y_pos = y * Board.CELL_SIZE
                y_pos += pos[1]
                if self.grid[x][y] == Board.CORRECT_SHOT:
                    self._draw_ship(screen, x_pos, y_pos)
                    top_left = (x_pos, y_pos)
                    bottom_right = (x_pos+Board.CELL_SIZE, y_pos+Board.CELL_SIZE)
                    pygame.draw.line(screen, (255,0,0), top_left, bottom_right,5)
                    top_right = (x_pos+Board.CELL_SIZE, y_pos)
                    bottom_left = (x_pos, y_pos+Board.CELL_SIZE)
                    pygame.draw.line(screen, (255,0,0), top_right, bottom_left,5)
                elif self.grid[x][y] == Board.SHIP_ID:
                    if fog: continue
                    self._draw_ship(screen, x_pos, y_pos)
                elif self.grid[x][y] == Board.FAILED_SHOT:
                    radius = Board.CELL_SIZE/3
                    pygame.draw.circle(
                        screen,
                        (255,255,255),
                        (x_pos+Board.CELL_SIZE/2, y_pos+Board.CELL_SIZE/2),
                        radius
                    )

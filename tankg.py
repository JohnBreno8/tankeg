import curses
import random
import time

MAP_WIDTH = 40
MAP_HEIGHT = 20
TANK_CHAR = "▩"
ENEMY_CHAR = "▅"
BULLET_CHAR = "◉"
OBSTACLE_CHAR = "▒"

def setup_colors():
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) 
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)   
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

GAME_MODES = ["Clássico", "Sobrevivência", "Estratégico", "Caótico"]

class Tank:
    def __init__(self, x, y, char, color, is_player=False):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.direction = "UP"
        self.is_player = is_player
        self.bullets = []
        self.lives = 3 if is_player else 1

    def move(self, direction, obstacles):
        new_x, new_y = self.x, self.y
        if direction == "UP": new_y -= 1
        elif direction == "DOWN": new_y += 1
        elif direction == "LEFT": new_x -= 1
        elif direction == "RIGHT": new_x += 1

        if 0 < new_x < MAP_WIDTH - 1 and 0 < new_y < MAP_HEIGHT - 1 and (new_x, new_y) not in obstacles:
            self.x, self.y = new_x, new_y
            self.direction = direction

    def shoot(self):
        directions = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
        dx, dy = directions[self.direction]
        self.bullets.append([self.x + dx, self.y + dy, self.direction])

class EnemyTank(Tank):
    def __init__(self, x, y, strategy):
        super().__init__(x, y, ENEMY_CHAR, 2)
        self.strategy = strategy

    def ai_move(self, player_x, player_y, obstacles):
        if self.strategy == "agressivo":
            if random.random() < 0.4: self.shoot()
            self.move(random.choice(["UP", "DOWN", "LEFT", "RIGHT"]), obstacles)
        elif self.strategy == "estratégico":
            if abs(player_x - self.x) <= 3 and abs(player_y - self.y) <= 3:
                self.shoot()
            else:
                self.move("UP" if player_y < self.y else "DOWN", obstacles)
                self.move("LEFT" if player_x < self.x else "RIGHT", obstacles)
        elif self.strategy == "furtivo":
            if random.random() < 0.1:
                self.move(random.choice(["UP", "DOWN", "LEFT", "RIGHT"]), obstacles)

    def shoot_at_player(self, player_x, player_y):
        directions = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
        if self.x < player_x:
            direction = "RIGHT"
        elif self.x > player_x:
            direction = "LEFT"
        elif self.y < player_y:
            direction = "DOWN"
        else:
            direction = "UP"
        
        dx, dy = directions[direction]
        self.bullets.append([self.x + dx, self.y + dy, direction])

class Game:
    def __init__(self, stdscr, mode):
        self.stdscr = stdscr
        self.mode = mode
        setup_colors()
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.timeout(100)

        self.reset_game()

    def reset_game(self):
        self.player = Tank(MAP_WIDTH // 2, MAP_HEIGHT - 2, TANK_CHAR, 1, is_player=True)
        self.enemies = [EnemyTank(random.randint(1, MAP_WIDTH - 2), random.randint(1, MAP_HEIGHT // 2), random.choice(["agressivo", "estratégico", "furtivo"])) for _ in range(3)]
        self.obstacles = {(random.randint(2, MAP_WIDTH - 3), random.randint(2, MAP_HEIGHT - 3)) for _ in range(10)}
        self.score = 0
        self.start_time = time.time()
        self.fps_counter = 0
        self.last_fps_update = time.time()
        self.fps = 0

    def update_bullets(self, bullets, owner):
        new_bullets = []
        for bullet in bullets:
            x, y, direction = bullet
            if direction == "UP": y -= 1
            elif direction == "DOWN": y += 1
            elif direction == "LEFT": x -= 1
            elif direction == "RIGHT": x += 1

            if (x, y) in self.obstacles:
                continue

            if owner.is_player:
                for enemy in self.enemies:
                    if (x, y) == (enemy.x, enemy.y):
                        self.enemies.remove(enemy)
                        self.score += 10
                        continue
            else:
                if (x, y) == (self.player.x, self.player.y):
                    self.player.lives -= 1
                    if self.player.lives == 0:
                        self.end_game(False)
                    continue

            if 0 < x < MAP_WIDTH - 1 and 0 < y < MAP_HEIGHT - 1:
                new_bullets.append([x, y, direction])

        return new_bullets

    def draw(self):
        self.stdscr.clear()
        self.stdscr.border(0)

        elapsed_time = time.time() - self.start_time
        if time.time() - self.last_fps_update > 1:
            self.fps = self.fps_counter
            self.fps_counter = 0
            self.last_fps_update = time.time()

        self.stdscr.addstr(0, 2, f"🏆 Pontos: {self.score} | ⏳ Tempo: {int(elapsed_time)}s | 🎞️ FPS: {self.fps} | ❤️ Vidas: {self.player.lives}", curses.color_pair(4))

        for obs in self.obstacles:
            self.stdscr.addch(obs[1], obs[0], OBSTACLE_CHAR, curses.color_pair(5))

        self.stdscr.addch(self.player.y, self.player.x, self.player.char, curses.color_pair(self.player.color))
        for enemy in self.enemies:
            self.stdscr.addch(enemy.y, enemy.x, enemy.char, curses.color_pair(enemy.color))

        for bullet in self.player.bullets:
            self.stdscr.addch(bullet[1], bullet[0], BULLET_CHAR, curses.color_pair(3))

        for enemy in self.enemies:
            for bullet in enemy.bullets:
                self.stdscr.addch(bullet[1], bullet[0], BULLET_CHAR, curses.color_pair(2))

        self.stdscr.refresh()
        self.fps_counter += 1

    def run(self):
        while True:
            key = self.stdscr.getch()

            if key == ord('q'):
                break
            elif key == curses.KEY_UP:
                self.player.move("UP", self.obstacles)
            elif key == curses.KEY_DOWN:
                self.player.move("DOWN", self.obstacles)
            elif key == curses.KEY_LEFT:
                self.player.move("LEFT", self.obstacles)
            elif key == curses.KEY_RIGHT:
                self.player.move("RIGHT", self.obstacles)
            elif key == ord('a'):
                self.player.shoot()

            for enemy in self.enemies:
                enemy.ai_move(self.player.x, self.player.y, self.obstacles)
                enemy.shoot_at_player(self.player.x, self.player.y)

            self.player.bullets = self.update_bullets(self.player.bullets, self.player)
            for enemy in self.enemies:
                enemy.bullets = self.update_bullets(enemy.bullets, enemy)

            self.draw()

            if self.player.lives <= 0 or len(self.enemies) == 0:
                self.end_game(True if self.player.lives > 0 else False)
                self.reset_game()

    def end_game(self, win):
        self.stdscr.clear()
        if win:
            self.stdscr.addstr(MAP_HEIGHT // 2, MAP_WIDTH // 2 - 5, "Você ganhou!", curses.color_pair(3))
        else:
            self.stdscr.addstr(MAP_HEIGHT // 2, MAP_WIDTH // 2 - 6, "Você perdeu!", curses.color_pair(2))
        self.stdscr.refresh()
        time.sleep(2)

def menu(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    stdscr.addstr(5, 10, "Jogo de Tanques de Guerra", curses.color_pair(4))
    stdscr.addstr(7, 10, "Escolha um modo:", curses.color_pair(4))

    for i, mode in enumerate(GAME_MODES):
        stdscr.addstr(9 + i, 10, f"{i + 1} - {mode}")

    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in range(ord('1'), ord('1') + len(GAME_MODES)):
            return GAME_MODES[key - ord('1')]

curses.wrapper(lambda stdscr: Game(stdscr, menu(stdscr)).run())

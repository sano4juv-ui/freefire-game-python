import math
import random
import sys

import pygame

# ------------------
# Config
# ------------------
WIDTH, HEIGHT = 1000, 700
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 220, 70)
ORANGE = (255, 140, 0)
GRAY = (120, 120, 120)


class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.radius = 16
        self.speed = 4
        self.health = 100
        self.ammo = 30
        self.max_health = 100
        self.fire_cooldown = 0
        self.last_direction = (1, 0)

    def move(self, keys):
        dx = 0
        dy = 0

        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1

        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
            self.x += dx * self.speed
            self.y += dy * self.speed

            self.last_direction = (dx, dy)

        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

    def shoot(self, target_x, target_y):
        if self.fire_cooldown > 0 or self.ammo <= 0:
            return None

        self.ammo -= 1
        self.fire_cooldown = 0.12

        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy) or 1

        bullet = {
            "x": self.x,
            "y": self.y,
            "vx": (dx / distance) * 8,
            "vy": (dy / distance) * 8,
            "radius": 5,
            "color": YELLOW,
        }
        return bullet

    def take_damage(self, amount):
        self.health -= amount
        self.health = max(0, self.health)

    def draw(self, screen):
        pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), self.radius)
        # a small direction indicator
        dir_x = self.x + self.last_direction[0] * (self.radius + 8)
        dir_y = self.y + self.last_direction[1] * (self.radius + 8)
        pygame.draw.line(screen, WHITE, (self.x, self.y), (dir_x, dir_y), 3)


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 14
        self.speed = random.randint(1, 2)
        self.health = 50

    def update(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.hypot(dx, dy) or 1
        self.x += (dx / distance) * self.speed
        self.y += (dy / distance) * self.speed

        if math.hypot(player.x - self.x, player.y - self.y) < self.radius + player.radius:
            player.take_damage(1)

    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)


class Loot:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.radius = 8
        self.kind = kind
        if kind == "medkit":
            self.color = GREEN
        elif kind == "ammo":
            self.color = ORANGE
        else:
            self.color = GRAY

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Battle Royale Prototype")
        self.clock = pygame.time.Clock()

        self.player = Player()
        self.enemies = []
        self.bullets = []
        self.loot = []
        self.game_over = False
        self.safe_zone = {
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "radius": 320,
            "damage": 5,
        }

        for _ in range(12):
            self.enemies.append(Enemy(random.randint(30, WIDTH - 30), random.randint(30, HEIGHT - 30)))

        for _ in range(12):
            kind = random.choice(["medkit", "ammo", "armor"])
            self.loot.append(Loot(random.randint(30, WIDTH - 30), random.randint(30, HEIGHT - 30), kind))

    def spawn_enemy(self):
        self.enemies.append(Enemy(random.randint(20, WIDTH - 20), random.randint(20, HEIGHT - 20)))

    def update_safe_zone(self):
        self.safe_zone["radius"] = max(80, self.safe_zone["radius"] - 0.08)
        dist = math.hypot(self.player.x - self.safe_zone["x"], self.player.y - self.safe_zone["y"])
        if dist > self.safe_zone["radius"]:
            self.player.take_damage(self.safe_zone["damage"])

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.game_over:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                bullet = self.player.shoot(mouse_x, mouse_y)
                if bullet:
                    self.bullets.append(bullet)

        keys = pygame.key.get_pressed()
        if not self.game_over:
            self.player.move(keys)
        return True

    def update(self):
        if self.game_over:
            return

        self.update_safe_zone()

        for enemy in self.enemies:
            enemy.update(self.player)

        for bullet in self.bullets[:]:
            bullet["x"] += bullet["vx"]
            bullet["y"] += bullet["vy"]

            if bullet["x"] < 0 or bullet["x"] > WIDTH or bullet["y"] < 0 or bullet["y"] > HEIGHT:
                self.bullets.remove(bullet)
                continue

            for enemy in self.enemies[:]:
                if math.hypot(enemy.x - bullet["x"], enemy.y - bullet["y"]) < enemy.radius + bullet["radius"]:
                    enemy.health -= 25
                    self.bullets.remove(bullet)
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                    break

        for item in self.loot[:]:
            if math.hypot(self.player.x - item.x, self.player.y - item.y) < self.player.radius + item.radius + 5:
                if item.kind == "medkit":
                    self.player.health = min(self.player.max_health, self.player.health + 25)
                elif item.kind == "ammo":
                    self.player.ammo += 12
                else:
                    self.player.health = min(self.player.max_health, self.player.health + 15)
                self.loot.remove(item)

        if len(self.enemies) < 15 and random.random() < 0.02:
            self.spawn_enemy()

        if self.player.health <= 0:
            self.game_over = True

    def draw_hud(self):
        font = pygame.font.SysFont(None, 32)
        health_text = font.render(f"Health: {self.player.health}", True, WHITE)
        ammo_text = font.render(f"Ammo: {self.player.ammo}", True, WHITE)
        zone_text = font.render(f"Zone Radius: {int(self.safe_zone['radius'])}", True, WHITE)

        self.screen.blit(health_text, (20, 20))
        self.screen.blit(ammo_text, (20, 55))
        self.screen.blit(zone_text, (20, 90))

        if self.game_over:
            over_font = pygame.font.SysFont(None, 60)
            text = over_font.render("YOU DIED", True, RED)
            self.screen.blit(text, (WIDTH // 2 - 140, HEIGHT // 2 - 30))
            hint = pygame.font.SysFont(None, 28)
            restart_text = hint.render("Press R to restart", True, WHITE)
            self.screen.blit(restart_text, (WIDTH // 2 - 95, HEIGHT // 2 + 30))

    def draw(self):
        self.screen.fill(BLACK)

        pygame.draw.circle(self.screen, (35, 60, 90), (int(self.safe_zone["x"]), int(self.safe_zone["y"])), int(self.safe_zone["radius"]), 2)

        for item in self.loot:
            item.draw(self.screen)

        for bullet in self.bullets:
            pygame.draw.circle(self.screen, bullet["color"], (int(bullet["x"]), int(bullet["y"])), bullet["radius"])

        for enemy in self.enemies:
            enemy.draw(self.screen)

        self.player.draw(self.screen)
        self.draw_hud()
        pygame.display.flip()

    def run(self):
        while True:
            running = self.handle_events()
            if not running:
                pygame.quit()
                sys.exit()

            if self.game_over:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_r]:
                    self.__init__()
            else:
                self.update()

            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
    game.run()

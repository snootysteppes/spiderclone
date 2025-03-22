import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Constants
# Get screen info
screen_info = pygame.display.Info()
WINDOW_WIDTH = screen_info.current_w
WINDOW_HEIGHT = screen_info.current_h
WORLD_WIDTH = WINDOW_WIDTH * 6  # 6 screens wide for more space
FPS = 60
GRAVITY = 0.5
SWING_SPEED = 12  # Lower launch speed for smoother movement
JUMP_SPEED = -15
NORMAL_TIME_SCALE = 1.0
SLOW_TIME_SCALE = 0.3
CAMERA_SCALE = 1.5
SWING_CONTROL_FORCE = 0.1  # Smoother control
MAX_SWING_SPEED = 8  # Add back swing speed limit

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
SKY_TOP = (135, 206, 235)
SKY_BOTTOM = (65, 105, 225)

# Initialize window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("SpiderClone")
clock = pygame.time.Clock()

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover = False

    def draw(self, surface):
        color = (min(self.color[0] + 30, 255), 
                min(self.color[1] + 30, 255), 
                min(self.color[2] + 30, 255)) if self.hover else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)
        
        font = pygame.font.Font(None, 36)
        text = font.render(self.text, True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hover:
                return True
        return False

class MainMenu:
    def __init__(self):
        self.buttons = {
            'play': Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 100, 300, 60, "Play", (50, 50, 200)),
            'help': Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2, 300, 60, "Help", (50, 150, 50)),
            'settings': Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 100, 300, 60, "Settings", (150, 50, 50)),
            'exit': Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 200, 300, 60, "Exit Game", (200, 50, 50))
        }
        self.splash_text = "Made by Snooty!"
        self.splash_scale = 1.0
        self.scale_increasing = True
        self.selected = None

    def update(self):
        # Update splash text pulsing
        if self.scale_increasing:
            self.splash_scale += 0.01
            if self.splash_scale >= 1.2:
                self.scale_increasing = False
        else:
            self.splash_scale -= 0.01
            if self.splash_scale <= 0.8:
                self.scale_increasing = True

    def draw(self, surface):
        # Draw gradient background
        draw_gradient_background(surface)
        
        # Draw title
        title_font = pygame.font.Font(None, 72)
        title = title_font.render("SpiderClone", True, WHITE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 150))
        surface.blit(title, title_rect)
        
        # Draw pulsating splash text
        splash_font = pygame.font.Font(None, int(36 * self.splash_scale))
        splash = splash_font.render(self.splash_text, True, (255, 255, 0))
        splash_rect = splash.get_rect(center=(WINDOW_WIDTH//2, 200))
        surface.blit(splash, splash_rect)
        
        # Draw buttons
        for button in self.buttons.values():
            button.draw(surface)

    def handle_event(self, event):
        for name, button in self.buttons.items():
            if button.handle_event(event):
                self.selected = name
                return True
        return False

def draw_gradient_background(surface):
    for y in range(WINDOW_HEIGHT):
        factor = y / WINDOW_HEIGHT
        color = [
            SKY_TOP[i] * (1 - factor) + SKY_BOTTOM[i] * factor
            for i in range(3)
        ]
        pygame.draw.line(surface, color, (0, y), (WINDOW_WIDTH, y))

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = WINDOW_WIDTH
        self.height = WINDOW_HEIGHT

    def apply(self, entity):
        return (entity.x - self.x, entity.y)

    def update(self, target):
        self.x = target.x - WINDOW_WIDTH // 2
        self.x = max(0, min(self.x, WORLD_WIDTH - WINDOW_WIDTH))

class Player:
    def __init__(self):
        self.x = 100
        self.y = 300
        self.vel_x = 0
        self.vel_y = 0
        self.size = 20
        self.is_swinging = False
        self.swing_point = None
        self.swing_length = 0
        self.swing_angle = 0
        self.swing_speed = 0  # Angular velocity for pendulum motion
        self.jumps_remaining = 2

    def jump(self):
        if self.jumps_remaining > 0:
            self.vel_y = JUMP_SPEED
            self.jumps_remaining -= 1

    def draw(self, screen, camera):
        screen_pos = camera.apply(self)
        if self.is_swinging and self.swing_point:
            screen_swing_point = (self.swing_point[0] - camera.x, self.swing_point[1])
            pygame.draw.line(screen, WHITE, screen_pos, screen_swing_point, 2)
        
        pygame.draw.circle(screen, RED, (int(screen_pos[0]), int(screen_pos[1])), self.size)
        pygame.draw.line(screen, BLACK, 
                        (screen_pos[0] - self.size/2, screen_pos[1]),
                        (screen_pos[0] + self.size/2, screen_pos[1]), 2)
        pygame.draw.line(screen, BLACK,
                        (screen_pos[0], screen_pos[1] - self.size/2),
                        (screen_pos[0], screen_pos[1] + self.size/2), 2)

    def update(self, time_scale, keys_pressed):
        if not self.is_swinging:
            # Regular movement
            self.vel_y += GRAVITY * time_scale
            self.x += self.vel_x * time_scale
            self.y += self.vel_y * time_scale
        else:
            # Simple swing physics
            if keys_pressed[pygame.K_a]:  # Swing left
                self.swing_speed -= SWING_CONTROL_FORCE * time_scale
            if keys_pressed[pygame.K_d]:  # Swing right
                self.swing_speed += SWING_CONTROL_FORCE * time_scale
            
            # Cap swing speed
            self.swing_speed = max(-MAX_SWING_SPEED, min(MAX_SWING_SPEED, self.swing_speed))
            
            # Update angle based on swing speed
            self.swing_angle += self.swing_speed * time_scale
            
            # Calculate new position
            self.x = self.swing_point[0] + math.cos(self.swing_angle) * self.swing_length
            self.y = self.swing_point[1] + math.sin(self.swing_angle) * self.swing_length
            
            # Store velocity for release
            self.vel_x = math.cos(self.swing_angle) * self.swing_speed * SWING_SPEED
            self.vel_y = math.sin(self.swing_angle) * self.swing_speed * SWING_SPEED

        self.x = max(self.size, min(self.x, WORLD_WIDTH - self.size))
        old_y = self.y
        self.y = max(self.size, min(self.y, WINDOW_HEIGHT - self.size))
        
        if self.y == WINDOW_HEIGHT - self.size and old_y != self.y:
            self.jumps_remaining = 2
            self.vel_y = 0

class Building:
    def __init__(self, x, width, height):
        self.x = x
        self.width = width
        self.height = height
        self.color = GRAY
        self.windows = []
        self.generate_windows()

    def generate_windows(self):
        window_size = 15
        window_spacing = 30
        for x in range(self.width // window_spacing):
            for y in range(self.height // window_spacing):
                if random.random() > 0.2:
                    self.windows.append((
                        x * window_spacing + window_spacing//2,
                        y * window_spacing + window_spacing//2,
                        window_size
                    ))

    def draw(self, screen, camera):
        screen_x = self.x - camera.x
        pygame.draw.rect(screen, self.color, 
                        (screen_x, WINDOW_HEIGHT - self.height, self.width, self.height))
        for wx, wy, ws in self.windows:
            pygame.draw.rect(screen, BLUE,
                           (screen_x + wx - ws//2,
                            WINDOW_HEIGHT - self.height + wy - ws//2,
                            ws, ws))

class Level:
    def __init__(self, number):
        self.buildings = []
        self.generate_buildings(number)
        self.start_x = 100
        self.end_x = WORLD_WIDTH - 100

    def generate_buildings(self, level_number):
        num_buildings = 12 + level_number * 2
        building_spacing = WORLD_WIDTH // (num_buildings - 1)
        
        for i in range(num_buildings):
            width = random.randint(100, 200)  # Even wider buildings
            height = random.randint(int(WINDOW_HEIGHT * 0.6), int(WINDOW_HEIGHT * 0.9))  # Scale with screen height
            x = i * building_spacing
            if i == 0:
                height = 250
            self.buildings.append(Building(x, width, height))

    def draw(self, screen, camera):
        draw_gradient_background(screen)
        for building in self.buildings:
            building.draw(screen, camera)
        finish_x = self.end_x - camera.x
        pygame.draw.line(screen, RED, (finish_x, 0), (finish_x, WINDOW_HEIGHT), 5)

class Game:
    def __init__(self):
        self.menu = MainMenu()
        self.state = "MENU"  # MENU, PLAYING, HELP, SETTINGS
        self.help_back_btn = Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT - 100, 300, 60, "Back to Menu", (200, 50, 50))
        self.settings_back_btn = Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT - 100, 300, 60, "Back to Menu", (200, 50, 50))
        self.reset_level(1)

    def reset_level(self, level_number):
        self.current_level = level_number
        self.level = Level(self.current_level)
        self.player = Player()
        self.camera = Camera()
        self.time_scale = NORMAL_TIME_SCALE
        self.running = True
        self.show_tutorial = True
        self.tutorial_timer = 600

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if self.state == "MENU":
                if self.menu.handle_event(event):
                    if self.menu.selected == "play":
                        self.state = "PLAYING"
                    elif self.menu.selected == "help":
                        self.state = "HELP"
                    elif self.menu.selected == "settings":
                        self.state = "SETTINGS"
                    elif self.menu.selected == "exit":
                        self.running = False
            elif self.state == "HELP":
                if self.help_back_btn.handle_event(event):
                    self.state = "MENU"
            elif self.state == "SETTINGS":
                if self.settings_back_btn.handle_event(event):
                    self.state = "MENU"
                        
            elif self.state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                    elif event.key == pygame.K_SPACE:
                        if self.show_tutorial:
                            self.show_tutorial = False
                        else:
                            self.player.jump()
                    elif event.key == pygame.K_r:
                        self.reset_level(self.current_level)
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.show_tutorial:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    world_mouse_x = mouse_x + self.camera.x
                    self.player.swing_point = (world_mouse_x, mouse_y)
                    self.player.is_swinging = True
                    dx = self.player.x - world_mouse_x
                    dy = self.player.y - mouse_y
                    self.player.swing_length = math.sqrt(dx*dx + dy*dy)
                    self.player.swing_angle = math.atan2(dy, dx)
                    self.player.swing_speed = 0  # Reset swing speed on new swing
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.player.is_swinging:
                        self.player.is_swinging = False
                        # Velocity is already stored during swing updates

    def update(self):
        if self.state == "MENU":
            self.menu.update()
        elif self.state == "PLAYING":
            if self.show_tutorial:
                self.tutorial_timer -= 1
                if self.tutorial_timer <= 0:
                    self.show_tutorial = False
                return

            if abs(self.player.vel_x) < 1 and abs(self.player.vel_y) < 1:
                self.time_scale = SLOW_TIME_SCALE
            else:
                self.time_scale = NORMAL_TIME_SCALE

            # Get keyboard state
            keys = pygame.key.get_pressed()
            self.player.update(self.time_scale, keys)
            self.camera.update(self.player)

            if self.player.x >= self.level.end_x:
                self.current_level += 1
                if self.current_level <= 3:
                    self.reset_level(self.current_level)
                else:
                    self.state = "MENU"

    def draw(self):
        if self.state == "MENU":
            self.menu.draw(screen)
        elif self.state == "PLAYING":
            self.level.draw(screen, self.camera)
            self.player.draw(screen, self.camera)
            
            font = pygame.font.Font(None, 36)
            level_text = font.render(f"Level {self.current_level}", True, WHITE)
            screen.blit(level_text, (10, 10))
            
            if self.show_tutorial:
                tutorial_font = pygame.font.Font(None, 32)
                messages = [
                    "Welcome to SpiderClone!",
                "Click and hold anywhere to shoot web and swing",
                "Use A and D to control your swing direction",
                "Swing from below for extra upward pull!",
                "Longer webs give stronger upward pull",
                    "Release to launch yourself",
                    "Press SPACE to jump (you can double jump!)",
                    "Time slows down when you're not moving",
                    "Press R to restart the current level",
                    "Press ESC to return to menu",
                    "Reach the red line to complete the level!",
                    "Press SPACE to skip tutorial"
                ]
                
                y_offset = WINDOW_HEIGHT // 3
                for msg in messages:
                    text = tutorial_font.render(msg, True, WHITE)
                    text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, y_offset))
                    pygame.draw.rect(screen, (0, 0, 0, 128), text_rect.inflate(20, 10))
                    screen.blit(text, text_rect)
                    y_offset += 40
        elif self.state == "HELP":
            draw_gradient_background(screen)
            font = pygame.font.Font(None, 36)
            # Help menu
            self.help_back_btn.draw(screen)
                
            messages = [
                "How to Play:",
                "- Click and hold to shoot web and swing",
                "- Use A and D to control swing direction",
                "- Build momentum by swinging",
                "- Release at the right moment to launch",
                "- Double jump with SPACE",
                "- Press R to restart level"
            ]
            y = WINDOW_HEIGHT//4
            for msg in messages:
                text = font.render(msg, True, WHITE)
                text_rect = text.get_rect(center=(WINDOW_WIDTH//2, y))
                screen.blit(text, text_rect)
                y += 50
        elif self.state == "SETTINGS":
            draw_gradient_background(screen)
            font = pygame.font.Font(None, 36)
            # Settings menu
            self.settings_back_btn.draw(screen)
            
            text = font.render("Settings", True, WHITE)
            text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//4))
            screen.blit(text, text_rect)
        
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()

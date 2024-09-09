import time  # currently unused

import pygame.event

from menu import *
from menu_components import *
from figure_class import *
from text_prompt import InputBox
import os
import colorsys


def render_multi_line_text(screen, text, font, position, gap, color=(0, 0, 0), anital=False, fill=False,
                           screen_color=(255, 255, 255)):
    """
    Renders multi-line text onto the screen.

    Parameters:
    - screen: The surface on which the text will be rendered.
    - text: The text string which may contain newline characters.
    - font: The pygame font object to be used for rendering.
    - position: A tuple specifying the (x, y) position where the top of the text block will begin.
    - gap: The vertical gap (in pixels) between lines.
    - color: The color of the text.
    """

    lines = text.split('\n')
    x, y = position
    if fill:
        screen.fill(screen_color)
    for line in lines:
        text_surface = font.render(line, anital, color)
        screen.blit(text_surface, (x, y))
        y += font.get_height() + gap


red = (255, 0, 0)


class UpgradeButton:
    def __init__(self, game_instance, name, position, width, height, text, font, font_size, color, hover_color,
                 click_function, upgrade):
        self.game_instance = game_instance
        self.name = name
        self.rect = pygame.Rect(position[0], position[1], width, height)
        self.text = text
        self.font = font
        self.font_size = font_size
        self.color = color
        self.hover_color = hover_color
        self.click_function = click_function
        self.hovered = False
        self.is_purchaseable = True
        self.not_purchaseable_color = (255, 0, 0)
        self.upgrade = upgrade

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.click_function()
                if self.is_purchaseable:
                    self.upgrade.cost = int(
                        self.upgrade.cost * 1.2)  # so the price does not increase if the upgrade can't be bought
                    if self.upgrade.max_uses:
                        self.upgrade.uses += 1
                        ic(self.upgrade.name, self.upgrade.uses, self.upgrade.max_uses)

    def multi_line_render(self, text, font, rect, color=(0, 0, 0)):
        #Renders multi-line text and blits it onto the window.

        # Split the text into lines
        lines = text.split('\n')
        total_height = len(lines) * font.get_height()
        start_y = rect.centery - total_height // 2  # This will vertically center the text block

        rendered_lines = []  # List to hold rendered text surfaces and their rects

        for line in lines:
            text_surface = font.render(line, False, color)
            text_rect = text_surface.get_rect(centerx=rect.centerx, top=start_y)
            rendered_lines.append((text_surface, text_rect))
            start_y += font.get_height()  # Move the y-position down for the next line

        return rendered_lines

    def draw_tooltip(self, window):
        if self.hovered:
            font_size = 24  # or any desired size
            font = pygame.font.Font(self.game_instance.game_font, font_size)

            # Define tooltip dimensions and position (you can adjust these):
            tooltip_width = 300
            tooltip_height = 100
            tooltip_x = self.rect.x + self.rect.width + 10  # Displaying tooltip to the right of the button
            tooltip_y = self.rect.y

            # Create tooltip surface and draw on it:
            tooltip_surface = pygame.Surface((tooltip_width, tooltip_height))
            tooltip_surface.fill((0, 0, 0))  # Fill with black color

            # Rendering multi-line description:
            lines = self.upgrade.description.split('\n')  # Split the text into lines
            y_text_start = 10  # Starting y position for the description

            for line in lines:
                description_text_line = font.render(line, True, (255, 255, 255))
                tooltip_surface.blit(description_text_line, (10, y_text_start))
                y_text_start += font_size  # Move the y position down for the next line

            # Render cost and blit onto tooltip:
            cost_text = font.render(f"Cost: {self.upgrade.cost} coins", True, (255, 255, 255))
            tooltip_surface.blit(cost_text, (10, y_text_start + 5))  # Adding a 5-pixel gap between description and cost

            # Blit tooltip surface onto the main window:
            window.blit(tooltip_surface, (tooltip_x, tooltip_y))

    def draw(self, window):
        font = pygame.font.Font(self.font, self.font_size)

        # Modify this line to handle the not purchaseable color:
        current_color = self.not_purchaseable_color if not self.is_purchaseable else (
            self.hover_color if self.hovered else self.color)

        pygame.draw.rect(window, current_color, self.rect)

        # Use the multi_line_render method
        rendered_lines = self.multi_line_render(self.text, font, self.rect)
        for text_surface, text_rect in rendered_lines:
            window.blit(text_surface, text_rect)
        self.draw_tooltip(window)


class Stage:
    def __init__(self, name, enemy_pool, max_enemies, score_threshold, bosses_destroyed_threshold, game,
                 boss_spawned=False,
                 spawn_interval_modifier=1.0, enemy_speed_modifier=1.0, stage_type="regular", placement_pattern=None):
        self.name = name
        self.enemy_pool = enemy_pool  # List of enemy types available in this stage
        self.max_enemies = max_enemies
        self.spawn_interval_modifier = spawn_interval_modifier  # Multiplier to adjust spawn interval
        self.enemy_speed_modifier = enemy_speed_modifier  # Multiplier to adjust enemy speed or behavior
        self.stage_type = stage_type
        self.score_threshold = score_threshold
        self.bosses_destroyed_threshold = bosses_destroyed_threshold
        self.boss_spawned = boss_spawned
        self.obstacle = obstacle_a  # uses a predefined obstacle of the figure class
        self.game = game
        self.obstacles_spawned = False
        self.placement_pattern = placement_pattern
        if self.placement_pattern == "two_pillars":
            self.generate_pillar_pattern()
        elif self.placement_pattern == "center":
            self.generate_center_pattern()
        elif self.placement_pattern == "cross":
            self.generate_cross_pattern()

    def generate_pillar_pattern(self):
        # one that fits a multitude of screens
        positions = []
        obstacle_height = self.obstacle.dimensions[1]

        # Calculate x positions for the two pillars
        x1 = self.game.window_dimensions[0] * 0.25  # 1/4 of the screen width from the left
        x2 = self.game.window_dimensions[0] * 0.75  # 3/4 of the screen width from the left

        # Calculate y positions for the top and bottom
        ytop = self.game.window_dimensions[1] // 6
        ybottom = self.game.window_dimensions[1] * 5 // 6

        # Generate positions for the pillars
        current_y = ytop
        while current_y < ybottom:
            positions.append([x1, current_y])
            positions.append([x2, current_y])
            current_y += obstacle_height * 2

        self.placement_pattern = positions

    def generate_center_pattern(self):

        # calculate the center of the screen
        x = self.game.window_dimensions[0] // 2
        y = self.game.window_dimensions[1] // 2

        pos1 = [x + self.obstacle.dimensions[0], y + self.obstacle.dimensions[1]]
        pos2 = [x - self.obstacle.dimensions[0], y + self.obstacle.dimensions[1]]
        pos3 = [x + self.obstacle.dimensions[0], y - self.obstacle.dimensions[1]]
        pos4 = [x - self.obstacle.dimensions[0], y - self.obstacle.dimensions[1]]

        self.placement_pattern = [pos1, pos2, pos3, pos4]

    def generate_cross_pattern(self):
        positions = []

        # Calculate the center of the screen
        screen_center_x = self.game.window_dimensions[0] // 2
        screen_center_y = self.game.window_dimensions[1] // 2

        # Calculate the half dimensions of the obstacle
        obstacle_width = self.obstacle.dimensions[0] * 1.2
        obstacle_height = self.obstacle.dimensions[1] * 1.2

        # Vertical part of the cross
        for i in range(-2, 2):  # Adjust the range to fit the desired number of obstacles in the vertical line
            x_pos = screen_center_x - obstacle_width
            y_pos = screen_center_y + i * obstacle_height
            positions.append([x_pos, y_pos])
        # Horizontal part of the cross
        for i in range(-2, 3):  # Adjust the range to fit the desired number of obstacles in the horizontal line
            x_pos = screen_center_x + i * obstacle_width
            y_pos = screen_center_y - obstacle_height
            if x_pos != screen_center_x:  # Leave the center open
                positions.append([x_pos, y_pos])

        self.placement_pattern = positions

    def manage_obstacles(self):
        obstacles = []
        if self.placement_pattern:
            if not self.obstacles_spawned:
                for pos in self.placement_pattern:
                    current_obstacle = self.obstacle.clone()
                    current_obstacle.position = pos
                    obstacles.append(current_obstacle)
                self.obstacles_spawned = True
        return obstacles
        # middle_x = self.game.window_dimensions[0] // 2
        # middle_y = self.game.window_dimensions[1] // 2
        # self.obstacle.position = [middle_x, middle_y]


class Game:
    def __init__(self, caption, window_dimensions, cursor, player_template=None, enemies=None, bosses=None, fps=60,
                 background_image_path=None, scale_background=True, game_font=None,
                 player_unkillable=False, debug_mode=False, animation_templates=None, screen_scale=None):

        self.game_over_time = None
        self.is_running = True
        self.caption = caption
        self.state = "main_menu"
        self.previous_state = "main_menu"
        pygame.display.set_caption(caption)
        self.window_dimensions = window_dimensions
        self.base_window_dimensions = [2560, 1440]
        self.object_scale_factor = [self.window_dimensions[0] / self.base_window_dimensions[0],
                                    self.window_dimensions[1] / self.base_window_dimensions[1]]
        self.player_alive = True
        self.stage_index = 0
        self.game_font = game_font
        self.debug_mode = debug_mode
        self.debug_text_boxes = []

        self.frame_counter = 0

        self.player_unkillable = player_unkillable

        self.cursor = cursor
        self.player_template = player_template
        player_template.x_limit = self.window_dimensions[0]
        player_template.y_limit = self.window_dimensions[1]
        self.player = player_template.clone()

        self.scale_background = scale_background
        if background_image_path is not None and scale_background:
            self.background_image = pygame.transform.scale(pygame.image.load(background_image_path), window_dimensions)
        elif background_image_path is not None and not scale_background:
            self.background_image = pygame.image.load(background_image_path)
        else:
            self.background_image = None
        self.window = pygame.display.set_mode(window_dimensions, pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.spawn_queue = []
        self.figures = []
        self.animation_templates = animation_templates
        self.animations = []
        self.enemies = enemies
        self.bosses = bosses

        self.obstacles = []
        self.bosses_destroyed = 0
        self.projectiles = []
        self.items = []
        self.item_templates = []
        self.mouse_pos = None
        self.score = 0
        self.score_additon = 0
        self.last_spawn_time = pygame.time.get_ticks()  # Initialize the last spawn time
        self.spawn_interval = 2000
        self.buttons = [Button(name="shop_resume_button", position=[0, 0], dimensions=[100, 40], text="RESUME",
                               alignment="right", click_function=lambda: self.change_state("playing"))]
        self.align_fixed_buttons(self.buttons[0], 10)
        self.created_buttons = set()  # is used to avoid adding the same button over and over again to self.buttons in the create_buttons method

        self.time_when_last_boss_was_killed = None
        self.time_since_last_kill = None
        self.kill_streak_counter = 0
        self.bonus_score = 0

        # options:
        self.enemies_active = True
        self.movement_mode = "arcade"
        self.keybindings = {
            "up": pygame.K_w,
            "down": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d
        }

        # Load the menu from JSON
        self.menus = {"pause_menu": CustomMenu.from_json("saved_menus/Pause_Menu.json"),
                      "main_menu": CustomMenu.from_json("saved_menus/Main_Menu.json"),
                      "options_menu": CustomMenu.from_json("saved_menus/Options_Menu.json")
                      }
        self.map_click_functions()

        # Define stages
        self.stages = [
            Stage("stage 1", enemy_pool=self.enemies[:1], max_enemies=10, score_threshold=2500,
                  bosses_destroyed_threshold=None, game=self, placement_pattern="cross",
                  spawn_interval_modifier=1, enemy_speed_modifier=1),
            Stage("boss stage 1", enemy_pool=self.bosses[0], max_enemies=1, score_threshold=None,
                  bosses_destroyed_threshold=1, game=self, placement_pattern="center",
                  spawn_interval_modifier=1, enemy_speed_modifier=1, stage_type="boss_stage"),
            Stage("stage 2", self.enemies[:2], max_enemies=10, score_threshold=6500,
                  bosses_destroyed_threshold=None, game=self, placement_pattern="pillars",
                  spawn_interval_modifier=0.8, enemy_speed_modifier=1.2),
            Stage("boss stage 2", enemy_pool=self.bosses[1], max_enemies=1, score_threshold=None,
                  bosses_destroyed_threshold=2, game=self,
                  spawn_interval_modifier=1, enemy_speed_modifier=1, stage_type="boss_stage"),
            Stage("stage 3", self.enemies[1:3], max_enemies=13, score_threshold=12000,
                  bosses_destroyed_threshold=None, game=self,
                  spawn_interval_modifier=0.5, enemy_speed_modifier=1.5),
            Stage("boss stage 3", enemy_pool=self.bosses[2], max_enemies=1, score_threshold=None,
                  bosses_destroyed_threshold=3, game=self,
                  spawn_interval_modifier=1, enemy_speed_modifier=1, stage_type="boss_stage"),
            Stage("stage 4", self.enemies, max_enemies=15, score_threshold=17500,
                  bosses_destroyed_threshold=None, game=self,
                  spawn_interval_modifier=0.5, enemy_speed_modifier=1.5)
            # Add more stages as needed
        ]

        self.current_stage = self.stages[self.stage_index]
        self.input_boxes = [
            InputBox("name_prompt", self.window_dimensions[0] / 2 - 125, self.window_dimensions[1] / 2, 250, 50)]

    def quit_game(self):
        self.is_running = False

    def map_click_functions(self):
        # Does also rearrange the components and the menus to look centered
        for menu_key, menu in self.menus.items():
            # change the menu rects to match the screen
            menu.rect.width, menu.rect.height = self.window.get_width(), self.window.get_height()

            for menu_component in menu.components:
                # I am not using isinstance here because i am not able to make it work because all
                # menu components created via json are a menu component and not their specific button or whatever
                # so type_ it is
                if menu_component.type_ == "Button":
                    # Center the button horizontally on the screen
                    menu_component.rect.x = (self.window.get_width() - menu_component.rect.width) // 2
                    if menu_component.click_function == "start_screen":
                        print("Mapping 'start_game' function")
                        menu_component.click_function = lambda: self.change_state("start_screen")

                    elif menu_component.click_function == "main_menu":
                        print("Mapping 'main_menu' function")
                        menu_component.click_function = lambda: self.change_state("main_menu")

                    elif menu_component.click_function == "open_options":
                        print("Mapping 'open_options' function")
                        menu_component.click_function = lambda: self.change_state("options")

                    elif menu_component.click_function == "quit_game":
                        menu_component.click_function = self.quit_game

                    elif menu_component.click_function == "playing":
                        menu_component.click_function = lambda: self.change_state("playing")

                    elif menu_component.click_function == "toggle_movement_mode":
                        print("Mapping 'toggle_movement_mode' function")
                        menu_component.click_function = self.movement_mode_toggler
                        menu_component.tooltip_text = f"current mode: {self.movement_mode}"

                    elif menu_component.click_function == "toggle_debug_mode":
                        print("Mapping 'toggle_debug_mode' function")
                        menu_component.click_function = self.debug_mode_toggler
                        menu_component.tooltip_text = f"debug mode is: {self.debug_mode}"

    def align_fixed_buttons(self, button, margin):

        if button.alignment:
            """Calculate the button's position based on alignment in the bottom corner with margin."""
            if button.alignment == "left":
                x = margin  # Positioned on the left with a margin
            elif button.alignment == "right":
                x = self.window_dimensions[0] - button.rect.width - margin  # Positioned on the right with a margin
            elif button.alignment == "middle":
                x = self.window_dimensions[0] / 2 - button.rect.width / 2
            else:
                return

            # Y position is the same for both alignments
            y = self.window_dimensions[1] - button.rect.height - margin  # Positioned at the bottom with a margin
            button.rect.x = x
            button.rect.y = y

    def debug_mode_toggler(self):
        if self.debug_mode:
            self.debug_mode = False
            self.player_unkillable = False
        else:
            self.debug_mode = True
            self.player_unkillable = True

        # Update tooltip text
        for component in self.menus["options_menu"].components:
            if component.name == "debug_mode":
                component.tooltip_text = f"debug mode is:  {self.debug_mode}"

    def movement_mode_toggler(self):
        # toggle between movement modes
        if self.movement_mode == "arcade":
            self.movement_mode = "thrust_vector"
        else:
            self.movement_mode = "arcade"

        # Update tooltip text with the new movement mode
        for component in self.menus["options_menu"].components:
            if component.name == "toggle_movement_mode":
                component.tooltip_text = f"current mode: {self.movement_mode}"

    def random_chance(self, odds):
        """Return True with a 1/odds chance."""
        return random.randint(1, odds) == 1

    def change_state(self, state):
        self.previous_state = self.state
        self.state = state
        print(f"previous state: {self.previous_state}, new state: {self.state}")

    def stage_manager(self):
        current_stage = self.stages[self.stage_index]

        # Check if it's time to progress to the next stage
        if self.should_progress_to_next_stage(current_stage):
            self.stage_index += 1
            self.clear_obstacles()

        # Again, check if we've exceeded the number of stages
        if self.stage_index >= len(self.stages):
            self.stage_index -= 1

        self.current_stage = self.stages[self.stage_index]

    def should_progress_to_next_stage(self, current_stage):
        # If it's a regular stage, check score to progress
        if current_stage.stage_type != "boss_stage":
            return self.score >= current_stage.score_threshold

        # If it's a boss stage, check if all enemies are defeated to progress
        if current_stage.stage_type == "boss_stage":
            if self.bosses_destroyed >= current_stage.bosses_destroyed_threshold:
                return time.time() - self.time_when_last_boss_was_killed > 5

        return False

    def clear_obstacles(self):
        for obstacle in self.obstacles:
            obstacle.marked_for_death = True

    def draw_background(self, window, background_image):
        if background_image is None:
            window.fill((255, 255, 255))
        else:
            window.blit(background_image, (0, 0))

    def draw_debug_data(self):
        color = (0, 255, 0)
        data1_font = pygame.font.Font(None, 32)
        debug_text = ""
        for text in self.debug_text_boxes:
            debug_text = text + "\n"

        render_multi_line_text(self.window, str(debug_text), data1_font, [50, 50], 5, color, False)

    def draw_hud(self, frame):

        def _draw_aiming_systems():

            # Calculate top-left corner of the rectangle to center it around the cursor
            pos_x = self.mouse_pos[0]
            pos_y = self.mouse_pos[1]

            # Line thickness for the rectangle outline
            line_thickness = 2

            # Draw the rectangle outline

            pygame.draw.circle(self.window, (255, 0, 0), (pos_x, pos_y), 100, line_thickness)

        def _color_changer():
            # Vary the hue between 0 and 1
            hue = (frame % 360) / 360.0  # Convert frame count to a value between 0 and 1
            saturation, value = 1, 1  # Full saturation and value for a vibrant color

            rgb_fractional = colorsys.hsv_to_rgb(hue, saturation, value)  # Returns colors in range [0, 1]
            rgb = tuple(int(c * 255) for c in rgb_fractional)  # Convert to range [0, 255]
            return rgb

        def _draw_stage_info():
            COLOR_WHITE = (255, 255, 255)
            font = pygame.font.Font(self.game_font, 64)
            stage_surface = font.render(self.current_stage.name.upper(), False, COLOR_WHITE)
            stage_rect = stage_surface.get_rect(center=(self.window_dimensions[0] - 650, 50))
            self.window.blit(stage_surface, stage_rect)

        def _draw_player_stats():
            COLOR_WHITE = (255, 255, 255)
            hitpoints_font = pygame.font.Font(self.game_font, 30)
            name_font = pygame.font.Font(self.game_font, 45)

            # Health
            health_bar_length = int(self.player.hit_points) * 2
            pygame.draw.rect(self.window, (255, 0, 0), (10, 10, health_bar_length, 20))
            hitpoints_surface = hitpoints_font.render(str(int(self.player.hit_points)), False, COLOR_WHITE)
            hitpoints_rect = hitpoints_surface.get_rect(topleft=(10, 10))
            self.window.blit(hitpoints_surface, hitpoints_rect)

            # Name
            name_surface = name_font.render(self.player.name.upper(), False, COLOR_WHITE)
            name_rect = name_surface.get_rect(center=(350, 50))

            # Shield
            shield_bar_length = int(self.player.shield) * 2
            pygame.draw.rect(self.window, (0, 0, 255), (10, 30, shield_bar_length, 20))
            shield_surface = hitpoints_font.render(str(int(self.player.shield)), False, COLOR_WHITE)
            shield_rect = shield_surface.get_rect(topleft=(10, 30))
            self.window.blit(shield_surface, shield_rect)
            self.window.blit(name_surface, name_rect)

        def _draw_weapon_info():
            COLOR_WHITE = (255, 255, 255)
            current_weapon = self.player.weapons[self.player.weapon_index]
            current_ammo_type = current_weapon.ammo_type
            if current_ammo_type is not None and current_ammo_type in self.player.ammo:
                current_ammo = self.player.ammo[current_ammo_type].current_ammo
                current_max_ammo = self.player.ammo[current_ammo_type].max
            else:
                current_ammo = 0
                current_max_ammo = 0
            current_weapon_projectile_count = current_weapon.projectiles_count
            font_2 = pygame.font.Font(self.game_font, 32)

            text = (
                f"equipped: {current_weapon.name}\ndamage: {int(current_weapon.damage)}x{current_weapon_projectile_count}\n"
                f"ammo type: {current_ammo_type}\nammo:{str(current_ammo)}/{current_max_ammo}")

            render_multi_line_text(screen=self.window,
                                   text=text,
                                   font=font_2,
                                   position=[5, self.window_dimensions[1] - 100],
                                   color=COLOR_WHITE,
                                   gap=5)

            # render ammo count near the curser
            ammo_text = f"{str(current_ammo)}/{current_max_ammo}"
            ammo_surface = font_2.render(ammo_text, False, COLOR_WHITE)
            ammo_rect = ammo_surface.get_rect(bottomright=self.cursor.position)
            self.window.blit(ammo_surface, ammo_rect)

            # Heat bar
            heat_bar_position = (10, 80)
            heat_bar_dimensions = (200, 20)
            heat_bar_colors = {'background': (150, 150, 150), 'fill': (255, 50, 50)}
            fill_width = (current_weapon.heat / current_weapon.max_heat) * heat_bar_dimensions[0]
            pygame.draw.rect(self.window, heat_bar_colors['background'], (*heat_bar_position, *heat_bar_dimensions))
            pygame.draw.rect(self.window, heat_bar_colors['fill'],
                             (heat_bar_position[0], heat_bar_position[1], fill_width, heat_bar_dimensions[1]))

        def _draw_other_info():
            COLOR_WHITE = (255, 255, 255)
            font = pygame.font.Font(self.game_font, 64)
            font_small = pygame.font.Font(self.game_font, 48)

            # Score
            score_surface = font.render(f"{self.bonus_score} + {str(self.score)}", False, COLOR_WHITE)
            score_rect = score_surface.get_rect(center=(self.window_dimensions[0] - 150, 50))
            self.window.blit(score_surface, score_rect)

            # Bonus
            if self.time_since_last_kill:
                bonus_surface = font.render(
                    f"{2 - (time.time() - self.time_since_last_kill):.2f} {self.kill_streak_counter}", False,
                    _color_changer())
                bonus_rect = bonus_surface.get_rect(center=(self.window_dimensions[0] - 300, 50))
                self.window.blit(bonus_surface, bonus_rect)

            """# Bosses destroyed
            boss_kill_surface = font_small.render(f"Eldar defeated: {str(self.bosses_destroyed)}/{len(self.bosses)}", False, COLOR_WHITE)
            boss_kill_rect = boss_kill_surface.get_rect(center=(self.window_dimensions[0] - 250, 100))
            self.window.blit(boss_kill_surface, boss_kill_rect)"""

            # Coins
            coins_surface = font.render(f"coins: {str(self.player.coins)}", False, COLOR_WHITE)
            coins_rect = coins_surface.get_rect(
                center=(self.window_dimensions[0] - 150, self.window_dimensions[1] - 50))
            self.window.blit(coins_surface, coins_rect)

        # Call all the inner functions
        # _draw_hud_background()
        _draw_stage_info()
        _draw_player_stats()
        _draw_weapon_info()
        _draw_other_info()

    def game_over_get_time(self):
        # Record the time when game over is triggered
        self.game_over_time = pygame.time.get_ticks()

    def update_game_over(self):
        print(self.game_over_time, self.state)
        # Check if the game is over and if 2 seconds have passed
        if self.state == "playing" and self.game_over_time:
            current_time = pygame.time.get_ticks()
            print(current_time - self.game_over_time)
            print(f" have 2 seconds passed? {current_time - self.game_over_time >= 2000}")
            if current_time - self.game_over_time >= 2000:
                self.change_state("game_over")
                print("Game Over! The state has been changed to 'game_over'.")

    def reset_game(self):
        # 1. Clear the existing game state
        self.figures = []
        self.projectiles = []
        self.items = []

        self.bosses_destroyed = 0
        self.last_spawn_time = pygame.time.get_ticks()
        self.time_when_last_boss_was_killed = None
        self.time_since_last_kill = None
        self.game_over_time = None
        self.stage_index = 0
        for stage in self.stages:
            stage.obstacles_spawned = False

        # 2. Reinitialize the player
        self.player = self.player_template.clone()
        self.add_figure(self.player)  # Update the player reference
        self.player.hit_points = 100
        self.player_alive = True
        self.score = 0
        self.player.current_weapon_index = 0

    def draw_start_screen(self):
        font = pygame.font.Font(self.game_font, 64)
        text_surface = font.render('Please enter a Name:', False, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.window_dimensions[0] // 2, self.window_dimensions[1] // 2 - 250))
        self.window.fill((15, 134, 150))
        self.window.blit(text_surface, text_rect)

    def high_score_handler(self):
        file_name = "highscores.txt"

        # Step 1 & 2: Check if the highscores.txt file exists and load the highscores.
        scores = {}
        if os.path.exists(file_name):
            with open(file_name, "r") as file:
                for line in file.readlines():
                    try:
                        name, score = line.strip().split(": ")
                        scores[name] = int(score)
                    except ValueError:
                        # skip malformatted or empty lines
                        pass

        # Step 3 & 4: Compare the current player's score with the highscores.
        if self.player.name not in scores or self.score > scores[self.player.name]:
            scores[self.player.name] = self.score

        # Step 5: Insert the player's score in the correct position to maintain a sorted list.
        sorted_scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))

        # Step 6: Overwrite the highscores.txt file with the updated scores.
        with open(file_name, "w") as file:
            for name, score in sorted_scores.items():
                file.write(f"{name}: {score}\n")

    def draw_high_score_display(self):
        font = pygame.font.Font(self.game_font, 90)

        # Step 1: Load the contents of the highscores.txt file.
        scores = []
        with open("highscores.txt", "r") as file:
            for line in file.readlines():
                try:
                    name, score = line.strip().split(": ")
                    scores.append((name, int(score)))
                except ValueError:
                    # Skip malformatted or empty lines.
                    pass

        # Step 2: Extract and format the high scores.
        text = "High Scores:\n"
        for name, score in scores:
            text += f"{name}: {score}\n"
        self.window.fill((5, 5, 5))
        # Step 3: Render each high score on the screen.
        render_multi_line_text(screen=self.window,
                               text=text,
                               font=font,
                               position=[self.window_dimensions[0] / 2 / 2, 100],
                               color=(0, 0, 0),
                               gap=5,
                               fill=True)

    def draw_pause_screen(self):
        # TODO create a small menu that can switch the movement modes of the player
        font = pygame.font.Font(self.game_font, 64)
        text_surface = font.render('Pause, to unpause press Space or ESC to quit', False, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.window_dimensions[0] // 2, self.window_dimensions[1] // 2))
        # self.window.fill((115, 110, 117))
        self.window.blit(text_surface, text_rect)

    def draw_shop(self):
        font = pygame.font.Font(self.game_font, 64)
        stats_font = pygame.font.Font(self.game_font, 32)  # A smaller font for the stats

        coins_surface = font.render(str(self.player.coins), False, (255, 255, 255))
        coins_rect = coins_surface.get_rect(center=(self.window_dimensions[0] - 150, self.window_dimensions[1] - 50))

        text_surface = font.render('Shop', False, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.window_dimensions[0] // 2, self.window_dimensions[1] // 2))
        self.window.fill((115, 110, 117))
        self.window.blit(text_surface, text_rect)
        self.window.blit(coins_surface, coins_rect)

        # Displaying player stats:
        y_position = 500  # Starting Y position for the stats
        spacing = 40  # Spacing between each line

        stats = [
            f"Shield recharge_rate: {self.player.shield_recharge_rate} per sec",
            f"Hit Points recharge_delay: {self.player.shield_recharge_delay} sec",
            f"Hit Point Overcharge: {self.player.hit_point_overcharge}",
            f"Shield Overcharge: {self.player.shield_overcharge}"
        ]

        for stat in stats:
            stat_surface = stats_font.render(stat, False, (255, 255, 255))
            self.window.blit(stat_surface, (0, y_position))  # Displaying on the left, adjust X position as needed
            y_position += spacing

        weapon_stats = [(weapon.name, {"damage": weapon.damage, "amount of projectiles": weapon.projectiles_count,
                                       "fire rate": weapon.cooldown, "heat per shot": weapon.heat_increase_per_shot,
                                       }) for weapon in self.player.weapons]
        for weapon_name, attributes in weapon_stats:
            # Access the weapon's name and its attributes
            damage = attributes['damage']
            projectiles_count = attributes['amount of projectiles']
            cooldown = attributes['fire rate']

            # Construct the display string for each weapon
            weapon_stat_string = f"{weapon_name} - Damage: {damage:.2f}, Projectiles: {projectiles_count:.2f}, fire rate: {cooldown:.2f}"

            # Render the display string to a surface
            weapon_stat_surface = stats_font.render(weapon_stat_string, False, (255, 255, 255))
            self.window.blit(weapon_stat_surface,
                             (0, y_position))  # Displaying on the left, adjust X position as needed
            y_position += spacing

    def draw_game_over_screen(self):
        font = pygame.font.Font(self.game_font, 64)
        text_surface = font.render('Game Over!', False, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.window_dimensions[0] // 2, self.window_dimensions[1] // 2))

        score_surface = font.render(f"{self.player.name} got {str(self.score)} points!", False, (0, 0, 0))
        score_rect = score_surface.get_rect(center=(self.window_dimensions[0] // 2, self.window_dimensions[1] // 3))
        self.window.fill(red)
        self.window.blit(text_surface, text_rect)
        self.window.blit(score_surface, score_rect)

    def add_figure(self, *figures):
        for figure in figures:
            self.figures.append(figure)

    def add_obstacle(self, *obstacles):
        for obstacle in obstacles:
            self.obstacles.append(obstacle)

    def add_item_template(self, *items):
        for item in items:
            self.item_templates.append(item)

    def add_item(self, *items):
        for item in items:
            self.items.append(item)

    def remove_figure(self, figure):
        self.figures.remove(figure)

    def remove_item(self, item):
        self.items.remove(item)

    def add_projectile(self, projectile):
        self.projectiles.append(projectile)

    def remove_projectile(self, projectile):
        self.projectiles.remove(projectile)

    def add_enemies(self, *enemies):
        for enemy in enemies:
            self.enemies.append(enemy)

    def random_pos(self):
        """Generate a random position inside the screen bounds."""
        return (random.randint(50, self.window_dimensions[0] - 100),
                random.randint(50, self.window_dimensions[1] - 100))

    def spawn_entity(self, template):
        new_entity = template.clone()
        new_entity.velocity *= self.current_stage.enemy_speed_modifier

        # The entities cannot leave the screen (hopefully)
        new_entity.x_limit = self.window_dimensions[0]
        new_entity.y_limit = self.window_dimensions[1]
        new_entity.override_position(list(self.random_pos()))

        if len(new_entity.animation) > 1:
            new_entity.animation[1].position = new_entity.position
            new_entity.animation[1].owner = new_entity

            self.animations.append(new_entity.animation[1])
            self.spawn_queue.append(new_entity)
        else:
            self.add_figure(new_entity)

    def spawn_enemy(self):

        max_enemies = self.current_stage.max_enemies
        stage_type = self.current_stage.stage_type
        spawn_interval_modifier = self.current_stage.spawn_interval_modifier

        # Get the current time
        current_time = pygame.time.get_ticks()

        # Adjust the spawn interval based on the current stage's spawn interval modifier
        adjusted_spawn_interval = self.spawn_interval * spawn_interval_modifier
        # generator function or something i don't know
        boss_count = sum(figure.type_ == "boss_enemy" for figure in self.figures)
        current_enemy_count = sum(figure.type_ == "enemy" for figure in self.figures)

        if stage_type == "boss_stage":
            # Handle boss spawning logic

            if boss_count == 0 and current_enemy_count == 0 and not self.current_stage.boss_spawned:
                boss_template = self.current_stage.enemy_pool
                self.spawn_entity(boss_template)
                self.current_stage.boss_spawned = True

        else:
            if current_time - self.last_spawn_time > adjusted_spawn_interval:
                if current_enemy_count < max_enemies:
                    self.last_spawn_time = current_time
                    enemy_template = random.choice(self.current_stage.enemy_pool)
                    self.spawn_entity(enemy_template)

    def manage_obstacles(self):
        for obstacle in self.current_stage.manage_obstacles():
            self.add_obstacle(obstacle)
        for obstacle in self.obstacles:
            obstacle.draw_figure(self.window)
            if self.debug_mode:
                obstacle.debug_visuals(self.window, frame=self.frame_counter)

    def kill_streak_handler(self):
        """count the time since last kill to create a time window in which the next kill needs to be performed to keep
        the streak going. This is then used to determine the bonus points. The streak can go up to a certain number
        ten in this case. This means that if ten kills are in a streak the player gets a ten percent bonus"""

        def reset_streak_handler():
            # below resets the streak
            self.kill_streak_counter = 0
            self.score_additon = 0
            self.bonus_score = 0
            self.time_since_last_kill = None

        # This handles kill-streaks up to ten kills
        if self.time_since_last_kill and self.kill_streak_counter > 0:
            if self.kill_streak_counter > 1:
                self.bonus_score = int(
                    self.score_additon * (1 + self.kill_streak_counter / 10))  # add the percentage of the bonus
            else:  # if there is no kill streak of at least 2, the addition will be the standard reward of the kill
                self.bonus_score = self.score_additon
            # now if the time of 2 seconds has passed or the kill streak exceeds 10, the streak resets
            if time.time() - self.time_since_last_kill > 2 or self.kill_streak_counter > 10:
                self.score += self.bonus_score

                self.player.coins += int(self.kill_streak_counter / 2)  # give some bonus coins

                reset_streak_handler()

    def animation_handler(self):
        finished_animations = []

        # Update and draw animations, and collect finished ones.
        for animation in self.animations:
            if not animation.is_finished():
                animation.draw_animation(self.window, animation.position)
                animation.update(self.frame_counter, self.fps)
            else:
                finished_animations.append(animation)

        # Handle finished animations.
        for animation in finished_animations:
            enemy = getattr(animation, 'owner', None)
            if enemy and enemy in self.spawn_queue:
                self.figures.append(enemy)  # Add the enemy to figures list
                self.spawn_queue.remove(enemy)  # Remove the enemy from spawn_queue
                enemy.spawn_animation_active = False
                self.animations.remove(animation)

    def random_position_on_screen(self):
        random_pos_on_screen = [random.randint(50, self.window_dimensions[0] - 50),
                                random.randint(50, self.window_dimensions[1] - 50)]
        return random_pos_on_screen

    def return_distance(self, obj1, obj2):
        # calculate the distance between two objects
        # the if statements are for when positions are fed directly into this method

        if hasattr(obj1, 'position'):
            x1, y1 = obj1.position
        elif isinstance(obj1, tuple):
            x1, y1 = obj1
        else:
            raise ValueError('wrong method input')

        if hasattr(obj2, 'position'):
            x2, y2 = obj2.position
        elif isinstance(obj2, tuple):
            x2, y2 = obj2
        else:
            raise ValueError('wrong method input')

        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance

    def spawn_item(self, *items, spawn_position):
        # If there are multiple items, choose one randomly
        if len(items) > 1:
            item_template = random.choice(items)
        else:
            # If there's only one item, use that one
            item_template = items[0]

        new_item = item_template.clone()
        self.add_item(new_item)
        new_item.override_position(spawn_position)

    def broad_phase_collision_check(self, entity1, entity2):
        if entity1.rect.colliderect(entity2.rect):
            print(f"broad phase collision detected between {entity1} and {entity2}")
            return True
        # This is kinda useless

    def check_collision(self, entity1, entity2):

        mask1 = entity1.mask
        x1 = entity1.position[0] - entity1.dimensions[0] // 2
        y1 = entity1.position[1] - entity1.dimensions[1] // 2

        mask2 = entity2.mask
        x2 = entity2.position[0] - entity2.dimensions[0] // 2
        y2 = entity2.position[1] - entity2.dimensions[1] // 2

        offset_x = x2 - x1
        offset_y = y2 - y1

        # Check if the masks overlap
        overlap = mask1.overlap(mask2, (offset_x, offset_y))

        return overlap is not None

    def check_boundary(self, entity):
        # maybe just use the window limits
        # TODO stupid shit. x and y limits are set by the window limits. so maybe just cut out the middleman
        if entity.position[0] > entity.x_limit:
            entity.position[0] = entity.x_limit
        if entity.position[0] < 0:
            entity.position[0] = 0
        if entity.position[1] > entity.y_limit:
            entity.position[1] = entity.y_limit
        if entity.position[1] < 0:
            entity.position[1] = 0

    def prevent_clipping(self, threshold=75):
        # takes the position of entities and prevents them of getting those points closer to each other than the
        # threshold.
        # TODO make the threshold depend on the figure size
        figures_to_check = self.figures + self.obstacles
        for i, entity1 in enumerate(figures_to_check):
            for j, entity2 in enumerate(figures_to_check[i + 1:]):
                x1_pos, y1_pos = entity1.position
                x2_pos, y2_pos = entity2.position

                # Calculate the distance between the two entities
                distance = math.sqrt((x2_pos - x1_pos) ** 2 + (y2_pos - y1_pos) ** 2)

                # Check if the distance is less than the threshold
                if distance < threshold:
                    # Calculate the direction vector from entity1 to entity2
                    dx = x2_pos - x1_pos
                    dy = y2_pos - y1_pos

                    # Normalize the direction vector to get the unit vector
                    if distance != 0:  # Prevent division by zero
                        dx /= distance
                        dy /= distance
                    # maybe let the obstacles be moveable?
                    # If one entity is an obstacle, only move the non-obstacle entity
                    if entity1.type_ == "obstacle" and entity2.type_ != "obstacle":
                        entity2.position[0] += dx * (threshold - distance)
                        entity2.position[1] += dy * (threshold - distance)
                    elif entity2.type_ == "obstacle" and entity1.type_ != "obstacle":
                        entity1.position[0] -= dx * (threshold - distance)
                        entity1.position[1] -= dy * (threshold - distance)
                    else:
                        # If neither or both are obstacles, move both entities as before
                        entity1.position[0] -= dx * (threshold - distance) / 2
                        entity1.position[1] -= dy * (threshold - distance) / 2
                        entity2.position[0] += dx * (threshold - distance) / 2
                        entity2.position[1] += dy * (threshold - distance) / 2

    def prevent_clipping_if_everything_had_vectors(self, threshold=75):
        """its a shame it dont work at the time"""
        for i, entity1 in enumerate(self.figures):
            for j, entity2 in enumerate(self.figures[i + 1:]):
                x1_pos, y1_pos = entity1.position
                x2_pos, y2_pos = entity2.position

                # Calculate the distance between the two entities
                distance = math.sqrt((x2_pos - x1_pos) ** 2 + (y2_pos - y1_pos) ** 2)

                # Check if the distance is less than the threshold
                if distance < threshold:
                    # Calculate the direction vector from entity1 to entity2
                    dx = x2_pos - x1_pos
                    dy = y2_pos - y1_pos

                    # Normalize the direction vector to get the unit vector
                    if distance != 0:  # Prevent division by zero
                        dx /= distance
                        dy /= distance

                    # Handle obstacle collision using the obstacle's rect
                    if entity1.type_ == "obstacle" and entity2.type_ != "obstacle":
                        if entity1.rect.colliderect(entity2.rect):
                            overlap = entity1.rect.clip(entity2.rect)
                            entity2.position[0] += dx * overlap.width
                            entity2.position[1] += dy * overlap.height

                            # Adjust the velocity to prevent "bouncing"
                            if abs(dx) > abs(dy):
                                entity2.velocity[0] = -entity2.velocity[0]  # Invert horizontal velocity
                            else:
                                entity2.velocity[1] = -entity2.velocity[1]  # Invert vertical velocity

                    elif entity2.type_ == "obstacle" and entity1.type_ != "obstacle":
                        if entity2.rect.colliderect(entity1.rect):
                            overlap = entity2.rect.clip(entity1.rect)
                            entity1.position[0] -= dx * overlap.width
                            entity1.position[1] -= dy * overlap.height

                            # Adjust the velocity to prevent "bouncing"
                            if abs(dx) > abs(dy):
                                entity1.velocity[0] = -entity1.velocity[0]  # Invert horizontal velocity
                            else:
                                entity1.velocity[1] = -entity1.velocity[1]  # Invert vertical velocity

                    else:
                        # If neither or both are obstacles, move both entities as before
                        entity1.position[0] -= dx * (threshold - distance) / 2
                        entity1.position[1] -= dy * (threshold - distance) / 2
                        entity2.position[0] += dx * (threshold - distance) / 2
                        entity2.position[1] += dy * (threshold - distance) / 2

    def player_enemy_projectile_collision_handler(self):
        figures_to_check = self.figures + self.obstacles
        for figure in figures_to_check:
            for projectile in self.projectiles:
                # collision between player and enemy projectiles
                if figure.type_ == "player" and self.player_alive and projectile.type_ in ["enemyprojectile",
                                                                                           "boss_enemyprojectile",
                                                                                           "shrapnel"]:
                    # Check collision between player and enemy projectiles
                    if self.check_collision(figure, projectile):
                        if not self.player_unkillable:
                            if projectile.hit(figure):
                                projectile.marked_for_death = True
                # collisions between enemies and player projectiles or shrapnel
                elif figure.type_ in ["enemy", "boss_enemy"] and projectile.type_ in ["playerprojectile", "shrapnel"]:
                    # Check collision between enemy and player projectiles
                    if self.check_collision(figure, projectile):
                        if projectile.hit(figure):
                            """projectile.hit calls the figure.get_hit method that manages the dealing of damage
                            as well as the determination if the figure is dead"""
                            projectile.marked_for_death = True
                        if figure.marked_for_death:
                            if figure.type_ == "boss_enemy":
                                figure.set_kill_time(time.time())
                                self.time_when_last_boss_was_killed = figure.kill_time
                                self.time_since_last_kill = figure.kill_time
                                self.time_since_last_kill = figure.kill_time
                                print(f"{figure.name, figure.kill_time, self.time_when_last_boss_was_killed}")
                            elif figure.type_ == "enemy":
                                figure.set_kill_time(time.time())
                                self.time_since_last_kill = figure.kill_time
                                print(f"figure.name: {figure.name}, figure.kill_time: {figure.kill_time}")
                elif figure.type_ == "obstacle" or isinstance(obstacle_a, Obstacle):
                    if self.check_collision(figure, projectile):
                        print(f"collision between {figure} and {projectile}")
                        projectile.marked_for_death = True

    def remove_dead_figures_and_projectiles(self):
        dead_figures = (figure for figure in self.figures if figure.marked_for_death)

        dead_projectiles = (projectile for projectile in self.projectiles if projectile.marked_for_death)

        dead_obstacles = (obstacle for obstacle in self.obstacles if obstacle.marked_for_death)

        pick_ups = [figure for figure in self.figures if figure.type_ == "pick_up"]

        for figure in dead_figures:
            print(f"figure type of dead figures: {figure.type_}")
            if figure.type_ != "player":
                if self.debug_mode:
                    self.debug_text_boxes.append(figure.name)
                if figure.reward:
                    self.score_additon += figure.reward
                self.kill_streak_counter += 1
                if figure.type_ == "boss_enemy":
                    self.bosses_destroyed += 1
                if figure.animation:
                    figure.animation[
                        0].position = figure.position  # the first index should hold the explosion animation
                    figure.animation[0].owner = figure
                    self.animations.append(
                        figure.animation[0])  # explosion of the figure gets added to the scene
                # handle item drops
                dropped_items = figure.handle_drop()
                for dropped_item in dropped_items:
                    if dropped_item and len(pick_ups) < 10:
                        self.add_item(dropped_item)
                        dropped_item.override_position(figure.position)
                    if dropped_item and dropped_item.type_ == "gun_pick_up":
                        self.add_item(dropped_item)
                        dropped_item.override_position(figure.position)

            self.remove_figure(figure)

        for projectile in dead_projectiles:
            if hasattr(projectile, "explosion_radius"):
                if projectile.explosion_radius:
                    projectile.explode(self.figures)
                    pygame.draw.circle(self.window, (255, 150, 255),
                                       (int(projectile.position[0]), int(projectile.position[1])),
                                       int(projectile.explosion_radius))
                if projectile.shrapnel_count:
                    shrapnel_projectiles = projectile.create_shrapnel()
                    if shrapnel_projectiles is not None:
                        for shrapnel in shrapnel_projectiles:
                            self.add_projectile(shrapnel)

            if projectile.animation:
                projectile.animation[0].position = projectile.position
                projectile.animation[0].owner = projectile
                self.animations.append(
                    projectile.animation[0].clone())  # explosion of the figure gets added to the scene
            self.projectiles.remove(projectile)

        for obstacle in dead_obstacles:
            self.obstacles.remove(obstacle)

    def collision_check_and_handling(self):
        self.prevent_clipping()
        self.player_enemy_projectile_collision_handler()
        self.remove_dead_figures_and_projectiles()

    def movement_handler(self, keys, angle=None):
        """Handles movement and orientation behaviors according to key inputs."""

        player = self.player  # This retrieves the player from the figures list using the property

        if not player:  # If there's no player, we don't need to process movement
            return
        if self.movement_mode == "arcade":
            player.orientation = angle
            if keys[self.keybindings["up"]]:
                player.arcade_movement(key_pressed=True, direction="up")
            elif keys[self.keybindings["down"]]:
                player.arcade_movement(key_pressed=True, direction="down")
            if keys[self.keybindings["left"]]:
                player.arcade_movement(key_pressed=True, direction="left")
            elif keys[self.keybindings["right"]]:
                player.arcade_movement(key_pressed=True, direction="right")
            else:
                player.arcade_movement(key_pressed=False, direction=None)

        if self.movement_mode == "thrust_vector":
            # Orient the player to look at the mouse position
            player.look_at(self.mouse_pos)

            # Check which movement key is pressed and call the appropriate movement method
            if keys[self.keybindings["up"]]:
                # "W" key is pressed: Move forward in the direction the player is facing
                player.handle_thrust_vector(key_pressed=True, mode="normal", direction="prograde")
            elif keys[pygame.K_s]:
                # "S" key is pressed: Move backward in the opposite direction of the player’s facing
                player.handle_thrust_vector(key_pressed=True, mode="normal", direction="retrograde")
            if keys[pygame.K_d]:
                # "E" key is pressed: Strafe right
                player.handle_thrust_vector(key_pressed=True, mode="strafing", direction="prograde")
            elif keys[pygame.K_a]:
                # "Q" key is pressed: Strafe left
                player.handle_thrust_vector(key_pressed=True, mode="strafing", direction="retrograde")
            else:
                # No key pressed: Maintain current velocity (possibly apply friction)
                player.handle_thrust_vector(key_pressed=False)

    def handle_fire_effects(self, character, angle=None):
        if angle is not None:  # If an angle is provided (for the player)
            character.orientation = angle
        projectiles, muzzle_flash = character.trigger_pull()
        """we are creating a list of projectiles, so that if we use a "shotgun", that spawns multiple projectiles we can
         handle it with the already implemented functions. Muzzle_flash should be always one so far, so no list"""
        if projectiles is not None:
            for projectile in projectiles:
                self.add_projectile(projectile)
        if muzzle_flash is not None:
            muzzle_flash.owner = character
            self.animations.append(muzzle_flash)

    def projectile_behaviour_handler(self):

        for projectile in self.projectiles:

            projectile.behave()
            if projectile.life_time:
                projectile.check_lifetime()

            # Draw the projectile on the screen
            projectile.draw_projectile(self.window)

            # Check if the projectile has reached its maximum travel distance
            if projectile.projectile_max_reach():
                # Mark the projectile for removal from the game
                projectile.marked_for_death = True

    def npc_behaviour_manager(self):  # TODO maybe implement in-fighting or some npc that fights alongside the player

        for npc in self.figures:
            if isinstance(npc, NPC) and self.player:  # Ensure it's an NPC and player exists
                npc.lead_target(self.player, debug_mode=self.debug_mode, window=self.window)
                player_in_attack_range = npc.is_in_range(target=self.player)
                if player_in_attack_range:
                    current_weapon = npc.weapons[npc.weapon_index]

                    # Check if current weapon is overheated
                    if current_weapon.heat >= current_weapon.max_heat - 0.5:
                        npc.change_weapon()

                    self.handle_fire_effects(npc)

                    npc.apply_thrust("prograde", "strafe")
                elif not player_in_attack_range:
                    npc.apply_thrust("prograde", "normal")

    def create_buttons(self):
        x_position = 100  # Starting X position for player upgrades
        y_position = 100
        spacing = 60  # The space between each button vertically

        if self.player.available_upgrades:
            y_position = 100
            spacing = 60  # The space between each button vertically
            for upgrade in self.player.available_upgrades:
                # Check if button for this upgrade has already been created
                if upgrade.name not in self.created_buttons and not upgrade.used_up:
                    def player_upgrade_function(upg=upgrade):  # Define the function within the loop
                        self.player.purchase_upgrade(upg)

                    button = UpgradeButton(name=upgrade.name, game_instance=self, position=[200, y_position], width=150,
                                           height=40,
                                           text=f"{upgrade.name}",
                                           font=self.game_font, font_size=16,
                                           color=(13, 5, 245), hover_color=(156, 153, 255),
                                           click_function=player_upgrade_function, upgrade=upgrade)

                    button.upgrade = upgrade
                    self.buttons.append(button)
                    self.created_buttons.add(upgrade.name)  # Add the upgrade name to the set
                    y_position += spacing
            x_position += 300  # Move to the next column after player upgrades
            y_position = 100  # Reset the Y position for the next column

        for weapon in self.player.weapons:
            if weapon.available_weapon_upgrades:
                for upgrade in weapon.available_weapon_upgrades:
                    combined_name = weapon.name + "_" + upgrade.name
                    if combined_name not in self.created_buttons and not upgrade.used_up:  # check if the upgrade is already in the list
                        print(combined_name)

                        def weapon_upgrade_function(upg=upgrade, wep=weapon):
                            wep.purchase_weapon_upgrade(upg)

                        button = UpgradeButton(name=combined_name, game_instance=self,
                                               position=[x_position, y_position],
                                               width=150,
                                               height=40,
                                               text=f"{weapon.name}\n{upgrade.name} - {upgrade.cost} coins",
                                               font=self.game_font, font_size=16,
                                               color=(13, 5, 245), hover_color=(156, 153, 255),
                                               click_function=weapon_upgrade_function, upgrade=upgrade)

                        button.upgrade = upgrade
                        self.buttons.append(button)
                        self.created_buttons.add(combined_name)
                        y_position += spacing  # Increment the Y position for every upgrade
                x_position += 200  # Increment the X position after processing all upgrades of a weapon
                y_position = 100  # Reset Y position for the next column

    def handle_start_screen(self):
        """Handles the start screen logic, including drawing and processing events."""
        self.draw_start_screen()

        for event in pygame.event.get():
            self.process_start_screen_event(event)

        self.update_input_boxes()
        self.draw_input_boxes()

    def process_start_screen_event(self, event):
        """Processes events specifically for the start screen."""
        if event.type == pygame.QUIT:
            self.quit_game()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.check_name_prompt()

        for input_box in self.input_boxes:
            input_box.handle_event(event)

    def check_name_prompt(self):
        """Validates the name entered in the input box."""
        for input_box in self.input_boxes:
            if input_box.name == "name_prompt":
                if input_box.text.strip() != "" and len(input_box.text) < 10:
                    self.player.name = input_box.text
                    self.change_state("playing")
                else:
                    # Handle case where name is empty or only spaces
                    print("Please enter a valid name.")

    def update_input_boxes(self):
        """Updates the state of input boxes."""
        for input_box in self.input_boxes:
            input_box.update()

    def draw_input_boxes(self):
        """Draws the input boxes on the screen."""
        for input_box in self.input_boxes:
            input_box.draw(self.window)

    def handle_main_menu_screen(self):
        """Handles the start screen logic, including drawing and processing events."""

        for event in pygame.event.get():
            self.menus["main_menu"].update(event)
        self.menus["main_menu"].draw(self.window)

    def handle_options_menu_screen(self):
        for comp in self.menus["options_menu"].components:
            if comp.name == "resume" and self.previous_state == "main_menu":
                comp.enabled = False
            else:
                comp.enabled = True
        for event in pygame.event.get():
            self.menus["options_menu"].update(event)
        self.menus["options_menu"].draw(self.window)

    def shop_state_handler(self):
        self.create_buttons()
        self.draw_shop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

        for button in self.buttons:
            if not button.hovered:
                button.draw(self.window)
            button.handle_event(event)
            # separating the buttons from the UpgradeButtons because they are not similar enough to combine
            # them into a single class.
            if isinstance(button, UpgradeButton):
                button.is_purchaseable = self.player.coins >= button.upgrade.cost
                if button.upgrade.uses >= button.upgrade.max_uses:
                    button.upgrade.used_up = True  # is that even necessary? I cannot remember
                    self.buttons.remove(button)
        # Draw hovered button last
        for button in self.buttons:
            if button.hovered:
                button.draw(self.window)

    def run(self):
        """
        The run method handles the main game loop logic.
        """

        left_mouse_held_down = False  # Flag to track if the left mouse button is held down
        right_mouse_held_down = False  # Flag to track if the right mouse button is held down
        self.add_figure(self.player)  # add the player to the field

        # Main game loop
        while self.is_running:
            pygame.display.update()
            # Hide the system cursor
            pygame.mouse.set_visible(False)
            # Get the current mouse position
            self.mouse_pos = pygame.mouse.get_pos()
            # Update the custom cursor position
            self.cursor.update_position(self.mouse_pos)
            # Limit the frame rate
            self.clock.tick(self.fps)

            # Display the start screen
            if self.state == "start_screen":
                self.handle_start_screen()

            if self.state == "main_menu":
                self.handle_main_menu_screen()

            if self.state == "options":
                self.handle_options_menu_screen()

            if self.state == "shop":
                self.create_buttons()
                self.draw_shop()

                for button in self.buttons:
                    if isinstance(button, UpgradeButton):
                        button.is_purchaseable = self.player.coins >= button.upgrade.cost
                        if button.upgrade.uses >= button.upgrade.max_uses:
                            button.upgrade.used_up = True  # is that even necessary? I cannot remember
                            self.buttons.remove(button)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_game()
                    for button in self.buttons:
                        button.handle_event(event)
                # this is due to the draw order that has to be like that so the tooltip is always readable
                for button in self.buttons:
                    if not button.hovered:
                        button.draw(self.window)
                for button in self.buttons:
                    if button.hovered:
                        button.draw(self.window)

            if self.state == "pause":

                # Process events on the start screen
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_game()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.change_state("playing")  # Start the game when space is pressed
                        if event.key == pygame.K_ESCAPE:
                            self.quit_game()

                    self.menus["pause_menu"].update(event)
                    self.draw_pause_screen()
                    self.menus["pause_menu"].draw(self.window)

            # Main game-playing state
            if self.state == "playing":
                self.frame_counter += 1

                enemy_figures = [figure for figure in self.figures if figure.type_ in ["enemy", "boss_enemy"]]

                # Handle player actions if the player is alive
                if self.player_alive:
                    current_player_weapon = self.player.weapons[self.player.weapon_index]
                    dx = self.mouse_pos[0] - self.player.position[0]
                    dy = self.mouse_pos[1] - self.player.position[1]
                    # angle is the orientation necessary for the player to look at the cursor
                    angle_in_radians = math.atan2(dy, dx)
                    angle_in_degrees = math.degrees(angle_in_radians) + 90

                    # Handle keyboard inputs
                    keys = pygame.key.get_pressed()
                    self.movement_handler(keys, angle=angle_in_degrees)

                    # If player has no energy ammo anymore:
                    if self.player.ammo["energy_ammo"].current_ammo == 0:
                        # Check if there is an existing energy ammo item on the screen
                        energy_ammo_exists = any(item.name == "Energy_Ammo_pick_up" for item in self.items)
                        # If there is no energy ammo item, spawn one
                        if not energy_ammo_exists:
                            self.spawn_item(self.item_templates[0], spawn_position=self.random_position_on_screen())

                    # Handle firing projectiles when left mouse button is held down
                    if left_mouse_held_down:
                        self.handle_fire_effects(self.player, angle_in_degrees)

                    # Update player orientation when right mouse button is held down
                    if right_mouse_held_down:
                        self.player.orientation = angle_in_degrees
                    # handle homing weapons
                    if current_player_weapon.type_ == "homing":
                        player.radar_active = True
                        closest_enemy = None
                        closest_distance = float('inf')  # Start with a very large distance

                        for figure in self.figures:
                            if figure.type_ in ["enemy", "boss_enemy"]:
                                distance = self.return_distance(self.mouse_pos, figure)
                                if distance < closest_distance:
                                    closest_distance = distance
                                    closest_enemy = figure

                            if closest_enemy:
                                # Set the closest enemy as the target for the homing weapon
                                player.current_target = closest_enemy
                                current_player_weapon.set_target(closest_enemy)
                                # Additional code to guide the homing weapon toward the target can go here
                        else:
                            player.radar_active = False
                            player.current_target = None  # Clear the target when not using a homing weapon

                # Handle game events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_game()

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # Left mouse button
                            left_mouse_held_down = True
                        if event.button == 3:  # Right mouse button
                            right_mouse_held_down = True

                    if event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:  # Left mouse button
                            left_mouse_held_down = False
                        if event.button == 3:  # Right mouse button
                            right_mouse_held_down = False

                    if event.type == pygame.MOUSEWHEEL:
                        if event.y > 0:
                            # Scroll up: Increase the weapon index and wrap around
                            self.player.weapon_index = (self.player.weapon_index + 1) % len(self.player.weapons)
                        elif event.y < 0:
                            # Scroll down: Decrease the weapon index and wrap around
                            self.player.weapon_index = (self.player.weapon_index - 1) % len(self.player.weapons)

                    if event.type == pygame.KEYDOWN:
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                            # Deduct 1 from the key value to get the index
                            index = event.key - pygame.K_1
                            if index < len(self.player.weapons):  # Check if the index is valid
                                self.player.weapon_index = index

                        if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                            self.change_state("pause")
                        if event.key == pygame.K_TAB:
                            self.state = "shop"

                # Draw the game background
                self.draw_background(self.window, self.background_image)

                # Spawn enemies periodically
                if self.enemies_active:
                    self.spawn_enemy()

                # Spawn Obstacles
                self.manage_obstacles()

                # Draw the player if they are alive
                if self.player and self.player_alive:
                    self.player.draw_figure(self.window)
                    self.player.hit_points_and_shield_dynamic()
                    # if self.player.radar_active:
                    #     self.player.radar_energy_cost()
                    if self.debug_mode:
                        self.player.debug_visuals(self.window, frame=self.frame_counter)

                # Handle NPCs, players, and their interactions
                for figure in self.figures:
                    # so that if the player gets destroyed the model disappears
                    if figure.type_ != "player":
                        figure.draw_figure(self.window)

                    if self.debug_mode:
                        figure.debug_visuals(self.window, frame=self.frame_counter)

                    # Draw health bars for enemies and bosses
                    if figure.type_ in ["enemy", "boss_enemy"]:
                        figure.draw_health_bar(self.window)

                    # Handle weapon cooldowns for relevant figures
                    if figure.type_ in ["enemy", "boss_enemy", "player"]:
                        for weapon in figure.weapons:
                            weapon.cool_down()

                    # Handle homing weapon targeting
                    if figure.type_ == "player" and current_player_weapon.type_ == "homing":
                        # Draw locking markers for enemies
                        self.player.draw_locking_markers(enemy_figures, self.window)

                        if current_player_weapon.locked_target:
                            self.player.draw_locked_target_marker(current_player_weapon.locked_target, self.window)
                    # checks that no entity leaves the screen
                    if figure.type_ != "obstacle":
                        self.check_boundary(figure)

                # Handle item spawn and despawn/effect mechanics separately
                for item in self.items:
                    item.draw_figure(self.window)
                    item.turn_item(5)

                    if item.item_in_range(target=self.player):
                        item.apply_effect(self.player)
                        self.remove_item(item)

                # animation handling
                self.animation_handler()

                # Move and draw projectiles
                self.projectile_behaviour_handler()

                # kill streak handling
                self.kill_streak_handler()

                # remove the lock if the locked target is destroyed
                if (hasattr(current_player_weapon, 'locked_target') and
                        current_player_weapon.locked_target and
                        current_player_weapon.locked_target.marked_for_death):
                    current_player_weapon.locked_target = None

                # Draw the custom cursor
                self.cursor.draw_cursor(self.window)

                # update the stage
                self.stage_manager()

                # Check for and handle collisions
                self.collision_check_and_handling()
                # check if player is still alive and act accordingly
                if self.player_alive and self.player.hit_points <= 0:
                    self.player_alive = False
                    self.game_over_get_time()
                    player_explosion = self.player.animation[0]
                    player_explosion.position = self.player.position
                    self.animations.append(player_explosion)

                if self.player_alive:
                    # Display the HUD (score, health, etc.)
                    self.draw_hud(self.frame_counter)

                self.update_game_over()

                # Handle NPC behaviors (e.g., targeting the player)
                self.npc_behaviour_manager()
                if self.debug_mode:
                    self.draw_debug_data()

            # Display the game over screen
            if self.state == "game_over":
                self.draw_game_over_screen()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_game()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = "display_highscore"

            if self.state == "display_highscore":
                self.high_score_handler()
                self.draw_high_score_display()
                self.reset_game()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_game()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = "main_menu"
            # display custom cursor
            self.cursor.draw_cursor(self.window)

        pygame.quit()  # Quit the game when the main loop exits

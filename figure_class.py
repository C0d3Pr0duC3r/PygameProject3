import math
import pygame
import time
import random
from collections import namedtuple
import copy
from icecream import ic
import colorsys

pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(32)  # Set to 32 channels

# screen info
info = pygame.display.Info()
screen_dimensions = [info.current_w, info.current_h]
# screen_dimensions = [1280, 720]
base_window_dimensions = [2560, 1440]

# Calculate the screen scale factor
rescaling_factor = min(screen_dimensions[0] / base_window_dimensions[0], screen_dimensions[1] / base_window_dimensions[1])
print(f"rescaling factor: {rescaling_factor}")
WEAPON_SWITCH_DELAY = 2

AmmoType = namedtuple(typename='AmmoType', field_names=['current_ammo', 'max'])

explosion_animation_sheet = 'graphics/animations/Explosion_A-Sheet.png'
explosion_sprite = 'graphics\\effects\\Some_explosion.png'
muzzle_flash_sheet = 'graphics/animations/muzzle_flash.png'
projectile_explosion_sheet = 'graphics/animations/Porjectile_hit.png'
portal_opening_sheet = 'graphics/animations/Portal.png'

player_model = "graphics/Models/player_model.png"
projectile_sheet = "graphics/Models/sprite_sheet_3d_pre_rendered_projectile.png"
scout_model = 'graphics/Models/scout_model.png'
brawler_model = 'graphics/Models/brawler_model.png'
torus_enemy_sprite = 'graphics/Models/torus_model.png'
mogus_spreader_model = 'graphics/Models/mogus_spreader_model.png'
missile_mogus_model = 'graphics/Models/missile_mogus_model.png'
shredder_model = 'graphics/Models/shredder_model.png'
aim_path = 'graphics/Cursors/aim.png'
health_pick_up_path = 'graphics/Models/health_pickup.png'
omega_health_model = 'graphics/Models/omega_health_model.png'
coin_model = 'graphics/Models/coin_model.png'
shield_model = 'graphics/Models/shield_model.png'
energy_ammo_model = 'graphics/Models/energy_ammo_sheet.png'
shell_ammo_model = 'graphics/Models/shell_ammo_item_model.png'
projectile_ammo_sheet = 'graphics/Models/projectile_ammo_item_model.png'
missile_model = 'graphics/Models/missile_model.png'
missile_launcher_model = 'graphics/Models/missile_launcher_model.png'

spreader_item_sheet = 'graphics/Models/spreader_item_model.png'
chain_gun_item_sheet = 'graphics/Models/chain_gun_item_model.png'


def time_it(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds to run")
        return result

    return wrapper


gun_sounds = {"blaster_sound": 'sound_fx\\player_sounds\\basic_blaster_sound.wav',
              "spreader_sound": 'sound_fx\\player_sounds\\spreader_sound.wav',
              "raaraa_sound": 'sound_fx\\player_sounds\\raaraa.wav',
              "rail_gun_sound": 'sound_fx/player_sounds/rail_gun_sound.wav',
              "enemy_blaster_sound": 'sound_fx\\enemy_sounds\\enemy_blaster.wav',
              "enemy_spreader_sound": 'sound_fx\\enemy_sounds\\enemy_spreader.wav',
              "enemy_rara_sound": 'sound_fx\\enemy_sounds\\enemy_raaraa.wav'
              }

player_sounds = [
    {"1": pygame.mixer.Sound("sound_fx\\player_sounds\\hit_sound_1.wav"),
     "2": pygame.mixer.Sound("sound_fx\\player_sounds\\hit_sound_2.wav"),
     "3": pygame.mixer.Sound("sound_fx\\player_sounds\\hit_sound_3.wav"),
     "4": pygame.mixer.Sound("sound_fx\\player_sounds\\hit_sound_4.wav"),
     "5": pygame.mixer.Sound("sound_fx\\player_sounds\\hit_sound_5.wav")},
    {"1": pygame.mixer.Sound("sound_fx\\player_sounds\\healing_sound.wav")}
]

enemy_hit_sounds = [
    {"1": pygame.mixer.Sound("sound_fx\\enemy_sounds\\enemy_hit_1.wav"),
     "2": pygame.mixer.Sound("sound_fx\\enemy_sounds\\enemy_hit_2.wav"),
     "3": pygame.mixer.Sound("sound_fx\\enemy_sounds\\enemy_hit_3.wav"),
     "4": pygame.mixer.Sound("sound_fx\\enemy_sounds\\enemy_hit_4.wav"),
     "5": pygame.mixer.Sound("sound_fx\\enemy_sounds\\enemy_hit_5.wav")},
    None
]
for dict_ in player_sounds:
    for key, sound in dict_.items():
        sound.set_volume(0.2)


class Animation:
    def __init__(self, sprite_sheet, frame_size, num_frames, fps, position, angle=0, name="Animation", is_path=True,
                 owner=None):
        self.name = name
        if is_path:
            self.sprite_sheet = pygame.image.load(sprite_sheet)
        else:
            self.sprite_sheet = sprite_sheet
        self.frame_size = frame_size
        self.num_frames = num_frames
        self.position = position
        self.fps = fps
        self.current_frame = 0
        self.sprites = []
        self.last_update = pygame.time.get_ticks()
        self.time_since_last_frame = 0
        self.duration = 1000 / fps  # Duration for each frame in milliseconds
        self.angle = angle
        self.owner = owner

        frame_width = self.frame_size[0] // num_frames
        for i in range(self.num_frames):
            x = i * frame_width
            y = 0  # Assuming all frames are in a single row
            sprite = self.sprite_sheet.subsurface(pygame.Rect(x, y, frame_width, self.frame_size[1]))
            self.sprites.append(sprite)

    """def update(self):
        now = pygame.time.get_ticks()
        self.time_since_last_frame += now - self.last_update
        if self.time_since_last_frame >= self.duration:
            print(f"self.owner: {self.owner}, self.owner.name: {self.owner.name}, self.name: {self.name} Animation frame: {self.current_frame}")  # Debug print
            self.current_frame = (self.current_frame + 1) % self.num_frames
            self.time_since_last_frame -= self.duration
        self.last_update = now"""

    def update(self, frame_counter, game_fps):
        update_interval = game_fps / self.fps

        if frame_counter % int(update_interval) == 0:
            self.current_frame = (self.current_frame + 1) % self.num_frames

    def draw_animation(self, window, position):
        current_frame = self.sprites[self.current_frame]
        frame_copy = pygame.transform.rotate(current_frame, self.angle)
        # this somehow centers the rotation so it doesn't look fucked up
        x = position[0] - int(frame_copy.get_width() / 2)
        y = position[1] - int(frame_copy.get_height() / 2)
        window.blit(frame_copy, [x, y])

    def is_finished(self):
        """Returns True if the animation has displayed all its frames."""
        return self.current_frame == self.num_frames - 1

    def clone(self):
        new_animation = Animation(
            name=self.name,
            sprite_sheet=self.sprite_sheet,
            frame_size=self.frame_size,
            num_frames=self.num_frames,
            fps=self.fps,
            position=self.position.copy(),
            is_path=False,
            angle=self.angle,
            owner=self.owner
        )
        # Copy other attributes if necessary
        new_animation.current_frame = self.current_frame
        new_animation.sprites = self.sprites.copy()
        new_animation.last_update = pygame.time.get_ticks()
        new_animation.time_since_last_frame = 0  # Resetting the time since the last frame for the cloned animation

        return new_animation


explosion_a = Animation(explosion_animation_sheet, [2560, 256], 10, 20, [0, 0], name="explosion_a")  # weird shit

muzzle_flash = Animation(muzzle_flash_sheet, [300, 150], 2, 60, [0, 0], name="muzzle_flash")

projectile_explosion = Animation(projectile_explosion_sheet, [600, 150], 4, 60, [0, 0], name="projectile_explosion")

portal_opening = Animation(portal_opening_sheet, [4200, 300], 14, 20, [0, 0], name="portal_opening")


class Sprite_sheet_loader_3d:
    def __init__(self, sprite_sheet_path, sprite_columns, scale=1, rescaling_factor=rescaling_factor):
        self.sprite_sheet = pygame.image.load(sprite_sheet_path)
        self.sprite_columns = sprite_columns
        self.scale = scale

        # Combine manual scale and screen scale
        final_scale = rescaling_factor * self.scale

        # Apply the scale to the sprite sheet
        self.scaled_sheet_width = int(self.sprite_sheet.get_width() * final_scale)
        self.scaled_sheet_height = int(self.sprite_sheet.get_height() * final_scale)
        self.sprite_sheet = pygame.transform.scale(self.sprite_sheet, (self.scaled_sheet_width, self.scaled_sheet_height))

        # Update sprite dimensions based on scaled sheet
        self.sprite_width = self.sprite_sheet.get_width() // self.sprite_columns
        self.sprite_height = self.sprite_sheet.get_height()

        # self.scale = final_scale
        self.step = 360 / self.sprite_columns
        self.oriented_sprites = self._precompute_sprites()

    def _precompute_sprites(self):
        sprites = []
        for column in range(self.sprite_columns):
            sprite_x = column * self.sprite_width
            sprite = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
            sprite.blit(self.sprite_sheet, (0, 0), (sprite_x, 0, self.sprite_width, self.sprite_height))
            sprites.append(sprite)
        return sprites

    def get_oriented_sprite(self, orientation):
        closest_orientation = round(orientation / self.step) * self.step % 360
        index = int(closest_orientation // self.step)
        return self.oriented_sprites[index]




class Figure:
    def __init__(self, name, position, **kwargs):
        # Identity attributes
        self.name = name
        self.type_ = kwargs.get('type_', 'standard')

        # Position and movement attributes
        self.position = list(position)
        self.velocity = kwargs.get('velocity', 0)
        self.orientation = kwargs.get('orientation', 0)
        self.turn_speed = kwargs.get('turn_speed', 0)
        self.y_limit = kwargs.get('y_limit', None)
        self.x_limit = kwargs.get('x_limit', None)

        # Visual attributes
        self.dimensions = kwargs.get('dimensions', [5, 5])
        self.color = kwargs.get('color', (255, 255, 255))
        self.animation = kwargs.get('animation', None)
        self.sprite_loader = kwargs.get('sprite_loader', None)
        self.rect = pygame.Rect(self.return_dimensions_and_position())
        if self.sprite_loader:
            self.mask = pygame.mask.from_surface(self.sprite_loader.get_oriented_sprite(self.orientation))
            self.mask_image = self.mask.to_surface()
        else:
            self.mask = pygame.mask.from_surface(pygame.Surface(self.dimensions))
            self.mask_image = self.mask.to_surface()

    # universal figure method
    def rotate_figure(self, direction):
        # Rotate animation
        if direction == "left":
            self.orientation -= self.turn_speed
        elif direction == "right":
            self.orientation += self.turn_speed

    # universal figure method
    def movement(self, direction):
        if direction == "up":
            self.position[1] -= self.velocity
        if direction == "down":
            self.position[1] += self.velocity
        if direction == "left":
            self.position[0] -= self.velocity
        if direction == "right":
            self.position[0] += self.velocity
        self.update_rect()

    # universal figure method
    def return_dimensions_and_position(self):
        # the // operation ensures, that the center of the rect is used as position of the object
        dimensions = (
            self.position[0] - self.dimensions[0] // 2, self.position[1] - self.dimensions[1] // 2, self.dimensions[0]*rescaling_factor,
            self.dimensions[1]*rescaling_factor)
        return dimensions

    # method for player and npcs as well as projectiles that spawn "shrapnel"
    def offset_spawn_position(self):  # so you don't shoot yourself
        angle_in_radians = math.radians(self.orientation)

        # Calculate the change in x and y based on the angle and offset distance
        dx = self.dimensions[1] * math.sin(angle_in_radians) / 2
        dy = self.dimensions[1] * math.cos(angle_in_radians) / 2

        # Calculate the new spawn position
        new_x = self.position[0] + dx * 0.9
        new_y = self.position[1] - dy * 0.9  # Subtract dy because the y-axis is inverted in Pygame

        return [new_x, new_y]

    # universal figure method
    def update_mask(self):
        self.mask = pygame.mask.from_surface(self.sprite_loader.get_oriented_sprite(self.orientation))
        self.mask_image = self.mask.to_surface()

    # universal figure method
    def update_rect(self):
        # Center the rect on the figure's position
        self.rect.x = self.position[0] - self.dimensions[0] // 2
        self.rect.y = self.position[1] - self.dimensions[1] // 2
        self.rect.width, self.rect.height = self.dimensions

    # universal figure method
    def update_dimensions_from_sprite(self, sprite):
        self.dimensions = sprite.get_width(), sprite.get_height()
        self.update_rect()  # Update the rect based on the new dimensions

    # universal figure method
    def override_position(self, new_position):
        self.position = new_position

    # universal figure method
    def debug_visuals(self, window, frame):
        # Vary the hue between 0 and 1
        hue = (frame % 360) / 360.0  # Convert frame count to a value between 0 and 1
        saturation, value = 1, 1  # Full saturation and value for a vibrant color

        # Convert HSV to RGB
        rgb_fractional = colorsys.hsv_to_rgb(hue, saturation, value)  # Returns colors in range [0, 1]
        rgb = tuple(int(c * 255) for c in rgb_fractional)  # Convert to range [0, 255]
        # draw position point
        pygame.draw.circle(window, (255, 0, 0), (int(self.position[0]), int(self.position[1])), 5)
        # Draw hitbox
        pygame.draw.rect(window, (0, 255, 0), self.rect, 2)

        # Draw orientation line
        length = 50  # Length of the orientation line
        angle_in_radians = math.radians(self.orientation)
        end_x = int(self.position[0] + length * math.sin(angle_in_radians))
        end_y = int(self.position[1] - length * math.cos(angle_in_radians))

        pygame.draw.line(window, (0, 0, 255), (int(self.position[0]), int(self.position[1])), (end_x, end_y), 2)
        # Draw mask
        window.blit(self.mask_image,
                    [self.position[0] + 0.5 * self.dimensions[0], self.position[1] + 0.5 * self.dimensions[1]])
        # because for npcs for some godforsaken reason the elements in the position are becoming a float at some point
        figure_position = [int(coord) for coord in self.position]
        # wich would spam the screen with numbers
        font = pygame.font.Font(None, 32)
        name_surface = font.render(f"{self.name}; {self.type_}; {figure_position}", False, rgb)
        name_rect = name_surface.get_rect(topright=self.position)
        window.blit(name_surface, name_rect)

    # universal figure method
    def draw_figure(self, window):
        if self.sprite_loader:  # If a SpriteSheetLoader instance is available
            sprite = self.sprite_loader.get_oriented_sprite(self.orientation)
            window.blit(sprite, (self.position[0] - self.sprite_loader.sprite_width // 2,
                                 self.position[1] - self.sprite_loader.sprite_height // 2))
            self.update_dimensions_from_sprite(sprite)
            self.update_mask()
        else:  # If no sprite sheet is provided, draw a green square
            self.update_rect()
            pygame.draw.rect(window, self.color, self.return_dimensions_and_position())

    # universal figure method
    def clone(self):
        """Creates a copy of the Figure instance."""

        # Create a new instance without calling __init__
        cloned_obj = self.__class__.__new__(self.__class__)

        # Copy over attributes
        for key, value in self.__dict__.items():
            if isinstance(value, pygame.Surface):
                # Create a copy of the Surface
                cloned_obj.__dict__[key] = value.copy()
            else:
                # Use shallow copy for other attributes
                cloned_obj.__dict__[key] = copy.copy(value)

        return cloned_obj


class Actor(Figure):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Health and defense attributes
        self.hit_points = kwargs.get('hit_points', None)
        self.shield = kwargs.get('shield', None)
        self.shield_cap = kwargs.get('shield_cap', None)
        self.hit_points_cap = kwargs.get('hit_points_cap', None)
        self.shield_recharge_rate = kwargs.get('shield_recharge_rate', None)
        self.shield_recharge_delay = kwargs.get('shield_recharge_delay', 2)
        self.last_got_hit_time = 0
        self.hit_point_overcharge = kwargs.get('hit_point_overcharge', None)
        self.shield_overcharge = kwargs.get('shield_overcharge', None)

        # Weapons and combat attributes
        self.weapons = []
        self.weapon_index = 0
        self.sound_effects = kwargs.get('sound_effects', None)
        self.weapon_switch_delay = kwargs.get('weapon_switch_delay', None)
        self.last_weapon_switch_time = 0
        self.current_weapon = None

        # Economy attributes
        self.coins = kwargs.get('coins', 0)

        # Miscellaneous attributes
        self.available_upgrades = kwargs.get('available_upgrades', None)
        self.no_clip = kwargs.get('no_clip', False)
        self.marked_for_death = False
        self.abilities = []  # Future use: create abilities like "phase jump" or dash

    # method for projectiles, npcs and player
    def apply_thrust(self, direction, mode):
        if mode == "normal":
            angle_in_radians = math.radians(self.orientation)
            modifier = 0.5
        elif mode == "strafe":
            angle_in_radians = math.radians(self.orientation - 90)
            modifier = 1

        # Calculate the change in x and y based on the angle and velocity
        dx = self.velocity * math.sin(angle_in_radians)
        dy = self.velocity * math.cos(angle_in_radians)

        if direction == "prograde":
            # Update the position values
            self.position[0] += dx
            self.position[1] -= dy
        if direction == "retrograde":
            self.position[0] -= dx * modifier
            self.position[1] += dy * modifier

        # Update the rect or any other attributes based on the new position
        self.update_rect()

    def look_at(self, target, instant=False):

        # Calculate the change in x and y
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]

        # Calculate the angle in radians between the positive x-axis and the ray to the point (dx, dy)
        angle_in_radians = math.atan2(dy, dx)

        # Convert the angle to degrees
        angle_in_degrees = math.degrees(angle_in_radians)
        desired_orientation = (angle_in_degrees + 90) % 360

        # Adjust the angle so it works with your game's orientation system
        # You might need to add or subtract 90 degrees or make other adjustments depending on how your sprites are oriented
        if instant:
            self.orientation = desired_orientation
        else:
            # Calculate the angle difference
            angle_diff = desired_orientation - self.orientation
            # Adjust for wrapping around 360 degrees
            if angle_diff > 180:
                angle_diff -= 360
            elif angle_diff < -180:
                angle_diff += 360

            # Adjust orientation based on turn speed
            if abs(angle_diff) < self.turn_speed:
                # If the remaining angle to turn is smaller than the turn speed, just set the orientation to the desired orientation
                self.orientation = desired_orientation
            elif angle_diff > 0:
                self.orientation += self.turn_speed
            else:
                self.orientation -= self.turn_speed

            # Ensure orientation stays between 0 and 359 degrees
            self.orientation %= 360

    # method for projectiles, npcs and player
    def get_hit(self, damage):

        self.last_got_hit_time = time.time()  # get the time of the hit

        if self.sound_effects:
            hit_sounds = self.sound_effects[0]  # Accessing the first dictionary
            random_sound_key = random.choice(list(hit_sounds.keys()))
            hit_sounds[random_sound_key].play()

        if self.shield and self.shield > 0:
            if damage > self.shield:
                self.shield = 0
                left_over_damage = damage - self.shield
                self.hit_points -= left_over_damage
                # TODO shield breaking = True -> stun the Figure for a few seconds or something
            else:
                self.shield -= damage
        else:
            try:
                self.hit_points -= damage
            except TypeError:
                print(TypeError, "figure_class.py 477")

        # Only set marked_for_death for non-Player instances
        if not isinstance(self, Player):
            try:
                if self.hit_points <= 0:
                    self.marked_for_death = True
            except TypeError:
                print(TypeError)

    # method for player and npcs
    def trigger_pull(self):
        self.current_weapon = self.weapons[self.weapon_index]
        if self.weapons:

            projectile_type = self.type_ + "projectile"
            if self.current_weapon.muzzle_flash and self.current_weapon.can_shoot():
                a = self.current_weapon.muzzle_flash
                a.position = self.offset_spawn_position()
                a.angle = -(self.orientation - 90)

                return self.current_weapon.weapon_shoot(self.orientation, self.offset_spawn_position(),
                                                        projectile_type), self.current_weapon.muzzle_flash.clone()
            else:
                return self.current_weapon.weapon_shoot(self.orientation, self.offset_spawn_position(),
                                                        projectile_type), None

        else:
            print("No Weapon available")
            return None

    # method for player and npcs
    def add_weapon(self, *weapons):
        for weapon in weapons:
            self.weapons.append(weapon)

    # method for npcs and player
    def get_healed(self, amount):
        if self.sound_effects:
            healing_sound_effect = self.sound_effects[1]
            healing_sound_effect["1"].play()
        self.hit_points += amount
        if self.hit_points_cap:
            if self.hit_points > self.hit_points_cap:
                self.hit_points = self.hit_points_cap

    # method for npcs and player
    def get_shield(self, amount):
        self.shield += amount
        if self.shield_cap:
            if self.shield > self.shield_cap:
                self.shield = self.shield_cap

    """TODO transform this into a method that "spawns" numbers that represent the dealt damage in green if its against
    enemies and in red if its against player and integrate it into the get_hit method"""

    def draw_hitpoints(self, window):
        hit_points_font = pygame.font.Font(None, 64)
        hit_points_surface = hit_points_font.render(str(self.hit_points), True, (255, 0, 0))
        hit_points_rect = hit_points_surface.get_rect(center=(self.position[0] + 70, self.position[1]))
        window.blit(hit_points_surface, hit_points_rect)
        pygame.display.update()


class Obstacle(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Player(Actor):
    def __init__(self, *args, radar_active=False, **kwargs):
        # Call the initialization method of the parent class, Figure
        super().__init__(*args, **kwargs)
        self.max_velocity = kwargs.get('max_velocity', 1)
        self.acceleration = kwargs.get('acceleration', 1)
        self.velocity = [0, 0]
        self.target_index = -1
        self.radar_active = radar_active
        self.is_moving = False
        self.ammo = {
            "energy_ammo": AmmoType(50, 200),
            "projectile_ammo": AmmoType(0, 500),
            "shell_ammo": AmmoType(5, 50),
            "missile_ammo": AmmoType(10, 20)

        }

    def handle_thrust_vector(self, key_pressed, mode="normal", direction="prograde"):
        """
        Update the player's position based on their velocity, acceleration, and direction.

        Args:
        - key_pressed (bool): True if a movement key is pressed, False if not.
        - mode (str): "normal" for forward/backward movement, "strafing" for side-to-side movement.
        - direction (str): "prograde" for forward/right movement, "retrograde" for backward/left movement.
        """

        # Convert the player's orientation to radians (assuming self.orientation is in degrees)
        angle_in_radians = math.radians(self.orientation - 90)

        if mode == "normal":
            # Normal mode: apply thrust forward/backward based on orientation
            if key_pressed:
                if direction == "prograde":
                    # Apply acceleration in the direction of orientation
                    acceleration_x = self.acceleration * math.cos(angle_in_radians)
                    acceleration_y = self.acceleration * math.sin(angle_in_radians)
                    self.velocity[0] += acceleration_x
                    self.velocity[1] += acceleration_y
                elif direction == "retrograde":
                    # Apply reverse acceleration
                    acceleration_x = self.acceleration * math.cos(angle_in_radians)
                    acceleration_y = self.acceleration * math.sin(angle_in_radians)
                    self.velocity[0] -= acceleration_x
                    self.velocity[1] -= acceleration_y

                # Cap the velocity to max_velocity
                velocity_magnitude = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
                if velocity_magnitude > self.max_velocity:
                    scale = self.max_velocity / velocity_magnitude
                    self.velocity[0] *= scale
                    self.velocity[1] *= scale

        elif mode == "strafing":
            # Strafing mode: apply thrust to the sides
            if key_pressed:
                if direction == "prograde":
                    # Strafe right (perpendicular to orientation)
                    acceleration_x = self.acceleration * math.cos(angle_in_radians + math.pi / 2)
                    acceleration_y = self.acceleration * math.sin(angle_in_radians + math.pi / 2)
                    self.velocity[0] += acceleration_x
                    self.velocity[1] += acceleration_y
                elif direction == "retrograde":
                    # Strafe left (perpendicular to orientation)
                    acceleration_x = self.acceleration * math.cos(angle_in_radians - math.pi / 2)
                    acceleration_y = self.acceleration * math.sin(angle_in_radians - math.pi / 2)
                    self.velocity[0] += acceleration_x
                    self.velocity[1] += acceleration_y

                # Cap the velocity to max_velocity times two because of some reason strafing is just half as fast
                velocity_magnitude = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
                if velocity_magnitude > self.max_velocity * 2:
                    scale = self.max_velocity * 2 / velocity_magnitude
                    self.velocity[0] *= scale
                    self.velocity[1] *= scale

        # Apply friction when no key is pressed
        if not key_pressed:
            friction = 0.98  # Example friction value
            self.velocity[0] *= friction
            self.velocity[1] *= friction

        # Update the position based on the current velocity
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

        # Update the player's rect (or any other related attributes)
        self.update_rect()

    def arcade_movement(self, key_pressed, direction):
        # Apply acceleration based on the direction
        if direction == "up":
            self.velocity[1] -= self.acceleration
        elif direction == "down":
            self.velocity[1] += self.acceleration
        elif direction == "left":
            self.velocity[0] -= self.acceleration
        elif direction == "right":
            self.velocity[0] += self.acceleration

        # Calculate the velocity magnitude
        velocity_magnitude = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)

        # Normalize diagonal movement to maintain consistent speed in all directions
        if velocity_magnitude > self.max_velocity:
            scale = self.max_velocity / velocity_magnitude
            self.velocity[0] *= scale
            self.velocity[1] *= scale

        # Apply friction when no key is pressed
        if not key_pressed:
            friction = 0.98  # Example friction value
            self.velocity[0] *= friction
            self.velocity[1] *= friction

        # Update the position based on the current velocity
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

        # Update the player's rect (or any other related attributes)
        self.update_rect()

    def draw_locking_markers(self, enemy_figures, window):
        # Line thickness for the rectangle outline
        line_thickness = 2

        for enemy in enemy_figures:
            # Dimensions of the red rectangle
            rect_width, rect_height = enemy.dimensions[0] * 0.8, enemy.dimensions[1] * 0.8
            # Calculate top-left corner of the rectangle to center it around the cursor
            rect_x = enemy.position[0] - rect_width // 2
            rect_y = enemy.position[1] - rect_height // 2

            # Draw the rectangle outline
            pygame.draw.rect(window, (255, 0, 0), (rect_x, rect_y, rect_width, rect_height), line_thickness)

    def draw_locked_target_marker(self, target, window):
        # Line thickness for the rectangle outline
        line_thickness = 2

        # Dimensions of the red rectangle
        rect_width, rect_height = target.dimensions[0] * 0.8, target.dimensions[1] * 0.8
        # Calculate top-left corner of the rectangle to center it around the cursor
        rect_x = target.position[0] - rect_width // 2
        rect_y = target.position[1] - rect_height // 2

        # Draw the rectangle outline
        pygame.draw.rect(window, (0, 255, 0), (rect_x, rect_y, rect_width, rect_height), line_thickness)

    def radar_energy_cost(self):
        # Calculate how much time has passed since the last reduction
        if self.shield <= 0:
            self.radar_active = False
        if self.shield > 0:
            # Reduce the shield by 3 units for each whole second
            self.shield -= 10 / 60

    # method for player
    def hit_points_and_shield_dynamic(self):

        """
        handles the shield recharge delay by getting the time the last hit received
        reduces the health and shield overcharge according to playerstats over time back to normal
        """

        current_time = time.time()

        if current_time - self.last_got_hit_time > self.shield_recharge_delay:
            if self.shield < self.shield_overcharge:
                # shield recharge rate is divided by 60 because that should be the frame rate and then
                # the shield recharge should act like a per second regeneration
                modified_recharge_rate = self.shield_recharge_rate / 60 * (1 - (self.shield / self.shield_cap))
                self.shield += modified_recharge_rate
        if self.hit_points > self.hit_point_overcharge:
            self.hit_points -= 3 / 60
        if self.shield > self.shield_overcharge + 1:
            self.shield -= 10 / 60

    # method for Player
    def get_coin(self):
        self.coins += 1

    # method for player
    def purchase_upgrade(self, upgrade):
        if self.coins >= upgrade.cost:
            self.coins -= upgrade.cost
            upgrade.apply_upgrade(self)
        else:
            print("Not enough coins!")  # This can be replaced with a more advanced feedback system.

    # method for player
    def increase_ammo(self, ammo_key, amount):
        current_ammo = self.ammo[ammo_key].current_ammo + amount
        # Ensure the ammo doesn't exceed the max limit
        current_ammo = min(self.ammo[ammo_key].max, current_ammo)
        self.ammo[ammo_key] = self.ammo[ammo_key]._replace(current_ammo=current_ammo)

    def debug_visuals(self, window, frame):
        # Vary the hue between 0 and 1
        hue = (frame % 360) / 360.0  # Convert frame count to a value between 0 and 1
        saturation, value = 1, 1  # Full saturation and value for a vibrant color

        # Convert HSV to RGB
        rgb_fractional = colorsys.hsv_to_rgb(hue, saturation, value)  # Returns colors in range [0, 1]
        rgb = tuple(int(c * 255) for c in rgb_fractional)  # Convert to range [0, 255]

        # Draw position point
        pygame.draw.circle(window, (255, 0, 0), (int(self.position[0]), int(self.position[1])), 5)

        # Draw hitbox
        pygame.draw.rect(window, (0, 255, 0), self.rect, 2)

        # Calculate the length of the velocity vector
        length = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2) * 50  # Scale factor for visual representation

        # Normalize the velocity vector to get the direction
        velocity_magnitude = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
        if velocity_magnitude != 0:
            direction_x = self.velocity[0] / velocity_magnitude
            direction_y = self.velocity[1] / velocity_magnitude
        else:
            direction_x, direction_y = 0, 0  # No movement, so no direction

        # Calculate the end position based on the velocity direction
        end_x = int(self.position[0] + direction_x * length)
        end_y = int(self.position[1] + direction_y * length)

        # Draw the velocity vector as a line
        pygame.draw.line(window, (255, 0, 0), (int(self.position[0]), int(self.position[1])), (end_x, end_y), 8)

        # Draw mask
        window.blit(self.mask_image,
                    [self.position[0] + 0.5 * self.dimensions[0], self.position[1] + 0.5 * self.dimensions[1]])

        # Convert position to integer to avoid float issues and prepare the text for debugging
        figure_position = [int(coord) for coord in self.position]

        # Render position and velocity information as text
        font = pygame.font.Font(None, 48)
        name_surface = font.render(
            f"{self.name}; {self.type_}; Pos: {figure_position}; Vel: {[round(v, 2) for v in self.velocity]}", False,
            rgb)
        name_rect = name_surface.get_rect(topright=self.position)

        # Draw the text next to the figure
        window.blit(name_surface, name_rect)

    def clone(self):
        cloned_player = Player(
            name=self.name,
            position=self.position,
            hit_points=self.hit_points,
            shield=self.shield,
            shield_cap=self.shield_cap,
            shield_overcharge=self.shield_overcharge,
            hit_points_cap=self.hit_points_cap,
            hit_point_overcharge=self.hit_point_overcharge,
            sprite_loader=self.sprite_loader,
            shield_recharge_rate=self.shield_recharge_rate,
            turn_speed=self.turn_speed,
            max_velocity=self.max_velocity,
            acceleration=self.acceleration,
            y_limit=self.y_limit,
            x_limit=self.x_limit,
            type_=self.type_,
            sound_effects=self.sound_effects,
            coins=self.coins,
            available_upgrades=self.available_upgrades,
            animation=self.animation
        )

        cloned_player.weapons = [weapon.clone() for weapon in self.weapons]
        cloned_player.animation = [animation.clone() for animation in self.animation]
        for weapon in cloned_player.weapons:
            weapon.owner = cloned_player
        cloned_player.weapon_index = self.weapon_index
        cloned_player.type_ = self.type_
        cloned_player.sound_effects = self.sound_effects

        return cloned_player


class NPC(Actor):
    def __init__(self, *args, reward, radius, spawn_animation_active=True, gets_locked=False, is_locked=False,
                 **kwargs):
        self.items_to_drop = []
        self.reward = reward
        self.radius = radius
        self.spawn_animation_active = spawn_animation_active
        self.gets_locked = gets_locked
        self.is_locked = is_locked
        self.kill_time = None

        super().__init__(*args, **kwargs)

    def random_chance(self, chance):
        """Return True with a 1/odds chance."""
        return random.randint(1, chance) == 1

    def add_potential_drop(self, *item_templates):
        for item_template in item_templates:
            self.items_to_drop.append(item_template)

    def set_kill_time(self, time_):
        self.kill_time = time_

    def change_weapon(self):
        self.weapon_index = (self.weapon_index + 1) % len(self.weapons)
        assert 0 <= self.weapon_index < len(self.weapons), f"Invalid weapon index for {self.name}!"
        self.last_weapon_switch_time = time.time()

    def handle_drop(self):
        """Determine if the figure drops an item upon death and returns it."""
        if self.items_to_drop:
            drop = []
            for item in self.items_to_drop:
                if self.random_chance(item.chance):
                    drop.append(item)
            return drop
        return None

    def draw_health_bar(self, window):
        health_bar_length = self.hit_points / 2
        pygame.draw.rect(window, (255, 0, 0), (
            self.position[0] - self.dimensions[0] / 2, self.position[1] - self.dimensions[1] / 2, health_bar_length,
            20))

    def is_in_range(self, target):
        if not (0 <= self.weapon_index < len(self.weapons)):
            print(f"ERROR: Invalid weapon index for {self.name}!")
            return False  # or some other default behavior

        distance = math.sqrt(
            (self.position[0] - target.position[0]) ** 2 + (self.position[1] - target.position[1]) ** 2)
        return distance < self.weapons[self.weapon_index].max_reach

    def calculate_lead_target(self, target_position, target_velocity, projectile_velocity):
        player_x, player_y = target_position
        npc_x, npc_y = self.position

        # Decompose target velocity into x and y components
        v_x, v_y = target_velocity  # Assume target_velocity is a tuple or list [vx, vy]

        # Calculate the distance between NPC and player
        distance = math.sqrt((npc_x - player_x) ** 2 + (npc_y - player_y) ** 2)

        # Estimate the time to impact
        if projectile_velocity > 0:
            T = distance / projectile_velocity
        else:
            T = 0  # Prevent division by zero

        # Calculate the lead position based on target velocity
        lead_x = player_x + v_x * T
        lead_y = player_y + v_y * T

        lead_pos = [lead_x, lead_y]

        return lead_pos

    def lead_target(self, target, window, debug_mode, instant=False, lead_target=True):

        if lead_target and self.current_weapon:
            lead_target_pos = self.calculate_lead_target(target.position, target.velocity,
                                                         self.current_weapon.projectile_velocity)
            if debug_mode:
                pygame.draw.circle(window, (0, 255, 0), lead_target_pos, 5)  # debug line

            # Calculate the change in x and y
            dx = lead_target_pos[0] - self.position[0]
            dy = lead_target_pos[1] - self.position[1]
        else:
            # Calculate the change in x and y
            dx = target.position[0] - self.position[0]
            dy = target.position[1] - self.position[1]

        # Calculate the angle in radians between the positive x-axis and the ray to the point (dx, dy)
        angle_in_radians = math.atan2(dy, dx)

        # Convert the angle to degrees
        angle_in_degrees = math.degrees(angle_in_radians)
        desired_orientation = (angle_in_degrees + 90) % 360

        if instant:
            self.orientation = desired_orientation
        else:
            # Calculate the angle difference
            angle_diff = desired_orientation - self.orientation
            # Adjust for wrapping around 360 degrees
            if angle_diff > 180:
                angle_diff -= 360
            elif angle_diff < -180:
                angle_diff += 360

            # Adjust orientation based on turn speed
            if abs(angle_diff) < self.turn_speed:
                # If the remaining angle to turn is smaller than the turn speed, just set the orientation to the desired orientation
                self.orientation = desired_orientation
            elif angle_diff > 0:
                self.orientation += self.turn_speed
            else:
                self.orientation -= self.turn_speed

            # Ensure orientation stays between 0 and 359 degrees
            self.orientation %= 360

    def clone(self):

        cloned_npc = NPC(
            name=self.name,
            position=self.position,
            hit_points=self.hit_points,
            radius=self.radius,
            dimensions=self.dimensions.copy(),
            sprite_loader=self.sprite_loader,
            turn_speed=self.turn_speed,
            velocity=self.velocity,
            orientation=self.orientation,
            reward=self.reward,
            color=self.color,
            y_limit=self.y_limit,
            x_limit=self.x_limit,
            no_clip=self.no_clip,
            weapon_switch_delay=self.weapon_switch_delay,
            spawn_animation_active=self.spawn_animation_active,
            is_locked=self.is_locked,
            gets_locked=self.gets_locked
        )
        cloned_npc.items_to_drop = [item.clone() for item in self.items_to_drop]
        cloned_npc.weapons = [weapon.clone() for weapon in self.weapons]
        cloned_npc.animation = [animation.clone() for animation in self.animation]
        for weapon in cloned_npc.weapons:
            weapon.owner = cloned_npc
        cloned_npc.weapon_index = self.weapon_index
        cloned_npc.type_ = self.type_
        cloned_npc.sound_effects = self.sound_effects

        return cloned_npc


class BossNPC(NPC):
    def __init__(self, *args, reward, radius, **kwargs):
        super().__init__(*args, reward=reward, radius=radius, **kwargs)

    # create some way to indicate to the player that the boss is about to fire
    def clone(self):
        cloned_boss = BossNPC(
            name=self.name,
            position=self.position,
            hit_points=self.hit_points,
            radius=self.radius,
            dimensions=self.dimensions.copy(),
            sprite_loader=self.sprite_loader,
            turn_speed=self.turn_speed,
            velocity=self.velocity,
            orientation=self.orientation,
            reward=self.reward,
            color=self.color,
            y_limit=self.y_limit,
            x_limit=self.x_limit,
            no_clip=self.no_clip,
            weapon_switch_delay=self.weapon_switch_delay,
            spawn_animation_active=self.spawn_animation_active,
            is_locked=self.is_locked,
            gets_locked=self.gets_locked
        )
        cloned_boss.items_to_drop = [item.clone() for item in self.items_to_drop]
        cloned_boss.weapons = [weapon.clone() for weapon in self.weapons]
        cloned_boss.animation = [animation.clone() for animation in self.animation]
        for weapon in cloned_boss.weapons:
            weapon.owner = cloned_boss
        cloned_boss.weapon_index = self.weapon_index
        cloned_boss.type_ = self.type_
        cloned_boss.sound_effects = self.sound_effects

        return cloned_boss

    def attack_indication(self, window):
        # Umwandeln des Winkels in Radiant
        angle_radians = math.radians(self.orientation - 90)

        # Berechnung des Richtungsvektors
        direction_x = math.cos(angle_radians)
        direction_y = math.sin(angle_radians)

        # Skalieren des Richtungsvektors auf 100 Pixel
        length = 100
        end_x = int(self.position[0] + direction_x * length)
        end_y = int(self.position[1] + direction_y * length)

        # Zeichne die rote Linie
        pygame.draw.line(window, (255, 0, 0), (int(self.position[0]), int(self.position[1])), (end_x, end_y), 2)

    """a Method that shows the boss enemy is aiming and about to shoot"""


class Projectile(Actor):
    def __init__(self, name, damage, orientation, velocity, position, life_time=None, sprite_loader=None,
                 max_reach=None, max_pierce=None, animation=None):

        self.damage = damage
        self.orientation = orientation
        self.sprite_loader = sprite_loader
        self.spawn_position = position.copy()  # Save the spawn position
        self.max_reach = max_reach
        self.hit_targets = []
        self.hit_count = 0
        self.max_pierce = max_pierce
        self.animation = animation
        self.birth_time = time.time()
        self.life_time = life_time

        if self.sprite_loader:
            self.mask = pygame.mask.from_surface(self.sprite_loader.get_oriented_sprite(self.orientation))
            self.mask_image = self.mask.to_surface()

        super().__init__(name, position, velocity=velocity, sprite_loader=sprite_loader, orientation=orientation,
                         animation=animation)

        if self.sprite_loader:
            # Set the mask explicitly for the projectile
            self.mask = pygame.mask.from_surface(self.sprite_loader.get_oriented_sprite(self.orientation))
            self.mask_image = self.mask.to_surface()

    def update_mask(self):
        self.mask = pygame.mask.from_surface(self.sprite_loader.get_oriented_sprite(self.orientation))
        self.mask_image = self.mask.to_surface()

    def projectile_max_reach(self):
        if self.max_reach:
            a = self.position[0] - self.spawn_position[0]
            b = self.position[1] - self.spawn_position[1]
            distance_traveled = math.sqrt(a ** 2 + b ** 2)

            if distance_traveled > self.max_reach:
                return True  # remove projectile
            else:
                return False  # dont
        return False

    def hit(self, target):
        """
        Marks the target as hit by the projectile, applying damage and tracking hit targets.
        Determines if the projectile should be removed based on its piercing ability.

        Parameters:
        - target (Figure): The target object that the projectile has hit.

        Returns:
        - bool: True if the projectile should be removed after the hit, otherwise False.

        Note:
        If the projectile has a max_pierce value, it checks whether this value is less than its hit count.
        If so, it returns True, indicating the projectile should be removed. Otherwise, it returns False.
        If the projectile's max_pierce is set to None, it always returns True, suggesting the projectile
        should be removed after a single hit.
        """

        if target not in self.hit_targets:
            target.get_hit(self.damage)

            self.hit_targets.append(target)
            self.hit_count += 1

        if self.max_pierce:
            if self.max_pierce < self.hit_count:
                return True
            else:
                return False
        elif not self.max_pierce:
            return True

    def draw_projectile(self, window):
        if self.sprite_loader:  # If a SpriteSheetLoader instance is available
            sprite = self.sprite_loader.get_oriented_sprite(self.orientation)
            window.blit(sprite, (self.position[0] - self.sprite_loader.sprite_width // 2,
                                 self.position[1] - self.sprite_loader.sprite_height // 2))

            self.update_dimensions_from_sprite(sprite)
            self.update_mask()

        else:  # If no sprite sheet is provided, draw a square
            self.update_rect()
            pygame.draw.rect(window, self.color, self.return_dimensions_and_position())

    def override_dimension(self, new_dimensions):
        self.dimensions = new_dimensions

    def override_color(self, color_code):
        self.color = color_code

    def behave(self):
        self.apply_thrust("prograde", "normal")

    def check_lifetime(self):
        if time.time() - self.birth_time > self.life_time:
            self.marked_for_death = True


class HomingProjectile(Projectile):
    def __init__(self,
                 *args,
                 locked_target,
                 associated_weapon,
                 explosion_radius=None,
                 shrapnel_count=None,
                 shrapnel_angle=0,
                 turn_speed=5,
                 **kwargs):
        # Handle turn_speed before calling the superclass's __init__ method
        self.turn_speed = turn_speed
        # Call the initialization method of the parent class, Projectile
        super().__init__(*args, **kwargs)
        self.turn_speed = turn_speed
        self.locked_target = locked_target
        self.associated_weapon = associated_weapon
        self.explosion_radius = explosion_radius
        self.shrapnel_count = shrapnel_count
        self.shrapnel_angle = shrapnel_angle

    def steer_at(self, target):

        try:
            target_pos = target.position
            # Calculate the change in x and y
            dx = target_pos[0] - self.position[0]
            dy = target_pos[1] - self.position[1]

            # Calculate the angle in radians between the positive x-axis and the ray to the point (dx, dy)
            angle_in_radians = math.atan2(dy, dx)

            # Convert the angle to degrees
            angle_in_degrees = math.degrees(angle_in_radians)
            # adjust angle to match the orientation of the game
            desired_orientation = (angle_in_degrees + 90) % 360
            # Calculate the angle difference
            angle_diff = desired_orientation - self.orientation
            # Adjust for wrapping around 360 degrees
            if angle_diff > 180:
                angle_diff -= 360
            elif angle_diff < -180:
                angle_diff += 360

            # Adjust orientation based on turn speed
            if abs(angle_diff) < self.turn_speed:
                # If the remaining angle to turn is smaller than the turn speed, just set the orientation to the desired orientation
                self.orientation = desired_orientation
            elif angle_diff > 0:
                self.orientation += self.turn_speed
            else:
                self.orientation -= self.turn_speed

            # Ensure orientation stays between 0 and 359 degrees
            self.orientation %= 360
        except AttributeError:
            ic(AttributeError, target)

    def create_shrapnel(self):
        shrapnel_projectiles = []

        # Calculate the starting angle for the shrapnel spread
        start_angle = self.orientation - self.shrapnel_angle / 2

        # Calculate the angle increment for each shrapnel piece
        angle_increment = self.shrapnel_angle / (self.shrapnel_count - 1)

        for i in range(self.shrapnel_count):
            # Calculate the angle for this shrapnel piece
            shrapnel_angle = start_angle + i * angle_increment

            # Create the shrapnel projectile (you'd need to define the appropriate parameters)
            shrapnel = Projectile(
                name="shrapnel",
                damage=self.damage,  # or some fraction of the original damage
                orientation=shrapnel_angle,
                velocity=25,  # or some predefined shrapnel speed
                position=self.position,
                animation=[projectile_explosion],
                max_reach=500
            )
            shrapnel.override_dimension([3, 3])

            shrapnel.type_ = "shrapnel"
            shrapnel_projectiles.append(shrapnel)

        return shrapnel_projectiles

    def explode(self, figures):
        """
        Causes the projectile to explode, affecting all figures within its explosion radius.

        Parameters:
        - figures (list): A list of Figure objects that can potentially be affected by the explosion.

        For each figure in the list:
        1. The method calculates the distance between the exploding projectile and the figure.
        2. If the figure is within the explosion radius and has a hit_points attribute that is not None,
           it will be "hit" by the explosion and will take damage.
        """

        for figure in figures:
            # Calculate the change in x and y between the projectile and the figure
            dx = figure.position[0] - self.position[0]
            dy = figure.position[1] - self.position[1]

            # Compute the Euclidean distance between the projectile and the figure
            distance = math.sqrt(dx ** 2 + dy ** 2)

            # Check if the figure is within the explosion radius and has hit points
            if distance < self.explosion_radius and figure.hit_points is not None:
                # Apply damage to the affected figure
                figure.get_hit(self.damage // 2)

    def behave(self):
        self.steer_at(self.locked_target)
        # Move the projectile in the direction it's currently facing
        self.apply_thrust("prograde", "normal")
        # If the projectile's locked target is destroyed, keep in mind for maybe later
        """if self.locked_target and self.locked_target.marked_for_death:
            # Reassign the projectile's locked target to the current player's locked target
            self.locked_target = current_locked_target"""

        if self.locked_target.marked_for_death:
            self.associated_weapon.locked_target = None


class Item(Figure):
    def __init__(self, *args, pick_up_distance, effect_function=None, chance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pick_up_distance = pick_up_distance
        self.effect_function = effect_function
        self.chance = chance
        self.used = False
        self.velocity = 1

    def item_in_range(self, target):
        distance = math.sqrt(
            (self.position[0] - target.position[0]) ** 2 + (self.position[1] - target.position[1]) ** 2)
        return distance < self.pick_up_distance

    def apply_effect(self, target):
        if self.effect_function:
            self.effect_function(target)

    def clone(self):
        """Creates a copy of the Item instance."""
        cloned_item = Item(
            name=self.name,
            position=self.position.copy(),
            sprite_loader=self.sprite_loader,  # Ensure this can be shallow-copied or has its own clone method
            pick_up_distance=self.pick_up_distance,
            effect_function=self.effect_function,
            chance=self.chance

        )
        cloned_item.pick_up_distance = self.pick_up_distance
        cloned_item.type_ = self.type_
        cloned_item.used = self.used
        return cloned_item

    def turn_item(self, speed):
        self.orientation += speed

    @staticmethod
    def heal_target(target):
        target.get_healed(50)
        print(f"Healed {target.name} for 50 HP!")

    @staticmethod
    def super_heal_target(target):
        target.get_healed(100)
        print(f"Healed {target.name} for 100 HP!")

    @staticmethod
    def shield_target(target):
        target.get_shield(50)
        print(f"Healed {target.name} for 50 shield!")

    @staticmethod
    def give_spreader(target):
        if spreader not in target.weapons:
            target.add_weapon(spreader)
            target.increase_ammo("shell_ammo", 10)
            spreader.owner = target
        else:
            target.increase_ammo("shell_ammo", 20)
        print(f"Gave {target.name} a New Blaster!")

    @staticmethod
    def give_chain_gun(target):
        if chain_gun not in target.weapons:
            target.add_weapon(chain_gun)
            target.increase_ammo("projectile_ammo", 50)
            chain_gun.owner = target
        else:
            target.increase_ammo("projectile_ammo", 100)
        print(f"Gave {target.name} a New Blaster!")

    @staticmethod
    def give_missile_launcher(target):
        if missile_launcher not in target.weapons:
            target.add_weapon(missile_launcher)
            target.increase_ammo("missile_ammo", 5)
            missile_launcher.owner = target
        else:
            target.increase_ammo("missile_ammo", 10)

    @staticmethod
    def give_coin(target):
        target.get_coin()

    @staticmethod
    def give_energy_ammo(target):
        target.increase_ammo("energy_ammo", 25)

    @staticmethod
    def give_projectile_ammo(target):
        target.increase_ammo("projectile_ammo", 80)

    @staticmethod
    def give_shell_ammo(target):
        target.increase_ammo("shell_ammo", 12)


class Cursor(Figure):
    def __init__(self, position, dimensions, sprite_path):
        # Load the cursor sprite
        self.sprite = pygame.image.load(sprite_path)
        # Resize the sprite to fit the cursor's dimensions
        self.sprite = pygame.transform.scale(self.sprite, dimensions)

        # Initialize the super class
        super().__init__("Cursor", position, dimensions=dimensions, no_clip=True)

    def update_position(self, new_position):
        self.position = new_position
        # Update any other attributes as needed

    # Override draw method to draw the sprite
    def draw_cursor(self, window):
        # Draw the cursor sprite centered around its position
        centered_x = self.position[0] - self.sprite.get_width() // 2
        centered_y = self.position[1] - self.sprite.get_height() // 2
        window.blit(self.sprite, (centered_x, centered_y))


class Weapon:
    """owner is only important for the player or if the owner is using finite ammo, so the weapon class has a reference
    to where to deduct the ammo"""

    def __init__(self, name, damage, projectile_velocity, cooldown, owner=None, sound_volume=0.2, shoot_sound=None,
                 projectile_color=None, projectile_dimensions=None, sprite_loader=None,
                 max_reach=None, max_pierce=None, spread=0, projectiles_count=1,
                 heat_increase_per_shot=5, heat_decrease_per_second=2, max_heat=100,
                 available_weapon_upgrades=None, ammo_type=None, unlimited_ammo=True,
                 muzzle_flash=None, animation=None):
        self.name = name
        self.damage = damage
        self.projectile_velocity = projectile_velocity
        self.cooldown = cooldown
        self.owner = owner
        self.sound_volume = sound_volume
        if shoot_sound:
            self.shoot_sound = pygame.mixer.Sound(shoot_sound)
            self.shoot_sound.set_volume(sound_volume)
        else:
            self.shoot_sound = None

        self.ammo_type = ammo_type
        self.unlimited_ammo = unlimited_ammo

        self.muzzle_flash = muzzle_flash
        self.animation = animation
        self.last_shot_time = 0
        self.projectile_color = projectile_color
        self.projectile_dimensions = projectile_dimensions
        self.sprite_loader = sprite_loader
        self.max_reach = max_reach
        self.max_pierce = max_pierce
        self.spread = spread  # in degrees
        self.projectiles_count = projectiles_count
        self.heat = 0  # starts at 0
        self.heat_increase_per_shot = heat_increase_per_shot
        self.heat_decrease_per_second = heat_decrease_per_second
        self.max_heat = max_heat
        self.is_jammed = False
        self.available_weapon_upgrades = available_weapon_upgrades
        self.type_ = "standard"

    def decrease_ammo(self):
        current_ammo = self.owner.ammo[self.ammo_type].current_ammo - 1
        # Ensure the ammo doesn't go negative
        current_ammo = max(0, current_ammo)
        self.owner.ammo[self.ammo_type] = self.owner.ammo[self.ammo_type]._replace(current_ammo=current_ammo)

    def purchase_weapon_upgrade(self, upgrade):
        print("Attempting to purchase upgrade for weapon.")
        print(f"owner associated with this weapon: {self.owner}")
        if self.owner:
            print(f"owner has {self.owner.coins} coins.")
            if self.owner.coins >= upgrade.cost:
                self.owner.coins -= upgrade.cost
                print(f"Purchasing upgrade: {upgrade.name} for {upgrade.cost} coins.")

                upgrade.apply_upgrade(self)
                print(f"upgrade {upgrade.name} cost {upgrade.cost}")
            else:
                print(
                    f"Not enough coins!{self.owner.coins} ")  # This can be replaced with a more advanced feedback system.

    def can_shoot(self):
        # Calculate the heat decrease since the last shot
        time_since_last_shot = time.time() - self.last_shot_time
        potential_cooling = self.heat_decrease_per_second * time_since_last_shot

        # Predict the heat after the potential cooling
        predicted_heat = self.heat - potential_cooling

        # If the weapon is jammed, it can't shoot even if it's cooled down a bit.
        # It must cool down to 0 to shoot again.
        if self.is_jammed and predicted_heat > 0:
            return False

        # If the heat is fully cooled down, unjam the weapon
        if predicted_heat <= 0:
            self.is_jammed = False

        # If ammo is depleted you cannot shoot
        if not self.unlimited_ammo:
            if self.owner.ammo[self.ammo_type].current_ammo <= 0:
                print("ammo empty")
                return False

        if self.owner.weapon_switch_delay:
            if time.time() - self.owner.last_weapon_switch_time < self.owner.weapon_switch_delay:
                return False

        # Can shoot if not overheated after the potential cooling, not jammed,
        # and enough time has passed since the last shot
        return predicted_heat < self.max_heat and time_since_last_shot >= self.cooldown

    def weapon_shoot(self, orientation, position, type_):
        if self.can_shoot():
            if not self.unlimited_ammo:
                # TODO Decrease the ammo count
                self.decrease_ammo()
            self.heat += self.heat_increase_per_shot * self.projectiles_count  # Increase heat on shooting
            self.last_shot_time = time.time()  # Update the last shot time
            origin_position = position.copy()
            if self.shoot_sound:
                self.shoot_sound.play()

            projectiles = []
            for _ in range(self.projectiles_count):
                # Randomly deviate the orientation for each projectile within the spread range
                deviation = (-self.spread / 2) + (self.spread * random.random())
                new_orientation = orientation + deviation

                projectile = Projectile(name=self.name + "projectile", damage=self.damage, orientation=new_orientation,
                                        velocity=self.projectile_velocity,
                                        position=origin_position, sprite_loader=self.sprite_loader,
                                        max_reach=self.max_reach,
                                        max_pierce=self.max_pierce, animation=self.animation)

                if self.sprite_loader is None and self.projectile_dimensions:
                    projectile.override_dimension(self.projectile_dimensions)
                    if self.projectile_color:
                        projectile.override_color(self.projectile_color)

                projectile.type_ = type_
                projectiles.append(projectile)

            # If heat goes above max_heat after shooting, jam the weapon
            if self.heat >= self.max_heat:
                self.heat = self.max_heat
                self.is_jammed = True

            return projectiles

    def cool_down(self):
        """Decreases the weapon's heat over time."""
        time_since_last_shot = time.time() - self.last_shot_time
        self.heat -= self.heat_decrease_per_second * time_since_last_shot
        self.heat = max(0, self.heat)  # Ensure it doesn't go negative

    def clone(self):
        return Weapon(
            name=self.name,
            damage=self.damage,
            owner=self.owner,
            projectile_velocity=self.projectile_velocity,
            cooldown=self.cooldown,
            sprite_loader=self.sprite_loader,  # Assuming this is okay to share the reference
            max_reach=self.max_reach,
            max_pierce=self.max_pierce,
            spread=self.spread,  # Added this
            projectiles_count=self.projectiles_count,  # Added this
            shoot_sound=self.shoot_sound,
            sound_volume=self.sound_volume,
            heat_increase_per_shot=self.heat_increase_per_shot,
            heat_decrease_per_second=self.heat_decrease_per_second,
            max_heat=self.max_heat,
            ammo_type=self.ammo_type,
            unlimited_ammo=self.unlimited_ammo,
            animation=self.animation,
            available_weapon_upgrades=self.available_weapon_upgrades

        )


class HomingWeapon(Weapon):
    def __init__(self, *args, locked_target=None, life_time=5, type_="homing", turn_speed=5, explosion_radius=None,
                 shrapnel_count=None, shrapnel_angle=0, **kwargs):
        # Call the initialization method of the parent class, Figure
        super().__init__(*args, **kwargs)
        self.locked_target = locked_target
        self.type_ = type_
        self.turn_speed = turn_speed
        self.explosion_radius = explosion_radius
        self.shrapnel_count = shrapnel_count
        self.shrapnel_angle = shrapnel_angle
        self.life_time = life_time

    def set_target(self, target):
        self.locked_target = target

    def can_shoot(self):
        if not self.locked_target:
            return False
        return super().can_shoot()

    def weapon_shoot(self, orientation, position, type_):
        if self.can_shoot():
            if not self.unlimited_ammo:
                self.decrease_ammo()
            self.heat += self.heat_increase_per_shot * self.projectiles_count // 2  # Increase heat on shooting
            self.last_shot_time = time.time()  # Update the last shot time
            origin_position = position.copy()
            if self.shoot_sound:
                self.shoot_sound.play()

            projectiles = []
            for _ in range(self.projectiles_count):
                # Randomly deviate the orientation for each projectile within the spread range
                deviation = (-self.spread / 2) + (self.spread * random.random())
                new_orientation = orientation + deviation
                projectile = HomingProjectile(name=self.name + "_projectile", damage=self.damage,
                                              orientation=new_orientation, velocity=self.projectile_velocity,
                                              position=origin_position, sprite_loader=self.sprite_loader,
                                              max_reach=self.max_reach, max_pierce=self.max_pierce,
                                              animation=self.animation, locked_target=self.locked_target,
                                              turn_speed=self.turn_speed, associated_weapon=self,
                                              explosion_radius=self.explosion_radius,
                                              shrapnel_count=self.shrapnel_count,
                                              shrapnel_angle=self.shrapnel_angle, life_time=self.life_time
                                              )

                if self.sprite_loader is None and self.projectile_dimensions:
                    projectile.override_dimension(self.projectile_dimensions)
                    if self.projectile_color:
                        projectile.override_color(self.projectile_color)

                projectile.type_ = type_
                projectiles.append(projectile)

            # If heat goes above max_heat after shooting, jam the weapon
            if self.heat >= self.max_heat:
                self.heat = self.max_heat
                self.is_jammed = True

            return projectiles

    def clone(self):
        return HomingWeapon(
            name=self.name,
            damage=self.damage,
            owner=self.owner,
            projectile_velocity=self.projectile_velocity,
            cooldown=self.cooldown,
            sprite_loader=self.sprite_loader,  # Assuming this is okay to share the reference
            max_reach=self.max_reach,
            max_pierce=self.max_pierce,
            spread=self.spread,  # Added this
            projectiles_count=self.projectiles_count,  # Added this
            shoot_sound=self.shoot_sound,
            sound_volume=self.sound_volume,
            heat_increase_per_shot=self.heat_increase_per_shot,
            heat_decrease_per_second=self.heat_decrease_per_second,
            max_heat=self.max_heat,
            ammo_type=self.ammo_type,
            unlimited_ammo=self.unlimited_ammo,
            animation=self.animation,
            locked_target=self.locked_target,
            life_time=self.life_time,
            type_=self.type_,
            turn_speed=self.turn_speed,
            explosion_radius=self.explosion_radius,
            shrapnel_count=self.shrapnel_count,
            shrapnel_angle=self.shrapnel_angle

        )


class Upgrade:  # TODO add more upgrades and create a way to make "use up" upgrades after a certain amount of purchases
    def __init__(self, name, description, cost, upgrade_function, max_uses=3, uses=0, type_=None):
        self.name = name
        self.description = description
        self.cost = cost
        self.upgrade_function = upgrade_function
        self.uses = uses
        self.max_uses = max_uses
        self.used_up = False
        self.type_ = type_

    def apply_upgrade(self, target):
        print(f"Applying upgrade of {self.name} upgrade.")

        if self.upgrade_function:
            self.upgrade_function(target)
        #self.used = True

    # player upgrades
    @staticmethod
    def upgrade_HP_overcharge(target):
        print(f"Applying upgrade_HP_overcharge to target.")
        target.hit_point_overcharge *= 1.1
        print(f"target.hit_point_overcharge: {target.hit_point_overcharge}")

    @staticmethod
    def upgrade_shield_overcharge(target):
        print(f"Applying upgrade_shield_overcharge to target.")
        target.shield_overcharge *= 1.1
        print(f"target.hit_point_overcharge: {target.hit_point_overcharge}")

    @staticmethod
    def upgrade_shield_delay(target):
        print(f"Applying upgrade_shield_delay to target.")

        target.shield_recharge_delay *= 0.8

    @staticmethod
    def upgrade_shield_recharge(target):
        print(f"Applying upgrade_shield_recharge to target.")

        target.shield_recharge_rate *= 1.3

    # weapon upgrade
    @staticmethod
    def upgrade_damage(target):
        print(f"Applying upgrade_damage to target.")

        target.damage *= 1.1

    @staticmethod
    def upgrade_fire_rate(target):
        print(f"Applying upgrade_fire_rate to target.")

        target.cooldown *= 0.9

    @staticmethod
    def upgrade_add_projectile(target):
        target.projectiles_count += 1
        target.spread += 1
        target.heat_increase_per_shot *= 1.5

    def clone(self):
        """Creates a copy of the Upgrade instance."""
        cloned_upgrade = Upgrade(
            name=self.name,
            description=self.description,
            cost=self.cost,
            upgrade_function=self.upgrade_function,
            uses=self.uses,
            max_uses=self.max_uses,
            type_=self.type_
        )
        return cloned_upgrade


class Ability:
    def __init__(self, name, owner, ability_function):
        self.name = name
        self.owner = owner
        self.ability_function = ability_function


"""instances are listed here"""

# ===============================
# Player Upgrades Definitions
# ===============================

hp_upgrade_overcharge = Upgrade("HP overcharge", "upgrade HP overcharge+10%.\nThis lets you keep more HP", 10,
                                upgrade_function=Upgrade.upgrade_HP_overcharge, type_="player_upgrade")
shield_upgrade_overcharge = Upgrade("Shield overcharge", "upgrade SP overcharge+10%.\nThis lets you keep more SP", 10,
                                    upgrade_function=Upgrade.upgrade_shield_overcharge, type_="player_upgrade")
shield_recharge_delay_upgrade = Upgrade("Shield Recharge Delay", "shorten the time until shield starts\nregenerating",
                                        15,
                                        upgrade_function=Upgrade.upgrade_shield_delay, type_="player_upgrade")
shield_recharge_rate_upgrade = Upgrade("Shield Recharge Rate", "The Shield recharges at a faster Rate", 20,
                                       upgrade_function=Upgrade.upgrade_shield_recharge, type_="player_upgrade")
# ===============================
# Weapon Upgrades Definitions
# ==============================

damage_upgrade = Upgrade("damage upgrade", "10% more damage!", 15,
                         upgrade_function=Upgrade.upgrade_damage, type_="weapon_upgrade")
fire_rate_upgrade = Upgrade("fire rate upgrade", "10% faster fire rate", 15,
                            upgrade_function=Upgrade.upgrade_fire_rate, type_="weapon_upgrade")
add_projectile_upgrade = Upgrade("add projectile", "adds an additional projectile\nthis will increase heat per shot",
                                 25,
                                 upgrade_function=Upgrade.upgrade_add_projectile, type_="weapon_upgrade")

# ===============================
# Player Model Definition
# ===============================

player = Player(name="player", position=[300, 300], hit_points=100, shield=0, shield_cap=150, shield_overcharge=100,
                hit_points_cap=200, hit_point_overcharge=120,
                sprite_loader=Sprite_sheet_loader_3d(player_model, 100, 0.8), shield_recharge_rate=10,
                turn_speed=5, max_velocity=10, acceleration=2, x_limit=500, y_limit=500, type_="player",
                sound_effects=player_sounds,
                coins=0,
                available_upgrades=[hp_upgrade_overcharge, shield_upgrade_overcharge, shield_recharge_rate_upgrade,
                                    shield_recharge_delay_upgrade], animation=[explosion_a]
                )
aim = Cursor([0, 0], [40, 40], aim_path)

# ===============================
# Obstacle Definitions
# ===============================
obstacle_a = Obstacle(name="obstacle", position=[500, 500], dimensions=[80, 80], type_="obstacle", color=(255, 30, 120))

# ===============================
# NPC Models Definitions
# ===============================

scout_enemy = NPC(name="scout", position=[50, 50], hit_points=100, reward=50, radius=500,
                  sprite_loader=Sprite_sheet_loader_3d(scout_model, 100, 0.5),
                  turn_speed=5, velocity=5, type_="enemy", sound_effects=None, animation=[explosion_a, portal_opening],
                  weapon_switch_delay=1)

brawler_enemy = NPC(name="brawler", position=[50, 50], hit_points=150, reward=100, radius=400,
                    sprite_loader=Sprite_sheet_loader_3d(brawler_model, 100, 0.5),
                    turn_speed=5, velocity=3, type_="enemy", sound_effects=None,
                    animation=[explosion_a, portal_opening])

torus_enemy = NPC(name="Torus", type_="enemy", position=[50, 50], hit_points=200, reward=300, radius=500, velocity=3,
                  turn_speed=5, sprite_loader=Sprite_sheet_loader_3d(torus_enemy_sprite, 100, 0.5), sound_effects=None,
                  animation=[explosion_a])

mogus_enemy = BossNPC(name="Mogus", type_="boss_enemy", position=[50, 50], hit_points=900, reward=300, radius=800,
                      velocity=4, turn_speed=7, sprite_loader=Sprite_sheet_loader_3d(mogus_spreader_model, 100),
                      sound_effects=None,
                      animation=[explosion_a, portal_opening], weapon_switch_delay=0.5)

shredder_enemy = BossNPC(name="Shredder", type_="boss_enemy", position=[50, 50], hit_points=1000, reward=300,
                         radius=500,
                         velocity=4,
                         turn_speed=10, sprite_loader=Sprite_sheet_loader_3d(shredder_model, 100), sound_effects=None,
                         animation=[explosion_a, portal_opening], weapon_switch_delay=0.5)

missile_mogus = BossNPC(name="missile_mogus", type_="boss_enemy", position=[50, 50], hit_points=800, reward=300,
                        radius=500,
                        velocity=3,
                        turn_speed=5, sprite_loader=Sprite_sheet_loader_3d(missile_mogus_model, 100, 1.3),
                        sound_effects=None,
                        animation=[explosion_a, portal_opening], weapon_switch_delay=0.5)
# ===============================
# Goodies (Items) Definitions
# ===============================

healing_item_template = Item(name="Health_pick up", type_="pick_up", position=[100, 100],
                             sprite_loader=Sprite_sheet_loader_3d(health_pick_up_path, 100, scale=0.4),
                             pick_up_distance=50,
                             effect_function=Item.heal_target,
                             turn_speed=5,
                             chance=3)

omega_health_template = Item(name="Omega Health_pick up", type_="pick_up", position=[100, 100],
                             sprite_loader=Sprite_sheet_loader_3d(omega_health_model, 100, 0.4),
                             pick_up_distance=50,
                             effect_function=Item.super_heal_target,
                             turn_speed=5,
                             chance=5)

coin_item_template = Item(name="Coin_pick up", type_="pick_up", position=[100, 100],
                          sprite_loader=Sprite_sheet_loader_3d(coin_model, 99, scale=0.4),
                          pick_up_distance=50,
                          effect_function=Item.give_coin,
                          turn_speed=5,
                          chance=1)

shield_item_template = Item(name="Shield_pick up", type_="pick_up", position=[100, 100],
                            sprite_loader=Sprite_sheet_loader_3d(shield_model, 100, scale=0.4),
                            pick_up_distance=50,
                            effect_function=Item.shield_target,
                            turn_speed=5,
                            chance=3)

energy_ammo_item_template = Item(name="Energy_Ammo_pick_up", type_="pick_up", position=[100, 100],
                                 sprite_loader=Sprite_sheet_loader_3d(energy_ammo_model, 100),
                                 pick_up_distance=50,
                                 effect_function=Item.give_energy_ammo,
                                 turn_speed=5,
                                 chance=2)

shell_ammo_item_template = Item(name="Shell Ammo_pick up", type_="pick_up", position=[100, 100],
                                sprite_loader=Sprite_sheet_loader_3d(shell_ammo_model, 100),
                                pick_up_distance=50,
                                effect_function=Item.give_shell_ammo,
                                turn_speed=5,
                                chance=1)

projectile_ammo_item_template = Item(name="Projectile Ammo_pick up", type_="pick_up", position=[100, 100],
                                     sprite_loader=Sprite_sheet_loader_3d(projectile_ammo_sheet, 100),
                                     pick_up_distance=50,
                                     effect_function=Item.give_projectile_ammo,
                                     turn_speed=5,
                                     chance=1)

spreader_pick_up = Item(name="Spreader", type_="gun_pick_up", position=[100, 100],
                        sprite_loader=Sprite_sheet_loader_3d(spreader_item_sheet, 100),
                        pick_up_distance=50,
                        effect_function=Item.give_spreader,
                        turn_speed=5,
                        chance=1)

chain_gun_pick_up = Item(name="Chain Gun", type_="gun_pick_up", position=[100, 100],
                         sprite_loader=Sprite_sheet_loader_3d(chain_gun_item_sheet, 100, scale=0.5),
                         pick_up_distance=50,
                         effect_function=Item.give_chain_gun,
                         turn_speed=5,
                         chance=1)

missile_launcher_pick_up = Item(name="Missile Launcher", type_="gun_pick_up", position=[100, 100],
                                sprite_loader=Sprite_sheet_loader_3d(missile_launcher_model, 100, scale=0.5),
                                pick_up_distance=50,
                                effect_function=Item.give_missile_launcher,
                                turn_speed=5,
                                chance=1)

scout_enemy.add_potential_drop(energy_ammo_item_template, coin_item_template, healing_item_template)
brawler_enemy.add_potential_drop(shell_ammo_item_template, coin_item_template, omega_health_template,
                                 shield_item_template)
torus_enemy.add_potential_drop(projectile_ammo_item_template, coin_item_template, omega_health_template,
                               shield_item_template)
mogus_enemy.add_potential_drop(spreader_pick_up)
shredder_enemy.add_potential_drop(chain_gun_pick_up)
missile_mogus.add_potential_drop(missile_launcher_pick_up)
# ===============================
# Weapons Definitions
# ===============================

basic_blaster = Weapon("blaster",
                       25,
                       20,
                       cooldown=0.15,
                       owner=player,
                       sprite_loader=None,
                       max_reach=1000,
                       max_pierce=None,
                       ammo_type="energy_ammo",
                       unlimited_ammo=False,
                       shoot_sound=gun_sounds["blaster_sound"],
                       sound_volume=0.2,
                       projectile_dimensions=[7, 7],
                       projectile_color=(252, 186, 3),
                       projectiles_count=1,
                       muzzle_flash=muzzle_flash,
                       available_weapon_upgrades=[damage_upgrade.clone(), fire_rate_upgrade.clone(),
                                                  add_projectile_upgrade.clone()],
                       animation=[projectile_explosion])

missile_launcher = HomingWeapon(name="missile launcher", damage=80, projectile_velocity=20, cooldown=1, owner=player,
                                sprite_loader=Sprite_sheet_loader_3d(missile_model, 100, 0.4),
                                max_reach=1000,
                                max_pierce=None,
                                ammo_type="missile_ammo",
                                unlimited_ammo=False,
                                shoot_sound=gun_sounds["blaster_sound"],
                                turn_speed=5,
                                projectile_dimensions=[7, 7],
                                projectile_color=(252, 186, 3),
                                projectiles_count=1,
                                muzzle_flash=muzzle_flash,
                                explosion_radius=125,
                                shrapnel_angle=100,
                                shrapnel_count=100,
                                available_weapon_upgrades=[damage_upgrade.clone(), fire_rate_upgrade.clone(),
                                                           add_projectile_upgrade.clone()],
                                animation=[projectile_explosion])

spreader = Weapon("spreader",
                  damage=20,
                  owner=player,
                  projectile_velocity=15,
                  projectile_dimensions=[10, 10],
                  projectile_color=(255, 0, 255),
                  cooldown=0.5,
                  unlimited_ammo=False,
                  spread=10,
                  projectiles_count=8,
                  max_reach=1000,
                  sprite_loader=None,
                  muzzle_flash=muzzle_flash,
                  animation=[projectile_explosion],
                  available_weapon_upgrades=[damage_upgrade.clone(), fire_rate_upgrade.clone(),
                                             add_projectile_upgrade.clone()],
                  shoot_sound=gun_sounds["spreader_sound"],
                  ammo_type="shell_ammo")

chain_gun = Weapon("chain_gun",
                   damage=25,
                   projectile_velocity=25,
                   cooldown=0.05,
                   owner=player,
                   sprite_loader=None,
                   projectile_color=(100, 248, 120),
                   projectile_dimensions=[5, 5],
                   spread=5,
                   unlimited_ammo=False,
                   max_reach=700,
                   shoot_sound=gun_sounds["raaraa_sound"],
                   sound_volume=0.2,
                   animation=[projectile_explosion],
                   muzzle_flash=muzzle_flash,
                   max_heat=250,
                   ammo_type="projectile_ammo")

burst_gun = Weapon("burst gun",
                   50,
                   40,
                   0,
                   sprite_loader=None,
                   projectile_color=(150, 248, 120),
                   projectile_dimensions=[5, 5],
                   max_reach=1000, max_pierce=2,
                   heat_increase_per_shot=26,
                   max_heat=100,
                   shoot_sound=gun_sounds["rail_gun_sound"],
                   sound_volume=1.2)

debug_gun = Weapon("debug_gun",
                   30,
                   25,
                   0.01,
                   sprite_loader=None,
                   projectile_color=(153, 151, 103),
                   projectile_dimensions=[5, 5],
                   spread=5,
                   max_reach=1000,
                   shoot_sound=gun_sounds["raaraa_sound"],
                   sound_volume=0.2,
                   heat_increase_per_shot=0,
                   muzzle_flash=muzzle_flash,
                   animation=None,
                   owner=player)

enemy_blaster = Weapon("enemy blaster", 13, 15, 0.5, sprite_loader=None,
                       projectile_color=(255, 0, 0), projectile_dimensions=[5, 5], spread=15,
                       max_reach=600, shoot_sound=gun_sounds["enemy_blaster_sound"], sound_volume=0.1,
                       heat_increase_per_shot=26,
                       max_heat=100,
                       animation=[projectile_explosion])

enemy_blaster_b = Weapon("enemy blaster", 10, 15, 0.5, sprite_loader=None,
                         projectile_color=(255, 0, 0), projectile_dimensions=[5, 5], spread=10,
                         max_reach=600, shoot_sound=gun_sounds["enemy_blaster_sound"], sound_volume=0.3)

enemy_chain_gun = Weapon("enemy blaster wacko mode", 5, 15, 0.01, sprite_loader=None,
                         projectile_color=(255, 0, 0), projectile_dimensions=[5, 5], spread=10,
                         max_reach=600, shoot_sound=gun_sounds["raaraa_sound"], sound_volume=0.3,
                         heat_decrease_per_second=0.5,
                         animation=[projectile_explosion])

shredder_chain_gun = Weapon("enemy shredder chaingun", 10, 38, 0.03, sprite_loader=None,
                            projectile_color=(255, 0, 0), projectile_dimensions=[5, 5], spread=10,
                            max_reach=600, shoot_sound=gun_sounds["raaraa_sound"], sound_volume=0.3,
                            heat_decrease_per_second=1,
                            max_heat=250, animation=[projectile_explosion])

enemy_spreader = Weapon("enemy spreader", damage=20, projectile_velocity=15, cooldown=0.5, spread=10,
                        projectile_dimensions=[10, 10], projectile_color=(136, 255, 122),
                        projectiles_count=5, max_reach=400, animation=[projectile_explosion],
                        sprite_loader=None, shoot_sound=gun_sounds["enemy_spreader_sound"], heat_increase_per_shot=35,
                        max_heat=100)

enemy_boss_spreader = Weapon("enemy spreader", damage=20, projectile_velocity=20, cooldown=0.2, spread=10,
                             projectile_dimensions=[10, 10], projectile_color=(136, 255, 122),
                             projectiles_count=5, max_reach=400, animation=[projectile_explosion],
                             sprite_loader=None, shoot_sound=gun_sounds["enemy_spreader_sound"],
                             heat_increase_per_shot=15,
                             max_heat=100)

enemy_rail_gun = Weapon("enemy rail gun", damage=100, projectile_velocity=30, cooldown=0.5, spread=10,
                        projectile_dimensions=[25, 25], projectile_color=(0, 255, 122),
                        projectiles_count=1, max_reach=800, max_heat=100, heat_increase_per_shot=101,
                        sprite_loader=None, shoot_sound=gun_sounds["rail_gun_sound"])

enemy_missile_launcher = HomingWeapon("homing_enemy_missile", damage=80, projectile_velocity=10, cooldown=3,
                                      sprite_loader=Sprite_sheet_loader_3d(missile_model, 100, 0.4),
                                      max_reach=1000,
                                      max_pierce=None,
                                      ammo_type="energy_ammo",
                                      unlimited_ammo=True,
                                      shoot_sound=gun_sounds["blaster_sound"],
                                      turn_speed=2,
                                      life_time=2,
                                      heat_increase_per_shot=20,
                                      max_heat=19,
                                      heat_decrease_per_second=5,
                                      projectile_dimensions=[7, 7],
                                      projectile_color=(252, 186, 3),
                                      projectiles_count=1,
                                      muzzle_flash=muzzle_flash,
                                      explosion_radius=125,
                                      shrapnel_angle=45,
                                      shrapnel_count=10,
                                      locked_target=player,
                                      available_weapon_upgrades=[damage_upgrade.clone(), fire_rate_upgrade.clone(),
                                                                 add_projectile_upgrade.clone()],
                                      animation=[projectile_explosion])

# ===============================
# adding stuff to figures
# ===============================

player.add_weapon(basic_blaster, debug_gun)
#player.coins = 1000

scout_enemy.add_weapon(enemy_blaster)

brawler_enemy.add_weapon(enemy_spreader)
torus_enemy.add_weapon(enemy_chain_gun)
mogus_enemy.add_weapon(enemy_chain_gun, enemy_boss_spreader)
shredder_enemy.add_weapon(shredder_chain_gun)
missile_mogus.add_weapon(enemy_missile_launcher)

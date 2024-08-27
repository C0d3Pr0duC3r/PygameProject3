from game_class import *
import cProfile

background_picture_path = "graphics\\backgrounds\\back_ground.jpg"
font_path = 'fonts\\Pixeltype.ttf'

info = pygame.display.Info()
screen_dimensions = [info.current_w, info.current_h]
variable = 0
variable_2 = 0
resource_logging = False

game = Game("ShootyMcPewPew", [screen_dimensions[0]-variable, screen_dimensions[1]-variable_2], cursor=aim,
            background_image_path=background_picture_path, scale_background=True, player_template=player,
            enemies=[scout_enemy, brawler_enemy, torus_enemy], bosses=[mogus_enemy, shredder_enemy, missile_mogus],
            game_font=font_path, player_unkillable=True, debug_mode=False, fps=60)

game.map_click_functions()

game.add_item_template(energy_ammo_item_template, healing_item_template)
print(game.player.shield_recharge_rate,
      game.player_template.shield_recharge_rate)
# game.enemies_active = False
# game.state = "playing"

if resource_logging:
    cProfile.run('game.run()')
else:
    game.run()



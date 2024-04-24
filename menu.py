import pygame_menu
import enum


class GameState(enum.Enum):
    START_SCREEN = 1
    MAIN_MENU = 2
    GAME = 3
    OPTIONS = 4


class Menu:
    def __init__(self, game_instance, title, width=600, height=400):
        self.game = game_instance
        self.menu = pygame_menu.Menu(title, width, height, theme=pygame_menu.themes.THEME_BLUE)


class StartScreenMenu(Menu):
    def __init__(self, game_instance):
        self.input_value = ''
        super().__init__(game_instance, "Enter your name")

        self.menu.add.text_input('Your Name: ', onchange=self.input_text_handler, default='')
        self.menu.add.button('confirm', self.confirm)

    def input_text_handler(self, value):
        print(f"The user entered: {value}")
        self.input_value = value  # Store the current input value
        return len(value) <= 10  # Ensure the input is 10 characters or less

    def confirm(self):
        if 0 < len(self.input_value) <= 10:  # Check if the input value is valid
            self.game.state_changer(GameState.MAIN_MENU)
        else:
            # Create a pop-up message or a label indicating the error
            error_message = "Name is either too long or invalid. Please enter a name with 10 characters or less."
            self.menu.add.label(error_message, max_char=-1, font_color=(255, 0, 0))

            # Optionally, add a button to close the message and reset the input
            self.menu.add.button('OK', self.close_message)

    def close_message(self):
        # Clear the menu or remove the error message and reset
        self.menu.clear()
        self.create_menu_items()  # You need to implement this method to recreate the menu items

    def create_menu_items(self):
        self.menu.add.text_input('Your Name: ', onchange=self.input_text_handler, default='')
        self.menu.add.button('confirm', self.confirm)


class MainMenu(Menu):
    def __init__(self, game_instance):
        super().__init__(game_instance, "Main Menu")  # Call the initializer of the base class

        # Add specific buttons for the main menu
        self.menu.add.button('Start Game', self.start_game)
        self.menu.add.button('Options', self.show_options)
        self.menu.add.button('Quit', pygame_menu.events.EXIT)

    def start_game(self):
        self.game.state_changer(GameState.GAME)

    def show_options(self):
        self.game.state_changer(GameState.OPTIONS)


class OptionsMenu(Menu):
    def __init__(self, game_instance):
        super().__init__(game_instance, "Options")

        # Define the onchange function for the slider
        def slider_changed(value, slider_id):
            print(f"Slider '{slider_id}' value changed to: {value}")
            # Handle the slider value change here



        self.menu.add.button('show debug data', lambda: self.debug_mode_toggle())
        self.menu.add.button('some option 2', lambda: print("option 2 clicked"))
        self.menu.add.range_slider('Volume', onchange=slider_changed, default=50, range_values=(0, 100), increment=1, slider_id='volume_slider')
        self.menu.add.button('Back', lambda: self.game.state_changer(GameState.MAIN_MENU))

    def debug_mode_toggle(self):
        if not self.game.debug_mode:
            self.game.debug_mode = True
        else:
            self.game.debug_mode = False
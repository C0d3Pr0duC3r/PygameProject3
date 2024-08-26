import sys

import re

import pygame

from menu_components import *
import enum
import json
import math
import os


def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


class Commands(enum.Enum):
    ADD_BUTTON = 1
    REMOVE_SELECTED_COMPONENT = 2
    MOVE = 3
    RESHAPE = 4
    CLOSE = 5
    ADD_TEXT_PROMPT = 6

    def __str__(self):
        # Return a user-friendly string for each command
        return {
            Commands.ADD_BUTTON: "Add Button",
            Commands.REMOVE_SELECTED_COMPONENT: "Remove selected Component",
            Commands.MOVE: "Move Component",
            Commands.RESHAPE: "Reshape Component",
            Commands.CLOSE: "Close Menu",
            Commands.ADD_TEXT_PROMPT: "Add Text Prompt"
        }.get(self, "Unknown Command")


class EditorStates(enum.Enum):
    NORMAL = 1
    MOVE_COMPONENT = 2
    RESHAPE_COMPONENT = 3
    START_UP = 4
    LITERAL_POSITIONING = 5
    LITERAL_RESHAPING = 6


pygame.init()

# Set up the display
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Menu Editor')


class DropdownMenu:
    def __init__(self, items, pos):
        self.items = items  # List of menu items
        self.position = pos
        self.width = 350
        self.height = 20 * len(items)  # Adjust height based on number of items
        self.active = True
        self.font = pygame.font.SysFont(None, 30)

    def draw(self, surface):
        # Draw the menu background
        pygame.draw.rect(surface, (60, 60, 60), [self.position[0], self.position[1], self.width, self.height])
        # Draw each menu item
        for index, item in enumerate(self.items):
            text_surf = self.font.render(str(item), True, (255, 255, 255))
            surface.blit(text_surf, (self.position[0] + 10, self.position[1] + index * 20))

    def select(self, pos):
        # Determine which menu item was selected
        """This checks if the x - coordinate of the click(pos[0]) is within the horizontal boundaries
        of the dropdown menu. The menu starts at self.position[0] and extends horizontally
         to self.position[0] + self.width"""
        if self.position[0] <= pos[0] <= self.position[0] + self.width:
            index = (pos[1] - self.position[1]) // 20
            if 0 <= index < len(self.items):
                return self.items[index]
        return None


class MenuEditor:
    def __init__(self, title, window_size):
        pygame.display.set_caption(title)
        self.menu_dimensions = None
        self.menu_background = None
        self.file_name = None
        self.last_printed_state = None
        self.window_size = window_size
        self.screen = pygame.display.set_mode(window_size)
        self.components = []  # Store all UI components here
        self.load_buttons = []
        self.temp_comps = []
        self.selected_component = None  # Reference to the currently selected component
        self.dropdown = None  # To store the active DropdownMenu instance
        self.running = True
        self.state = EditorStates.START_UP
        self.font = pygame.font.SysFont('Arial', 16)  # Font for displaying coordinates

        self.fixed_components = [
            Button(name="SAVE_FILE", position=[0, 0], dimensions=[60, 40], text="save", alignment="right", click_function=self.save_menu_to_file),
            Button(name="OPEN_FILE", position=[0, 0], dimensions=[60, 40], text="open", alignment="middle", click_function=self.create_buttons_for_loadable_files),
            Button(name="NEW_FILE", position=[0, 0], dimensions=[60, 40], text="new", alignment="left", click_function=self.new_file)

        ]

    def state_changer(self, new_state):
        self.state = new_state

    def cursor_is_on_thing(self, pos):
        for comp in self.components:
            return comp.rect.collidepoint(pos)

    def add_component(self, component):
        self.components.append(component)

    def remove_component(self):
        # Safely remove the selected component
        if self.selected_component in self.components:
            self.components.remove(self.selected_component)
            self.selected_component = None  # Clear the selection
        else:
            # selected component is somehow not in the components list
            print("Selected component not found in the list!")

    def add_fixed_component(self, *components):
        for comp in components:
            self.fixed_components.append(comp)

    def add_load_button(self, button):
        self.load_buttons.append(button)

    def clear_load_buttons(self):
        self.load_buttons = []

    def add_temp_comp(self, *components):
        # this method will add temporary "fixed" components and will make sure, not to spam those components
        # this is necessary due to the method getting called every event that takes place i.e. a mouse movement
        for comp in components:
            if not any(existing_comp.name == comp.name for existing_comp in self.temp_comps):
                self.temp_comps.append(comp)

    def clear_temp_comp(self):
        self.temp_comps = []

    def remove_fixed_component(self, component_to_remove):
        # Safely remove the selected component
        self.fixed_components.remove(component_to_remove)

    def component_mover(self, mouse_pos):
        if self.selected_component:
            # Update the component's position to follow the mouse cursor
            self.selected_component.rect.x = mouse_pos[0]
            self.selected_component.rect.y = mouse_pos[1]

    def align_fixed_buttons(self, button, margin):

        if button.alignment:
            """Calculate the button's position based on alignment in the bottom corner with margin."""
            if button.alignment == "left":
                x = margin  # Positioned on the left with a margin
            elif button.alignment == "right":
                x = self.window_size[0] - button.rect.width - margin  # Positioned on the right with a margin
            elif button.alignment == "middle":
                x = self.window_size[0]/2 - button.rect.width / 2
            else:
                return

            # Y position is the same for both alignments
            y = self.window_size[1] - button.rect.height - margin  # Positioned at the bottom with a margin
            button.rect.x = x
            button.rect.y = y

    def reshape_component(self, mouse_pos):
        if self.state != EditorStates.LITERAL_RESHAPING:
            if self.selected_component:
                # calculates the distance between the cursor and the top right corner of the selected component,
                # so it can use those values to dynamically reshape/resize the component
                x1 = self.selected_component.rect.x
                x2 = mouse_pos[0]
                y1 = self.selected_component.rect.y
                y2 = mouse_pos[1]
                x_diff = x2 - x1
                y_diff = y2 - y1
                self.selected_component.rect.width = max(10, x_diff)
                self.selected_component.rect.height = max(10, y_diff)
        else:
            self.selected_component.rect.width = max(10, mouse_pos[0])
            self.selected_component.rect.height = max(10, mouse_pos[1])

    def display_coordinates(self, mouse_pos):
        # Display the current mouse coordinates near the cursor
        coords_text = f'X: {mouse_pos[0]}, Y: {mouse_pos[1]}'
        text_surf = self.font.render(coords_text, True, (255, 255, 255))
        # Offset the text slightly from the cursor for visibility
        self.screen.blit(text_surf, (mouse_pos[0] - 20, mouse_pos[1] - 20))

    def display_file_name(self):
        display_font = pygame.font.SysFont('Arial', 36)  # Font for displaying coordinates
        font_surface = display_font.render(self.file_name, True, (255, 255, 255))
        self.screen.blit(font_surface, (self.window_size[0] / 2 - font_surface.get_width(), 0))

    def display_component_dimensions(self, mouse_pos):
        # Display the current mouse coordinates near the cursor
        coords_text = f'height: {self.selected_component.rect.height}, width: {self.selected_component.rect.width}'
        text_surf = self.font.render(coords_text, True, (255, 255, 255))
        # Offset the text slightly from the cursor for visibility
        self.screen.blit(text_surf, (mouse_pos[0] + 20, mouse_pos[1] + 20))

    def display_info(self, mouse_pos):
        if self.state == EditorStates.MOVE_COMPONENT:
            self.display_coordinates(mouse_pos)
        elif self.state == EditorStates.RESHAPE_COMPONENT:
            self.display_component_dimensions(mouse_pos)

    def handle_editor_dropdown(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if event.button == 3:  # Right-click
                component_clicked = False  # Initialize flag for component checking

                # Check for clicks on components to display context-specific dropdowns
                for component in self.components:
                    if component.rect.collidepoint(mouse_pos):
                        print("Component-specific dropdown menu")
                        self.dropdown = DropdownMenu([Commands.RESHAPE, Commands.MOVE, Commands.REMOVE_SELECTED_COMPONENT, Commands.CLOSE], mouse_pos)
                        self.selected_component = component
                        component_clicked = True
                        break

                # Display a general dropdown if no component was clicked
                if not component_clicked:
                    print("General dropdown menu")
                    self.dropdown = DropdownMenu([Commands.ADD_BUTTON, Commands.ADD_TEXT_PROMPT, Commands.CLOSE], mouse_pos)
                    self.selected_component = None

                # Adjust dropdown position to prevent off-screen rendering
                x = min(mouse_pos[0], self.screen.get_width() - self.dropdown.width)
                y = min(mouse_pos[1], self.screen.get_height() - self.dropdown.height)
                self.dropdown.position = (x, y)

            elif event.button == 1:  # Left-click
                if self.dropdown and self.dropdown.active:
                    selected_item = self.dropdown.select(mouse_pos)
                    if selected_item:
                        print(f"Selected: {selected_item.name}")
                        self.execute_command(selected_item, mouse_pos)
                        self.dropdown = None  # Close dropdown after selection
                    return

                # Clicks outside components or dropdowns should clear selections and close dropdowns
                self.selected_component = None
                self.dropdown = None
                for component in self.components:
                    if component.rect.collidepoint(mouse_pos):
                        self.selected_component = component

                print("Clicked on empty space")

    def execute_command(self, command, position):
        # Define actions based on the dropdown selection
        if command == Commands.ADD_BUTTON:
            self.add_component(Button(name="new_button", position=position, dimensions=[50, 50], text=""))  # Add a new Button component
        elif command == Commands.REMOVE_SELECTED_COMPONENT:
            if self.selected_component:
                self.remove_component()
            else:
                print("No component selected to remove!")
        elif command == Commands.ADD_TEXT_PROMPT:
            self.add_component(InputBox(name="new_input_box", position=position))
        elif command == Commands.CLOSE:
            if self.dropdown:
                self.dropdown = None
        elif command == Commands.MOVE:
            self.state_changer(EditorStates.MOVE_COMPONENT)
        elif command == Commands.RESHAPE:
            self.state_changer(EditorStates.RESHAPE_COMPONENT)

    #  fixed menu buttons and functions
    def to_dict(self):
        return {
            'dimensions': self.menu_dimensions,
            'components': [component.to_dict() for component in self.components]
        }

    def save_menu_to_file(self):
        directory = 'saved_menus'
        file_name = self.file_name

        # Create directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Save the JSON file in the specified directory
        data = self.to_dict()  # Include dimensions in the dictionary
        with open(os.path.join(directory, f'{file_name}.json'), 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Menus saved to {directory}/{file_name}.json")

    def list_json_files(self):
        directory = 'saved_menus'
        if not os.path.exists(directory):
            return []

        # List all files in the directory
        files = os.listdir(directory)

        # Filter out files that do not end with .json
        json_files = [file for file in files if file.endswith('.json')]
        return json_files

    def create_buttons_for_loadable_files(self):
        files = self.list_json_files()
        if not files:
            print("No files found")

        for index, file in enumerate(files):
            load_button = Button(
                "load_button",
                [50, index * 40],
                [150, 30],
                file,
                click_function=lambda f=file: self.load_menu_from_file(f)
            )
            self.add_load_button(load_button)

    def load_menu_from_file(self, file_name):
        directory = 'saved_menus'

        with open(os.path.join(directory, f'{file_name}'), 'r') as f:
            data = json.load(f)
            print("Loaded data:", data)  # Debug print
            self.components = []
            self.menu_dimensions = data['dimensions']  # Load dimensions from the JSON file
            self.menu_background = pygame.Rect(0, 0, self.menu_dimensions[0], self.menu_dimensions[1])  # Adjust the window size
            for component_data in data["components"]:
                print("Processing component:", component_data)  # Debug print
                component_type = component_data.pop('type')
                if component_type == 'Button':
                    self.components.append(Button.from_dict(component_data))
                elif component_type == 'InputBox':
                    self.components.append(InputBox.from_dict(component_data))
        print(f"Menus loaded from {directory}/{file_name}")
        file_name = file_name[:-5]  # remove the .json ending on the file name string
        self.file_name = file_name
        self.clear_load_buttons()
        self.state_changer(EditorStates.NORMAL)

    def new_file(self):
        file_name_box = InputBox("NEW_FILE_NAME_INPUT", position=[self.window_size[0]/2, self.window_size[1]/2 - 100], title="File Name")
        file_name_box.rect.x -= file_name_box.rect.width / 2 # centers the textbox along x-axis TODO: maybe add feature inside class
        menu_dimension_box = InputBox("menu_dimensions", [self.window_size[0]/2, self.window_size[1]/2],
                                        title="X, Y")
        menu_dimension_box.rect.x -= menu_dimension_box.rect.width / 2  # centers the textbox along x-axis TODO: maybe add feature inside class

        self.add_temp_comp(file_name_box, menu_dimension_box)

    def literal_change_mini_menu(self):

        x_box = InputBox("X_COORD", (self.window_size[0] / 2, self.window_size[1] / 2), title=None)
        y_box = InputBox("Y_COORD", (self.window_size[0] / 2, self.window_size[1] / 2 + x_box.rect.height + 10), title=None)

        def confirm_position():
            try:
                x = int(x_box.text)
                y = int(y_box.text)
                if x < self.window_size[0] and y < self.window_size[1]:
                    self.component_mover((x, y))
            except ValueError:
                print("Invalid input! Please enter valid integers for coordinates.")
            finally:
                self.clear_temp_comp()
                self.state_changer(EditorStates.NORMAL)

        def confirm_shape():
            try:
                width = int(x_box.text)
                height = int(y_box.text)
                self.reshape_component([width, height])
            except ValueError:
                print("Invalid input! Please enter valid integers for coordinates.")
            finally:
                self.clear_temp_comp()
                self.state_changer(EditorStates.NORMAL)

        if self.state == EditorStates.LITERAL_POSITIONING:
            button_func = confirm_position
            x_box.title = "X-Coordinate"
            y_box.title = "Y-Coordinate"
        if self.state == EditorStates.LITERAL_RESHAPING:
            button_func = confirm_shape
            x_box.title = "width"
            y_box.title = "height"
        confirm_button = Button(
            "CONFIRM_BUTTON",
            (self.window_size[0] / 2, y_box.rect.y + y_box.rect.height + 20),
            (100, 25),
            text="confirm",
            click_function=button_func
        )
        self.add_temp_comp(x_box, y_box, confirm_button)

    def run(self):

        for component in self.fixed_components:
            if isinstance(component, Button):
                self.align_fixed_buttons(button=component, margin=10)

        while self.running:
            if self.state != self.last_printed_state:  # Check if the state has changed
                print(self.state)  # Print the new state
                self.last_printed_state = self.state  # Update the last printed state

            self.screen.fill((200, 200, 200))  # Clear the screen

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.state == EditorStates.START_UP:
                            for temp_comp in self.temp_comps:
                                if temp_comp.name == "NEW_FILE_NAME_INPUT":
                                    if temp_comp.text.strip() != "" and len(temp_comp.text) < 10:
                                        self.file_name = temp_comp.text
                                    else:
                                        # Handle case where name is empty or only spaces
                                        print("Please enter a valid name.")
                                if temp_comp.name == "menu_dimensions":
                                    # Remove any extra spaces around the comma
                                    text = re.sub(r'\s*,\s*', ', ', temp_comp.text.strip())

                                    # Check if text is in "##, ##" format
                                    if re.match(r'^\d{1,10}, \d{1,10}$', text):
                                        # Split the string by ", " and convert each part to an integer
                                        self.menu_dimensions = list(map(int, text.split(', ')))
                                    else:
                                        print("Invalid format! Please enter dimensions in the format '##, ##'")

                                if self.menu_dimensions and self.file_name:
                                    self.clear_temp_comp()
                                    self.state_changer(EditorStates.NORMAL)

                # Centralized mouse button handler to exit any state but start up
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                    if self.state != EditorStates.NORMAL and self.state != EditorStates.START_UP and self.state != EditorStates.LITERAL_POSITIONING and self.state != EditorStates.LITERAL_RESHAPING:
                        self.state_changer(EditorStates.NORMAL)

                if self.state == EditorStates.NORMAL:
                    self.handle_editor_dropdown(event)  # Handle dropdown interactions

                elif self.state == EditorStates.MOVE_COMPONENT:
                    if event.type == pygame.MOUSEMOTION:
                        self.component_mover(event.pos)  # Move the component with the mouse

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_p:
                            self.state_changer(EditorStates.LITERAL_POSITIONING)

                    # add text prompt that accepts parameters
                elif self.state == EditorStates.LITERAL_POSITIONING:
                    self.literal_change_mini_menu()

                elif self.state == EditorStates.RESHAPE_COMPONENT:
                    if event.type == pygame.MOUSEMOTION:
                        self.reshape_component(event.pos)

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_p:
                            self.state_changer(EditorStates.LITERAL_RESHAPING)

                elif self.state == EditorStates.LITERAL_RESHAPING:
                    self.literal_change_mini_menu()

                for component in self.fixed_components + self.temp_comps:
                    component.handle_event(event)
                    component.update()
                # the buttons that appear when the load button is clicked
                for button in self.load_buttons:
                    button.handle_event(event)

            if self.menu_background:
                pygame.draw.rect(self.screen, (255, 0, 0), self.menu_background)  # Yellow border for selection
            elif not self.menu_background:
                if self.menu_dimensions:
                    self.menu_background = pygame.Rect(self.window_size[0]//2, self.window_size[1]//2, self.menu_dimensions[0],
                                                       self.menu_dimensions[1])
            # TODO the background should become a component as well that can be altered as all the other components

            # Draw all components
            for component in self.components:
                is_selected = (component == self.selected_component)
                component.draw(self.screen, is_selected)


            # Draw fixed components
            for component in self.fixed_components + self.temp_comps:
                component.draw(self.screen)
                if isinstance(component, Button):
                    self.align_fixed_buttons(button=component, margin=10)
            # draw dynamic buttons
            for button in self.load_buttons:
                button.draw(self.screen)

            # Draw dropdown if active
            if self.dropdown:
                self.dropdown.draw(self.screen)

            self.display_file_name()

            mouse_pos = pygame.mouse.get_pos()
            self.display_info(mouse_pos)

            pygame.display.flip()  # Update the display

        pygame.quit()
        sys.exit()




menu_editor = MenuEditor("menu editor 3000", [800, 600])

menu_editor.run()
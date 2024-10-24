from menu_components import *
import json
import pygame


class CustomMenu:
    def __init__(self, dimensions, position=(0, 0), color=colors["BLACK"]):
        self.components = []
        self.position = position
        self.selected_button = None
        self.dimensions = dimensions
        self.color = color
        self.rect = pygame.Rect(position[0], position[1], dimensions[0], dimensions[1])

    def update(self, event):
        for comp in self.components:
            comp.update()
            comp.handle_event(event)

    def draw(self, window):
        pygame.draw.rect(window, self.color, self.rect)
        for comp in self.components:
            if comp.enabled:
                comp.draw(window)

    """def to_dict(self):
        return {
            'buttons': [button.to_dict() for button in self.buttons],
            'position': self.position,
            'dimensions': self.dimensions,
            'color': self.color
        }"""

    @classmethod
    def from_json(cls, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            dimensions = data.get('dimensions', [800, 600])  # Default dimensions if not provided
            color = data.get('color', [0, 0, 0])  # Default color if not provided
            position = data.get('position', [0, 0])  # Default position if not provided
            menu = cls(dimensions, position, color)
            for component_data in data['components']:
                component_type = component_data.pop('type')
                if component_type == 'Button':
                    menu.components.append(Button.from_dict(component_data))
                elif component_type == 'InputBox':
                    menu.components.append(InputBox.from_dict(component_data))
            return menu





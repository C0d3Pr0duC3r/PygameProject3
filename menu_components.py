import pygame

pygame.init()

colors = {
    "COLOR_INACTIVE": (130, 116, 247),
    "COLOR_ACTIVE": (14, 3, 110),
    "BLUE": (0, 0, 255),
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "DARK_GREEN": (34, 120, 56)
}


class MenuComponent:
    def __init__(self, name, position, dimensions, type_=None):
        self.name = name
        self.rect = pygame.Rect(position[0], position[1], dimensions[0], dimensions[1])
        self.hovered = False
        self.type_ = type_

    def handle_event(self, event):
        raise NotImplementedError("This method should be overridden by subclasses")

    def update(self):
        raise NotImplementedError("This method should be overridden by subclasses")

    def draw(self, window, selected=False):
        # Draw the selection indicator if selected
        if selected:
            pygame.draw.rect(window, (255, 255, 0), self.rect, 4)  # Yellow border for selection

    def to_dict(self):
        raise NotImplementedError("This method should be overridden by subclasses")

    @classmethod
    def from_dict(cls, data):
        raise NotImplementedError("This method should be overridden by subclasses")


class MenuBackGround(MenuComponent):
    def __init__(self, name, position, dimensions, color=()):
        super().__init__(name, position, dimensions)
        self.color = color

    def draw(self, window, selected=False):
        pygame.draw.rect(window, self.color, self.rect)


class Button(MenuComponent):
    def __init__(self, name, position, dimensions, text, alignment=None, font=None, tooltip_text=None, font_size=32, color=(0, 255, 0), hover_color=(34, 120, 56), click_function=None):
        super().__init__(name, position, dimensions)
        self.text = text
        self.tooltip_text = tooltip_text
        self.font_size = font_size
        self.font = font if font else pygame.font.Font(None, font_size)
        self.color = color
        self.hover_color = hover_color
        self.click_function = click_function
        self.is_pressable = True
        self.alignment = alignment
        self.type_ = "Button"

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and self.click_function:
                print(self.click_function, type(self.click_function))  # debug line
                self.click_function()
            elif self.rect.collidepoint(event.pos) and not self.click_function:
                print(f"{self.name} has no function")

    def update(self):
        pass

    def draw(self, window, selected=False):
        current_color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(window, current_color, self.rect)
        super().draw(window, selected)
        font_surface = self.font.render(self.text, True, (255, 255, 255))
        font_rect = font_surface.get_rect(center=self.rect.center)
        window.blit(font_surface, font_rect)
        self.draw_tooltip(window)

    def draw_tooltip(self, window):
        if self.hovered and self.tooltip_text:
            tooltip_font = pygame.font.Font(None, 24)
            tooltip_surf = tooltip_font.render(self.tooltip_text, True, (255, 255, 255))
            tooltip_rect = tooltip_surf.get_rect()
            tooltip_rect.x = self.rect.right + 10
            tooltip_rect.y = self.rect.y
            background_rect = tooltip_rect.inflate(10, 10)
            pygame.draw.rect(window, (0, 0, 0), background_rect)
            window.blit(tooltip_surf, tooltip_rect)

    def to_dict(self):
        return {
            'type': 'Button',
            'name': self.name,
            'position': [self.rect.x, self.rect.y],
            'dimensions': [self.rect.width, self.rect.height],
            'text': self.text,
            'tooltip_text': self.tooltip_text,
            'font_size': self.font_size,
            'color': self.color,
            'hover_color': self.hover_color,
            'click_function': self.click_function
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            position=data['position'],
            dimensions=data['dimensions'],
            text=data['text'],
            tooltip_text=data['tooltip_text'],
            alignment=data.get('alignment'),
            font_size=data.get('font_size', 32),
            color=tuple(data.get('color', (0, 255, 0))),
            hover_color=tuple(data.get('hover_color', (34, 120, 56))),
            click_function=data['click_function']
        )


COLOR_INACTIVE = (130, 116, 247)
COLOR_ACTIVE = (14, 3, 110)
FONT = pygame.font.Font(None, 32)


class InputBox(MenuComponent):
    def __init__(self, name, position, font=None, font_size=32, title=None, dimensions=(200, 50), text=''):
        super().__init__(name, position, dimensions)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False
        self.title = title
        self.font = font if font else pygame.font.Font(None, font_size)
        self.type_ = "inputbox"

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    print("inside class print ==>", self.text)
                    self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def return_input(self):
        return self.text

    def draw(self, window, selected=False):
        super().draw(window, selected)  # Call the superclass draw method to handle selection indication
        window.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(window, self.color, self.rect, 2)
        if self.title:
            title_surface = self.font.render(self.title, True, (255, 255, 255))
            font_rect = title_surface.get_rect(midbottom=self.rect.midtop)
            window.blit(title_surface, font_rect)
        #  TODO add some background option

    def to_dict(self):
        return {
            'type': 'InputBox',
            'name': self.name,
            'position': [self.rect.x, self.rect.y],
            'dimensions': [self.rect.width, self.rect.height],
            'text': self.text,
            'color': self.color,
            'active': self.active
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            position=data['position'],
            dimensions=data['dimensions'],
            text=data['text']
        )




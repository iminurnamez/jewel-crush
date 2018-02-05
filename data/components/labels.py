from itertools import cycle
import string

import pygame as pg

from .. import prepare, tools


#To avoid instantiating unnecessary Font objects,
#Fonts are stored in this dict. When creating a Label or
#Button object, this dict is checked first to see if the
#font already exists in LOADED_FONTS.
LOADED_FONTS = {}

#Default values for Button objects - see Button class for specifics
BUTTON_DEFAULTS = {
        "button_size": (128, 32),
        "call": None,
        "args": None,
        "call_on_up": True,
        "font_path": None,
        "font_size": 36,
        "text": None,
        "hover_text": None,
        "disable_text": None,
        "text_color": pg.Color("white"),
        "hover_text_color": None,
        "disable_text_color": None,
        "fill_color": None,
        "hover_fill_color": None,
        "disable_fill_color": None,
        "idle_image": None,
        "hover_image": None,
        "disable_image": None,
        "hover_sound": None,
        "click_sound": None,
        "visible": True,
        "active": True,
        "bindings": ()}

#Default values for Label objects - see Label class for specifics
LABEL_DEFAULTS = {
        "font_path": prepare.FONTS["vipond_angular"],
        "font_size": 12,
        "text_color": "white",
        "fill_color": None,
        "alpha": 255}

MULTILINE_LABEL_DEFAULTS = {
        "font_path": None,
        "font_size": 12,
        "text_color": "white",
        "fill_color": None,
        "alpha": 255,
        "char_limit": 42,
        "align": "left",
        "vert_space": 0}

TEXTBOX_DEFAULTS = {
        "active": True,
        "visible": True,
        "call": None,         #call(self.final) will be called on enter
        "validator": None, #function to validate textbox input, checked on enter command
        "accept": string.ascii_letters + string.digits+ string.punctuation + " ",

        "box_size": (256, 64),
        "box_image": None,
        "fill_color": pg.Color("gray70"),
        "outline_color": pg.Color("gray50"),
        "outline_width": 2,

        "cursor_visible": True,
        "cursor_active": True,
        "cursor_image": None,
        "cursor_color": pg.Color("white"),
        "cursor_size": None,
        "cursor_offset": 1,
        "cursor_blink": True,
        "blink_frequency": 100,

        "text_color": pg.Color("gray85"),
        "font_path": None,
        "font_size": 32,
        "left_margin": 4,

        "type_sound": None,
        "final_sound": None,
        "invalid_sound": None,

        "visible": True,
        "active": True,
        "clear_on_enter" : True,
        "inactive_on_enter" : False,
        "invisible_on_enter": False,
        "bindings":
                {"enter": (pg.K_RETURN, pg.K_KP_ENTER),
                "backspace": (pg.K_BACKSPACE,),
                "delete": (pg.K_DELETE,),
                "back": (pg.K_LEFT,),
                "forward": (pg.K_RIGHT,)}}


#Helper function for MultiLineLabel class
def wrap_text(text, char_limit, separator=" "):
    """
    Split a string into a list of strings no longer than char_limit
    without splitting individual words.
    """
    words = text.split(separator)
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if len(word) + current_length <= char_limit:
            current_length += len(word) + len(separator)
            current_line.append(word)
        else:
            lines.append(separator.join(current_line))
            current_line = [word]
            current_length = len(word) + len(separator)
    if current_line:
        lines.append(separator.join(current_line))
    return lines


#Helper function to allow multiple ways to pass color arguments
def _parse_color(color):
    """
    Accepts an RGB, RGBA or pygame color-name and returns
    a pygame.Color object.
    """
    if color is not None:
        try:
            return pg.Color(str(color))
        except ValueError as e:
            return pg.Color(*color)
    return color


class Label(pg.sprite.Sprite, tools._KwargMixin):
    """
    Parent class all labels inherit from. Color arguments can use color names
    or an RGB tuple. rect_attr should be a dict with keys of pygame.Rect
    attribute names (strings) and the relevant position(s) as values.

    Creates a surface with text blitted to it (self.image) and an associated
    rectangle (self.rect). Label will have a transparent bg if
    fill_color is not passed to __init__.
    """
    def __init__(self, text, rect_attr, *groups, **kwargs):
        """
        ARGS

        text: the text to be displayed on the screen
        rect_attr: a dict of pygame.Rect attributes
                        ex. {"midtop": (100, 100)}
        groups: sprite groups the label should be added to

        KEYWORD ARGS

        font_path: path to font file, font objects are cached to LOADED_FONTS
        font_size: font size for text to be rendered at
        text_color: color for text to be rendered in
                          accepts pygame.Color object, RGB tuple or colorname string
        fill_color: background color for label
                       accepts pygame.Color object, RGB tuple or colorname string
                       background will be transparent if None
        alpha: surface alpha

        args that are not passed will use the default values in LABEL_DEFAULTS
        """
        super(Label, self).__init__(*groups)
        self.process_kwargs("Label", LABEL_DEFAULTS, kwargs)
        path, size = self.font_path, self.font_size
        if (path, size) not in LOADED_FONTS:
            LOADED_FONTS[(path, size)] = pg.font.Font(path, size)
        self.font = LOADED_FONTS[(path, size)]
        self.fill_color = _parse_color(self.fill_color)
        self.text_color = _parse_color(self.text_color)
        self.rect_attr = rect_attr
        self.set_text(text)

    def set_text(self, text):
        """Set the text to display."""
        self.text = text
        self.update_text()

    def update_text(self):
        """Update the surface using the current properties and text."""
        if self.alpha != 255:
            self.fill_color = pg.Color(*[x + 1 if x < 255 else x - 1 for x in self.text_color[:3]])
        if self.fill_color:
            render_args = (self.text, True, self.text_color, self.fill_color)

        else:
            render_args = (self.text, True, self.text_color)
        self.image = self.font.render(*render_args)
        if self.alpha != 255:
            self.image.set_colorkey(self.fill_color)
            self.image.set_alpha(self.alpha)
        self.rect = self.image.get_rect(**self.rect_attr)

    def update(self, *args):
        pass

    def draw(self, surface):
        """Blit self.image to target surface."""
        surface.blit(self.image, self.rect)


class Blinker(Label):
    def __init__(self, text, rect_attributes, frequency, *groups, **kwargs):
        super(Blinker, self).__init__(text, rect_attributes, *groups, **kwargs)
        self.original_text = text
        self.frequency = frequency
        self.timer = 0
        self.visible = True

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.frequency:
            self.timer -= self.frequency
            self.visible = not self.visible
            text = self.original_text if self.visible else ""
            self.set_text(text)


class MultiLineLabel(pg.sprite.Sprite, tools._KwargMixin):
    """Create a single surface with multiple lines of text rendered on it."""
    def __init__(self, text, rect_attr, *groups, **kwargs):
        """
        ARGS
        text: the text to be displayed on the screen
        rect_attr: a dict of pygame.Rect attributes
                        ex. {"midtop": (100, 100)}
        groups: sprite groups the label should be added to

        KEYWORD ARGS
        char_limit: max number of characters in each line of text
                         text is split by words, not characters
        align: how text should be aligned/justified - valid args are
                 "left", "center", or "right"
        vert_space: vertical space in between each line
        args that are not passed will use the default values in MULTILINE_LABEL_DEFAULTS
        """
        super(MultiLineLabel, self).__init__(*groups)
        self.process_kwargs("MultiLineLabel", MULTILINE_LABEL_DEFAULTS, kwargs)
        self.rect_attr = rect_attr
        self.make_image(text)

    def make_image(self, text):
        attr = {"center": (0, 0)}
        lines = wrap_text(text, self.char_limit)
        labels = [Label(line, attr, font_path=self.font_path, font_size=self.font_size,
                              text_color=self.text_color, fill_color=self.fill_color) for line in lines]
        width = max([label.rect.width for label in labels])
        spacer = self.vert_space * (len(lines)-1)
        height = sum([label.rect.height for label in labels])+spacer
        if self.fill_color is not None:
            self.image = pg.Surface((width, height)).convert()
            self.image.fill(self.fill_color)
        else:
            self.image = pg.Surface((width, height)).convert_alpha()
            self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect(**self.rect_attr)
        aligns = {"left"  : {"left": 0},
                      "center": {"centerx": self.rect.width//2},
                      "right" : {"right": self.rect.width}}
        y = 0
        for label in labels:
            label.rect = label.image.get_rect(**aligns[self.align])
            label.rect.top = y
            label.draw(self.image)
            y += label.rect.height + self.vert_space

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class ButtonGroup(pg.sprite.Group):
    """
    A sprite Group modified to allow calling each sprite in the group's
    get_event method similar to using Group.update to call each sprite's
    update method.
    """
    def get_event(self, event, *args, **kwargs):
        check = (s for s in self.sprites() if s.active and s.visible)
        for s in check:
            s.get_event(event, *args, **kwargs)


class Button(pg.sprite.Sprite, tools._KwargMixin):
    """
    A clickable button which accepts a number of keyword
    arguments to allow customization of a button's
    appearance and behavior.
    """
    _invisible = pg.Surface((1,1)).convert_alpha()
    _invisible.fill((0,0,0,0))

    def __init__(self, rect_attr, *groups, **kwargs):
        """
        Instantiate a Button object based on the keyword arguments. Buttons
        have three possible states (idle, hovered and disabled) and appearance
        options for each state. The button is idle when the mouse is not over
        the button and hovered when it is. The button is disabled when
        Button.active is False and will not respond to events.

        USAGE

        For buttons to function properly, Button.update must be called
        each frame/tick/update with the current mouse position and
        Button.get_event must be called for each event in the event queue.

        ARGS

       rect_attr: a dict of pygame.Rect attributes
                        ex. {"midtop": (100, 100)}
        groups: sprite groups the button should be added to

        KWARGS

        Buttons accept a number of keyword arguments that may be
        passed individually, as a dict of "keyword": value pairs or a combination
        of the two. Any args that are not passed to __init__ will use the default
        values stored in the BUTTON_DEAFULTS dict

        button_size: the size of the button in pixels
        call: callback function
        args: args to be passed to callback function
        call_on_up: set to True for clicks to occur on mouseup/keyup
                             set to False for clicks to occur on mousedown/keydown
        font: path to font - uses pygame's default if None
        font_size: font size in pixels
        text: text to be displayed when button is idle
        hover_text: text to be displayed when mouse is over button
        disable_text: text to be displayed when button is disabled
        text_color: text color when button is idle
        hover_text_color: text_color when mouse is hovering over button
        disable_text_color: text color when button is disabled (self.active == False)
        fill_color: button color when button is idle, transparent if None
        hover_fill_color: button color when hovered, transparent if None
        disable_fill_color: button color when disabled, transparent if None
        idle_image: button image when idle, ignored if None
        hover_image: button image when hovered, ignored if None
        disable_image: button image when disabled, ignored if None
        hover_sound: Sound object to play when hovered, ignored if None
        click_sound: Sound object to play when button is clicked, ignored if None
        visible: whether the button should be drawn to the screen
        active: whether the button should respond to events
        bindings: which keyboard keys, if any, should be able to click the button
                      values should be a sequence of pygame key constants, e.g, (pg.K_UP, pg.K_w)
        """
        super(Button, self).__init__(*groups)
        color_args = ("text_color", "hover_text_color", "disable_text_color",
                           "fill_color", "hover_fill_color", "disable_fill_color")
        for c_arg in color_args:
            if c_arg in kwargs and kwargs[c_arg] is not None:
                 kwargs[c_arg] = _parse_color(kwargs[c_arg])
        self.process_kwargs("Button", BUTTON_DEFAULTS, kwargs)
        self.rect = pg.Surface(self.button_size).get_rect(**rect_attr)
        rendered = self.render_text()
        self.idle_image = self.make_image(self.fill_color, self.idle_image,
                                          rendered["text"])
        self.hover_image = self.make_image(self.hover_fill_color,
                                           self.hover_image, rendered["hover"])
        self.disable_image = self.make_image(self.disable_fill_color,
                                             self.disable_image,
                                             rendered["disable"])
        self.image = self.idle_image
        self.clicked = False
        self.hover = False

    def render_text(self):
        """Render text for each button state."""
        font, size = self.font_path, self.font_size
        if (font, size) not in LOADED_FONTS:
            LOADED_FONTS[font, size] = pg.font.Font(font, size)
        self.font = LOADED_FONTS[font, size]
        text = self.text and self.font.render(self.text, 1, self.text_color)
        hover = self.hover_text and self.font.render(self.hover_text, 1,
                                                     self.hover_text_color)
        disable = self.disable_text and self.font.render(self.disable_text, 1,
                                                       self.disable_text_color)
        return {"text": text, "hover": hover, "disable": disable}

    def make_image(self, fill, image, text):
        """Create needed button images."""
        if not any((fill, image, text)):
            return None
        final_image = pg.Surface(self.rect.size).convert_alpha()
        final_image.fill((0,0,0,0))
        rect = final_image.get_rect()
        fill and final_image.fill(fill, rect)
        image and final_image.blit(image, rect)
        text and final_image.blit(text, text.get_rect(center=rect.center))
        return final_image

    def get_event(self, event):
        """Process events."""
        if self.active and self.visible:
            if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                self.on_up_event(event)
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                self.on_down_event(event)
            elif event.type == pg.KEYDOWN and event.key in self.bindings:
                self.on_down_event(event, True)
            elif event.type == pg.KEYUP and event.key in self.bindings:
                self.on_up_event(event, True)

    def on_up_event(self, event, onkey=False):
        """Process mouseup and keyup events."""
        if self.clicked and self.call_on_up:
            self.click_sound and self.click_sound.play()
            self.call and self.call(self.args or self.text)
        self.clicked = False

    def on_down_event(self, event, onkey=False):
        """Process mousedown and keydown events."""
        if self.hover or onkey:
            self.clicked = True
            if not self.call_on_up:
                self.click_sound and self.click_sound.play()
                self.call and self.call(self.args or self.text)

    def update(self, prescaled_mouse_pos):
        """
        Determine whehter the mouse is over the button and
        change button appearance if necessary. Calling
        ButtonGroup.update will call update on any Buttons
        in the group.
        """
        hover = self.rect.collidepoint(prescaled_mouse_pos)
        pressed = pg.key.get_pressed()
        if any(pressed[key] for key in self.bindings):
            hover = True
        if not self.visible:
            self.image = Button._invisible
        elif self.active:
            self.image = (hover and self.hover_image) or self.idle_image
            if not self.hover and hover:
                self.hover_sound and self.hover_sound.play()
            self.hover = hover
        else:
            self.image = self.disable_image or self.idle_image

    def draw(self, surface):
        """Draw the button to the screen."""
        surface.blit(self.image, self.rect)


class Textbox(pg.sprite.Sprite, tools._KwargMixin):
    """
    Allows the user to type and enter text. Textboxes accept a number
    of keyword arguments to allow customization of a textbox's appearance
    and behavior. Keywords for which no value is provided will use the values
    in TEXTBOX_DEFAULTS.

    ARGS

    rect_attr: a dict of pygame.Rect attributes used to position the textbox
                   on the screen, ex. {"midtop": (100, 100)}
    groups: sprite groups for the textbox to be added to

    KWARGS
    all color args accept pygame.Color objects, RGB tuples or colorname strings

    active: whether the textbox should respond to events
    visible: whether the textbox should be visible on the screen
    call: callback function called on enter
              user-entered text will be passed as the sole argument
    validator: function to validate textbox input
                      called on enter
    accept: string of valid characters
    box_size: width, height of textbox in pixels
    box_image: image to be used for textbox
                          if None, a rect will be drawn instead
    fill_color: fill color of textbox, ignored if box_image is not None
    outline_color: box outline color, set equal to fill_color for no outline
    outline_width: outline thickness in pixels

    font_path: path to font file, font objects are cached to LOADED_FONTS
    font_size: font size for text to be rendered at
    text_color: color for text to be rendered ine visible
    left_margin: number of pixels to offset text by
    cursor_image: image to use for the cursor
                           if None, a cursor image will be created
    cursor_color: color for created cursor image
                         ignored if cursor_image is not None
    cursor_size: width, height of cursor
                        defaults to font_size//4, font_size
    cursor_offset: width in pixels of space between text and cursor
    cursor_blink: whether the cursor should blink
    blink_frequency: cursor blink frequency in milliseconds
                                 ignored if cursor_blink is False

    type_sound: Sound object to be played on typing a valid character
    final_sound: Sound object to be played on enter command
    invalid_sound: Sound object to be played on typing an invalid character
    clear_on_enter: whether the input buffer should be cleared on enter
    inactive_on_enter: whether to deactivate textbox on enter
    invisible_on_enter: whether to set visible to False on enter
    bindings: dict for mapping textbox commands to keyboard keys
                  dict should have a key for each of Textbox's commands:
                      "enter": finalize text input
                      "backspace": remove the character to the left of the cursor
                      "delete": remove the character to the right of the ciursor
                      "back": move the cursor left
                      "forward": move the cursor right
                  dict values should be sequences of pygame key constants
    """
    _invisible = pg.Surface((1,1)).convert_alpha()
    _invisible.fill((0,0,0,0))

    def __init__(self, rect_attr, *groups, **kwargs):
        super(Textbox, self).__init__(*groups)
        self.rect_attr = rect_attr
        color_args = ("text_color", "cursor_color", "fill_color", "outline_color")
        for c_arg in color_args:
            if c_arg in kwargs and kwargs[c_arg] is not None:
                 kwargs[c_arg] = _parse_color(kwargs[c_arg])
        self.process_kwargs("Textbox", TEXTBOX_DEFAULTS, kwargs)
        if self.box_image is None:
            self.make_box_image()
        else:
            self.rect = self.box_image.get_rect(**self.rect_attr)
        self.cursor_active = True
        if self.cursor_image is None:
            if self.cursor_size is None:
                self.cursor_size = max(1, self.font_size // 4), self.font_size
            self.make_cursor_image()
        self.bound_keys = []
        for v in self.bindings.values():
            self.bound_keys.extend(list(v))
        self.commands = {
            "enter": self.enter,
            "backspace": self.backspace,
            "back": self.back,
            "forward": self.forward}

        self.buffer = ""
        self.buffer_index = 0
        self.final = None
        self.timer = 0
        self.buffer_label = Label(self.buffer,
                {"midleft": (self.left_margin, self.rect.h // 2)},
                text_color=self.text_color, font_size=self.font_size,
                font_path=self.font_path)

    def make_box_image(self):
        self.box_image = pg.Surface(self.box_size)
        self.box_image.fill(self.fill_color)
        self.rect = self.box_image.get_rect(**self.rect_attr)
        if self.outline_color:
            pg.draw.rect(self.box_image, self.outline_color,
                              self.box_image.get_rect(), self.outline_width)

    def get_event(self, event):
        if self.active and event.type == pg.KEYDOWN:
            for command in self.bindings:
                if event.key in self.bindings[command]:
                    self.commands[command]()
            if event.unicode in self.accept and event.key not in self.bound_keys:
                head = self.buffer[:self.buffer_index]
                tail = self.buffer[self.buffer_index:]
                self.buffer = head + event.unicode + tail
                self.buffer_index += 1
                self.type_sound and self.type_sound.play()

    def update(self, dt):
        if self.cursor_blink:
            self.timer += dt
            if self.timer >= self.blink_frequency:
                self.timer -= self.blink_frequency
                self.cursor_active = not self.cursor_active
        self.buffer_label.set_text(self.buffer)
        if not self.visible:
            self.image = Textbox._invisible
        else:
            self.make_image()

    def make_image(self):
        self.image = self.box_image.copy()
        self.buffer_label.draw(self.image)
        if self.cursor_active:
            left = self.buffer_label.rect.right + self.cursor_offset
            if self.buffer_index < len(self.buffer):
                percent = float(self.buffer_index) / len(self.buffer)
                left -= int(self.buffer_label.rect.w * (1 - percent))
            midleft = (left, self.buffer_label.rect.centery)
            rect = self.cursor_image.get_rect(midleft=midleft)
            self.image.blit(self.cursor_image, rect)

    def make_cursor_image(self):
        self.cursor_image = pg.Surface((self.cursor_size))
        self.cursor_image.fill(self.cursor_color)

    def clear(self):
        self.buffer = ""

    def enter(self):
        self.final = self.buffer
        if self.clear_on_enter:
            self.clear()
        if self.inactive_on_enter:
            self.active = False
        if self.invisible_on_enter:
            self.visible = False
        if self.call is not None:
            if self.validator is None or self.validator(self.final):
                self.call(self.final)
                self.final_sound and self.final_sound.play()
            else:
                self.invalid_sound and self.invalid_sound.play()
        else:
            self.final_sound and self.final_sound.play()

    def backspace(self):
        if self.buffer_index > 0:
            self.buffer_index -= 1
            head = self.buffer[:self.buffer_index]
            tail = self.buffer[self.buffer_index + 1:]
            self.buffer = head + tail
            self.type_sound and self.type_sound.play()

    def delete(self):
        head = self.buffer[:self.buffer_index + 1]
        tail = self.buffer[self.buffer_index + 2:]
        self.buffer = head + tail
        self.type_sound and self.type_sound.play()

    def back(self):
        if self.buffer_index > 0:
            self.buffer_index -= 1
            self.type_sound and self.type_sound.play()

    def forward(self):
        if self.buffer_index < len(self.buffer):
            self.buffer_index += 1
            self.type_sound and self.type_sound.play()

    def draw(self, surface):
        surface.blit(self.image, self.rect)

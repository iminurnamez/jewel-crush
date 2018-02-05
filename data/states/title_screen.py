import os
import json


import pygame as pg

from .. import tools, prepare
from ..components.animation import Animation
from ..components.labels import Label, Button, ButtonGroup
from ..components.ui import BouncingBackground, StainedGlass


class TitleScreen(tools._State):
    def __init__(self):
        super(TitleScreen, self).__init__()
        self.labels = pg.sprite.Group()
        self.animations = pg.sprite.Group()
        self.buttons = ButtonGroup()
        self.make_title()
        self.background = BouncingBackground((0, 0),
                    prepare.SCREEN_SIZE, prepare.GFX["bg-big"], 40)

    def load_game(self):
        p = os.path.join("resources", "saved.json")
        try:
            with open(p, "r") as f:
                self.saved = json.load(f)
        except IOError:
            self.saved = None
        self.make_buttons()

    def make_buttons(self):
        top = 500
        cx = prepare.SCREEN_RECT.centerx
        image = prepare.GFX["button-continue"]
        info = [] if self.saved is None else [(image, "continue")]
        info.append((prepare.GFX["button-newgame"], "new game"))
        offsets = [700, -700]
        for i, off in zip(info, offsets):
            img, args = i
            b = Button({"midtop": (cx + off, top)}, self.buttons,
                        button_size=img.get_size(), idle_image=img,
                        call=self.to_game, args=args)
            ani = Animation(centerx=cx, duration=2000,
                        round_values=True, transition="out_elastic")
            ani.start(b.rect)
            self.animations.add(ani)
            top += 100

    def to_game(self, saved):
        self.persist["fade in"] = True
        self.persist["new game"] = False
        self.persist["new board"] = False
        if saved == "continue":
            self.persist["saved"] = self.saved
        else:
            self.persist["saved"] = None
            self.persist["new game"] = True
        self.next = "GAMEPLAY"
        self.done = True

    def make_title(self):
        cx, cy = prepare.SCREEN_RECT.center
        jewely, crushy = 236, 420
        dist = 500
        duration = 1500
        colors= [(0, 227, 255), (236, 230, 255),
                    (255, 120, 255), (236, 230, 255)]
        jewel = StainedGlass((prepare.SCREEN_RECT.centerx, jewely - dist),
                    prepare.GFX["title"], prepare.GFX["title-cover"], colors,
                    40, 2000, self.labels)
        ani = Animation(centery=jewely, duration=duration,
                    round_values=True, transition="out_bounce")
        ani.callback = self.load_game
        ani.start(jewel.rect)
        self.animations.add(ani)

    def startup(self, persistent):
        self.persist = persistent

    def get_event(self,event):
        if event.type == pg.QUIT:
            self.quit = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.quit = True
        self.buttons.get_event(event)

    def update(self, dt):
        self.animations.update(dt)
        self.background.update(dt)
        self.labels.update(dt)
        self.buttons.update(pg.mouse.get_pos())



    def draw(self, surface):
        self.background.draw(surface)
        for label in self.labels:
            label.draw(surface)
        for b in self.buttons:
            clipped = prepare.SCREEN_RECT.clip(b.rect)
            if clipped.w:
                r = pg.Rect(clipped.left - b.rect.left, clipped.top - b.rect.top,
                            clipped.w, clipped.h)
                img = b.image.subsurface(r)
                surface.blit(img, clipped)
        surface.blit(prepare.GFX["crystal-frame"], (0, 0))

from random import shuffle
from itertools import cycle

import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, Blinker
from ..components.animation import Animation, Task
from ..components.ui import StainedGlass, ScreenBackground


class BonusIcon(pg.sprite.Sprite):
    def __init__(self, center, color, gem_num, *groups):
        self.color = color
        self.gem_num = gem_num
        self.base_image = prepare.JEWELS[color][gem_num][0]
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=center)
        self.width, self.height = self.rect.size
        self.selected = False

    def get_event(self, event):
        if event.type == pg.MOUSEBUTTONUP:
            if self.rect.collidepoint(event.pos):
                self.selected = True

    def update(self):
        if (self.width, self.height) != self.rect.size:
            self.image = pg.transform.smoothscale(
                        self.base_image, (self.width, self.height))
            self.rect = self.image.get_rect(center=self.rect.center)

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class BonusScreen(tools._State):
    def __init__(self):
        super(BonusScreen, self).__init__()
        self.bg = ScreenBackground(prepare.GFX["bg-screen"],
                    [(0, 0, 378, 150),(904, 4, 371, 544)])

    def startup(self, persistent):
        self.animations = pg.sprite.Group()
        self.persist = persistent
        self.grid = self.persist["grid"]
        self.make_labels()
        self.cover_alpha = 0
        self.cover = None
        self.leaving = False
        self.bonus_selected = False
        self.icons_added = False
        self.icon_cycle_time = 200
        self.timer = 0
        self.icons = []
        self.icon = None
        self.bg.clear(pg.display.get_surface())

    def make_labels(self):
        self.labels = pg.sprite.Group()
        cx, cy = self.grid.rect.centerx, self.grid.rect.centery - 64

        dist = 400
        duration = 750
        delay= 750
        colors = [(0, 227, 255), (236, 230, 255),
                    (255, 120, 255), (236, 230, 255)]
        self.label1 = StainedGlass((cx, cy - dist), prepare.GFX["word-bonus"],
                    prepare.GFX["cover-bonus"], colors, 120, 1500)
        ani = Animation(bottom=cy, duration=duration, delay=delay,
                    round_values=True, transition="out_bounce")
        ani.start(self.label1.rect)
        self.animations.add(ani)

    def make_cover(self):
        self.cover = pg.Surface(self.grid.background.image.get_size())
        self.cover.blit(self.grid.background.image, (0, 0))
        ani = Animation(cover_alpha=255, duration=1000)
        ani.start(self)
        self.animations.add(ani)

    def to_bonus_clear(self):
        self.done = True
        self.next = "CLEAR_BONUS"

    def select_bonus(self, color, gem_num):
        self.bonus_selected = True
        ani = Animation(cover_alpha=0, duration=1000)
        ani.start(self)
        ani.callback = self.to_bonus_clear
        ani2 = Animation(top=self.label1.rect.top - 800, duration=750,
                    round_values=True, transition="in_back")
        ani2.start(self.label1.rect)
        w, h = self.icon.rect.size
        ani3 = Animation(width=w*2, height=h*2, duration=1000,
                    round_values=True)
        ani3.start(self.icon)
        self.animations.add(ani, ani2, ani3)

        self.persist["bonus color"] = color
        self.persist["gem num"] = gem_num

    def make_bonus_icons(self):
        center = self.grid.rect.centerx, self.grid.rect.centery + 32
        self.icons = cycle([BonusIcon(center, *combo)
                    for combo in self.grid.jewel_combos])
        self.icon = next(self.icons)
        self.icons_added = True

    def get_event(self,event):
        if event.type == pg.QUIT:
            self.quit = True
        if self.icon is not None:
            self.icon.get_event(event)

    def update(self, dt):
        self.animations.update(dt)
        self.label1.update(dt)
        self.grid.update(dt)
        if not any((self.grid.animations,
                    self.grid.points_animations, self.leaving)):
            self.make_cover()
            duration = 1000
            ani = Animation(cover_alpha=255, duration=duration)
            ani.callback = self.make_bonus_icons
            ani.start(self)
            self.animations.add(ani)
            self.leaving = True
        elif self.icons_added and not self.bonus_selected:
            if self.icon is None or not self.icon.selected:
                self.timer += dt
                while self.timer >= self.icon_cycle_time:
                    self.timer -= self.icon_cycle_time
                    self.icon = next(self.icons)
            if self.icon is not None and self.icon.selected:
                self.select_bonus(self.icon.color, self.icon.gem_num)
        if self.icon is not None:
            self.icon.update()
        if self.cover is not None:
            self.cover.blit(self.grid.background.image, (0, 0))
            self.cover.set_alpha(self.cover_alpha)
        if self.grid.ui.quit:
            self.quit_game()

    def draw(self, surface):
        self.bg.draw(surface)
        self.grid.draw(surface)
        if self.cover is not None:
            surface.blit(self.cover, self.grid.rect)
        if self.icon is not None:
            self.icon.draw(surface)
        self.label1.draw(surface)
        self.grid.ui.draw(surface)
        surface.blit(prepare.GFX["crystal-frame"], (0, 0))
        surface.blit(prepare.GFX["crystal-frame2"], (374, 0))
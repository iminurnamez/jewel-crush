import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, Blinker
from ..components.animation import Animation, Task
from ..components.ui import StainedGlass, ScreenBackground


class LevelUp(tools._State):
    def __init__(self):
        super(LevelUp, self).__init__()
        self.bg = ScreenBackground(prepare.GFX["bg-screen"],
                    [(0, 0, 378, 150),(904, 4, 371, 544)])

    def startup(self, persistent):
        self.animations = pg.sprite.Group()
        self.persist = persistent
        self.grid = self.persist["grid"]
        if not self.grid.ui.volume_slider.muted:
            prepare.SFX["jewel-levelup"].set_volume(
                        self.grid.ui.volume_slider.volume)
            prepare.SFX["jewel-levelup"].play()
        self.make_labels()
        self.cover_alpha = 0
        self.leaving = False
        self.make_cover()

    def make_labels(self):
        self.labels = pg.sprite.Group()
        cx, cy = self.grid.rect.center
        dist = 400
        duration = 750
        delay=1200
        space = 0
        colors = [(0, 227, 255), (236, 230, 255),
                    (255, 120, 255), (236, 230, 255)]
        self.label1 = StainedGlass((cx, (cy - space) - dist),
                    prepare.GFX["word-level"], prepare.GFX["cover-level"],
                    colors, 80, 200, self.labels)
        self.label2 = StainedGlass((cx, (cy + space) - dist),
                    prepare.GFX["word-up"], prepare.GFX["cover-up"],
                    colors, 80, 200, self.labels)
        ani = Animation(bottom=cy-space, duration=duration, delay=delay,
                    round_values=True, transition="out_back")
        ani.callback = self.grid.level_up
        ani.start(self.label1.rect)
        ani2 = Animation(top=cy+space, duration=duration, delay=delay,
                    round_values=True, transition="out_back")
        ani2.start(self.label2.rect)
        self.animations.add(ani, ani2)


    def make_cover(self):
        self.cover = pg.Surface(self.grid.background.image.get_size())
        self.cover.blit(self.grid.background.image, (0, 0))
        self.cover.set_alpha(self.cover_alpha)

    def to_game(self):
        self.persist["new board"] = True
        self.done = True
        self.next = "GAMEPLAY"

    def get_event(self,event):
        if event.type == pg.QUIT:
            self.quit = True

    def fade_out(self):
        leave = Task(self.to_game, 1500)
        duration = 750
        dist = 800
        ani = Animation(top=self.label1.rect.top - dist, duration=duration,
                    round_values=True, transition="in_back")
        ani.start(self.label1.rect)
        ani2 = Animation(top=self.label2.rect.top - dist, duration=duration,
                    round_values=True, transition="in_back")
        ani2.start(self.label2.rect)
        self.animations.add(leave, ani, ani2)

    def update(self, dt):
        self.animations.update(dt)
        self.labels.update(dt)
        self.grid.update(dt)
        if not any((self.grid.animations,
                    self.grid.points_animations, self.leaving)):
            duration = 2000
            ani = Animation(cover_alpha=255, duration=duration)
            ani.callback = self.fade_out
            ani.start(self)
            self.animations.add(ani)
            self.leaving = True
        self.cover.set_alpha(self.cover_alpha)
        if self.grid.ui.quit:
            self.quit_game()

    def draw(self, surface):
        self.bg.draw(surface)
        self.grid.draw(surface)
        surface.blit(self.cover, self.grid.rect)
        for label in self.labels:
            label.draw(surface)
        self.grid.ui.draw(surface)
        surface.blit(prepare.GFX["crystal-frame"], (0, 0))
        surface.blit(prepare.GFX["crystal-frame2"], (374, 0))


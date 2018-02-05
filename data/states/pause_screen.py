import pygame as pg

from .. import tools, prepare
from ..components.labels import Label
from ..components.animation import Animation, Task
from ..components.ui import StainedGlass, ScreenBackground


class PauseScreen(tools._State):
    def __init__(self):
        super(PauseScreen, self).__init__()
        self.bg = ScreenBackground(prepare.GFX["bg-screen"],
                    [(0, 0, 378, 150),(904, 4, 371, 544)])

    def startup(self, persistent):
        self.animations = pg.sprite.Group()
        self.persist = persistent
        self.grid = self.persist["grid"]
        self.make_labels()
        self.cover_alpha = 0
        self.leaving = False
        self.make_cover()

        self.bg.clear(pg.display.get_surface())

    def make_labels(self):
        self.labels = pg.sprite.Group()
        cx, cy = self.grid.rect.centerx, self.grid.rect.centery
        dist = 400
        duration = 750
        delay= 750
        space = 0
        colors= [(0, 227, 255), (236, 230, 255),
                    (255, 120, 255), (236, 230, 255)]
        self.label1 = StainedGlass((cx, (cy - space) - dist),
                    prepare.GFX["word-pause"], prepare.GFX["cover-pause"],
                    colors, 80, 1000, self.labels)
        ani = Animation(bottom=cy-space, duration=duration, delay=delay,
                    round_values=True, transition="out_bounce")
        ani.start(self.label1.rect)
        self.animations.add(ani)
        Label("Press Space to resume",
                    {"midtop": (self.grid.rect.centerx, self.grid.rect.bottom + 38)},
                    self.labels, font_size=36,
                    font_path=prepare.FONTS["vipond_octic"],
                    text_color="antiquewhite")

    def make_cover(self):
        self.cover = pg.Surface(self.grid.background.image.get_size())
        self.cover.blit(self.grid.background.image, (0, 0))
        self.cover.set_alpha(self.cover_alpha)
        duration = 1500
        ani = Animation(cover_alpha=255, duration=duration)
        ani.start(self)
        self.animations.add(ani)

    def unpause(self):
        leave = Task(self.to_game, 1500)
        duration = 750
        dist = 800
        delay = 500
        ani = Animation(top=self.label1.rect.top - dist, duration=duration,
                    round_values=True, transition="in_back", delay=delay)
        ani.start(self.label1.rect)
        self.animations.add(leave, ani)

    def to_game(self):
        self.persist["new board"] = True
        self.done = True
        self.next = "GAMEPLAY"

    def get_event(self,event):
        if event.type == pg.QUIT:
            self.quit = True
        if event.type == pg.KEYUP:
            if event.key == pg.K_SPACE:
                self.unpause()

    def update(self, dt):
        self.animations.update(dt)
        self.labels.update(dt)


        if self.cover is not None:
            self.cover.blit(self.grid.background.image, (0, 0))
            self.cover.set_alpha(self.cover_alpha)
        if self.grid.ui.quit:
            self.quit_game()

    def draw(self, surface):
        self.bg.draw(surface)
        self.grid.draw(surface)
        surface.blit(self.cover, self.grid.rect)
        self.labels.draw(surface)
        self.grid.ui.draw(surface)
        surface.blit(prepare.GFX["crystal-frame"], (0, 0))
        surface.blit(prepare.GFX["crystal-frame2"], (374, 0))


from itertools import cycle

import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, Blinker
from ..components.animation import Animation, Task
from ..components.ui import ScreenBackground


class ClearBonus(tools._State):
    def __init__(self):
        super(ClearBonus, self).__init__()
        self.remove_time = 250
        self.bg = ScreenBackground(prepare.GFX["bg-screen"],
                    [(0, 0, 378, 150),(904, 4, 371, 544)])

    def startup(self, persistent):
        self.animations = pg.sprite.Group()
        self.persist = persistent
        self.grid = self.persist["grid"]
        self.grid.bonus = self.grid.max_bonus // 2
        color = self.persist["bonus color"]
        gem_num = self.persist["gem num"]
        self.to_remove = []
        for cell in self.grid.cells.values():
            if cell.jewel is None:
                continue
            if cell.jewel.color == color and cell.jewel.gem_num == gem_num:
                self.to_remove.append(cell)
        self.timer = 0
        self.jewel_count = 0
        self.bg.clear(pg.display.get_surface())

    def remove_jewel(self):
        try:
            cell = self.to_remove.pop()
        except IndexError:
            return
        cell.jewel = None
        self.jewel_count += 1
        num = self.jewel_count
        if num > 21:
            num = 1
        prepare.SFX["jewel-note{}".format(num)].play()
        self.grid.add_points_label(cell.rect.center, 10 * self.grid.level)

    def to_gameplay(self):
        self.done = True
        self.persist["fade in"] = False
        self.next = "GAMEPLAY"

    def update(self, dt):
        self.animations.update(dt)


        if self.to_remove:
            self.grid.points_animations.update(dt)
            for label in self.grid.points_labels:
                label.image.set_alpha(label.alpha)
            self.grid.spin_jewels(dt)
            self.grid.background.update(dt)
            self.grid.ui.update(dt, self.grid)
            self.timer += dt
            if self.timer >= self.remove_time:
                self.timer -= self.remove_time
                self.remove_jewel()
        else:
            self.grid.update(dt)
            if not self.grid.animations:
                task = Task(self.to_gameplay, 1000)
                self.animations.add(task)
        if self.grid.ui.quit:
            self.quit_game()

    def draw(self, surface):
        self.bg.draw(surface)
        self.grid.draw(surface)
        self.grid.ui.draw(surface)
        surface.blit(prepare.GFX["crystal-frame"], (0, 0))
        surface.blit(prepare.GFX["crystal-frame2"], (374, 0))
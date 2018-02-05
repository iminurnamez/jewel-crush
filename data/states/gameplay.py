from random import randint

import pygame as pg

from .. import tools, prepare
from ..components.angles import get_distance
from ..components.animation import Animation
from ..components.labels import Label, Button, ButtonGroup
from ..components.grid import TileGrid
from ..components.ui import ScreenBackground


class Gameplay(tools._State):
    def __init__(self):
        super(Gameplay, self).__init__()
        self.color_scheme = 1
        self.animations = pg.sprite.Group()
        self.bg = ScreenBackground(prepare.GFX["bg-screen"],
                    [(0, 0, 378, 150),(904, 4, 371, 544)])

    def startup(self, persistent):
        self.persist = persistent
        if self.persist["new game"]:
            self.grid = TileGrid((384, 9), 8, 8, (64, 64), self.color_scheme)
            self.persist["new game"] = False
        elif self.persist["new board"]:
            self.grid.fill_board()
            self.grid.reset()
            self.persist["new board"] = False
        elif self.persist["saved"]:
            s = self.persist["saved"]
            self.grid = TileGrid(s["topleft"], s["num_rows"], s["num_columns"],
                        (64, 64), s["color_scheme_num"], s)
            self.persist["saved"] = None
        self.grabbed = None
        self.dest_tile = None
        self.last_click = 0
        self.click_cooldown = 250
        if self.persist["fade in"]:
            self.fade_in()
        else:
            self.cover_alpha = 0
        self.persist["fade in"] = True
        self.bg.clear(pg.display.get_surface())
        self.pause_label = Label("Press Space To pause",
                    {"midtop": (self.grid.rect.centerx, self.grid.rect.bottom + 38)},
                    font_size=36, font_path=prepare.FONTS["vipond_octic"],
                    text_color="antiquewhite")

    def fade_in(self):
        self.cover = pg.Surface(self.grid.background.image.get_size())
        self.cover.blit(self.grid.background.image, (0, 0))
        self.cover_alpha = 255
        ani = Animation(cover_alpha=0, duration=1000)
        ani.start(self)
        self.animations.add(ani)

    def quit_game(self, *args):
        self.grid.save()
        self.quit = True

    def pause(self):
        self.done = True
        self.next = "PAUSE_SCREEN"
        self.persist["grid"] = self.grid

    def get_event(self,event):
        if event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.quit_game()
            elif event.key == pg.K_SPACE:
                self.pause()
        elif event.type == pg.MOUSEBUTTONDOWN:
            if self.last_click < self.click_cooldown:
                return
            else:
                self.last_click = 0
            for cell in self.grid.cells.values():
                if cell.rect.collidepoint(event.pos) and cell.jewel is not None:
                    self.grabbed = cell
                    self.grid.score_multiplier = 1
                    self.grab_point = (event.pos[0] - self.grabbed.jewel.rect.left,
                                event.pos[1] - self.grabbed.jewel.rect.top)
        elif event.type == pg.MOUSEBUTTONUP:
            if self.grabbed:
                if self.dest_tile is not None and self.dest_tile.jewel is None:
                    self.grid.reseat_jewel(self.grabbed)
                    return
                valid = self.grid.check_move(self.grabbed, self.dest_tile)
                if valid:
                    self.swap_tiles(self.grabbed, self.dest_tile)
                else:
                    self.grid.reseat_jewel(self.grabbed)
                    self.grid.reseat_jewel(self.dest_tile)
                self.grabbed = None
        self.grid.ui.get_event(event)

    def swap_tiles(self, grabbed_tile, tile2):
        gj = grabbed_tile.jewel
        dj = tile2.jewel
        speed = 3.5
        dist = get_distance(gj.rect.topleft, tile2.rect.topleft)
        if dist != 0:
            duration = int(speed * dist)
            ani = Animation(left=tile2.rect.left, top=tile2.rect.top,
                        duration=duration, round_values=True)
            ani.start(gj.rect)
            ani2 = Animation(left=grabbed_tile.rect.left, top=grabbed_tile.rect.top,
                        duration=duration, round_values=True)
            ani2.start(dj.rect)
            self.grid.animations.add(ani, ani2)
        tile2.jewel = gj
        grabbed_tile.jewel = dj
        self.grid.recheck = True

    def update(self, dt):
        self.last_click += dt
        self.animations.update(dt)
        if self.cover_alpha:
            self.cover.set_alpha(self.cover_alpha)
        if self.grabbed:
            current_dest = self.dest_tile
            jewel = self.grabbed.jewel
            if jewel is None:
                self.grabbed = None
                return
            gr = self.grabbed.rect
            neighbors = self.grabbed.neighbors
            x, y = pg.mouse.get_pos()
            jewel.rect.left = x - self.grab_point[0]
            jewel.rect.top = y - self.grab_point[1]
            dx = abs(jewel.rect.left - self.grabbed.rect.left)
            dy = abs(jewel.rect.top - self.grabbed.rect.top)
            if dx >= dy:
                if jewel.rect.left < gr.left:
                    if neighbors["left"] is not None:
                        jewel.rect.left = max(jewel.rect.left, neighbors["left"].rect.left)
                        self.dest_tile = neighbors["left"]
                        if self.dest_tile.jewel is not None:
                            right = gr.left + (self.dest_tile.rect.right - jewel.rect.left)
                            self.dest_tile.jewel.rect.right = right
                    else:
                        jewel.rect.left = gr.left
                elif jewel.rect.right > gr.right:
                    if neighbors["right"] is not None:
                        jewel.rect.right = min(jewel.rect.right, neighbors["right"].rect.right)
                        self.dest_tile = neighbors["right"]
                        if self.dest_tile.jewel is not None:
                            self.dest_tile.jewel.rect.left = gr.right - (jewel.rect.right - self.dest_tile.rect.left)
                    else:
                        jewel.rect.right = gr.right
                jewel.rect.top = gr.top
            else:
                if jewel.rect.top < gr.top:
                    if neighbors["up"] is not None:
                        jewel.rect.top = max(jewel.rect.top, neighbors["up"].rect.top)
                        self.dest_tile = neighbors["up"]
                        if self.dest_tile.jewel is not None:
                            self.dest_tile.jewel.rect.bottom = gr.top - (jewel.rect.top - self.dest_tile.rect.bottom)
                    else:
                        jewel.rect.top = gr.top
                elif jewel.rect.bottom > gr.bottom:
                    if neighbors["down"] is not None:
                        jewel.rect.bottom = min(jewel.rect.bottom, neighbors["down"].rect.bottom)
                        self.dest_tile = neighbors["down"]
                        if self.dest_tile.jewel is not None:
                            self.dest_tile.jewel.rect.top = gr.bottom - (jewel.rect.bottom - self.dest_tile.rect.top)
                    else:
                        jewel.rect.bottom = gr.bottom
                jewel.rect.left = gr.left
            if current_dest is not None and current_dest != self.dest_tile:
                if current_dest.jewel is not None:
                    current_dest.jewel.rect.topleft = current_dest.rect.topleft

        self.grid.bonus -= self.grid.bonus_cooldown * dt
        if self.grid.bonus <= 0:
            self.grid.done = True

        self.grid.update(dt)
        if self.grid.bonus >= self.grid.max_bonus:
            self.done = True
            self.next = "BONUS_SCREEN"
            self.persist["grid"] = self.grid
        elif self.grid.done:
            self.persist["color_scheme_num"] = self.grid.color_scheme_num
            self.persist["score"] = self.grid.score
            self.persist["elapsed"] = self.grid.elapsed
            self.grid.ui.bonus_bar.stop()
            self.done = True
            self.next = "GAMEOVER"
        elif self.grid.no_moves:
            self.done = True
            self.persist["grid"] = self.grid
            self.next = "NO_MOVES"
        elif self.grid.score >= self.grid.level_targets[self.grid.level]:
            self.done = True
            self.next = "LEVELUP"
            self.persist["grid"] = self.grid
        if self.grid.ui.quit:
            self.quit_game()

    def draw(self, surface):
        self.bg.draw(surface)
        self.pause_label.draw(surface)
        self.grid.draw(surface)
        if self.grabbed is not None and self.grabbed.jewel is not None:
            self.grabbed.jewel.draw(surface)
        if self.cover_alpha:
            surface.blit(self.cover, self.grid.rect.topleft)
        self.grid.ui.draw(surface)
        surface.blit(prepare.GFX["crystal-frame"], (0, 0))
        surface.blit(prepare.GFX["crystal-frame2"], (374, 0))

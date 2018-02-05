import os
from random import randint
from itertools import cycle
import json

import pygame as pg

from .. import tools, prepare
from ..components.angles import get_distance
from ..components.animation import Animation
from ..components.labels import Label, Blinker, Button, ButtonGroup


class ScreenSprite(pg.sprite.Sprite):
    def __init__(self,center, image, *groups):
        super(ScreenSprite, self).__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect(center=center)


class GridUI(object):
    def __init__(self, grid):
        topleft = (grid.rect.left - 1, grid.rect.bottom + 9)
        self.bonus_bar = BonusBar(topleft, grid.bonus, grid.max_bonus)
        self.high_scores_table = HighScoresTable(pg.Rect(904, 128, prepare.SCREEN_RECT.right - 904, 500), grid.score)
        self.make_labels(grid)
        self.quit = False
        self.buttons = ButtonGroup()
        img = prepare.GFX["icon-close"]
        Button({"topright": (prepare.SCREEN_RECT.right -10, 10)},
                    self.buttons, idle_image=img, button_size=img.get_size(),
                    call=self.quit_game)
        self.volume_slider = VolumeSlider((910, 20))

    def quit_game(self, *args):
        self.quit = True

    def make_labels(self, grid):
        self.labels = pg.sprite.Group()
        self.level_label = Label("Level {}".format(grid.level),
                    {"midtop": (182, 16)}, self.labels, font_size=64)
        self.score_label = Label("{}".format(grid.score),
                    {"midtop": (182, 64)}, self.labels, font_size=48)
        target = grid.level_targets[grid.level]
        self.next_level_label = Label("Next Level {}".format(target),
                    {"midtop": (182, 128)}, self.labels, font_size=24)


    def get_event(self, event):
        self.buttons.get_event(event)
        self.volume_slider.get_event(event)

    def update(self, dt, grid):
        self.buttons.update(pg.mouse.get_pos())
        level = "Level {}".format(grid.level)
        score = "{}".format(grid.score)
        next_level = "Next Level {}".format(grid.level_targets[grid.level])
        if self.level_label.text != level:
            self.level_label.set_text(level)
        if self.score_label.text != score:
            self.score_label.set_text(score)
        if self.next_level_label.text != next_level:
            self.next_level_label.set_text(next_level)
        self.bonus_bar.update(dt, grid.bonus)
        self.high_scores_table.update(dt, grid.score)
        self.volume_slider.update()

    def draw(self, surface):
        self.labels.draw(surface)
        self.buttons.draw(surface)
        self.bonus_bar.draw(surface)
        self.high_scores_table.draw(surface)
        self.volume_slider.draw(surface)


class HighScoresTable(pg.sprite.Sprite):
    def __init__(self, rect, player_score, *groups):
        super(HighScoresTable, self).__init__(*groups)
        self.rect = rect
        self.image = pg.Surface(self.rect.size).convert_alpha()
        self.title = Label("High Scores",
                    {"midtop": (self.rect.centerx, self.rect.top + 8)},
                    font_size=48, font_path=prepare.FONTS["vipond_octic"])
        self.player_score = self.last_score = player_score
        self.saved_scores = self.load_saved_scores()
        self.make_high_score_labels(self.saved_scores)

    def load_saved_scores(self):
        p = os.path.join("resources", "high_scores.json")
        try:
            with open(p, "r") as f:
                scores = json.load(f)
        except IOError:
            scores = []
        ranked = sorted(scores, reverse=True)
        return ranked

    def update_scores(self, player_score):
        self.player_score = player_score

        if self.player_score != self.last_score:
            ranked = self.saved_scores[:]
            if len(self.saved_scores) < 10 or self.player_score >= ranked[-1]:
                ranked.append(self.player_score)
            ranked = sorted(ranked, reverse=True)[:10]
            self.make_high_score_labels(ranked)
        self.last_score = self.player_score

    def make_high_score_labels(self, scores):
        self.score_labels = pg.sprite.Group()
        top = self.rect.top + 60
        right = self.rect.right - 16
        current = None
        for score in scores:
            if score == self.player_score and current is None:
                Blinker("{}".format(score), {"topright": (right, top)}, 500,
                            self.score_labels, font_size=40)
                current = True
            else:
                Label("{}".format(score), {"topright": (right, top)},
                            self.score_labels, font_size=40)
            top += 35

    def update(self, dt, score):
        self.score_labels.update(dt)
        self.update_scores(score)

    def draw(self, surface):
        self.title.draw(surface)
        self.score_labels.draw(surface)


class BonusBar(pg.sprite.Sprite):
    def __init__(self, topleft, value, max_value):
        self.animations = pg.sprite.Group()
        self.value = value
        self.max_value = max_value
        self.rect = pg.Rect(topleft, (514, 18))
        self.bg_color = "gray20"
        colors= [(0, 227, 255), (236, 230, 255),
                    (255, 120, 255), (236, 230, 255)]
        self.colors = cycle(colors)
        self.color_change_duration = 1000
        self.color = self.draw_color = next(self.colors)
        self.next_color = next(self.colors)
        self.change_color()
        self.image = pg.Surface(self.rect.size)
        self.bar_image = pg.Surface(self.rect.size)
        self.bar_image.set_colorkey((0, 0, 0))
        self.make_image()
        self.warning_sounds = {
                    x: prepare.SFX["jewel-warning{}".format(x)]
                    for x in range(1, 5)}
        self.warning_sound_num = None

    def stop(self):
        for sound in self.warning_sounds.values():
            sound.stop()

    def change_color(self):
        self.color = self.next_color
        self.next_color = next(self.colors)
        self.lerp_val = 0
        ani = Animation(lerp_val=1, duration=self.color_change_duration)
        ani.start(self)
        ani.callback = self.change_color
        self.animations.add(ani)

    def make_image(self):
        self.image.fill((0, 0, 0))
        w = int((self.value / float(self.max_value)) * self.rect.w)
        self.bar_image.fill((0, 0, 0))
        pg.draw.rect(self.bar_image, pg.Color(*self.draw_color),
                    (0, 0, w, self.rect.h))

    def update(self, dt, value):
        self.animations.update(dt)
        self.draw_color = tools.lerp(self.color,
                    self.next_color, self.lerp_val)
        self.value = value
        self.make_image()
        val = self.value / float(self.max_value)
        if val >= .2:
            self.stop()
            self.warning_sound_num = None
        else:
            new_num = None
            if val < .05:
                if self.warning_sound_num != 4:
                    new_num = 4
            elif val < .1:
                if self.warning_sound_num != 3:
                    new_num = 3
            elif val < .15:
                if self.warning_sound_num != 2:
                    new_num = 2
            elif self.warning_sound_num != 1:
                new_num = 1
            if new_num is not None:
                self.stop()
                self.warning_sound_num = new_num
                self.warning_sounds[self.warning_sound_num].play(-1)

    def draw(self, surface):
        surface.blit(self.bar_image, self.rect)


class VolumeSlider(pg.sprite.Sprite):
    def __init__(self, topleft, *groups):
        self.muted = False
        self.sounds = {x: prepare.SFX["jewel-{}note".format(x)]
                    for x in range(3, 9)}
        self.icon = prepare.GFX["icon-speaker"]
        self.muted_icon = prepare.GFX["icon-muted"]
        self.icon_rect = self.icon.get_rect(topleft=topleft)
        self.slider_image = prepare.GFX["slider"]
        self.slider_box = pg.Rect(self.icon_rect.right + 8, 0, 256, 16)
        self.slider_box.centery =  self.icon_rect.centery
        self.slider_rect = self.slider_image.get_rect(
                    center=self.slider_box.center)
        self.volume = 0.
        self.set_volume()
        self.grabbed = False
        self.grab_point = None

    def get_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.slider_rect.collidepoint(event.pos):
                self.grabbed = True
                self.grab_point = (event.pos[0] - self.slider_rect.left,
                            event.pos[1] - self.slider_rect.top)
        elif event.type == pg.MOUSEBUTTONUP:
            self.grabbed = False
            if self.icon_rect.collidepoint(event.pos):
                self.muted = not self.muted

    def set_volume(self):
        rect, box = self.slider_rect, self.slider_box
        volume = (rect.left - box.left) / float(box.w - rect.w)
        if self.muted:
            volume = 0
        if volume != self.volume:
            for s in prepare.SFX.values():
                s.set_volume(volume)
            self.volume = volume

    def update(self):
        if self.grabbed:
            mx, my = pg.mouse.get_pos()
            left = mx -  self.grab_point[0]
            self.slider_rect.left = min(max(self.slider_box.left, left),
                        self.slider_box.right - self.slider_rect.w)
        self.set_volume()

    def draw(self, surface):
        icon = self.icon
        if self.muted:
            icon = self.muted_icon
        surface.blit(icon, self.icon_rect)
        pg.draw.line(surface, pg.Color("white"), self.slider_box.midleft,
                    self.slider_box.midright, 2)
        surface.blit(self.slider_image, self.slider_rect)


class ScreenBackground(object):
    def __init__(self, image, rects):
        self.image = image
        self.images = [(image.subsurface(rect), pg.Rect(rect))
                    for rect in rects]

    def clear(self, surface):
        surface.blit(self.image, (0, 0))

    def draw(self, surface):
        for image, rect in self.images:
            surface.blit(image, rect)


class BouncingBackground(pg.sprite.Sprite):
    def __init__(self, topleft, view_size, image, speed, *groups):
        super(BouncingBackground, self).__init__(*groups)
        self.speed = speed
        self.base_image = image.convert_alpha()
        self.base_rect = self.base_image.get_rect()
        self.rect = pg.Rect(topleft, view_size)
        self.bounce_rect = self.rect.copy()
        self.bounce_rect.center = self.base_rect.center
        self.image = self.base_image.subsurface(self.bounce_rect)
        self.animations = pg.sprite.Group()

    def update(self, dt):
        self.animations.update(dt)
        clamped = self.bounce_rect.clamp(self.base_rect)
        if clamped != self.bounce_rect or not self.animations:
            self.bounce_rect = clamped
            self.random_destination()
        self.image = self.base_image.subsurface(self.bounce_rect)

    def random_destination(self):
        self.animations.empty()
        x = randint(0, self.base_rect.w - self.rect.w)
        y = randint(0, self.base_rect.h - self.rect.h)
        dist = get_distance(self.bounce_rect.topleft, (x, y))
        ani = Animation(left=x, top=y, duration=dist*self.speed)
        ani.start(self.bounce_rect)
        self.animations.add(ani)

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class StainedGlass(pg.sprite.Sprite):
    def __init__(self, center, image, cover_image, colors, alpha,
                color_change_duration, *groups):
        super(StainedGlass, self).__init__(*groups)
        self.animations = pg.sprite.Group()
        self.frame = image
        self.rect = self.frame.get_rect(center=center)
        self.image = pg.Surface(self.rect.size).convert_alpha()
        self.cover = cover_image
        self.surf = pg.Surface(self.rect.size)
        self.surf.set_colorkey((0, 0 ,0, 255))
        self.alpha = alpha
        self.surf.set_alpha(self.alpha)
        self.colors = cycle(colors)
        self.color_change_duration = color_change_duration
        self.color = next(self.colors)
        self.next_color = next(self.colors)
        self.last_draw_color = None
        self.change_color()

    def change_color(self):
        self.color = self.next_color
        self.next_color = next(self.colors)
        self.lerp_val = 0
        ani = Animation(lerp_val=1, duration=self.color_change_duration)
        ani.start(self)
        ani.callback = self.change_color
        self.animations.add(ani)

    def make_image(self, draw_color):
        self.surf.fill(draw_color)
        self.surf.blit(self.cover, (0, 0))
        self.surf.set_alpha(self.alpha)
        self.image.fill((0,0,0,0))
        self.image.blit(self.surf, (0, 0))
        self.image.blit(self.frame, (0, 0))

    def update(self, dt):
        self.animations.update(dt)
        draw_color = tools.lerp(self.color, self.next_color, self.lerp_val)
        if draw_color != self.last_draw_color:
            self.make_image(draw_color)
            self.last_draw_color = draw_color

    def draw(self, surface):
        surface.blit(self.image, self.rect)


import os
from itertools import cycle
import json

import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, Button, ButtonGroup, Blinker
from ..components.animation import Animation
from ..components.grid import BouncingBackground
from ..components.ui import StainedGlass


class GameOver(tools._State):
    def __init__(self):
        super(GameOver, self).__init__()
        self.font = prepare.FONTS["vipond_angular"]
        self.bg_num = 1
        self.background = BouncingBackground((0, 0), prepare.SCREEN_SIZE,
                    prepare.GFX["bg-big"], 40)

    def startup(self, persistent):
        self.animations = pg.sprite.Group()
        self.persist = persistent

        colors= [(0, 227, 255), (236, 230, 255),
                    (255, 120, 255), (236, 230, 255)]
        self.title = StainedGlass((prepare.SCREEN_RECT.centerx, 64),
                    prepare.GFX["word-gameover"], prepare.GFX["cover-gameover"],
                    colors, 80, 500)
        self.score = self.persist["score"]
        elapsed = self.persist["elapsed"]
        minutes = elapsed / 60000.
        try:
            per_minute = self.score / float(minutes)
        except ZeroDivisionError:
            per_minute = 0
        self.high_scores = self.load_high_scores()
        self.labels = pg.sprite.Group()
        self.buttons = ButtonGroup()
        cx = prepare.SCREEN_RECT.centerx
        Label("SCORE", {"midtop": (cx, 110)}, self.labels, font_size=64)
        Label("{}".format(self.score), {"midtop": (cx, 160)},
                    self.labels, font_size=32)
        Button({"midleft": (cx + 20, 650)}, self.buttons, button_size=(256, 64),
                   call=self.play_again, idle_image=prepare.GFX["button-play"])
        Button({"midright": (cx - 20, 650)}, self.buttons, button_size=(256,64),
                   call=self.quit_game, idle_image=prepare.GFX["button-quit"])
        self.make_high_score_labels(self.high_scores)

    def make_high_score_labels(self, scores):
        Label("High Scores", {"midtop": (prepare.SCREEN_RECT.centerx, 195)},
                    self.labels, font_size=64)
        top = 260
        cx = prepare.SCREEN_RECT.centerx
        current = None
        for score in scores:
            if score == self.score and current is None:
                Blinker("{}".format(score), {"center": (cx, top)}, 500,
                            self.labels, font_size=32)
                current = True
            else:
                Label("{}".format(score), {"center": (cx, top)},
                            self.labels, font_size=32)
            top += 35

    def load_high_scores(self):
        p = os.path.join("resources", "high_scores.json")
        try:
            with open(p, "r") as f:
                scores = json.load(f)
        except IOError:
            scores = []
        ranked = sorted(scores, reverse=True)
        if len(ranked) < 10 or self.score >= ranked[-1]:
            ranked.append(self.score)
        ranked = sorted(ranked, reverse=True)[:10]
        self.save_high_scores(ranked)
        return ranked

    def save_high_scores(self, scores):
        p = os.path.join("resources", "high_scores.json")
        with open(p, "w") as f:
            json.dump(scores, f)

    def quit_game(self, *args):
        self.done = True
        self.quit = True

    def get_event(self,event):
        if event.type == pg.QUIT:
            self.quit = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.quit = True
        self.buttons.get_event(event)

    def play_again(self, *args):
        self.done = True
        self.persist["new game"] = True
        self.next = "GAMEPLAY"

    def update(self, dt):
        self.animations.update(dt)
        self.labels.update(dt)
        self.background.update(dt)
        self.buttons.update(pg.mouse.get_pos())
        self.title.update(dt)

    def draw(self, surface):
        self.background.draw(surface)
        self.title.draw(surface)
        self.labels.draw(surface)
        self.buttons.draw(surface)
        surface.blit(prepare.GFX["crystal-frame"], (0, 0))
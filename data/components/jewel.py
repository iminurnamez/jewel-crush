from itertools import cycle
from random import randint

import pygame as pg

from .. import tools, prepare


class Jewel(pg.sprite.Sprite):
    def __init__(self, topleft, color, gem_num, *groups):
        super(Jewel, self).__init__(*groups)
        self.color = color
        self.gem_num = gem_num
        self.images = prepare.JEWELS[color][gem_num]
        self.image = self.images[0]
        self.rect = self.image.get_rect(topleft=topleft)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
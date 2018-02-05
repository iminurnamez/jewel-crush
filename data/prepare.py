import os
import pygame as pg
from . import tools


SCREEN_SIZE = (1280, 720)
ORIGINAL_CAPTION = "Game"

pg.mixer.pre_init(44100, -16, 1, 512)

pg.init()
os.environ['SDL_VIDEO_CENTERED'] = "TRUE"
pg.display.set_caption(ORIGINAL_CAPTION)
SCREEN = pg.display.set_mode(SCREEN_SIZE, pg.NOFRAME)
SCREEN_RECT = SCREEN.get_rect()

FONTS = tools.load_all_fonts(os.path.join("resources", "fonts"))
MUSIC = tools.load_all_music(os.path.join("resources", "music"))
SFX   = tools.load_all_sfx(os.path.join("resources", "sound"))
GFX   = tools.load_all_gfx(os.path.join("resources", "graphics"))
SCREEN.blit(GFX["crystal-frame"], (0, 0))
pg.display.update()

JEWELS = {}
JEWEL_COLORS = ["blue", "pink", "clear"]
p = os.path.join("resources", "jewels")
for color in JEWEL_COLORS:
    JEWELS[color] = {}
    d_path = os.path.join(p, color)
    for i in [1, 3, 4, 5]:
        imgs  = tools.load_all_gfx(os.path.join(d_path, "gem{}".format(i)))
        JEWELS[color][i] = [imgs["000{}".format(x)] for x in range(1, 10)]
        limit = 61
        if i == 5:
            limit = 31
        JEWELS[color][i].extend(
                    [imgs["00{}".format(x)] for x in range(10, limit)])
        if i == 5:
            JEWELS[color][i].extend(JEWELS[color][i])

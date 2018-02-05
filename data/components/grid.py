import os
from random import choice, shuffle
from itertools import cycle
import json

import pygame as pg

from .. import prepare
from ..components.angles import get_distance
from ..components.animation import Animation, Task
from ..components.labels import Label
from ..components.jewel import Jewel
from ..components.grid_funcs import find_repeats
from ..components.ui import GridUI, BouncingBackground


JEWEL_COLORS = ["blue", "pink", "clear"]
JEWEL_NUMS = [1, 4, 5, 3]
JEWEL_COMBOS = {}
JEWEL_COMBOS = [(color, num) for color in JEWEL_COLORS
            for num in JEWEL_NUMS]
ANI_SPEED = 4


class GridCell(object):
    def __init__(self, topleft, index, size):
        self.index = index
        w, h = size
        self.rect = pg.Rect(topleft[0] + (w * index[0]),
                    topleft[1] + (h *index[1]), w, h)
        self.jewel = None

    def get_neighbor_cells(self, grid):
        offsets = {
            "left": (self.index[0] - 1, self.index[1]),
            "right": (self.index[0] + 1, self.index[1]),
            "up": (self.index[0], self.index[1] - 1),
            "down": (self.index[0], self.index[1] + 1)}
        self.neighbors = {}
        for off in offsets:
            self.neighbors[off] = grid[offsets[off]] if offsets[off] in grid else None

    def send_jewel(self, new_cell, animations):
        dist = new_cell.rect.top - self.rect.top
        ani = Animation(top=new_cell.rect.top, left=new_cell.rect.left,
                    duration=int(dist*ANI_SPEED), round_values=True)
        ani.start(self.jewel.rect)
        animations.add(ani)
        new_cell.jewel = self.jewel
        self.jewel = None


class TileGrid(object):
    level_targets = {x: 2500 * (2**(x-1)) for x in range(1, 20)}

    def __init__(self, topleft, num_rows, num_columns, cell_size,
                color_scheme_num, saved=None):
        self.topleft = topleft
        self.num_rows = num_rows
        self.num_columns = num_columns
        self.color_scheme_num = color_scheme_num
        self.rect = pg.Rect(topleft,
                    (num_columns * cell_size[0], num_rows * cell_size[1]))
        self.reset()
        self.recheck = False
        if saved is None:
            self.score = 0
            self.elapsed = 0
            self.max_bonus = 1000
            self.bonus = int(self.max_bonus * .5)
            self.bonus_cooldown = .01
            self.level = 1
            self.num_combos = 6
            self.jewel_combos = self.make_combos()
            self.make_cells(cell_size)
            self.fill_board()
        else:
            self.num_combos = saved["num combos"]
            self.jewel_combos = saved["jewel combos"]
            self.score = saved["score"]
            self.elapsed = saved["elapsed"]
            self.bonus = saved["bonus"]
            self.max_bonus = saved["max bonus"]
            self.bonus_cooldown = saved["bonus cooldown"]
            self.level = saved["level"]
            self.make_cells(cell_size)
            self.load_cells(saved["jewel cells"])

        self.animations = pg.sprite.Group()
        self.points_labels = pg.sprite.Group()
        self.points_animations = pg.sprite.Group()
        self.spin_animations = pg.sprite.Group()
        self.background = BouncingBackground(self.rect.topleft,
                    (self.rect.w, self.rect.h + 32),
                    prepare.GFX["bg-jewels"], 60)
        self.ui = GridUI(self)

    def save(self):
        saved = {
                "topleft": self.topleft,
                "num_rows": self.num_rows,
                "num_columns": self.num_columns,
                "color_scheme_num": self.color_scheme_num,
                "jewel combos": self.jewel_combos,
                "num combos": self.num_combos,
                "score": self.score,
                "elapsed": self.elapsed,
                "bonus": self.bonus,
                "max bonus": self.max_bonus,
                "bonus cooldown": self.bonus_cooldown,
                "level": self.level}
        jewel_cells = []
        for indx, cell in self.cells.items():
            if cell.jewel is not None:
                jewel_cells.append((indx, cell.jewel.color, cell.jewel.gem_num))
        saved["jewel cells"] = jewel_cells
        p = os.path.join("resources", "saved.json")
        with open(p, "w") as f:
            json.dump(saved, f)

    def load_cells(self, cells):
        for indx, color, gem_num in cells:
            cell = self.cells[tuple(indx)]
            cell.jewel = Jewel(cell.rect.topleft, color, gem_num)

    def make_cells(self, cell_size):
        self.cells = {(x, y): GridCell(self.topleft, (x, y), (cell_size))
                         for x in range(self.num_columns)
                         for y in range(self.num_rows)}
        for cell in self.cells:
            self.cells[cell].get_neighbor_cells(self.cells)
        self.rows = []
        for y in range(self.num_rows):
            row = []
            for x in range(self.num_columns):
                row.append(self.cells[(x, y)])
            self.rows.append(row)
        self.columns = []
        for x in range(self.num_columns):
            column = []
            for y in range(self.num_rows):
                column.append(self.cells[(x, y)])
            self.columns.append(column)

    def reset(self):
        self.done = False
        self.no_moves = False
        self.spin_speed = 100
        self.spin_timer = 0
        self.spin_index = 0
        self.spin_time = 500
        self.max_spin_index = 59
        self.score_multiplier = 1

    def make_combos(self):
        colors = JEWEL_COLORS[:]
        shuffle(colors)
        colors = cycle(colors)
        nums = cycle(JEWEL_NUMS)

        combos = []
        for _ in range(self.num_combos):
            combos.append((next(colors), next(nums)))
        return combos

    def fill_board(self):
        for cell in self.cells.values():
            color, num = choice(self.jewel_combos)
            cell.jewel = Jewel(cell.rect.topleft, color, num)
        while True:
            matches = self.find_all_matches()
            if not matches:
                break
            for match in matches:
                for indx in match:
                    color, num = choice(self.jewel_combos)
                    c = self.cells[indx]
                    c.jewel = Jewel(c.rect.topleft, color, num)

    def fill_jewels(self):
        for cell in self.rows[0]:
            if cell.jewel is None:
                topleft = cell.rect.left, cell.rect.top - cell.rect.height
                color, num = choice(self.jewel_combos)
                cell.jewel = Jewel(topleft,color, num)
                dist = cell.rect.top - cell.jewel.rect.top
                ani = Animation(top=cell.rect.top,
                            duration=int(dist*ANI_SPEED),
                            round_values=True)
                ani.start(cell.jewel.rect)
                self.animations.add(ani)
        self.recheck = True

    def find_row_matches(self):
        matches = []
        for i, row in enumerate(self.rows):
            colors = ((cell.jewel.color, cell.jewel.gem_num)
                        if cell.jewel else None
                        for cell in row)
            row_matches = find_repeats(colors, 3)
            for match in row_matches:
                matches.append([(row_index, i) for row_index in match])
        return matches

    def find_column_matches(self):
        matches = []
        for i, column in enumerate(self.columns):
            colors = ((cell.jewel.color, cell.jewel.gem_num)
                        if cell.jewel else None
                        for cell in column)
            column_matches = find_repeats(colors, 3)
            for match in column_matches:
                matches.append([(i, column_index) for column_index in match])
        return matches

    def find_all_matches(self):
        matches = self.find_row_matches()
        matches.extend(self.find_column_matches())
        return matches

    def clear_matches(self, matches):
        delay = 0
        for match in sorted(matches, key=len):
            length = len(match)
            points_per = 10 * (length - 2)
            score = length * points_per * self.score_multiplier * self.level
            self.score += score
            self.bonus += length * points_per
            self.score_multiplier += 1
            task = Task(self.ui.volume_slider.sounds[len(match)].play, delay)
            self.points_animations.add(task)
            delay += 250
            centers = [self.cells[m].rect.center for m in match]
            cx = sum((c[0] for c in centers)) / len(centers)
            cy = sum((c[1] for c in centers)) / len(centers)
            self.add_points_label((cx, cy), score)
            for indx in match:
                self.cells[indx].jewel = None
        if matches:
            self.spin_up(len(matches[-1]))

    def spin_up(self, num):
        self.spin_animations.empty()
        speeds = {3: 10, 4: 5, 5: 2, 6: 1, 7: 1, 8: 1}
        spin_up = Animation(spin_speed=speeds[num],
                    duration=350, round_values=True)
        spin_up.callback=self.spin_down
        spin_up.start(self)
        self.spin_animations.add(spin_up)

    def spin_down(self):
        spin = Animation(spin_speed=100, duration=3500,
                    round_values=True)
        spin.start(self)
        self.spin_animations.add(spin)

    def add_points_label(self, centerpoint, points):
        cx, cy = centerpoint
        label = Label("{}".format(points), {"center": (cx, cy + 20)},
                           self.points_labels, alpha=254, font_size=32,
                           text_color="gray90",
                           font_path=prepare.FONTS["vipond_octic"])
        dur = 1750
        ani = Animation(alpha=0, duration=dur, transition="in_quad")
        ani.callback = label.kill
        ani.start(label)

        ani2 = Animation(centery=cy - 20, duration=dur, round_values=True)
        ani2.start(label.rect)
        self.points_animations.add(ani, ani2)

    def find_moves(self):
        for x in range(self.num_columns):
            for y in range(self.num_rows):
                cell = self.cells[(x, y)]
                jewel = cell.jewel
                for d in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    try:
                        other = self.cells[(x + d[0], y + d[1])]
                    except KeyError:
                        continue
                    other_jewel = other.jewel
                    cell.jewel = other_jewel
                    other.jewel = jewel
                    match = self.find_all_matches()
                    cell.jewel = jewel
                    other.jewel = other_jewel
                    if match:
                        return cell.index, d

    def check_move(self, grabbed_tile, dest_tile):
        existing_matches = self.find_all_matches()
        g = grabbed_tile
        d = dest_tile
        if g is None or d is None:
            return False
        gj = grabbed_tile.jewel
        dj = dest_tile.jewel
        if gj is None or dj is None:
            return False
        g.jewel = dj
        d.jewel = gj
        valid = self.find_all_matches()
        g.jewel = gj
        d.jewel =dj
        for matched in valid:
            if matched not in existing_matches:
                return True
        return False

    def spin_jewels(self, dt):
        self.spin_timer += dt
        while self.spin_timer >= self.spin_speed:
            self.spin_index += 1
            if self.spin_index > self.max_spin_index:
                self.spin_index = 0
            self.spin_timer -= self.spin_speed

            for cell in self.cells.values():
                if cell.jewel is not None:
                    cell.jewel.image = cell.jewel.images[self.spin_index]

    def make_background(self):
        img = self.bg_image_base
        h = self.bg_image_base.get_height()
        if int(self.bg_scroll) >= h:
            self.bg_scroll = self.bg_scroll - h
        if int(self.bg_scroll) + self.rect.h > h:
            bottom_rect = pg.Rect(0, int(self.bg_scroll),
                        self.rect.w, h - int(self.bg_scroll))
            top_rect = pg.Rect(0, 0, self.rect.w,
                        self.rect.h - (h - int(self.bg_scroll)))
            self.bg_image.blit(img.subsurface(top_rect), (0, 0))
            self.bg_image.blit(img.subsurface(bottom_rect), (0, top_rect.h))
        else:
            r = pg.Rect((0, self.bg_scroll), self.rect.size)
            self.bg_image.blit(img.subsurface(r), (0, 0))

    def update(self, dt):
        self.elapsed += dt
        self.animations.update(dt)
        self.points_animations.update(dt)
        self.spin_animations.update(dt)
        for label in self.points_labels:
            label.image.set_alpha(label.alpha)
        self.spin_jewels(dt)
        self.background.update(dt)
        if not self.animations:
            self.update_cells()

            empty_cells = any(
                        (cell.jewel is None for cell in self.cells.values()))
            if empty_cells:
                self.fill_jewels()
            if not self.animations and self.recheck and not empty_cells:
                matches = self.find_all_matches()
                self.clear_matches(matches)
                if not any((cell.jewel is None for cell in self.cells.values())):
                    self.possible_matches = self.find_moves()
                    if not self.possible_matches:
                        self.no_moves = True
                self.recheck = False
        self.ui.update(dt, self)

    def level_up(self):
        self.level += 1
        if self.num_combos < 13:
            if self.level % 2:
                self.num_combos += 1
        else:
            self.bonus_cooldown += .001
        self.jewel_combos = self.make_combos()

    def swap_cells(self, cell1, cell2):
        jewel1 = cell1.jewel
        jewel2 = cell2.jewel
        cell1.jewel = jewel2
        cell1.jewel.rect.topleft = cell1.rect.topleft
        cell2.jewel = jewel1
        cell2.jewel.rect.topleft = cell2.rect.topleft

    def reseat_jewel(self, cell):
        jewel = cell.jewel
        if jewel is None:
            return
        dist = get_distance(jewel.rect.topleft, cell.rect.topleft)
        if dist > 0:
            ani = Animation(top=cell.rect.top, left=cell.rect.left,
                        duration=int(dist*3), round_values=True,
                        transition="out_bounce")
            ani.start(jewel.rect)
            self.animations.add(ani)

    def update_cells(self):
        for y in range(self.num_rows - 1, -1, -1):
            for x in range(self.num_columns):
                cell = self.cells[(x, y)]
                if cell.jewel is not None:
                    try:
                        dest = self.cells[(cell.index[0], cell.index[1] + 1)]
                        if dest.jewel is None:
                            cell.send_jewel(dest, self.animations)
                    except KeyError:
                        pass

    def draw(self, surface):
        self.background.draw(surface)
        for cell in self.cells.values():
            if cell.jewel is not None:
                cell.jewel.draw(surface)
        self.points_labels.draw(surface)
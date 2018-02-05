from . import prepare,tools
from .states import (title_screen, gameplay, game_over, no_moves_screen,
            level_up, bonus_screen, clear_bonus, pause_screen)

def main():
    controller = tools.Control(prepare.ORIGINAL_CAPTION)
    states = {"TITLE": title_screen.TitleScreen(),
                   "GAMEPLAY": gameplay.Gameplay(),
                   "GAMEOVER": game_over.GameOver(),
                   "NO_MOVES": no_moves_screen.NoMovesScreen(),
                   "LEVELUP": level_up.LevelUp(),
                   "BONUS_SCREEN": bonus_screen.BonusScreen(),
                   "CLEAR_BONUS": clear_bonus.ClearBonus(),
                   "PAUSE_SCREEN": pause_screen.PauseScreen()}
    controller.setup_states(states, "TITLE")
    controller.main()

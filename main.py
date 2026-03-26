from game import *
from pygame.locals import *

def main():
    # game = Game(player1=AlphaBeta(chess.WHITE), player2=MCTS(chess.BLACK))
    game = Game(player1=None, player2=MCTS(chess.BLACK))
    game.init_game()
    game.play()

if __name__ == "__main__":
    main()
from game import *
from pygame.locals import *
from stockfishBot import StockfishPlayer

PATH= "stockfish-windows-x86-64-sse41-popcnt\stockfish\stockfish-windows-x86-64-sse41-popcnt.exe" 

def main():
    player1= AlphaBeta(color= chess.WHITE)
    player2= StockfishPlayer(color= chess.BLACK, engine_path= PATH)
    game = Game(player1= player1, player2= player2, games= 1)
    game.init_game()
    game.play()

if __name__ == "__main__":
    main()
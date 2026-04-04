import chess.engine
from game import Player

class StockfishPlayer(Player):
    def __init__(self, color, engine_path, time_limit=0.1, skill_level=5):
        super().__init__(color)
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        # Giới hạn sức mạnh Stockfish để bot của mình có cơ hội đánh (Skill Level: 0 - 20)
        self.engine.configure({"Skill Level": skill_level, "Threads": 1})
        self.time_limit = time_limit

    def get_move(self, board):
        result = self.engine.play(board, chess.engine.Limit(time=self.time_limit))
        return result.move

    def close(self):
        self.engine.quit()
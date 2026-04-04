import chess
import chess.engine
import time
import multiprocessing
from functools import partial
from game import MCTS, AlphaBeta 
from stockfishBot import StockfishPlayer
import os, warnings
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
warnings.filterwarnings("ignore", category=UserWarning)

STOCKFISH_PATH = "stockfish-windows-x86-64-sse41-popcnt\\stockfish\\stockfish-windows-x86-64-sse41-popcnt.exe" 
MATCHES = 100
# Số luồng chạy song song (thường để bằng số nhân CPU)
PROCESSES = multiprocessing.cpu_count() 

def calculate_cpl(engine, board, move):
    """Tính Centipawn Loss (CPL) của một nước đi"""
    info_best = engine.analyse(board, chess.engine.Limit(depth=10))
    best_score = info_best["score"].white().score(mate_score=10000)

    board.push(move)
    info_actual = engine.analyse(board, chess.engine.Limit(depth=10))
    actual_score = info_actual["score"].white().score(mate_score=10000)
    board.pop()

    if board.turn == chess.BLACK:
        best_score = -best_score
        actual_score = -actual_score

    loss = best_score - actual_score
    return max(0, min(loss, 1000))

def play_single_game(game_id, bot_class):
    """Hàm chạy 1 ván đấu đơn lẻ trong một process"""
    # Khởi tạo referee riêng cho mỗi tiến trình
    referee = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    referee.configure({"Threads": 1})
    
    board = chess.Board()
    bot_color = chess.WHITE if game_id % 2 == 0 else chess.BLACK
    sf_color = chess.BLACK if game_id % 2 == 0 else chess.WHITE
    
    bot = bot_class(bot_color)
    sf = StockfishPlayer(sf_color, STOCKFISH_PATH, time_limit=0.05, skill_level=20)
    
    game_cpl = 0
    bot_moves = 0

    while not board.is_game_over():
        if board.turn == bot.color:
            move = bot.get_move(board)
            cpl = calculate_cpl(referee, board, move)
            game_cpl += cpl
            bot_moves += 1
        else:
            move = sf.get_move(board)
        
        board.push(move)

    outcome = board.outcome()
    result = 0 # 0: Hòa, 1: Bot thắng, -1: Bot thua
    if outcome.winner == bot.color:
        result = 1
    elif outcome.winner == sf_color:
        result = -1

    # Dọn dẹp
    sf.close()
    referee.quit()
    
    print(f"Game {game_id + 1}/{MATCHES} - Result: {'Bot Win' if result == 1 else 'Stockfish Win' if result == -1 else 'Draw'} - CPL: {round(game_cpl / bot_moves, 2) if bot_moves > 0 else 'N/A'}")

    return {
        "result": result,
        "total_cpl": game_cpl,
        "moves": bot_moves
    }

def run_parallel_tournament(bot_class, bot_name):
    print(f"--- BẮT ĐẦU TEST SONG SONG: {bot_name} ({MATCHES} VÁN) ---")
    print(f"Sử dụng {PROCESSES} tiến trình...")

    start_time = time.time()
    
    # Tạo pool để chạy song song
    with multiprocessing.Pool(processes=PROCESSES) as pool:
        # Sử dụng partial để truyền bot_class vào hàm map
        func = partial(play_single_game, bot_class=bot_class)
        results = pool.map(func, range(MATCHES))

    # Tổng hợp kết quả
    wins, losses, draws = 0, 0, 0
    total_cpl = 0
    total_bot_moves = 0

    for res in results:
        if res["result"] == 1: wins += 1
        elif res["result"] == -1: losses += 1
        else: draws += 1
        
        total_cpl += res["total_cpl"]
        total_bot_moves += res["moves"]

    avg_cpl = total_cpl / total_bot_moves if total_bot_moves > 0 else 0
    accuracy = max(0, 100 - (avg_cpl / 10))
    winrate = (wins + 0.5 * draws) / MATCHES * 100

    print(f"\n=== KẾT QUẢ CUỐI CÙNG: {bot_name} ===")
    print(f"Tổng thời gian: {round(time.time() - start_time, 2)} giây")
    print(f"Thắng: {wins} | Thua: {losses} | Hòa: {draws}")
    print(f"Winrate: {winrate}%")
    print(f"Average CPL: {round(avg_cpl, 2)}")
    print(f"Accuracy: ~{round(accuracy, 2)}%")

if __name__ == "__main__":
    # Quan trọng: Trên Windows, code multiprocessing phải nằm trong if __name__ == "__main__"
    multiprocessing.freeze_support() 
    run_parallel_tournament(AlphaBeta, "AlphaBeta Bot")
import chess
import chess.engine
import time

from game import MCTS, AlphaBeta 
from stockfishBot import StockfishPlayer

STOCKFISH_PATH = "stockfish-windows-x86-64-sse41-popcnt\\stockfish\\stockfish-windows-x86-64-sse41-popcnt.exe" 
MATCHES = 100

def calculate_cpl(engine, board, move):
    """Tính Centipawn Loss (CPL) của một nước đi có giới hạn an toàn"""
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
    
    # Ép giới hạn: CPL không được âm, và tối đa là 1000 (tránh ngoại lệ do chiếu bí làm hỏng trung bình)
    return max(0, min(loss, 1000))

def run_headless_tournament(bot_class, bot_name):
    print(f"--- BẮT ĐẦU TEST: {bot_name} vs STOCKFISH ({MATCHES} VÁN) ---")
    
    # Khởi tạo trọng tài (chỉ cần 1 lần)
    referee = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    referee.configure({"Threads": 1})

    wins, losses, draws = 0, 0, 0
    total_cpl = 0
    total_bot_moves = 0

    start_time = time.time()

    for i in range(MATCHES):
        board = chess.Board()
        
        # ĐƯA VÀO TRONG VÒNG LẶP: Đảm bảo bot được reset trí nhớ (bộ nhớ tạm) sau mỗi ván
        bot_color = chess.WHITE if i % 2 == 0 else chess.BLACK
        sf_color = chess.BLACK if i % 2 == 0 else chess.WHITE
        
        bot = bot_class(bot_color)
        sf = StockfishPlayer(sf_color, STOCKFISH_PATH, time_limit=0.05, skill_level=0)
        
        while not board.is_game_over():
            if board.turn == bot.color:
                move = bot.get_move(board)
                cpl = calculate_cpl(referee, board, move)
                total_cpl += cpl
                total_bot_moves += 1
            else:
                move = sf.get_move(board)
            
            board.push(move)

        outcome = board.outcome()
        if outcome.winner is None:
            draws += 1
        elif outcome.winner == bot.color:
            wins += 1
        else:
            losses += 1
            
        print(f"Ván {i+1}/{MATCHES} kết thúc. Thắng: {wins} | Thua: {losses} | Hòa: {draws}")
        
        # Đóng Stockfish đối thủ sau mỗi ván để giải phóng RAM
        sf.close()

    # Đóng trọng tài
    referee.quit()

    avg_cpl = total_cpl / total_bot_moves if total_bot_moves > 0 else 0
    accuracy = max(0, 100 - (avg_cpl / 10))
    winrate = (wins + 0.5 * draws) / MATCHES * 100

    print(f"\n=== KẾT QUẢ {bot_name} ===")
    print(f"Thời gian test: {round(time.time() - start_time, 2)} giây")
    print(f"Thắng: {wins} | Thua: {losses} | Hòa: {draws}")
    print(f"Winrate: {winrate}%")
    print(f"Average Centipawn Loss (CPL): {round(avg_cpl, 2)}")
    print(f"Độ chính xác (Accuracy): ~{round(accuracy, 2)}%")

if __name__ == "__main__":
    print("BẮT ĐẦU ĐÁNH GIÁ...")
    # Chạy luôn, không cần khởi tạo pygame hay màn hình gì cả!
    run_headless_tournament(MCTS, "MCTS Bot")
    run_headless_tournament(AlphaBeta, "AlphaBeta Bot")
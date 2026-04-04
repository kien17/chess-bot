import chess
import chess.engine
import time
import multiprocessing
import os

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

def play_single_match(args):
    """Hàm chạy 1 ván đấu độc lập, được gọi bởi multiprocessing.Pool"""
    match_index, bot_class, bot_name = args
    
    # Xác định màu quân
    bot_color = chess.WHITE if match_index % 2 == 0 else chess.BLACK
    sf_color = chess.BLACK if match_index % 2 == 0 else chess.WHITE
    
    # 1. KHỞI TẠO TRỌNG TÀI RIÊNG CHO TIẾN TRÌNH NÀY
    # Tắt log/debug để tránh spam console khi chạy song song
    referee = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    referee.configure({"Threads": 1})
    
    # 2. KHỞI TẠO NGƯỜI CHƠI
    bot = bot_class(bot_color)
    sf = StockfishPlayer(sf_color, STOCKFISH_PATH, time_limit=0.05, skill_level=0)
    
    board = chess.Board()
    total_cpl = 0
    total_bot_moves = 0
    
    while not board.is_game_over():
        if board.turn == bot.color:
            move = bot.get_move(board)
            cpl = calculate_cpl(referee, board, move)
            total_cpl += cpl
            total_bot_moves += 1
        else:
            move = sf.get_move(board)
        
        board.push(move)

    # 3. KẾT QUẢ VÁN ĐẤU
    outcome = board.outcome()
    if outcome.winner is None:
        result = "draw"
    elif outcome.winner == bot.color:
        result = "win"
    else:
        result = "loss"
        
    # 4. DỌN DẸP RAM (Rất quan trọng khi chạy multiprocessing)
    sf.close()
    referee.quit()
    
    return match_index, result, total_cpl, total_bot_moves

def run_headless_tournament_mp(bot_class, bot_name, num_processes=None):
    print(f"\n--- BẮT ĐẦU TEST: {bot_name} vs STOCKFISH ({MATCHES} VÁN) ---")
    
    # Nếu không chỉ định số processes, dùng nửa số luồng CPU hiện có để máy không bị đơ
    if num_processes is None:
        num_processes = max(1, multiprocessing.cpu_count() // 2)
        
    print(f"Đang chạy song song với {num_processes} tiến trình...")

    wins, losses, draws = 0, 0, 0
    total_cpl = 0
    total_bot_moves = 0
    completed = 0

    start_time = time.time()

    # Chuẩn bị danh sách tham số cho từng ván
    tasks = [(i, bot_class, bot_name) for i in range(MATCHES)]

    # Dùng Pool để chạy song song
    with multiprocessing.Pool(processes=num_processes) as pool:
        # imap_unordered giúp lấy kết quả ngay khi một ván bất kỳ hoàn thành (không cần đợi theo thứ tự)
        for match_index, result, cpl, bot_moves in pool.imap_unordered(play_single_match, tasks):
            completed += 1
            if result == "win":
                wins += 1
            elif result == "loss":
                losses += 1
            else:
                draws += 1
                
            total_cpl += cpl
            total_bot_moves += bot_moves
            
            print(f"[{completed}/{MATCHES}] Ván của {bot_name} kết thúc. Thắng: {wins} | Thua: {losses} | Hòa: {draws}")

    # Tính toán kết quả tổng quát
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
    # Bắt buộc phải có __name__ == "__main__" trên Windows để chạy multiprocessing
    print("BẮT ĐẦU ĐÁNH GIÁ (MULTIPROCESSING)...")
    
    run_headless_tournament_mp(MCTS, "MCTS Bot", num_processes=2)
    # run_headless_tournament_mp(AlphaBeta, "AlphaBeta Bot", num_processes=4)
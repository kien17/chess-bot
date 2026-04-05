import chess
import chess.polyglot
import os
from collections import defaultdict
# Các hằng số cho Transposition Table (Bảng chuyển đổi)
EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2


class ALPHABETA_Bot:
    def __init__(self):
        self.INF = int(1e9)
        

        self.PIECE_VALUES = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        
        # Bảng điểm vị trí (PST)
        self.pst = {
            chess.PAWN: [
                0,  0,  0,  0,  0,  0,  0,  0,
                50, 50, 50, 50, 50, 50, 50, 50,
                10, 10, 20, 30, 30, 20, 10, 10,
                5,  5, 10, 25, 25, 10,  5,  5,
                0,  0,  0, 20, 20,  0,  0,  0,
                5, -5,-10,  0,  0,-10, -5,  5,
                5, 10, 10,-20,-20, 10, 10,  5,
                0,  0,  0,  0,  0,  0,  0,  0
            ],
            chess.KNIGHT: [
                -50,-40,-30,-30,-30,-30,-40,-50,
                -40,-20,  0,  5,  5,  0,-20,-40,
                -30,  5, 10, 15, 15, 10,  5,-30,
                -30,  0, 15, 20, 20, 15,  0,-30,
                -30,  5, 15, 20, 20, 15,  5,-30,
                -30,  0, 10, 15, 15, 10,  0,-30,
                -40,-20,  0,  0,  0,  0,-20,-40,
                -50,-40,-30,-30,-30,-30,-40,-50
            ],
            chess.BISHOP: [
                -20,-10,-10,-10,-10,-10,-10,-20,
                -10,  5,  0,  0,  0,  0,  5,-10,
                -10, 10, 10, 10, 10, 10, 10,-10,
                -10,  0, 10, 10, 10, 10,  0,-10,
                -10,  5,  5, 10, 10,  5,  5,-10,
                -10,  0,  5, 10, 10,  5,  0,-10,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -20,-10,-10,-10,-10,-10,-10,-20
            ],
            chess.ROOK: [ 
                0,  0,  0,  5,  5,  0,  0,  0,
                5, 10, 10, 10, 10, 10, 10,  5,
               -5,  0,  0,  0,  0,  0,  0, -5,
               -5,  0,  0,  0,  0,  0,  0, -5,
               -5,  0,  0,  0,  0,  0,  0, -5,
               -5,  0,  0,  0,  0,  0,  0, -5,
               -5,  0,  0,  0,  0,  0,  0, -5,
                0,  0,  0,  2,  2,  0,  0,  0
            ],
            chess.QUEEN: [ 
                -20,-10,-10, -5, -5,-10,-10,-20,
                -10,  0,  5,  0,  0,  0,  0,-10,
                -10,  5,  5,  5,  5,  5,  0,-10,
                  0,  0,  5,  5,  5,  5,  0, -5,
                 -5,  0,  5,  5,  5,  5,  0, -5,
                -10,  0,  5,  5,  5,  5,  0,-10,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -20,-10,-10, -5, -5,-10,-10,-20
            ],
            chess.KING: [
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -20,-30,-30,-40,-40,-30,-30,-20,
                -10,-20,-20,-20,-20,-20,-20,-10,
                 20, 20,  0,  0,  0,  0, 20, 20,
                 20, 30, 10,  0,  0, 10, 30, 20
            ]
        }
        
        # Memory cho bot
        self.book_moves_cache = {}
        self.tt = {}                                      # Transposition Table
        self.killer_moves = defaultdict(lambda: [None, None]) # Killer Heuristic
        self.history = defaultdict(int)                   # History Heuristic
        self.nodes_evaluated = 0

    def next_move(self, board, max_depth=4):
        self.nodes_evaluated = 0
        

        if board.fullmove_number <= 10:  # Giai đoạn khai cuộc (10 nước đầu)
            book_moves = self.get_book_moves(board)
            if book_moves:
                return book_moves[0]

        best_move = None
        
        # 1: Iterative Deepening 
        for depth in range(1, max_depth + 1):
            score, move = self.negamax(board, depth, -self.INF, self.INF)
            if move:
                best_move = move
                
        return best_move

    def negamax(self, board, depth, alpha, beta):
        self.nodes_evaluated += 1
        original_alpha = alpha
        
        # 2: Transposition Table Lookup
        fen = board.fen()
        tt_entry = self.tt.get(fen)
        if tt_entry and tt_entry['depth'] >= depth:
            if tt_entry['flag'] == EXACT:
                return tt_entry['score'], tt_entry['move']
            elif tt_entry['flag'] == LOWERBOUND:
                alpha = max(alpha, tt_entry['score'])
            elif tt_entry['flag'] == UPPERBOUND:
                beta = min(beta, tt_entry['score'])
            if alpha >= beta:
                return tt_entry['score'], tt_entry['move']

        #  Tìm kiếm tĩnh
        if board.is_game_over() or depth <= 0:
            if depth <= 0:
                score = self.quiescence_search(board, alpha, beta)
            else:
                score = self.evaluate_board(board)
            return score, None

        # 3: Null Move Pruning
        if depth >= 3 and not board.is_check() and self.has_non_pawn_material(board, board.turn):
            board.push(chess.Move.null())
            score, _ = self.negamax(board, depth - 3, -beta, -beta + 1)
            score = -score
            board.pop()
            if score >= beta:
                return beta, None # Cắt tỉa sớm

        best_move = None
        best_val = -self.INF
        
        # Lấy nước đi tốt nhất từ TT để duyệt trước
        tt_move = tt_entry['move'] if tt_entry else None
        
        # 4: Move Ordering (Sắp xếp nước đi)
        moves = self.get_ordered_moves(board, depth, tt_move, captures_only=False)
        
        for move in moves:
            board.push(move)
            # Công thức Negamax: đảo dấu alpha/beta và score
            val, _ = self.negamax(board, depth - 1, -beta, -alpha)
            val = -val
            board.pop()

            if val > best_val:
                best_val = val
                best_move = move

            alpha = max(alpha, val)
            if alpha >= beta:
                # 5: Cập nhật Killer Moves và History
                if not board.is_capture(move):
                    self.killer_moves[depth][1] = self.killer_moves[depth][0]
                    self.killer_moves[depth][0] = move
                    self.history[(board.turn, move.from_square, move.to_square)] += depth ** 2
                break # Cắt tỉa Beta

        # Lưu vào Transposition Table
        flag = EXACT
        if best_val <= original_alpha:
            flag = UPPERBOUND
        elif best_val >= beta:
            flag = LOWERBOUND
            
        self.tt[fen] = {'depth': depth, 'score': best_val, 'flag': flag, 'move': best_move}

        return best_val, best_move

    def quiescence_search(self, board, alpha, beta):
        """ TỐI ƯU 6: Tìm kiếm tĩnh, giải quyết Horizon Effect bằng cách chỉ duyệt các nước ăn quân """
        self.nodes_evaluated += 1
        
        # Điểm hiện tại trước khi ăn
        stand_pat = self.evaluate_board(board)
        
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        # Chỉ sinh các nước đi ăn quân
        moves = self.get_ordered_moves(board, 0, None, captures_only=True)
        
        for move in moves:
            board.push(move)
            score = -self.quiescence_search(board, -beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
                
        return alpha

    def get_ordered_moves(self, board, depth, tt_move, captures_only=False):
        """ Hàm đánh giá và sắp xếp các nước đi để Beta-Cutoff xảy ra sớm nhất """
        moves = list(board.legal_moves)
        if captures_only:
            moves = [m for m in moves if board.is_capture(m)]

        def score_move(move):
            if move == tt_move:
                return 1000000  # Luôn thử nước đi từ Transposition Table đầu tiên

            score = 0
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                # MVV-LVA: Quân yếu ăn quân mạnh được điểm cao nhất
                moving_piece = board.piece_at(move.from_square)
                score = 100000 + self.PIECE_VALUES[captured_piece.piece_type] * 10 - self.PIECE_VALUES[moving_piece.piece_type]
            else:
                # Ưu tiên Killer moves nếu không ăn quân
                if depth > 0 and move in self.killer_moves[depth]:
                    score = 90000
                else:
                    # History Heuristic
                    score = self.history.get((board.turn, move.from_square, move.to_square), 0)

            # Ưu tiên phong cấp
            if move.promotion:
                score += self.PIECE_VALUES[move.promotion]

            return score

        moves.sort(key=score_move, reverse=True)
        return moves

    def evaluate_board(self, board):
        """ 7: Hàm đánh giá có tính góc nhìn phe và Pawn Structure cơ bản """
        if board.is_checkmate():
            return -99999 if board.turn == chess.WHITE else 99999
        if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves():
            return 0

        score = 0
        for square, piece in board.piece_map().items():
            p_type = piece.piece_type
            val = self.PIECE_VALUES[p_type]
            
            # Cấu trúc tốt: Phạt điểm tốt chồng (Doubled Pawns)
            if p_type == chess.PAWN:
                file_idx = chess.square_file(square)
                pawns_in_file = len(board.pieces(chess.PAWN, piece.color) & chess.BB_FILES[file_idx])
                if pawns_in_file > 1:
                    val -= 20 # Trừ 0.2 điểm Tốt

            actual_sq = square if piece.color == chess.WHITE else chess.square_mirror(square)
            pst_val = self.pst.get(p_type, [0]*64)[actual_sq]

            # Điểm thực tế: Trắng +, Đen -
            if piece.color == chess.WHITE:
                score += (val + pst_val)
            else:
                score -= (val + pst_val)

        # Trong Negamax, hàm đánh giá LUÔN TRẢ VỀ theo góc nhìn của phe đang đến lượt
        perspective = 1 if board.turn == chess.WHITE else -1
        return score * perspective

    def has_non_pawn_material(self, board, color):
        """ Kiểm tra xem phe 'color' có quân nào khác Tốt và Vua không """
        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            if len(board.pieces(piece_type, color)) > 0:
                return True
        return False

    def get_book_moves(self, board):
        fen = board.fen()
        if fen in self.book_moves_cache:
            return self.book_moves_cache[fen]
        
        book_moves = {}
        try:
            book_path = os.path.join(os.path.dirname(__file__), "..", "data", "gm2001.bin")
            with chess.polyglot.open_reader(book_path) as reader:
                for move in board.legal_moves:
                    temp_board = board.copy()
                    temp_board.push(move)
                    entry = reader.get(temp_board)
                    if entry: book_moves[move] = entry.weight
        except Exception:
            pass
        
        sorted_moves = [move for move, _ in sorted(book_moves.items(), key=lambda x: x[1], reverse=True)]
        self.book_moves_cache[fen] = sorted_moves
        return sorted_moves
    
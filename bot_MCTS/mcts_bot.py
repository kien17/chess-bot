import chess
import chess.polyglot
from bot_MCTS.mcts_node import MCTS_node
import random
import os

class MCTS_bot:
    def __init__(self, color, current_board, max_iterations=5000):
        self.root = None
        self.max_iterations = max_iterations
        self.color = color
        self.current_board = current_board
        self.book_moves_cache = {}  # Cache cho get_book_moves

        # Bảng điểm vị trí (PST) - Càng cao càng tốt
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
            chess.KING: [
                20, 30, 10,  0,  0, 10, 30, 20,
                20, 20,  0,  0,  0,  0, 20, 20,
                -10,-20,-20,-20,-20,-20,-20,-10,
                -20,-30,-30,-40,-40,-30,-30,-20,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30
            ]
        }
    def evaluate(self, color, board):
        """
        Hàm đánh giá thông minh cho MCTS
        Không dùng bongcloud check, tính điểm dựa trên:
        1. Giá trị quân cờ (Material)
        2. Vị trí tấn công (Activity)
        3. An toàn vua (King Safety)
        4. Cấu trúc tốt (Pawn Structure)
        5. Kiểm soát trung tâm (Center Control)
        """
        # 1. KIỂM TRA GAME OVER
        if board.is_checkmate():
            return -100000 if board.turn == color else 100000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        
        # === 2. GIÁ TRỊ QUÂN CỜ + VỊ TRÍ ===
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        # Bảng điểm vị trí trung tâm
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        
        for square, piece in board.piece_map().items():
            piece_val = piece_values.get(piece.piece_type, 0)
            
            # Cộng giá trị quân cờ
            if piece.color == color:
                score += piece_val
            else:
                score -= piece_val
            
            # === VỊ TRÍ TẤN CÔNG (Activity Bonus) ===
            # Bonus cho quân ở trung tâm
            if square in center_squares:
                center_bonus = 30 if piece.piece_type != chess.PAWN else 20
                if piece.color == color:
                    score += center_bonus
                else:
                    score -= center_bonus
            
            # Bonus cho quân mở ra (attack squares)
            if piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                attack_count = len(board.attacks(square))
                activity_bonus = attack_count * 2
                if piece.color == color:
                    score += activity_bonus
                else:
                    score -= activity_bonus
            
            # === VỊ TRÍ TỐI ƯU CHO MỖI QUÂN ===
            if piece.piece_type in self.pst:
                idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
                pst_val = self.pst[piece.piece_type][idx] * 0.3
                if piece.color == color:
                    score += pst_val
                else:
                    score -= pst_val
        
        # === 3. AN TOÀN VUA & NHẬP THÀNH (King Safety & Castling) ===
        king_sq = board.king(color)
        opp_king_sq = board.king(not color)
        
        # THƯỞNG NHẬP THÀNH
        castling_bonus = 0
        if king_sq is not None:
            # Kiểm tra xem vua đã nhập thành chưa
            if king_sq in [chess.G1, chess.G8, chess.C1, chess.C8]:
                castling_bonus = 300  # Thưởng nếu vua đã nhập thành
            
            # Kiểm tra quyền nhập thành còn lại
            if color == chess.WHITE:
                if not board.has_kingside_castling_rights(chess.WHITE):
                    castling_bonus += 50  # Đã nhập thành hoặc bỏ quyền (có lý do)
                if not board.has_queenside_castling_rights(chess.WHITE):
                    castling_bonus += 50
            else:
                if not board.has_kingside_castling_rights(chess.BLACK):
                    castling_bonus += 50
                if not board.has_queenside_castling_rights(chess.BLACK):
                    castling_bonus += 50
        
        score += castling_bonus
        
        # BẢO VỆ VUA BẰNG TỐT (Pawn Shield)
        if king_sq is not None:
            # Đôi Tốt bảo vệ vua (Pawn shield)
            if king_sq in [chess.G1, chess.G8, chess.C1, chess.C8]:
                shield_bonus = 0
                # Kiểm tra các ô xung quanh vua
                for offset in [-9, -8, -7, 1, -1, 7, 8, 9]:
                    shield_sq = king_sq + offset
                    if 0 <= shield_sq < 64:
                        p = board.piece_at(shield_sq)
                        if p and p.piece_type == chess.PAWN and p.color == color:
                            shield_bonus += 30
                score += shield_bonus
            else:
                # Nếu vua chưa nhập thành, ưu tiên phát triển quân nhẹ
                back_rank = [chess.B1, chess.C1, chess.F1, chess.G1] if color == chess.WHITE else [chess.B8, chess.C8, chess.F8, chess.G8]
                developed_count = 0
                for sq in back_rank:
                    p = board.piece_at(sq)
                    if not p or p.piece_type not in [chess.KNIGHT, chess.BISHOP]:
                        developed_count += 1
                
                # Thưởng phát triển quân nhẹ (để có thể nhập thành v.v.)
                score += developed_count * 20
        
        if opp_king_sq is not None:
            # Phạt cho vua đối thủ nếu không an toàn
            if opp_king_sq not in [chess.G1, chess.G8, chess.C1, chess.C8]:
                opp_shield_bonus = 0
                for offset in [-9, -8, -7, 1, -1, 7, 8, 9]:
                    shield_sq = opp_king_sq + offset
                    if 0 <= shield_sq < 64:
                        p = board.piece_at(shield_sq)
                        if p and p.piece_type == chess.PAWN and p.color != color:
                            opp_shield_bonus += 10
                score += opp_shield_bonus * 2
        
        # Kiểm tra chiếu
        if board.is_check():
            if board.turn == color:
                score -= 50
            else:
                score += 50
        
        # === 4. CẤU TRÚC TỐT (Pawn Structure) ===
        # Phạt đôi tốt
        pawn_files = {}
        for square in chess.SQUARES:
            p = board.piece_at(square)
            if p and p.piece_type == chess.PAWN:
                file_idx = chess.square_file(square)
                if file_idx not in pawn_files:
                    pawn_files[file_idx] = {'white': 0, 'black': 0}
                if p.color == chess.WHITE:
                    pawn_files[file_idx]['white'] += 1
                else:
                    pawn_files[file_idx]['black'] += 1
        
        for file_idx, pawns in pawn_files.items():
            if pawns['white'] > 1:
                score -= pawns['white'] * 50
            if pawns['black'] > 1:
                score += pawns['black'] * 50
        
        # === 5. KIỂM SOÁT TRUNG TÂM (Center Control) ===
        for sq in center_squares:
            # Đếm quân tấn công vào ô trung tâm
            for attacker_sq in board.attackers(color, sq):
                score += 5
            for attacker_sq in board.attackers(not color, sq):
                score -= 5
        
        # === 6. ĐỘ CƠ ĐỘNG (Mobility) ===
        legal_moves_count = len(list(board.legal_moves))
        score += legal_moves_count * 1.5

        # === 7. AN TOÀN QUÂN (Piece Safety) ===
        for square, piece in board.piece_map().items():
            attackers = len(board.attackers(not piece.color, square))
            defenders = len(board.attackers(piece.color, square))
            if attackers > defenders:
                risk = (attackers - defenders) * 30
                if piece.color == color:
                    score -= risk  # phạt quân đang bị dọa
                else:
                    score += risk  # thưởng đối thủ có quân bị dọa

        return score

    def get_force_info(self, board):
        """Trả về thông tin lực lượng giá trị và số lượng quân"""
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000,
        }

        force = {
            'white_material': 0,
            'black_material': 0,
            'white_pieces': 0,
            'black_pieces': 0,
        }

        for square, piece in board.piece_map().items():
            value = piece_values.get(piece.piece_type, 0)
            if piece.color == chess.WHITE:
                force['white_material'] += value
                force['white_pieces'] += 1
            else:
                force['black_material'] += value
                force['black_pieces'] += 1

        force['material_diff'] = force['white_material'] - force['black_material']
        force['piece_diff'] = force['white_pieces'] - force['black_pieces']
        return force
    
    def get_book_moves(self, board):
        """Lấy danh sách các nước từ opening book (có cache)"""
        fen = board.fen()
        
        # Kiểm tra cache
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
                    if entry:
                        book_moves[move] = entry.weight
        except:
            pass
        
        # Nếu không có từ gm2001, thử komodo
        if not book_moves:
            try:
                book_path = os.path.join(os.path.dirname(__file__), "..", "data", "komodo.bin")
                with chess.polyglot.open_reader(book_path) as reader:
                    for move in board.legal_moves:
                        temp_board = board.copy()
                        temp_board.push(move)
                        entry = reader.get(temp_board)
                        if entry:
                            book_moves[move] = entry.weight
            except:
                pass
        
        # Sắp xếp theo weight giảm dần
        sorted_moves = sorted(book_moves.items(), key=lambda x: x[1], reverse=True)
        result = [move for move, _ in sorted_moves]
        
        # Lưu vào cache
        self.book_moves_cache[fen] = result
        
        return result

    def get_best_move(self):
        # *** KHAI CUỘC: Return nước từ sách ngay lập tức ***
        move_count = len(self.current_board.move_stack)
        if move_count <= 5:  # Giai đoạn khai cuộc (5 nước đầu)
            book_moves = self.get_book_moves(self.current_board)
            if book_moves:
                move = book_moves[0]
                # print(f"[BOOK MOVE] {move} (move {move_count + 1})")
                return move
        
        # *** TRUNG CUỘC: Dùng MCTS ***
        self.root = MCTS_node(self.current_board.copy())
        
        next_move = None

        for _ in range(self.max_iterations):
            node = self.root

            if node is None:
                break

            # 1. Selection
            while node.is_fully_expanded() and node.children and not node.board.is_game_over():
                node = node.select_child()

            # 2. Expansion
            if not node.board.is_game_over():
                new_node = node.expand()
                if new_node: 
                    node = new_node

            # 3. Simulation
            temp_board = node.board.copy()
            for _ in range(15):
                if temp_board.is_game_over():
                    break
                legal_moves = list(temp_board.legal_moves)
                if not legal_moves:
                    break

                random_move = random.choice(legal_moves)

                temp_board.push(random_move)

            res = self.evaluate(self.color, temp_board)

            # 4. Backpropagation
            cur = node
            while cur is not None:
                cur.visits += 1
                if (cur.board.turn != self.color):
                    cur.wins += res
                else:
                    cur.wins -= res
                cur = cur.parent 
        
        if self.root.children:
            best_child = max(self.root.children, key=lambda c: c.visits)
            next_move = best_child.move
            force = self.get_force_info(self.current_board)
            # print(
            #     f"[MCTS MOVE] {next_move} | Visits: {best_child.visits} | Score: {best_child.wins:.0f} "
            #     f"| W_mat={force['white_material']} B_mat={force['black_material']} "
            #     f"| W_pcs={force['white_pieces']} B_pcs={force['black_pieces']} "
            #     f"| Δ_mat={force['material_diff']} Δ_pcs={force['piece_diff']}"
            # )

        return next_move

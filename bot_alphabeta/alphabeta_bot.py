import chess
import math
class ALPHABETA_Bot:
    def __init__(self):
        self.INF= 1e9
        self.PIECE_VALUES = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 3,
            chess.QUEEN: 9,
            chess.KING: 20
        }
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
            chess.ROOK: [ # Ưu tiên hàng 7 và các cột trung tâm
                0,  0,  0,  5,  5,  0,  0,  0,
                5, 10, 10, 10, 10, 10, 10,  5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
                0,  0,  0,  2,  2,  0,  0,  0
            ],
            chess.QUEEN: [ # Hậu nên tránh ra sớm nhưng cần kiểm soát trung tâm
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

    def alpha_beta_prunning(self, alpha, beta, depth, isMax, board: chess.Board):
        best_move= None
        if depth == 0 or self.isEnd(board):
            return self.getPoint(board), best_move
        if isMax:
            value= - self.INF
            possibleMove= self.getPossibleMove(board)
            possibleMove= sorted(possibleMove, key= lambda m: self.evaluate_move(board, m), reverse= True)

            for move in possibleMove:
                board.push(move)
                val, _= self.alpha_beta_prunning(alpha, beta, depth - 1, False, board)
                board.pop()
                if value < val:
                    value= val
                    best_move= move
                if alpha >= beta:
                    break
                alpha= max(alpha, value)
            return value, best_move
        
        value= self.INF
        possibleMove= self.getPossibleMove(board)
        possibleMove= sorted(possibleMove, key= lambda m: self.evaluate_move(board, m), reverse= True)
        for move in possibleMove:
            board.push(move)
            val, _ = self.alpha_beta_prunning(alpha, beta, depth - 1, True, board)
            board.pop()
            if value > val:
                value= val
                best_move= move
            if alpha >= beta:
                break
            beta= min(beta, value)
        return value, best_move
    
    def isEnd(self, board: chess.Board):
        possibleMove= self.getPossibleMove(board)

        if self.check_win(board):
            return True

        if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves():
            return True

        if (possibleMove.count() > 0):
            return False
        return True

    def check_win(self, board: chess.Board):
        if board.is_checkmate():
            return True
        return False

    def getPoint(self, board: chess.Board):
        # Nếu game kết thúc, trả về điểm vô cực
        if board.is_checkmate():
            return -99999 if board.turn == chess.WHITE else 99999

        total_score = 0
        
        # Duyệt qua tất cả các ô có quân cờ
        for square, piece in board.piece_map().items():
            p_type = piece.piece_type
            
            # 1. Lấy giá trị quân cờ (Material)
            material_val = self.PIECE_VALUES.get(p_type, 0)
            
            # 2. Lấy giá trị vị trí (PST)
            table = self.pst.get(p_type, [0] * 64)
            
            # Đảo ngược bảng nếu là quân Đen để nhìn đúng hướng
            actual_sq = square
            if piece.color == chess.BLACK:
                actual_sq = chess.square_mirror(square)
                
            pst_val = table[actual_sq]
            
            # Cộng vào tổng điểm (Trắng cộng, Đen trừ)
            if piece.color == chess.WHITE:
                total_score += (material_val + pst_val)
            else:
                total_score -= (material_val + pst_val)
                
        return total_score
    
    def evaluate_move(self, board: chess.Board, move: chess.Move):
        """
        Trả về một con số đánh giá mức độ 'hấp dẫn' của nước đi.
        Giá trị càng cao, nước đi càng được ưu tiên duyệt trước.
        """
        score = 0
        from_sq = move.from_square
        to_sq = move.to_square
        
        # 1. Ưu tiên ăn quân (MVV-LVA)
        captured_piece = board.piece_at(to_sq)
        moving_piece = board.piece_at(from_sq)
        enemy_color = not board.turn
        if captured_piece:
            # Công thức: 10 * giá_trị_nạn_nhân - giá_trị_kẻ_tấn_công
            # Ví dụ: Tốt (1) ăn Xe (3) => 10*3= 30
            score += 10 * self.PIECE_VALUES[captured_piece.piece_type]

        # 2. KIỂM TRA AN TOÀN (Lấy thêm điểm ở đây)
        # Nếu Tốt (1) ăn Xe (3) sau đó có khả năng bị ăn lại thì trừ (1)
        if board.is_attacked_by(enemy_color, to_sq):
            # Trừ điểm dựa trên giá trị quân cờ mình định đưa vào đó
            score -= self.PIECE_VALUES[moving_piece.piece_type]

        # 3. THOÁT HIỂM
        # Nếu quân mình đang đứng ở ô bị tấn công, và nước đi này dẫn đến ô an toàn
        if board.is_attacked_by(enemy_color, from_sq) and not board.is_attacked_by(enemy_color, to_sq):
            score += self.PIECE_VALUES[moving_piece.piece_type] // 2 # Cộng điểm khuyến khích chạy quân

        # 4. Ưu tiên phong cấp (Promotion)
        if move.promotion:
            score += self.PIECE_VALUES[move.promotion]

        # 5. Trừ điểm nước đi lặp lại
        # Lấy nước đi trước đó của chính quân cờ này
        if len(board.move_stack) >= 2:
            last_move = board.move_stack[-2] # Nước đi trước của phe mình
            if move.to_square == last_move.from_square and move.from_square == last_move.to_square:
                # Phạt điểm vì đi lùi về vị trí cũ ngay lập tức
                score -= 50
        return score

    def is_square_under_attack(self, board: chess.Board, square: chess.Square, attacker_color: chess.Color):
        # Trả về True nếu 'square' đang bị 'attacker_color' tấn công
        return board.is_attacked_by(attacker_color, square)

    def getPossibleMove(self, board: chess.Board):
        return board.legal_moves
                    
    def next_move(self, current_board, player):
        isMax= True
        if player == 2:
            isMax= False
        value, best_move= self.alpha_beta_prunning(-self.INF, self.INF, 5, isMax, current_board)
        if best_move == None:
            best_move= self.getPossibleMove(current_board)[0]
        print(player, " ",isMax, " ", value)
        return best_move


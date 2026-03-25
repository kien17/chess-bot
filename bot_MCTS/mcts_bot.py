import chess
from mcts_node import MCTS_node

class MCTS_bot:
    def __init__(self, color, current_board, max_iterations=1000):
        self.root = None
        self.max_iterations = max_iterations
        self.color = color
        self.current_board = current_board

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
                -40,-20,  0,  0,  0,  0,-20,-40,
                -30,  0, 10, 15, 15, 10,  0,-30,
                -30,  5, 15, 20, 20, 15,  5,-30,
                -30,  0, 15, 20, 20, 15,  0,-30,
                -30,  5, 10, 15, 15, 10,  5,-30,
                -40,-20,  0,  5,  5,  0,-20,-40,
                -50,-40,-30,-30,-30,-30,-40,-50
            ],
            chess.BISHOP: [
                -20,-10,-10,-10,-10,-10,-10,-20,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -10,  0,  5, 10, 10,  5,  0,-10,
                -10,  5,  5, 10, 10,  5,  5,-10,
                -10,  0, 10, 10, 10, 10,  0,-10,
                -10, 10, 10, 10, 10, 10, 10,-10,
                -10,  5,  0,  0,  0,  0,  5,-10,
                -20,-10,-10,-10,-10,-10,-10,-20
            ],
            chess.KING: [ # Bảng cho Khai cuộc/Trung cuộc (Cần ẩn nấp)
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
    
    def evaluate(self, color, board):
        if board.is_checkmate():
            return 100000 if board.turn != color else -100000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        piece_values = {
            chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
        }

        # Duyệt qua từng quân cờ đang có trên bàn
        for square, piece in board.piece_map().items():
            # 1. Lấy giá trị cơ bản
            val = piece_values.get(piece.piece_type, 0)
            
            # 2. Lấy điểm thưởng vị trí (PST)
            pst_val = 0
            if piece.piece_type in self.pst:
                # Nếu là quân Đen, phải lật ngược bảng điểm (mirror)
                idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
                pst_val = self.pst[piece.piece_type][idx]

            # 3. Cộng nếu là quân mình, trừ nếu là quân đối thủ
            if piece.color == color:
                score += (val + pst_val)
            else:
                score -= (val + pst_val)

        # Thêm điểm cơ động (Mobility)
        score += len(list(board.legal_moves)) * 10
        
        # Tính độ cơ động đối thủ
        if not board.is_check():
            board.push(chess.Move.null())
            score -= len(list(board.legal_moves)) * 10
            board.pop()

        return score

    def get_best_move(self):
        if self.root is None:
            self.root = MCTS_node(self.current_board)
        
        next_move = None

        for _ in range(self.max_iterations):
            pass

        return next_move

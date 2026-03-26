import pygame
import chess
import os, threading
from bot_alphabeta.alphabeta_bot import *
from bot_MCTS.mcts_bot import *
from bot_MCTS.mcts_node import *

# Cấu hình cơ bản
WIDTH, HEIGHT = 512, 512
DIMENSION = 8 
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

class Player:
    def __init__(self, color):
        self.color = color # chess.color
    
    def get_move(self, board):
        pass
class MCTS(Player):
    def __init__(self, color):
        super().__init__(color)
        self.bot = None
    
    def get_move(self, board):
        if self.bot is None:
            self.bot = MCTS_bot(self.color, board)
        
        return self.bot.get_best_move()

class AlphaBeta(Player):
    def __init__(self, color):
        super().__init__(color)
        self.bot = ALPHABETA_Bot()

    def get_move(self, board):
        if self.color == chess.WHITE:
            return self.bot.next_move(board, 1)
        else:
            return self.bot.next_move(board, 1)
        
class Game:
    def __init__(self, display=True, player1=None, player2=None, games=10):
        self.screen = None
        self.clock = None
        self.display = display
        self.running = True
        self.board_lock = threading.Lock()
        self.bot_thread = None

        # game stuff
        self.board = None
        self.promoting = False
        self.src_sq = None
        self.dest_sq = None

        self.player1 = player1
        self.player2 = player2
        if player1 is not None:
            self.player1.color = chess.WHITE 
        if player2 is not None:
            self.player2.color = chess.BLACK

        # scoring
        self.white = 0
        self.black = 0
        self.matches = 0
        self.max_matches = games

    def init_game(self):
        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess MCTS - Dev Mode")

        self.clock = pygame.time.Clock()

        self.load_images()

        self.board = chess.Board()

    def reset_game(self):
        self.board.reset()
        self.src_sq = None
        self.dest_sq = None

    def load_images(self):
        pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 
                'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
        for piece in pieces:
            path = f"assets/{piece}.png"
            IMAGES[piece] = pygame.transform.scale(pygame.image.load(path), (SQ_SIZE, SQ_SIZE))

    def check_game_over(self):
        if self.board.is_checkmate():
            # Nếu đang lượt Trắng mà bị chiếu bí -> Đen thắng và ngược lại
            winner = "DEN" if self.board.turn == chess.WHITE else "TRANG"
            return True, winner
        
        if self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_seventyfive_moves():
            return True, "HOA"

        return False, None
    
    def draw_board(self):
        colors = [pygame.Color("white"), pygame.Color("gray")]
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                color = colors[((r + c) % 2)]
                pygame.draw.rect(self.screen, color, pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        
        if self.src_sq is not None:
            legal_moves = [m for m in self.board.legal_moves if m.from_square == self.src_sq]
            for move in legal_moves:
                to_sq = move.to_square
                row = 7 - (to_sq // 8)
                col = to_sq % 8
                highlight_rect = pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
                overlay = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                overlay.fill((255, 255, 0, 100))
                self.screen.blit(overlay, highlight_rect)

    def draw_pieces(self):
        for i in range(64):
            piece = self.board.piece_at(i)
            if piece:
                row = 7 - (i // 8)
                col = i % 8
                color = "w" if piece.color == chess.WHITE else "b"
                symbol = piece.symbol().upper() 
                if symbol == 'P': symbol = 'p'
                p_str = color + symbol
                self.screen.blit(IMAGES[p_str], pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    def draw_promotion_ui(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180) 
        overlay.fill((30, 30, 30))
        self.screen.blit(overlay, (0,0))
        
        color = "w" if self.board.turn == chess.WHITE else "b"
        options = ['Q', 'R', 'B', 'N']
        
        # Vẽ hướng dẫn
        font = pygame.font.SysFont("Arial", 24, True)
        text = font.render("Chon quan phong cap (Q, R, B, N):", True, pygame.Color("white"))
        self.screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - SQ_SIZE))

        for i, opt in enumerate(options):
            rect = pygame.Rect(i * SQ_SIZE + SQ_SIZE*2, HEIGHT//2 - SQ_SIZE//2, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(self.screen, (200, 200, 200), rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
            piece_key = color + opt
            self.screen.blit(IMAGES[piece_key], rect)

    def draw(self):
        if self.display:
            self.draw_board()
            self.draw_pieces()
            if self.promoting:
                self.draw_promotion_ui()

            pygame.display.flip()

    def handle_promotion(self, event):
        # check if that pawn is allowed to move
        move = chess.Move(self.src_sq, self.dest_sq, promotion=chess.QUEEN)
        if move not in self.board.legal_moves:
            self.src_sq = None
            self.dest_sq = None
        if event is None or event.type != pygame.KEYDOWN:
            return
        chosen = None
        match event.key:
            case pygame.K_q:
                chosen = chess.QUEEN
            case pygame.K_r:
                chosen = chess.ROOK
            case pygame.K_n:
                chosen = chess.KNIGHT
            case pygame.K_b:
                chosen = chess.BISHOP
            case _:
                return None
        if chosen is not None:
            move.promotion = chosen
            self.board.push(move)
            self.src_sq = None
            self.dest_sq = None
            self.promoting = False
            
    def handle_click(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        mouse_pos = event.pos
        col, row = mouse_pos[0] // SQ_SIZE, mouse_pos[1] // SQ_SIZE
        sq = chess.square(col, 7 - row)
        piece = self.board.piece_at(sq)
        if piece is not None and (self.board.turn == piece.color):
            # just change/choose the piece to move
            self.src_sq = sq
            self.dest_sq = None
        else:
            if self.src_sq is None:
                # not chosen what piece to move
                return
            else:
                self.dest_sq = sq

    def update(self):
        with self.board_lock:
            # else handle normal user movement
            if self.promoting:
                return
            if self.src_sq is None or self.dest_sq is None:
                return
            
            move = chess.Move(self.src_sq, self.dest_sq)
            # check if promotion move:
            piece = self.board.piece_at(self.src_sq)
            if piece.piece_type == chess.PAWN and chess.square_rank(self.dest_sq) in [0, 7]:
                self.promoting = True
                return
            
            if move in self.board.legal_moves:
                self.board.push(move)
                print(f"{move.uci()}")
                self.src_sq = None
                self.dest_sq = None
            return

    def game_end(self, outcome):
        if outcome == "Draw":
            pass
        else:
            if outcome == "TRANG":
                self.white += 1
            else:
                self.black += 1    
        self.matches += 1
        if self.matches >= self.max_matches:
            self.running = False
        else:
            self.reset_game()

    def bot_play(self, player):
        move = player.get_move(self.board.copy())
        if move and move in self.board.legal_moves:
            # push the move safely
            with self.board_lock:
                self.board.push(move)

    def play(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                # player/bot control handling
                if self.board.turn == chess.WHITE and self.player1 is not None and not self.promoting:
                    if self.bot_thread is None or not self.bot_thread.is_alive():
                        self.bot_thread = threading.Thread(target=self.bot_play, args=(self.player1,))
                        self.bot_thread.start()
                elif self.board.turn == chess.BLACK and self.player2 is not None and not self.promoting:
                    if self.bot_thread is None or not self.bot_thread.is_alive():
                        self.bot_thread = threading.Thread(target=self.bot_play, args=(self.player2,))
                        self.bot_thread.start()
                if self.board.turn == chess.WHITE and self.player1 is None or self.board.turn == chess.BLACK and self.player2 is None:
                    # handle manual player move
                    if self.promoting:
                        self.handle_promotion(event)
                    else:
                        self.handle_click(event)

            self.update()
            is_end, outcome = self.check_game_over()
            if is_end:
                self.game_end(outcome)
            self.draw()
            self.clock.tick(MAX_FPS)

        # print game stats:
        if self.matches > 0:
            print(f"SỐ GAME CHƠI: {self.matches}")
            print(f"TRẮNG THẮNG: {self.white} ({self.white / self.matches})")
            print(f"ĐEN THẮNG: {self.black} ({self.white / self.matches})")
        else:
            print("Aborted")
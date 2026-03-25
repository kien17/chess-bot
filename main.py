import pygame
import chess
import os

# Cấu hình cơ bản
WIDTH, HEIGHT = 512, 512
DIMENSION = 8 
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

def load_images():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 
              'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        path = f"assets/{piece}.png"
        IMAGES[piece] = pygame.transform.scale(pygame.image.load(path), (SQ_SIZE, SQ_SIZE))

def draw_board(screen):
    colors = [pygame.Color("white"), pygame.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            pygame.draw.rect(screen, color, pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_pieces(screen, board):
    for i in range(64):
        piece = board.piece_at(i)
        if piece:
            row = 7 - (i // 8)
            col = i % 8
            color = "w" if piece.color == chess.WHITE else "b"
            symbol = piece.symbol().upper() 
            if symbol == 'P': symbol = 'p'
            p_str = color + symbol
            screen.blit(IMAGES[p_str], pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def check_game_over(board):
    if board.is_checkmate():
        # Nếu đang lượt Trắng mà bị chiếu bí -> Đen thắng và ngược lại
        winner = "DEN" if board.turn == chess.WHITE else "TRANG"
        return True, winner
    
    if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves():
        return True, "HOA"

    return False, None

def draw_promotion_ui(screen, board):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180) 
    overlay.fill((30, 30, 30))
    screen.blit(overlay, (0,0))
    
    color = "w" if board.turn == chess.WHITE else "b"
    options = ['Q', 'R', 'B', 'N']
    
    # Vẽ hướng dẫn
    font = pygame.font.SysFont("Arial", 24, True)
    text = font.render("Chon quan phong cap (Q, R, B, N):", True, pygame.Color("white"))
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - SQ_SIZE))

    for i, opt in enumerate(options):
        rect = pygame.Rect(i * SQ_SIZE + SQ_SIZE*2, HEIGHT//2 - SQ_SIZE//2, SQ_SIZE, SQ_SIZE)
        pygame.draw.rect(screen, (200, 200, 200), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)
        piece_key = color + opt
        screen.blit(IMAGES[piece_key], rect)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess MCTS - Dev Mode")
    clock = pygame.time.Clock()
    board = chess.Board()
    load_images()
    
    waiting_for_promotion = False
    temp_move = None
    selected_sq = None
    player_clicks = []

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            
            # Xử lý chọn quân khi đang đợi phong cấp
            elif e.type == pygame.KEYDOWN and waiting_for_promotion:
                promotion_piece = None
                if e.key == pygame.K_q: promotion_piece = chess.QUEEN
                elif e.key == pygame.K_r: promotion_piece = chess.ROOK
                elif e.key == pygame.K_b: promotion_piece = chess.BISHOP
                elif e.key == pygame.K_n: promotion_piece = chess.KNIGHT
                
                if promotion_piece:
                    temp_move.promotion = promotion_piece
                    if temp_move in board.legal_moves:
                        board.push(temp_move)
    
                    waiting_for_promotion = False
                    temp_move = None
                    player_clicks = []
                    selected_sq = None

            elif e.type == pygame.MOUSEBUTTONDOWN and not waiting_for_promotion:
                location = pygame.mouse.get_pos()
                col, row = location[0] // SQ_SIZE, location[1] // SQ_SIZE
                sq = chess.square(col, 7 - row)

                if selected_sq == sq:
                    selected_sq, player_clicks = None, []
                else:
                    selected_sq = sq
                    player_clicks.append(selected_sq)
                
                if len(player_clicks) == 2:
                    from_sq, to_sq = player_clicks[0], player_clicks[1]
                    move = chess.Move(from_sq, to_sq)
                    piece = board.piece_at(from_sq)

                    if piece and piece.piece_type == chess.PAWN and chess.square_rank(to_sq) in [0, 7]:
                        # Kiểm tra xem nước đi này có hợp lệ nếu giả định phong Hậu không
                        test_move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
                        if test_move in board.legal_moves:
                            waiting_for_promotion = True
                            temp_move = move
                        else:
                            player_clicks = []
                    else:
                        if move in board.legal_moves:
                            board.push(move)
                            print(f"{move.uci()}") 

                            is_over, outcome = check_game_over(board)
                            if is_over:
                                print("\n" + "*"*30)
                                if outcome == "Draw":
                                    print("KẾT THÚC: VÁN ĐẤU HÒA!")
                                else:
                                    print(f"KẾT THÚC: PHE {outcome.upper()} THẮNG TUYỆT ĐỐI!")
                                print("*"*30 + "\n")
                           
                        player_clicks, selected_sq = [], None

        # VẼ GIAO DIỆN
        draw_board(screen)
        draw_pieces(screen, board)
        
        if waiting_for_promotion:
            draw_promotion_ui(screen, board)
            
        pygame.display.flip()
        clock.tick(MAX_FPS)

if __name__ == "__main__":
    main()
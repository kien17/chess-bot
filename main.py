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
            
            if symbol == 'P':
                symbol = 'p'
            
            p_str = color + symbol
            screen.blit(IMAGES[p_str], pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def check_game_over(board):
    if board.is_checkmate():
        winner = "Đen" if board.turn == chess.WHITE else "Trắng"
        print(f"CHIẾU BÍ! {winner} thắng.")
        return True, winner
    
    if board.is_stalemate():
        print("HÒA! Thế cờ hết nước đi (Stalemate).")
        return True, "Draw"
    
    if board.is_insufficient_material():
        print("HÒA! Không đủ quân để chiếu bí.")
        return True, "Draw"
    
    if board.is_fivefold_repetition() or board.can_claim_draw():
        print("HÒA! Lặp lại thế cờ hoặc luật 50 nước.")
        return True, "Draw"

    return False, None

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    board = chess.Board()
    load_images()
    
    selected_sq = None
    player_clicks = []

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            
            elif e.type == pygame.MOUSEBUTTONDOWN:
                location = pygame.mouse.get_pos()
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                
                chess_row = 7 - row
                chess_col = col
                sq = chess.square(chess_col, chess_row)

                if selected_sq == sq:
                    selected_sq = None
                    player_clicks = []
                else:
                    selected_sq = sq
                    player_clicks.append(selected_sq)
                
                # CHỈ THỰC HIỆN KHI ĐÃ CÓ ĐỦ 2 LẦN CLICK
                if len(player_clicks) == 2:
                    move = chess.Move(player_clicks[0], player_clicks[1])
                    
                    # Xử lý phong cấp mặc định thành Hậu (Queen) nếu đi Tốt xuống cuối hàng
                    piece = board.piece_at(player_clicks[0])
                    if piece and piece.piece_type == chess.PAWN:
                        if (chess_row == 7 and board.turn == chess.WHITE) or \
                        (chess_row == 0 and board.turn == chess.BLACK):
                            move.promotion = chess.QUEEN

                    # Kiểm tra hợp lệ và thực hiện nước đi
                    if move in board.legal_moves:
                        board.push(move)
                        print(f"Nước đi: {move}")
                        
                        # Sau khi đi xong, kiểm tra thắng thua ngay
                        game_over, winner = check_game_over(board)
                        if game_over:
                            print(f"Trận đấu kết thúc! Người thắng: {winner}")
                            # Bạn có thể để running = False nếu muốn đóng game ngay
                    else:
                        print("Nước đi không hợp lệ, mời chọn lại.")
                    
                    # Quan trọng: Reset click dù đi đúng hay sai để sẵn sàng cho lượt mới
                    selected_sq = None
                    player_clicks = []

        draw_board(screen)
        draw_pieces(screen, board)
        pygame.display.flip()
        clock.tick(MAX_FPS)

if __name__ == "__main__":
    main()
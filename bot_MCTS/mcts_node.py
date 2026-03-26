import chess
import math

class MCTS_node:
    def __init__(self, board: chess.Board, parent=None, move=None):
        self.board = board
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.wins = 0
    
    def is_fully_expanded(self):
        return len(self.children) == len(list(self.board.legal_moves))
    
    def UCB1(self, parent_visits, exploration_param=0.8):
        if self.visits == 0:
            return float('inf')
        win_rate = self.wins / self.visits
        exploration_term = exploration_param * math.sqrt(math.log(parent_visits) / self.visits)
        return win_rate + exploration_term

    def select_child(self):
        node_child = None
        max_ucb1 = float('-inf')

        for child in self.children:
            ucb1_value = child.UCB1(self.visits)
            if ucb1_value > max_ucb1:
                max_ucb1 = ucb1_value
                node_child = child
        
        return node_child
    
    def expand(self):
        legal_moves = list(self.board.legal_moves)
        existing_moves = [child.move for child in self.children]

        for move in legal_moves:
            if move not in existing_moves:
                new_board = self.board.copy()
                new_board.push(move)
                new_node = MCTS_node(new_board, parent=self, move=move)
                self.children.append(new_node)
                return new_node
        
        return None
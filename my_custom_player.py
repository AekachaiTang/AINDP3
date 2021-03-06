from sample_players import DataPlayer
import random
from itertools import count
from isolation import DebugState


class CustomPlayer(DataPlayer):
	""" Implement your own agent to play knight's Isolation
	The get_action() method is the only required method for this project.
	You can modify the interface for get_action by adding named parameters
	with default values, but the function MUST remain compatible with the
	default interface.
	**********************************************************************
	NOTES:
	- The test cases will NOT be run on a machine with GPU access, nor be
	  suitable for using any other machine learning techniques.
	- You can pass state forward to your agent on the next turn by assigning
	  any pickleable object to the self.context attribute.
	**********************************************************************
	"""
	def get_action(self, state):
		""" Employ an adversarial search technique to choose an action
		available in the current state.
		This method must call self.queue.put(ACTION) at least once, and may
		call it as many times as you want; the caller will be responsible
		for cutting off the function after the search time limit has expired.
		See RandomPlayer and GreedyPlayer in sample_players for more examples.
		**********************************************************************
		NOTE: 
		- The caller is responsible for cutting off search, so calling
		  get_action() from your own code will create an infinite loop!
		  Refer to (and use!) the Isolation.play() function to run games.
		**********************************************************************
		"""

		if self.context is None: self.context = {'n_nodes': 0, 'n_layers': 0}

		if state.ply_count < 2:
			self.queue.put(random.choice(state.actions()))
		else:
			for depth in count(1):
				pre_nodes = self.context['n_nodes']

				self.queue.put(self.alpha_beta_search(state, depth, self.deeper_heuristic))

				self.context['n_layers'] += depth
				if self.context['n_nodes'] - pre_nodes == depth: return #finish early, because we ran out of nodes
				

	# Straight outta the lecture coding example
	def alpha_beta_search(self, state, depth, heuristic):
		""" Return the move along a branch of the game tree that
		has the best possible value.  A move is a pair of coordinates
		in (column, row) order corresponding to a legal move for
		the searching player.
		
		You can ignore the special case of calling this function
		from a terminal state.
		"""
		# helper function definitions
		def min_value(state, depth, alpha, beta):
			""" Return the value for a win (+1) if the game is over,
			otherwise return the minimum value over all legal childz
			nodes.
			"""
			self.context['n_nodes'] += 1

			if state.terminal_test():
				return state.utility(self.player_id)

			if depth <= 0: return heuristic(state)
			
			v = float("inf")
			for a in state.actions():
				v = min(v, max_value(state.result(a), depth-1, alpha, beta))
				if v <= alpha: return v
				beta = min(beta, v)
			return v

		def max_value(state, depth, alpha, beta):
			""" Return the value for a loss (-1) if the game is over,
			otherwise return the maximum value over all legal child
			nodes.
			"""
			self.context['n_nodes'] += 1

			if state.terminal_test():
				return state.utility(self.player_id)
			
			if depth <= 0: return heuristic(state)

			v = float("-inf")
			for a in state.actions():
				v = max(v, min_value(state.result(a), depth-1, alpha, beta))
				if v >= beta: return v
				alpha = max(alpha, v)
			return v

		# kick it off
		self.context['n_nodes'] += 1
		alpha = float("-inf")
		beta = float("inf")
		best_score = float("-inf")
		best_move = state.actions()[0]
		for a in state.actions():
			v = min_value(state.result(a), depth-1, alpha, beta)
			alpha = max(alpha, v) # this line disallows calling with just max(key=lambda)
			if v > best_score:
				best_score = v
				best_move = a
		return best_move

	def moves_diff_heuristic(self, state):
		return len(state.liberties(state.locs[self.player_id])) - \
				len(state.liberties(state.locs[1-self.player_id]))	

	# stay near the opponent, blocking his liberties if possible
	# pure aggression
	def chase_opponent_heuristic(self, state):
		ind1 = state.locs[self.player_id]
		x1, y1 = (ind1 % (11 + 2), ind1 // (11 + 2))
		ind2 = state.locs[1-self.player_id]
		x2, y2 = (ind2 % (11 + 2), ind2 // (11 + 2))
		# Minimize Euler distance, so negative if far from opponent
		return -(x1-x2)**2 - (y1-y2)**2

	def avoid_opponent_heuristic(self, state):
		return -self.chase_opponent_heuristic(state)

	def center_heuristic(self, state):
		ind1 = state.locs[self.player_id]
		x1, y1 = (ind1 % (11 + 2), ind1 // (11 + 2))
		ind2 = state.locs[1-self.player_id]
		x2, y2 = (ind2 % (11 + 2), ind2 // (11 + 2))

		# (5, 4) is the center of the board. Try to stay there.
		# If opponent is off to the edge, that's better too.
		return -(x1-5)**2 - (y1-4)**2 + (x2-5)**2 + (y2-4)**2

	def multi_heuristic(self, state):
		return self.moves_diff_heuristic(state) + \
			0.5*self.center_heuristic(state)

	# sum up the liberties and the liberties of liberties
	def deeper_heuristic(self, state):
		val = 0
		for liberty in state.liberties(state.locs[self.player_id]):
			val += 1 + len(state.liberties(liberty))
		for liberty in state.liberties(state.locs[1-self.player_id]):
			val -= 1 + len(state.liberties(liberty))
		return val
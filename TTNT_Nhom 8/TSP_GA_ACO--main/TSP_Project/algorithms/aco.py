import random
import numpy as np
from utils.tsp_utils import total_distance

class ACO:
    def __init__(self, cities, n_ants=50, n_iter=500,
                 alpha=1, beta=2, rho=0.1, q=1, patience=200):
        self.cities = cities
        self.n = len(cities)
        self.n_ants = n_ants
        self.n_iter = n_iter
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.q = q
        self.patience = patience  # Tham số kiên nhẫn

        self.dist = self._calc_dist()
        self.pheromone = np.ones((self.n, self.n))
        self.history = []

    def _calc_dist(self):
        d = np.zeros((self.n, self.n))
        for i in range(self.n):
            for j in range(self.n):
                d[i][j] = np.linalg.norm(
                    np.array(self.cities[i]) - np.array(self.cities[j])
                )
        return d

    def _select_next(self, cur, visited):
        probs = []
        for j in range(self.n):
            if j not in visited:
                tau = self.pheromone[cur][j] ** self.alpha
                eta = (1 / (self.dist[cur][j] + 1e-6)) ** self.beta
                probs.append((j, tau * eta))

        total = sum(p[1] for p in probs)
        if total == 0:
            unvisited = [node for node in range(self.n) if node not in visited]
            return random.choice(unvisited) if unvisited else probs[-1][0]

        r = random.random() * total
        s = 0
        for city, p in probs:
            s += p
            if s >= r:
                return city
        return probs[-1][0]

    def _build_tour(self):
        start = random.randint(0, self.n - 1)
        tour = [start]
        visited = {start}
        while len(tour) < self.n:
            nxt = self._select_next(tour[-1], visited)
            tour.append(nxt)
            visited.add(nxt)
        return tour

    def _update_pheromone(self, tours):
        self.pheromone *= (1 - self.rho)
        for tour in tours:
            length = total_distance(tour, self.cities)
            for i in range(len(tour)):
                a = tour[i]
                b = tour[(i + 1) % self.n]
                self.pheromone[a][b] += self.q / length
                self.pheromone[b][a] += self.q / length

    def run_stepwise(self):
        best_tour = None
        best_len = float("inf")
        no_improve = 0 

        for it in range(self.n_iter):
            # Kiểm tra kiên nhẫn
            if no_improve >= self.patience:
                yield it, best_tour, best_len, False # False = Đã dừng
                break

            tours = []
            improved = False
            for _ in range(self.n_ants):
                tour = self._build_tour()
                tours.append(tour)
                length = total_distance(tour, self.cities)
                
                if length < best_len:
                    best_len = length
                    best_tour = list(tour)
                    improved = True

            # Logic Patience
            if improved:
                no_improve = 0
            else:
                no_improve += 1

            self._update_pheromone(tours)
            self.history.append((it, best_len))
            
            # Trả về thêm biến 'improved' để GUI biết thời điểm update
            yield it, best_tour, best_len, improved
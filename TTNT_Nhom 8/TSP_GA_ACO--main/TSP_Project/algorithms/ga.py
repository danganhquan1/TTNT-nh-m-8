import random
import copy
from utils.tsp_utils import total_distance

class GA:
    def __init__(self, cities, pop_size=50, generations=500, mutation_rate=0.05, patience=200):
        self.cities = cities
        self.n = len(cities)
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.patience = patience
        self.history = []

    def _create_individual(self):
        path = list(range(self.n))
        random.shuffle(path)
        return path

    def _crossover(self, p1, p2):
        a, b = sorted(random.sample(range(self.n), 2))
        child = [-1] * self.n
        child[a:b] = p1[a:b]
        ptr = 0
        for x in p2:
            if x not in child:
                while child[ptr] != -1:
                    ptr += 1
                child[ptr] = x
        return child

    def _mutate(self, ind):
        if random.random() < self.mutation_rate:
            i, j = random.sample(range(self.n), 2)
            ind[i], ind[j] = ind[j], ind[i]

    def run_stepwise(self):
        pop = [self._create_individual() for _ in range(self.pop_size)]
        best = min(pop, key=lambda x: total_distance(x, self.cities))
        best_dist = total_distance(best, self.cities)
        
        no_improve = 0

        for gen in range(self.generations):
            if no_improve >= self.patience:
                yield gen, list(best), best_dist, False
                break

            new_pop = []
            new_pop.append(list(best)) # Elitism
            
            while len(new_pop) < self.pop_size:
                p1 = random.choice(pop)
                p2 = random.choice(pop)
                child = self._crossover(p1, p2)
                self._mutate(child)
                new_pop.append(child)

            pop = new_pop
            current_best = min(pop, key=lambda x: total_distance(x, self.cities))
            current_dist = total_distance(current_best, self.cities)

            improved = False
            if current_dist < best_dist:
                best = current_best
                best_dist = current_dist
                no_improve = 0
                improved = True
            else:
                no_improve += 1

            self.history.append((gen, best_dist))
            yield gen, list(best), best_dist, improved
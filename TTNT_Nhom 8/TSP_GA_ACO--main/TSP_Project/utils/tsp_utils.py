import random
import math
def generate_cities(n, width=800, height=600):
    # Tạo thành phố ngẫu nhiên trong khung hình, chừa lề 50px
    return [(random.randint(50, width - 50), random.randint(50, height - 50)) for _ in range(n)]

def total_distance(path, cities):
    dist = 0
    for i in range(len(path)):
        x1, y1 = cities[path[i]]
        # Nối điểm hiện tại với điểm kế tiếp (dùng % để nối điểm cuối về đầu)
        x2, y2 = cities[path[(i + 1) % len(path)]]
        dist += math.hypot(x1 - x2, y1 - y2)
    return dist
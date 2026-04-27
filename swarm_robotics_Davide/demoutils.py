"""
utils.py - Helper functions for food cluster generation.
Person A: implement generate_food_clusters with seed-controlled randomness.
"""

import numpy as np

def generate_food_clusters(width, height, num_clusters, coverage, random_gen):
    total_food_cells=int(height*width*coverage)
    cells_per_cluster=total_food_cells//num_clusters
    food_grid=np.zeros((width,height),dtype=int)
    for _ in range(num_clusters):
        cx=ramdom_gen.randint(0,width-1)
        cy=ramdom_gen.randint(0,height-1)
        placed=0
        attempts=0
        max_attempts=cells_per_cluster*10
        while (placed<cells_per_cluster) and (attempts<max_attempts):
            if food_grid[cx,cy]==0:
                amount=random_gen.randint(20,100)
                food_grid[cx,cy]=amount
                placed+=1
            dx=random_gen.choice([-1,0,1])
            dy=random_gen.choice([-1,0,1])
            cx+=dx
            cy+=dy
            cx=max(0,min(width-1,cx)) 
            cy=max(0,min(height-1,cy))
            attempts+=1
    return food_grid



    """
    Create a grid with clustered finite food.
    Parameters:
        width, height: grid dimensions
        num_clusters: number of food clusters (10-12)
        coverage: fraction of cells that contain food (0.15)
        random_gen: a seeded random.Random object (model.random)
    Returns:
        2D numpy array of ints, shape (width, height), 0 = no food, >0 = food amount.
    
    TODO: Implement algorithm:
    1. total_food_cells = int(width * height * coverage)
    2. cells_per_cluster = total_food_cells // num_clusters
    3. food_grid = np.zeros((width, height), dtype=int)
    4. For each cluster:
        - Choose a random seed cell (cx, cy) using random_gen.randint
        - placed = 0
        - while placed < cells_per_cluster:
            - if food_grid[cx,cy] == 0:
                - amount = random_gen.randint(20, 100)
                - food_grid[cx,cy] = amount
                - placed += 1
            - move to a random neighbor: dx,dy in [-1,0,1] using random_gen.choice
            - cx = max(0, min(width-1, cx+dx))
            - cy = max(0, min(height-1, cy+dy))
    5. Return food_grid
    Hint: Avoid infinite loops by limiting iterations; simple clusters are fine.
    """
    pass


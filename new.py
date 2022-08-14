import multiprocessing
from multiprocessing.connection import Listener, Client
import matplotlib
matplotlib.use('module://pygame_matplotlib.backend_pygame')
import matplotlib.pyplot as plt
import pygame
import numpy as np
from scipy import special
from math import comb
import scipy.stats
WIDTH, HEIGHT = 1200,600
WHITE = (255, 255, 255)
BLACK = (0,0,0)
FPS = 25
ADDRESS = ('localhost', 9000)
pygame.font.init()
POINTS_FONT = pygame.font.SysFont('comicsans', 30)
POINTS_FONT2 = pygame.font.SysFont('comicsans', 15)


def send():
    win1 = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    conn = Client(ADDRESS, authkey=b'sacharya')
    exiting = False
    pos = 1
    table = pygame.image.load("table.webp.webp")
    border = pygame.Rect(WIDTH/2 - 10, 0, 5, HEIGHT)
    normal_image = pygame.image.load("heads.png")
    normal = pygame.transform.scale(normal_image, (100,100))
    tails_image = pygame.image.load("tails.png")
    tails = pygame.transform.scale(tails_image, (100,100))
    side_image = pygame.image.load("coin_side.jpg")
    side = pygame.transform.scale(side_image, (100,100))
    all = [normal, tails, side]
    game_num = 1
    trials = 0
    total_heads = 0
    biased_prob_head = 0.8
    prev_games = None
    prev_heads = None
    num_heads = 0
    alpha = 5
    beta = 1
    x_axis = np.linspace(0,1,num=100,endpoint=True)


    def draw_coin():
        nonlocal all, pos, win1
        win1.blit(all[pos%3], (970, 360))
            


    def display_points():
        global POINTS_FONT, BLACK, WIDTH
        nonlocal prev_games, game_num, prev_heads, game_num, num_heads
        if not prev_games and not prev_heads:


            points = POINTS_FONT.render(f"Curr Game# {game_num} HEADS# {num_heads}",1,BLACK)
            win1.blit(points, (WIDTH-points.get_width()-10, 10))
        else:

            points0 = POINTS_FONT.render(f"Prev Games# {prev_games} HEADS# {prev_heads}",1,BLACK)
            points = POINTS_FONT.render(f"Curr Game# {game_num} HEADS# {num_heads}",1,BLACK)
            win1.blit(points0, (WIDTH-points0.get_width()-10, 10))
            win1.blit(points, (WIDTH-points.get_width()-10, 10+points.get_height()))
            




    def beta_distribution():
        nonlocal alpha, beta, trials, total_heads, x_axis
        gamma_funcs = special.gamma(alpha + beta + trials) / (special.gamma(alpha + total_heads) * special.gamma(beta + trials - total_heads))
        return (x_axis ** (alpha + total_heads - 1)) * ((1-x_axis)**(beta + trials - total_heads - 1)) * gamma_funcs

    def plot_distribution():
        nonlocal x_axis, win1
        global POINTS_FONT2
        fig, axes = plt.subplots(1, 1,)
        axes.plot(x_axis, beta_distribution(), color='green', label='test')
        axes.set_title("Probability of Head Dist.")
        fig.canvas.draw()
        win1.blit(fig, (0,50))
        win1.blit(POINTS_FONT2.render("Probability of head",1,BLACK), (250, 500))



    def update():
        nonlocal win1, border, table
        global WHITE
        win1.fill(WHITE)
        plot_distribution()
        display_points()
        pygame.draw.rect(win1, BLACK, border)
        win1.blit(table, (750, 300))
        draw_coin()
        pygame.display.update()





    pygame.init()
    while not exiting:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            pos += 1

        for event in pygame.event.get():
            if ( event.type == pygame.QUIT ):
                exiting = True
            if event.type == pygame.KEYUP:
                if trials % 10 == 0 and trials != 0:
                    prev_games = game_num
                    prev_heads = total_heads
                    game_num += 1
                    num_heads = 0
                trials += 1
                side = np.random.binomial(1, biased_prob_head)
                num_heads += side
                total_heads += side
                pos = side
                conn.send([trials, total_heads, prev_games, num_heads])
        update()
    pygame.quit()

def recv():
    win2 = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    exiting = False
    listener = Listener(ADDRESS, authkey=b'sacharya')
    conn = listener.accept()
    ys = np.linspace(0, 10, num=11, endpoint=True)
    pygame.init()

    def update(msg):
        nonlocal win2
        win2.fill(WHITE)
        plot_distribution(msg)
        pygame.display.update()


    def plot_distribution(msg):
        nonlocal ys, win2
        global POINTS_FONT2
        trials, total_heads, prev_games, num_heads = msg
        if msg:
            exp_r = total_heads/trials
        else:
            exp_r = 1
        y_axis = get_binomial_pmfs(ys, exp_r)
        fig, axes = plt.subplots(1, 1,)
        colors = ["g", "g", "g", "g", "g", "g", "g", "r", "r", "r", "r"]

        axes.bar(ys, y_axis, color=colors)
        axes.set_title("Probability of Head Dist.")
        fig.canvas.draw()
        win2.blit(fig, (0,50))
        win2.blit(POINTS_FONT2.render("Probability of head",1,BLACK), (250, 500))


    def get_binomial_pmfs(arr,r):
        def get(x):
            return scipy.stats.binom(10, r).pmf(x)
        np.vectorize(get)
        return get(arr)







    while not exiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if ( event.type == pygame.QUIT ):
                exiting = True
    
        msg = conn.recv()
        update(msg)
    pygame.quit()



if __name__ == "__main__":
    t1 = multiprocessing.Process(target=send).start()
    t2 = multiprocessing.Process(target=recv).start()
    t1.join()
    t2.join()

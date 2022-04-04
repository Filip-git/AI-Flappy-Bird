from distutils.command.config import config
from re import T
from tkinter import CENTER
import pygame
import neat
import time
import os
import random
pygame.font.init()

WIN_WIDTH = 500  #velikim slovima jer je konstanta
WIN_HEIGHT = 800 #velikim slovima jer je konstanta
pygame.display.set_caption('AI FLAPPY BIRD')
pygame.display.set_icon(pygame.image.load(os.path.join("assets", "icon.png")))

PTICE_SLIKE =  [  pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird1.png"))), 
            pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird2.png"))), 
            pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird3.png")))] #iz mape assets uzimamo sliku bird3.png

CIJEV = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "pipe.png"))) #sa ovim scale 2x uvecavamo sliku za 2x
POD = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "base.png")))
POZADINA = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)

GEN = 0
broj_ptica = 100

class Bird:
    SLIKE = PTICE_SLIKE
    MAX_ROTACIJA = 25 #naginjanje ptice (slike ptice)
    ROT_VEL = 20 #koliko se rotira svaki frame per second
    ANIMATION_TIME = 5 #koliko brzo maše krilima

    def __init__(self, x, y):
        self.x = x #x pozicija
        self.y = y #y pozicija
        self.tilt = 0 #naginjanje
        self.tick_count = 0 #skok i pad
        self.vel = 0 #velocity
        self.height = self.y 
        self.img_count = 0 #da znam koja mi slika treba za pticu
        self.img = self.SLIKE[0] #slike ptica iz niza

    def jump(self):
        self.vel = -10.5 #prema gore je - , prema dole je + , lijevo je - , desno je + (jer ide od gornjeg desnog kuta (0,0)) 
        self.tick_count = 0 #ovdje pratimo kad je bio zadnji skok
        self.height = self.y #da se zna odakle je ptice skocila

    def move(self):
        self.tick_count += 1 

        d = self.vel*self.tick_count + 1.5*self.tick_count**2 #fizika pokreta skoka i pada , self.tick_count mjeri

        if d >= 16: #ako se kreće (dole) brze od 16px da ostane na 16
            d = 16 

        if d < 0: #za skakanje fizika i podesavanje visine
            d -= 2
        
        self.y = self.y + d #pomjeranje ptice pomalo gore ili dole

        if d < 0 or self.y < self.height + 50: #ako ide gore ili ako je iznad zadnje pozicije
            if self.tilt < self.MAX_ROTACIJA: #da se ne okrene naopako ptica
                self.tilt = self.MAX_ROTACIJA
        else:  #ako ne ide dole, okrecem pticu dole
            if self.tilt > -90: 
                self.tilt -= self.ROT_VEL 
    
    def draw (self, win):
        self.img_count += 1

        #mijenjanje slike ptice 
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.SLIKE[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.SLIKE[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.SLIKE[2]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.SLIKE[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.SLIKE[0]
            self.img_count = 0
        
        if self.tilt <= -80: #kad pada dole da ne maše krilima
            self.img = self.SLIKE[1] 
            self.img_count = self.ANIMATION_TIME*2 #kad skoči gore da ne preskače frame

        rotated_image = pygame.transform.rotate(self.img, self.tilt) #rotiranje slike 
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center) #sa stackoverflow 
        win.blit(rotated_image, new_rect.topleft) 

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

   


def draw_window(win, birds, pipes, base, score, gen, broj_ptica):
    win.blit(POZADINA, (0,0)) #blitanje na prozor
    for pipe in pipes:
        pipe.draw(win)

    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    generacija = STAT_FONT.render("Gen: " + str(gen),1,(255,255,255))
    win.blit(generacija, (10, 10))

    broj_ptica = STAT_FONT.render("Alive: " + str(broj_ptica),1,(255,255,255))
    win.blit(broj_ptica, (10, 50))
  
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update() #refresh display


class Pipe:
    GAP = 175 #razmak izmedu cijevi
    VEL = 5 #brzina ptice

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0 
        self.bottom = 0 
        self.PIPE_TOP = pygame.transform.flip(CIJEV, False, True) #ista je slika pa da se okrene naopako ovako se okrece
        self.PIPE_BOTTOM = CIJEV

        self.passed = False #je li prosla ptica zbog AI
        self.set_height() #odredivanje top i bottom i gdje su, bit će random

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height() #u negativnoj y osi cratit pa da ne prekrije cijeli ekran nego npr. samo pola
        self.bottom = self.height + self.GAP #donja ne mora biti u minusu jer se gleda gornji desni vrh i onda je on na ekranu u plus koordinatama i racuna se gornja + GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)  #bottom
        t_point = bird_mask.overlap(top_mask, top_offset)  #top
    
        if t_point or b_point:
            return True
        
        return False


class Base:  #za pod, jer se i slika mora micati pa kad se pomjeri do kraja da se vrati oept na pocetak i krene iz pocetka
    VEL = 5 #kao kod pipe da idu istom brzinom
    WIDTH = POD.get_width()
    IMG = POD 

    def __init__(self, y):
        self.y = y
        self.x1 = 0 #prva slika
        self.x2 = self.WIDTH #druga odmah iza nje

    def move(self):   #dvije su iste slike i zajedno se pomjeraju i kad se prva pomjeri skroz do kraja i "skloni" s prozora ide opet na pocetak i opet ide u lijevo i tako u krug
        self.x1 -= self.VEL #pomjeranje slike 1
        self.x2 -= self.VEL #pomjeranje slike 2

        if self.x1 + self.WIDTH < 0: #provjera prve je li na ekranu
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0: #provjera druge je li na ekranu
            self.x2 = self.x1 + self.WIDTH

    def draw(self,win): #blitanje pozadine na ekran
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))



def main(genomes, config):
    global GEN
    global broj_ptica
    broj_ptica = 100
    GEN += 1
    nets = []
    ge = []
    birds = []

    for _,g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(700)]
    score = 0
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    run = True

    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: #na X se gasi
                run = False                
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break


        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()

        #bird.move() #pokretanje pomjeranja ptice
        base.move() #pokretanje pomjeranja baze
        add_pipe = False
        rem = [] #lista remove
        
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird): #ako se sudare ptica i cijev
                    ge[x].fitness -= 1 #kadgod ptica udari u cijev fitness -1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                    broj_ptica -= 1
                    #birds.remove(bird) #uklonjena ta ptica

                if not pipe.passed and pipe.x < bird.x:
                        pipe.passed = True
                        add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0: #ako je cijev izvan prozora
                    rem.append(pipe) #dodaj u listu tu cijev koja je izvan prozora

            pipe.move()
        
        if add_pipe: #ako smo prosli cijev dodaj bod
            score += 1
            for g in ge:
                g.fitness += 5 #povecanje fitnessa nakon prolaska kroz cijev
            pipes.append(Pipe(700))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() > 730 or bird.y < 0: #ako je ptica pala na pod, ili ide iznad ekrana preko cijevi
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
                broj_ptica -= 1

        draw_window(win, birds, pipes, base, score, GEN, broj_ptica)


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)


    p = neat.Population(config) #populacija stavljena u config file
    p.add_reporter(neat.StdOutReporter(True))  #statistika
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    winner = p.run(main,50)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
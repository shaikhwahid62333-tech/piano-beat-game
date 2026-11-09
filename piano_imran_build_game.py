
import pygame
import random
import math
import array
import sys

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

# AUDIO
AUDIO = False
notes = []
music = None

try:
    pygame.mixer.init()
    AUDIO = True
except:
    pass

# SCREEN
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()

clock = pygame.time.Clock()

font = pygame.font.Font(None, 42)
big = pygame.font.Font(None, 75)

# CLASSIC COLORS
BLACK = (5, 8, 25)
WHITE = (255, 255, 255)
BLUE = (20, 90, 190)
CYAN = (20, 220, 255)
PINK = (255, 40, 180)

# SETTINGS
LANES = 4
LANE_W = W // 4
TILE_H = 125
HIT_LINE = H - 170

tiles = []
particles = []

score = 0
best_score = 0
combo = 0

speed = 8
spawn_delay = 0.65
spawn_timer = 0

game_state = "menu"
last_tap = 0

# --------------------
# PIANO SOUND
# --------------------

def make_note(freq):

    samples = array.array("h")
    rate = 22050

    for i in range(5000):

        t = i / rate
        envelope = math.exp(-6 * t)

        wave = (
            math.sin(2 * math.pi * freq * t)
            + 0.3 * math.sin(2 * math.pi * freq * 2 * t)
        )

        samples.append(int(9000 * envelope * wave))

    return pygame.mixer.Sound(buffer=samples.tobytes())


if AUDIO:
    try:
        notes = [
            make_note(f)
            for f in [262, 294, 330, 349, 392, 440, 494, 523]
        ]

        for n in notes:
            n.set_volume(0.7)

        # Background melody
        sequence = [
            262, 330, 392, 523,
            392, 330, 294, 392,
            349, 440, 523, 440,
            392, 330, 294, 262
        ]

        samples = array.array("h")

        for freq in sequence:

            for i in range(5500):

                t = i / 22050
                envelope = min(1, i / 350) * math.exp(-2*t)

                value = int(
                    3000 * envelope *
                    math.sin(2 * math.pi * freq * t)
                )

                samples.append(value)

        music = pygame.mixer.Sound(buffer=samples.tobytes())
        music.set_volume(0.25)

    except:
        AUDIO = False


def play_note():

    if AUDIO and notes:
        random.choice(notes).play()


def start_music():

    if AUDIO and music:
        music.play(-1)


# --------------------
# RESET
# --------------------

def reset_game():

    global tiles, score, combo
    global speed, spawn_delay, spawn_timer

    tiles = []
    score = 0
    combo = 0

    speed = 8
    spawn_delay = 0.65
    spawn_timer = 0


# --------------------
# TEXT
# --------------------

def draw_text(txt, f, color, x, y):

    img = f.render(txt, True, color)

    screen.blit(
        img,
        (x-img.get_width()//2,
         y-img.get_height()//2)
    )


# --------------------
# SPAWN
# --------------------

def spawn_tile():

    lane = random.randint(0, 3)

    tiles.append({
        "lane": lane,
        "y": -TILE_H
    })


# --------------------
# BACKGROUND
# --------------------

def draw_background():

    screen.fill(BLACK)

    for i in range(1, 4):

        x = i * LANE_W

        pygame.draw.line(
            screen,
            (35, 45, 75),
            (x, 0),
            (x, H),
            2
        )

    pygame.draw.line(
        screen,
        PINK,
        (0, HIT_LINE),
        (W, HIT_LINE),
        4
    )


# --------------------
# TILES
# --------------------

def draw_tiles():

    for tile in tiles:

        x = tile["lane"] * LANE_W + 6
        y = int(tile["y"])

        rect = pygame.Rect(
            x, y,
            LANE_W-12,
            TILE_H
        )

        pygame.draw.rect(
            screen,
            BLUE,
            rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            CYAN,
            rect,
            4,
            border_radius=12
        )

        inner = rect.inflate(-16, -16)

        pygame.draw.rect(
            screen,
            (15, 75, 160),
            inner,
            border_radius=8
        )


# --------------------
# PARTICLES
# --------------------

def create_particles(x, y):

    for i in range(8):

        particles.append([
            x, y,
            random.uniform(-3, 3),
            random.uniform(-4, 2),
            20
        ])


def update_particles():

    for p in particles[:]:

        p[0] += p[2]
        p[1] += p[3]
        p[4] -= 1

        if p[4] <= 0:
            particles.remove(p)


def draw_particles():

    for p in particles:

        pygame.draw.circle(
            screen,
            CYAN,
            (int(p[0]), int(p[1])),
            3
        )


# --------------------
# GAME SCREEN
# --------------------

def draw_game():

    draw_background()
    draw_tiles()
    draw_particles()

    draw_text(
        "SCORE: " + str(score),
        font, WHITE,
        W//2, 40
    )

    draw_text(
        "BEST: " + str(best_score),
        font, CYAN,
        W//2, 85
    )

    draw_text(
        "COMBO: " + str(combo),
        font, WHITE,
        W//2, 130
    )

    draw_text(
        "TAP THE BLUE TILES",
        font, WHITE,
        W//2, H-65
    )


# --------------------
# TOUCH
# --------------------

def handle_tap(x, y):

    global score, combo
    global game_state, best_score
    global speed, spawn_delay, last_tap

    now = pygame.time.get_ticks()

    if now - last_tap < 65:
        return

    last_tap = now

    if game_state == "menu":

        reset_game()
        game_state = "playing"
        start_music()
        return

    if game_state == "over":

        reset_game()
        game_state = "playing"
        start_music()
        return

    if game_state != "playing":
        return

    # Select lane
    lane = max(0, min(3, int(x // LANE_W)))

    candidates = []

    for tile in tiles:

        if tile["lane"] == lane:

            rect = pygame.Rect(
                lane * LANE_W + 6,
                int(tile["y"]),
                LANE_W-12,
                TILE_H
            )

            if rect.collidepoint(x, y):
                candidates.append(tile)

    if not candidates:
        return

    # Nearest tile
    selected = min(
        candidates,
        key=lambda t: abs(t["y"] + TILE_H/2 - y)
    )

    tiles.remove(selected)

    create_particles(
        lane * LANE_W + LANE_W//2,
        int(selected["y"] + TILE_H//2)
    )

    score += 1
    combo += 1

    best_score = max(best_score, score)

    play_note()

    # SPEED INCREASE
    speed = min(
        27,
        8 + (score // 5) * 1.5
    )

    # SPAWN INCREASE
    spawn_delay = max(
        0.25,
        0.65 - (score // 10) * 0.05
    )


# --------------------
# UPDATE
# --------------------

def update_game(dt):

    global spawn_timer
    global game_state, best_score, combo

    spawn_timer += dt

    if spawn_timer >= spawn_delay:

        spawn_timer = 0
        spawn_tile()

    for tile in tiles[:]:

        tile["y"] += speed * 60 * dt

        if tile["y"] > HIT_LINE:

            best_score = max(best_score, score)

            combo = 0
            game_state = "over"

            pygame.mixer.stop()
            break

    update_particles()


# --------------------
# MENU
# --------------------

def draw_menu():

    screen.fill(BLACK)

    draw_text(
        "PIANO BEAT",
        big, CYAN,
        W//2, H//3
    )

    draw_text(
        "MUSIC GAME",
        font, WHITE,
        W//2, H//3+65
    )

    button = pygame.Rect(
        W//2-145, H//2,
        290, 90
    )

    pygame.draw.rect(
        screen, BLUE, button,
        border_radius=15
    )

    pygame.draw.rect(
        screen, CYAN, button,
        3, border_radius=15
    )

    draw_text(
        "PLAY",
        big, WHITE,
        W//2, H//2+45
    )


# --------------------
# GAME OVER
# --------------------

def draw_game_over():

    screen.fill(BLACK)

    draw_text(
        "GAME OVER",
        big, PINK,
        W//2, H//3
    )

    draw_text(
        "SCORE: " + str(score),
        font, WHITE,
        W//2, H//2
    )

    draw_text(
        "BEST: " + str(best_score),
        font, CYAN,
        W//2, H//2+50
    )

    button = pygame.Rect(
        W//2-145,
        H//2+100,
        290, 85
    )

    pygame.draw.rect(
        screen, BLUE, button,
        border_radius=15
    )

    pygame.draw.rect(
        screen, CYAN, button,
        3, border_radius=15
    )

    draw_text(
        "RESTART",
        big, WHITE,
        W//2, H//2+142
    )


# --------------------
# MAIN LOOP
# --------------------

running = True

while running:

    dt = min(clock.tick(60)/1000, 0.05)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

        elif event.type == pygame.FINGERDOWN:

            handle_tap(
                int(event.x * W),
                int(event.y * H)
            )

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:
                handle_tap(*event.pos)

    if game_state == "menu":

        draw_menu()

    elif game_state == "playing":

        update_game(dt)
        draw_game()

    elif game_state == "over":

        draw_game_over()

    pygame.display.flip()


pygame.quit()
sys.exit()

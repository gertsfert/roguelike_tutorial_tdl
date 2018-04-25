import tdl

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20
MAP_WIDTH = 80
MAP_HEIGHT = 45


tdl.set_font('libtcod_fonts/arial10x10.png', greyscale=True, altLayout=True)

root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title='Roguelike', fullscreen=False)
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
color_dark_wall = (0, 0, 100)
color_dark_ground = (50, 50, 150)


class GameObject:
    # this is a generic object: the player, a monster, an item, the stairs...
    # it's always represented by a character on screen.
    def __init__(self, x, y, char, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    def move(self, dx, dy):
        # check if movement blocked
        if not my_map[self.x + dx][self.y + dy].blocked:
            # move by the given amount
            self.x += dx
            self.y += dy

    def draw(self):
        # draw the character that represents this object at its position
        con.draw_char(self.x, self.y, self.char, self.color)

    def clear(self):
        # erase the character that represents this object
        con.draw_char(self.x, self.y, ' ', self.color, bg=None)


class Tile:
    # a tile of the map and its properties
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        # by default if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked

        self.block_sight = block_sight


def make_map():
    global my_map

    # fill map with "unblocked" tiles
    # uses nested list comprehension
    my_map = [[Tile(False)
              for y in range(MAP_HEIGHT)]
              for x in range(MAP_WIDTH)]

    my_map[30][22].blocked = True
    my_map[30][22].block_sight = True
    my_map[50][22].blocked = True
    my_map[50][22].block_sight = True


def handle_keys():
    global playerx, playery

    user_input = tdl.event.key_wait()

    # system keys
    if user_input.key == 'ENTER' and user_input.alt:
        # ALT + ENTER: Toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        return True  # exit game

    # movement keys
    if user_input.key == 'UP':
        player.move(0, -1)
    elif user_input.key == 'DOWN':
        player.move(0, 1)
    elif user_input.key == 'LEFT':
        player.move(-1, 0)
    elif user_input.key == 'RIGHT':
        player.move(1, 0)


def render_all():
    # draw all objects in the list
    for obj in objects:
        obj.draw()

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            wall = my_map[x][y].block_sight
            if wall:
                con.draw_char(x, y, None, fg=None, bg=color_dark_wall)
            else:
                con.draw_char(x, y, None, fg=None, bg=color_dark_ground)

    root.blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)


tdl.setFPS(LIMIT_FPS)

player = GameObject(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, '@', (255, 255, 255))
npc = GameObject(SCREEN_WIDTH//2 - 5, SCREEN_HEIGHT//2, '@', (255, 255, 0))
objects = [npc, player]

make_map()

# main loop
while not tdl.event.is_window_closed():
    render_all()

    tdl.flush() # draw frame

    # clear objects
    for obj in objects:
        obj.clear()

    # handle keys and exit game if needed
    exit_game = handle_keys()
    if exit_game:
        break

import tdl
from random import randint
import colors
import math

# windows size in characters
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# map size in characters
MAP_WIDTH = 80
MAP_HEIGHT = 45

REALTIME = False
LIMIT_FPS = 20

# room properties
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

MAX_ROOM_MONSTERS = 3

# Lighting Properties
FOV_ALGO = 'BASIC' # default fox algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

color_dark_wall = (0, 0, 150)
color_light_wall = (130, 110, 50)
color_dark_ground = (50, 50, 150)
color_light_ground = (200, 180, 50)


class GameObject:
    # this is a generic object: the player, a monster, an item, the stairs...
    # it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None):
        self.name = name
        self.blocks = blocks
        self.x = x
        self.y = y
        self.char = char
        self.color = color

        self.fighter = fighter
        if self.fighter:  # let the fighter component know who owns it
            self.fighter.owner = self

        self.ai = ai
        if self.ai:  # let the AI component know who owns it
            self.ai.owner = self

    def move(self, dx, dy):
        # check if movement blocked
        if not is_blocked(self.x + dx, self.y + dy):
            # move by the given amount
            self.x += dx
            self.y += dy

    def draw(self):
        global visible_tiles

        # check if visible
        if (self.x, self.y) in visible_tiles:
            # draw the character that represents this object at its position
            con.draw_char(self.x, self.y, self.char, self.color)

    def clear(self):
        # erase the character that represents this object
        con.draw_char(self.x, self.y, ' ', self.color, bg=None)

    def move_towards(self, target_x, target_y):
        # vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx **2 + dy ** 2)

        # normalize it to length 1 (preserving direction), then round it
        # and convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

class Fighter:
    # combat-related properties and methods (monster, player, NPC)
    def __init__(self, hp, defense, power):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power


class BasicMonster:
    # AI for a basic monster
    def take_turn(self):
        # a basic monster takes its turn. if you can see it, it can see you
        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:
            # move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)

            elif player.fighter.hp > 0:
                print('The attack of the {} bounces off your shiny metal armour'
                      .format(monster.name))


class Rect:
    # a rectangle on the map, used to characterize a room
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2)//2
        center_y = (self.y1 + self.y2)//2
        return center_x, center_y

    def intersect(self, other):
        # returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


class Tile:
    # a tile of the map and its properties
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        # by default if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked

        self.block_sight = block_sight

        self.explored = False


def create_room(room):
    global my_map
    # go through the tiles in the rectangle and make them passable
    # leave one tile out in all directions (so that if two rooms are next to each-other
    # but not overlapping, there will always be one wall separating them.
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            my_map[x][y].blocked = False
            my_map[x][y].block_sight = False


def create_h_tunnel(x1, x2, y):
    global my_map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False


def create_v_tunnel(y1, y2, x):
    global my_map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False


def make_map():
    global my_map

    # fill map with "blocked" tiles
    my_map = [[Tile(True)
           for y in range(MAP_HEIGHT)]
           for x in range(MAP_WIDTH)]

    # create random rooms
    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        # random width and height
        w = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        # random position without going out of the boundaries of the map
        x = randint(0, MAP_WIDTH-w-1)
        y = randint(0, MAP_HEIGHT-h-1)

        new_room = Rect(x, y, w, h)

        # run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        # start player in center of first room
        if not failed:
            # this means there are no intersections, so this room is valid

            # "paint" it to the map's tiles
            create_room(new_room)

            # center coordinates of the new room, will be useful later
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                # this is the first room that the player starts
                player.x = new_x
                player.y = new_y

            else:
                # all rooms after the first:
                # connect it to the previous room with a tunnel

                # center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms - 1].center()

                # flip a coin
                if randint(0, 1):
                    # first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    # first move vertically then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            # add objects to room
            place_objects(new_room)

            # append new room to the list
            rooms.append(new_room)
            num_rooms += 1


def place_objects(room):
    # choose random number of monsters
    num_monsters = randint(0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        x = randint(room.x1, room.x2)
        y = randint(room.y1, room.y2)

        # check if blocked
        if not is_blocked(x, y):
            if randint(0, 100) < 80: # 80% chance of getting an orc
                # create an orc
                fighter_component = Fighter(hp = 10, defense=0, power=3)
                ai_component = BasicMonster()
                monster = GameObject(x, y, 'o', 'orc', colors.desaturated_green,
                                     blocks=True, fighter=fighter_component, ai=ai_component)
            else:
                # create a troll
                fighter_component = Fighter(hp=16, defense=1, power=4)
                ai_component = BasicMonster()
                monster = GameObject(x, y, 'T', 'troll', colors.darker_green,
                                     blocks=True, fighter=fighter_component, ai=ai_component)

            objects.append(monster)


def is_blocked(x, y):
    # first test the map tile
    if my_map[x][y].blocked:
        return True

    # now check for any blocking objects
    for obj in objects:
        if obj.blocks and obj.x == x and obj.y == y:
            return True

    return False


def handle_keys():
    global playerx, playery
    global fov_recompute

    if REALTIME:
        keypress = False
        for event in tdl.event.get():
            if event.type == 'KEYDOWN':
                user_input = event
                keypress = True
        if not keypress:
            return

    else: # turn-based
        user_input = tdl.event.key_wait()

    # system keys
    if user_input.key == 'ENTER' and user_input.alt:
        # ALT + ENTER: Toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        return 'exit'  # exit game

    if game_state == 'playing':
        # movement keys
        if user_input.key == 'UP':
            player_move_or_attack(0, -1)
        elif user_input.key == 'DOWN':
            player_move_or_attack(0, 1)
        elif user_input.key == 'LEFT':
            player_move_or_attack(-1, 0)
        elif user_input.key == 'RIGHT':
            player_move_or_attack(1, 0)
        else:
            return 'didnt-take-turn'


def player_move_or_attack(dx, dy):
    global fov_recompute

    # the coordinates the player is moving to/attacking
    x = player.x + dx
    y = player.y + dy

    # try to find an attackable object there
    target = None
    for obj in objects:
            if obj.x == x and obj.y == y:
                target = obj
                break

    # attack if target found, move otherwise
    if target is not None:
        print('The {} laughs at your puny efforts to attack her!'
              .format(target.name))
    else:
        player.move(dx, dy)
        fov_recompute = True


def is_visible_tile(x, y):
    global my_map

    if x >= MAP_WIDTH or x < 0:
        return False
    elif y >= MAP_HEIGHT or y < 0:
        return False
    elif my_map[x][y].blocked:
        return False
    elif my_map[x][y].block_sight:
        return False
    else:
        return True


def render_all():
    global fov_recompute
    global visible_tiles

    if fov_recompute:
        # recompute FOV if needed (the player moved or something)
        fov_recompute = False
        visible_tiles = tdl.map.quickFOV(player.x, player.y,
                                         is_visible_tile,
                                         fov=FOV_ALGO,
                                         radius=TORCH_RADIUS,
                                         lightWalls=FOV_LIGHT_WALLS)

        # set bg color according to the FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = (x, y) in visible_tiles
                wall = my_map[x][y].block_sight
                if not visible:
                    # out of player FOV
                    # if it's not visible right now, the player can only see it if its explored
                    if my_map[x][y].explored:
                        if wall:
                            con.draw_char(x, y, None, fg=None, bg=color_dark_wall)
                        else:
                            con.draw_char(x, y, None, fg=None, bg=color_dark_ground)
                else:
                    # visible
                    if wall:
                        con.draw_char(x, y, None, fg=None, bg=color_light_wall)
                    else:
                        con.draw_char(x, y, None, fg=None, bg=color_light_ground)
                    my_map[x][y].explored = True

    # draw all objects in the list
    for obj in objects:
        obj.draw()

    root.blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)


# ------------------------------------------------------------------------- #
# Initialization and main loop                                              #
# ------------------------------------------------------------------------- #

tdl.set_font('libtcod_fonts/arial10x10.png', greyscale=True, altLayout=True)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title='Roguelike', fullscreen=False)
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
tdl.setFPS(LIMIT_FPS)

# create object representing the player
fighter_component = Fighter(hp=30, defense=2, power=5)
player = GameObject(0, 0, '@', 'player', colors.white, blocks=True, fighter=fighter_component)

objects = [player]

fov_recompute = True

make_map()

game_state = 'playing'
player_action = None

# main loop
while not tdl.event.is_window_closed():
    # draw all objects in list
    render_all()
    tdl.flush()

    # clear objects before they are redrawn
    for obj in objects:
        obj.clear()

    # handle keys and exit game if needed
    player_action= handle_keys()
    if player_action == 'exit':
        break

    # let monsters take their turn
    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for obj in objects:
            if obj.ai:
                obj.ai.take_turn()
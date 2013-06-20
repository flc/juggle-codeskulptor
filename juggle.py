import simplegui
import math
import random


CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
BALL_IMG_URL = "https://dl.dropboxusercontent.com/u/33683340/sb_1.png"
BALL_IMG_SIZE = (256, 256)

#SOUND_URL_PATTERN = "https://dl.dropboxusercontent.com/u/33683340/juggle_sounds/ball/%02d.mp3"
#SOUND_URLS = [SOUND_URL_PATTERN % i for i in range(1, 7)]
#SOUNDS = [simplegui.load_sound(url) for url in SOUND_URLS]
SOUNDS = []

BALL_RADIUS = BALL_IMG_SIZE[0] / 4
BALL_IMG = simplegui.load_image(BALL_IMG_URL)
GRAVITY = 0.4
STOP_THRESHOLD = GRAVITY  * 6.5  # based on experiments, better solution needed
KICK_POWER = 10
ELASTICITY_Y = 0.7  #  how high the ball bounces after it hits the ground
ELASTICITY_X = 0.7
PI = math.pi
PI2 = PI * 2


def distance(p1, p2):
    """Helper function to return the distance of
    two points."""
    return math.sqrt(
        (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) **2
        )


class ImageLoader(object):
    """A generic class for loading images. It's useful if
    you want to make sure that some images are loaded.
    You can query the progress and the number of loaded images as well."""

    def __init__(self, images, finished_callback=None, check_interval=250):
        self.images = images
        self.images_len = len(images)
        self.timer = simplegui.create_timer(check_interval, self._timer_handler)
        self.finished_callback = finished_callback

        self.total_count = len(images)
        self.loaded_count = 0
        self.progress = 0

    def _timer_handler(self):
        loaded = 0
        for img in self.images:
            if img.get_width() == 0:
                # not loaded
                continue
            loaded += 1

        self.loaded_count = loaded
        self.progress = int((self.loaded_count / float(self.total_count)) * 100)
        if not self.finished():
            return

        self.stop()
        if self.finished_callback:
            self.finished_callback()

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def finished(self):
        return self.loaded_count == self.total_count


class Cloud(object):
    """
    Just a very lame class that builds a "cloud" from a
    few circles with a totally ad-hoc algorythm
    I just came up with.
    """

    def __init__(self, pos, size=None, vel=None):
        """
        :param pos:
            the center of the first circle component
        :param size:
            from how many circle components the cloud builds
            if None, it randomizes the size
        :param velocity:
            if None, it randomizes the velocity
        """
        self.pos_x, self.pos_y = pos

        if size is None:
            size = random.randrange(5, 10)

        if vel is None:
            vel = (random.random() * 0.5, random.random() * 0.001)
        self.vel_x, self.vel_y = vel

        self.rad = [random.randrange(20, 40) for i in range(size)]
        self.dist_x = [random.randrange(i // 4, i) for i in self.rad]
        self.dist_y = [random.randrange(i // 4, i // 2) for i in self.rad]

    def move(self):
        self.pos_x += self.vel_x
        self.pos_y += self.vel_y

    def draw(self, canvas):
        pos_x = self.pos_x
        # unfortunately no enumerate in codeskluptor
        i = 0
        for rad, dist_x, dist_y in zip(self.rad,
                                       self.dist_x,
                                       self.dist_y):
            if i == 0:
                pos_x = self.pos_x
                pos_y = self.pos_y
            else:
                pos_x += dist_x
                if i % 2 == 0:
                    pos_y = self.pos_y + dist_y
                else:
                    pos_y = self.pos_y - dist_y
            canvas.draw_circle(
                 (pos_x, pos_y),
                 rad, 1, "white", "White")
            i += 1

    def is_gone(self, width):
        if self.pos_x - self.rad[0] > width:
            return True
        return False


class Ball(object):

    def __init__(self, game, radius=BALL_RADIUS, init_pos=None):
        self.game = game

        self.set_radius(radius)

        self.img = BALL_IMG
        self.img_size = BALL_IMG_SIZE
        self.img_center = [BALL_IMG_SIZE[0] / 2, BALL_IMG_SIZE[1] / 2]

        if not init_pos:
            init_pos = self.get_init_pos()
        self.pos_x, self.pos_y = init_pos

        self.vel_x = 0
        self.vel_y = 0

        self.rot = 0  # rotation
        self.rot_vel = 0 # rotation speed

    def set_radius(self, radius):
        self.radius = radius
        self.diameter = self.radius * 2

    def set_vel_x(self, value):
        self.vel_x = value
        self.rot_vel = (self.vel_x / 180) * PI

    def get_pos(self):
        return (self.pos_x, self.pos_y)

    def get_init_pos(self):
        return [CANVAS_WIDTH / 2,
                self.game.height - self.game.ground_height- self.radius]

    def click(self, click_pos):
        dist = distance(self.get_pos(), click_pos)
        if dist > self.radius:
            # ignore click
            return

        self.kick(click_pos)

    def kick(self, pos):
        self.game.scored()

        self.vel_y = -KICK_POWER

        dist_from_center = self.pos_x - pos[0]
        ratio = dist_from_center / self.radius

        self.set_vel_x(ratio * KICK_POWER)
#        print self.rot_vel

    def stop(self):
        self.vel_y = 0
        self.vel_x = 0

    def move(self):
        self.pos_x += self.vel_x
        self.pos_y += self.vel_y
        self.vel_y += GRAVITY

        self.rot += self.rot_vel
        if self.rot > PI2:
            self.rot -= PI2

        if self.pos_y + self.radius > self.game.height - self.game.ground_height:
            self.pos_y = self.game.height - self.game.ground_height - self.radius
            a = self.pos_y + self.radius
            b = self.game.height - self.game.ground_height
            if abs(self.vel_y) > 0:
                # hit the ground
                self.game.ball_falled(self)
                self.set_vel_x(self.vel_x * 0.9)
                if abs(self.vel_y) < STOP_THRESHOLD:
                    self.vel_y = 0
                else:
                    self.pos_y = self.game.height - self.game.ground_height - self.radius
                    self.vel_y *= -ELASTICITY_Y

        if self.vel_y == 0:
            self.set_vel_x(self.vel_x * 0.97)
            if abs(self.vel_x) < 0.2:
                self.set_vel_x(0)

        # hit left wall
        if self.pos_x - self.radius < 0:
            self.pos_x = self.radius
            self.set_vel_x(self.vel_x * -ELASTICITY_X)
            self.game.ball_hit_left_wall(self)

        # hit right wall
        if self.pos_x + self.radius > CANVAS_WIDTH:
            self.pos_x = CANVAS_WIDTH - self.radius
            self.set_vel_x(self.vel_x * -ELASTICITY_X)
            self.game.ball_hit_right_wall(self)

    def update(self):
        self.move()

    def draw(self, canvas):
        # The optional last parameter is the rotation in radians.
        canvas.draw_image(self.img,
                          self.img_center,
                          self.img_size,
                          self.get_pos(),
                          (self.diameter, self.diameter),
                          self.rot)


class Game(object):
    title = "Juggle"

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.balls = []
        self.score = 0
        self.best_score = 0
        self.current_radius = BALL_RADIUS
        self.radius_shrink = False
        self.ground_height = 50

        self.clouds = []
        self.sounds = SOUNDS

        self.img_loader = ImageLoader([BALL_IMG])

    def play_sound(self):
        if SOUNDS:
            r = random.randrange(0, len(SOUNDS))
            sound = SOUNDS[r]
            sound.rewind()
            sound.play()

    def scored(self):
        self.play_sound()
        self.score += 1
        if self.score % 10 == 0:
            self.shrink_radius()

    def set_radius(self, radius):
        self.current_radius = radius
        for ball in self.balls:
            ball.set_radius(self.current_radius)

    def shrink_radius(self):
        if not self.radius_shrink:
            return
        self.set_radius(int(self.current_radius * 0.9))

    def set_radius_shrink(self, value):
        self.radius_shrink = value
        if value:
            text = "Disable radius shrink"
        else:
            text = "Enable radius shrink"
        self.rs_button.set_text(text)

    def toggle_radius_shrink(self):
        """Button handler."""
        return self.set_radius_shrink(not self.radius_shrink)

    def ball_falled(self, ball):
        self.play_sound()
        if self.score > self.best_score:
            self.best_score = self.score
        self.score = 0
        self.set_radius(BALL_RADIUS)

    def ball_hit_wall(self, ball, right=False):
        """
        :param ball: Ball obj that hit the wall
        :param right: True if the wall is the right wall
        """
        self.play_sound()

    def ball_hit_left_wall(self, ball):
        """
        Shortcut method.
        """
        return self.ball_hit_wall(ball)

    def ball_hit_right_wall(self, ball):
        """
        Shortcut method.
        """
        return self.ball_hit_wall(ball, right=True)

    def add_ball(self, radius=BALL_RADIUS, init_pos=None):
        ball = Ball(self, radius, init_pos)
        self.balls.append(ball)
        return ball

    def mouse_click_handler(self, pos):
        for ball in self.balls:
            ball.click(pos)

    def draw_current_score(self, canvas):
        canvas.draw_text("Current score: %d" % self.score,
                         (20, self.height - self.ground_height / 2),
                         20,
                         "White",
                         "serif")

    def draw_best_score(self, canvas):
        canvas.draw_text("Best score: %d" % self.best_score,
                         (self.width - 200, self.height - self.ground_height / 2),
                         20,
                         "White",
                         "serif")

    def draw_scores(self, canvas):
        self.draw_best_score(canvas)
        self.draw_current_score(canvas)

    def draw_ground(self, canvas):
        canvas.draw_line(
            (0, self.height - self.ground_height / 2),
            (self.width, self.height - self.ground_height / 2),
            self.ground_height,
            "Green"
            )

    def draw_clouds(self, canvas):
        clouds_to_remove = []
        for cloud in self.clouds:
            cloud.move()
            if cloud.is_gone(self.width):
                clouds_to_remove.append(cloud)
            else:
                cloud.draw(canvas)

        for cloud in clouds_to_remove:
            self.clouds.remove(cloud)

    def draw_balls(self, canvas):
        for ball in self.balls:
            ball.update()
            ball.draw(canvas)

    def draw_handler(self, canvas):
        if not self.img_loader.finished():
            canvas.draw_text("Loading ...", (100, 100), 50, "White", "serif")
            return

        self.draw_ground(canvas)
        self.draw_clouds(canvas)
        self.draw_balls(canvas)
        self.draw_scores(canvas)

    def add_cloud(self, visible=False):
        if len(self.clouds) >= 3:
            # do not allow too many clouds
            return

        pos_x, pos_y = (
            random.randrange(20, self.width - 20),
            random.randrange(10, 200)
            )
        if not visible:
            pos_x = -400

        self.clouds.append(Cloud((pos_x, pos_y)))

    def clear_clouds(self):
        self.clouds = []

    def init_clouds(self, num=1):
        for i in range(num):
            self.add_cloud(True)

    def init_balls(self, num=1):
        for i in range(num):
            self.add_ball(self.current_radius)

    def start(self):
        self.img_loader.start()

        frame = simplegui.create_frame(
            self.title,
            self.width,
            self.height
            )

        frame.set_draw_handler(self.draw_handler)
        frame.set_mouseclick_handler(self.mouse_click_handler)

        frame.set_canvas_background("#87CEEB")

        frame.start()

        self.init_balls()
        self.init_clouds(2)
        self.cloud_timer = simplegui.create_timer(
                            10 * 1000,
                            self.add_cloud)
        self.cloud_timer.start()

        frame.add_button("Clear sky", self.clear_clouds)
#        frame.add_button("Add cloud", self.add_cloud)
        self.rs_button = frame.add_button("Enable radius shrink", self.toggle_radius_shrink)


game = Game(CANVAS_WIDTH, CANVAS_HEIGHT)
game.start()
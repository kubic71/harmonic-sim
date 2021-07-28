#!/usr/bin/env python3
import sys
import pygame
import math
from pygame.locals import *
from constants import *

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF)
font = pygame.font.SysFont("monospace", 15)

clock = pygame.time.Clock()


def point_in_rect(pos, x, y, width, height):
    if x < pos[0] < x + width and y < pos[1] < y + height:
        return True
    return False


def rotate_vector(v, angle):
    return [math.cos(angle) * v[0] - math.sin(angle) * v[1], math.sin(angle) * v[0] + math.cos(0.5) * v[1]]


class PropertiesModifier:
    def __init__(self, screen, object):

        # laod icons
        self.plus_icon = pygame.image.load("plus.png")
        self.minus_icon = pygame.image.load("minus.png")

        self.screen = screen
        self.object = object
        self.properties = object.properties
        self.buttons = []

    def handle_click(self, pos):
        for b in self.buttons:
            rect, prop, type = b
            if rect.collidepoint(pos):
                current = getattr(self.object, prop)
                setattr(self.object, prop, current * (1.1 if type == 'plus' else 1 / 1.1))

    def render(self):
        self.buttons = []

        for i, prop in enumerate(self.properties):
            label = font.render(prop + ":" + ("%.5f" % getattr(self.object, prop)), 1, WHITE)
            r = label.get_rect()
            top = i * r.height + 20
            r.right = WINDOW_WIDTH - 50
            r.top = top
            self.screen.blit(label, r)

            # add icons rectangles to list, so that click can be detected
            prect = self.plus_icon.get_rect()
            prect.top = top
            prect.left = r.right + 10
            mrect = self.minus_icon.get_rect()
            mrect.top = top
            mrect.left = prect.right
            self.screen.blit(self.plus_icon, prect)
            self.screen.blit(self.minus_icon, mrect)

            self.buttons.append((prect, prop, 'plus'))
            self.buttons.append((mrect, prop, 'minus'))


class Plot():
    def __init__(self, screen, oscilator, x, y, width=300, height=200, time_speed=2):
        self.screen = screen
        self.oscilator = oscilator
        self.x, self.y = x, y
        self.width = width
        self.height = height
        self.time_speed = time_speed

        # visuals
        self.color = (124, 124, 124)
        self.thickness = 2
        self.properties = ["width", "time_speed", "thickness"]

        self.points = []

    def clicked(self, pos):
        pass

    def step(self):
        #
        deflection = self.oscilator.get_deflection()
        self.points.append([0, deflection])
        shifted_points = []

        # shift points in plot
        for p in self.points:
            p[0] += self.time_speed
            if p[0] < self.width:
                shifted_points.append(p)

        self.points = shifted_points

        # draw axes
        # X axis
        self.draw_line((0, self.height / 2), (self.width, self.height / 2))
        # Y axis
        self.draw_line((0, 0), (0, self.height))

        # render points
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            p1 = (p1[0], p1[1] + self.height / 2)
            p2 = (p2[0], p2[1] + self.height / 2)

            self.draw_line(p1, p2, WHITE, self.thickness)

        # render label
        label = font.render(self.oscilator.name, 1, GREEN)
        r = label.get_rect()
        r.left, r.top = self.x + 30, self.y
        self.screen.blit(label, r)

    def draw_line(self, p1, p2, color=WHITE, thickness=2):
        # draw line in relative coordinates to Plot object
        pygame.draw.line(self.screen, color, (p1[0] + self.x, p1[1] + self.y), (p2[0] + self.x, p2[1] + self.y),
                         int(thickness))


class SwingOScilator():
    def __init__(self, screen, name, x, y, initial_deflection, gravity=20, damping=0.03, time_step=0.1):
        self.x = x
        self.y = y
        self.width = 250
        self.height = 200

        self.screen = screen
        self.name = name
        self.angle = initial_deflection
        self.gravity = gravity
        self.time_step = time_step
        self.damping = damping
        self.angular_velocity = 0
        self.rope_length = 200
        self.push_force = 0.2

        self.push_button_icon = pygame.image.load("push_button.png")
        self.child_image_orig = pygame.image.load("child.png").convert()
        self.child_image = self.child_image_orig.copy()
        self.child_image_rect = self.child_image.get_rect()
        self.push_button_rect = self.push_button_icon.get_rect()

        self.properties = ["gravity", "time_step", "damping", "rope_length", "push_force"]

    def step(self):
        angular_acceleration = -self.gravity * math.sin(self.angle) / self.rope_length
        self.angular_velocity += angular_acceleration * self.time_step
        self.angular_velocity *= (1 - self.damping / 10)
        self.angle += self.angular_velocity * self.time_step

        center = (int(self.x + self.width / 2 + self.rope_length * math.sin(self.angle)),
                  int(self.y + self.rope_length * math.cos(self.angle)))

        self.child_image = pygame.transform.rotate(self.child_image_orig, self.angle / math.pi * 180)
        self.child_image_rect = self.child_image.get_rect()
        self.child_image_rect.center = center
        self.screen.blit(self.child_image, self.child_image_rect)
        # self.draw_vector(center, (center[0], center[1] + self.velocity))
        pygame.draw.line(self.screen, WHITE, (int(self.x + self.width / 2), self.y), center, 3)
        pygame.draw.circle(self.screen, GREY, (int(self.x + self.width / 2), self.y), 10)

        force_vector = [angular_acceleration * self.rope_length * 6, 0]
        force_vector = rotate_vector(force_vector, -self.angle)
        force_vector[0], force_vector[1] = force_vector[0] + center[0], force_vector[1] + center[1]
        self.draw_vector(center, force_vector)

        label = font.render(self.name, 1, GREEN)
        r = label.get_rect()
        r.left, r.top = self.x + 30, self.y
        self.screen.blit(label, r)

        # draw push button
        self.push_button_rect.left = self.x + 20
        self.push_button_rect.top = self.y + 20
        self.screen.blit(self.push_button_icon, self.push_button_rect)

    def draw_vector(self, v1, v2, thickness=4):
        pygame.draw.line(self.screen, RED, v1, v2, thickness)

        t = (0.2 * (v1[0] - v2[0]), 0.2 * (v1[1] - v2[1]))
        t1 = rotate_vector(t, 0.5)
        t1[0], t1[1] = t1[0] + v2[0], t1[1] + v2[1]
        t2 = rotate_vector(t, -0.5)
        t2[0], t2[1] = t2[0] + v2[0], t2[1] + v2[1]

        pygame.draw.line(self.screen, YELLOW, v2, t1, thickness)
        pygame.draw.line(self.screen, YELLOW, v2, t2, thickness)

    def clicked(self, pos):
        if point_in_rect(pos, 20, 20, 30, 30):
            self.angular_velocity += self.push_force
            print("pushed")

    def get_deflection(self):
        return self.rope_length * math.sin(self.angle) * 0.65


class SpringOscilator():
    def __init__(self, screen, name, x, y, initial_deflection, initial_velocity=0, weight=1, rigidity=1, damping=0.1,
                 time_step=0.1):
        self.x = x
        self.y = y
        self.width = 75
        self.height = 200

        self.screen = screen
        self.name = name
        self.deflection = initial_deflection
        self.velocity = initial_velocity
        self.weight = weight
        self.rigidity = rigidity
        self.time_step = time_step
        self.damping = damping

        self.properties = ["rigidity", "time_step", "weight", "damping"]

        # position, where weight is in equilibrium
        self.equilibrium_position = 100

    def step(self):

        acceleration = -self.rigidity * self.deflection / self.weight
        self.velocity += acceleration * self.time_step
        self.velocity *= (1 - self.damping / 10)
        self.deflection += self.velocity * self.time_step

        center = (int(self.x) + 20, int(self.y + self.deflection + self.equilibrium_position))
        pygame.draw.circle(self.screen, WHITE, center, int(10 * self.weight ** (1 / 3)))
        self.draw_spring()
        self.draw_vector(center, (center[0], center[1] + self.velocity))

        label = font.render(self.name, 1, GREEN)
        r = label.get_rect()
        r.left, r.top = self.x + 30, self.y
        self.screen.blit(label, r)

    def draw_vector(self, v1, v2, thickness=4):
        pygame.draw.line(self.screen, RED, v1, v2, thickness)

        t = (0.2 * (v1[0] - v2[0]), 0.2 * (v1[1] - v2[1]))
        t1 = rotate_vector(t, 0.5)
        t1[0], t1[1] = t1[0] + v2[0], t1[1] + v2[1]
        t2 = rotate_vector(t, -0.5)
        t2[0], t2[1] = t2[0] + v2[0], t2[1] + v2[1]

        pygame.draw.line(self.screen, YELLOW, v2, t1, thickness)
        pygame.draw.line(self.screen, YELLOW, v2, t2, thickness)

    def draw_spring(self):

        number_of_points = 20

        points = []

        for i in range(number_of_points):
            x = (-1) ** i * 5 + 20
            y = i * (self.equilibrium_position + self.deflection) / (number_of_points - 1)
            points.append((x, y))

        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            self.draw_line(p1, p2)

    def draw_line(self, p1, p2, color=WHITE, thickness=2):
        pygame.draw.line(self.screen, color, (p1[0] + self.x, p1[1] + self.y), (p2[0] + self.x, p2[1] + self.y),
                         thickness)

    def clicked(self, pos):
        self.velocity = 0
        self.deflection = pos[1] - self.equilibrium_position

    def get_deflection(self):
        return self.deflection


class Simulation:
    MODE_MOVE = "move"
    REMOVE_MODE = "remove"

    def __init__(self, screen):
        self.screen = screen
        self.objects = []
        self.mouse_button_down = False
        self.selected_object = None
        self.mode = ""
        self.number_of_oscilators = 1
        self.prop_modifier = None

        self.load_resources()



    def start(self):
        while True:
            clock.tick(FPS)
            screen.fill(BLACK)

            for object in self.objects:
                object.step()
                if self.mode == self.MODE_MOVE or self.mode == self.REMOVE_MODE:  # draw rectangles around objects
                    r = pygame.Rect(object.x, object.y, object.width, object.height)
                    pygame.draw.rect(self.screen, BLUE if self.mode == self.MODE_MOVE else RED, r, 3)

            self.draw_ui()

            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                    elif event.key == K_f:
                        screen.fill(WHITE)

                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # left mouse button was clicked
                        self.mouse_button_down = True

                        self.handle_mouse_button_click()



                elif event.type == MOUSEBUTTONUP:
                    if event.button == 1:  # left mouse button was clicked
                        self.mouse_button_down = False


                elif event.type == MOUSEMOTION:
                    vector = pygame.mouse.get_rel()
                    if self.mode == self.MODE_MOVE and self.mouse_button_down:
                        pos = pygame.mouse.get_pos()
                        for o in self.objects:
                            if point_in_rect(pos, o.x, o.y, o.width, o.height):
                                o.x += vector[0]
                                o.y += vector[1]
                                break

            pygame.display.flip()

    def handle_mouse_button_click(self):
        pos = pygame.mouse.get_pos()

        # Move button clicked
        if self.move_icon_rect.collidepoint(pos):
            if self.mode == self.MODE_MOVE:
                self.mode = ""
            else:
                self.mode = self.MODE_MOVE

        # remove button clicked
        elif self.trash_icon_rect.collidepoint(pos):
            if self.mode == self.REMOVE_MODE:
                self.mode = ""
            else:
                self.mode = self.REMOVE_MODE

        # Spawn SpringOscilator button
        elif self.spring_icon_rect.collidepoint(pos):
            label = "Spring #" + str(self.number_of_oscilators)
            osc = SpringOscilator(screen, label, 200, 200, 70)
            self.objects.append(osc)
            self.number_of_oscilators += 1

            # Plot(screen, oscilator, x, y, width = 300, height = 200, time_speed = 2)
            plot1 = Plot(screen, osc, 0, 500, 500)
            self.objects.append(plot1)

        elif self.swing_icon_rect.collidepoint(pos):
            label = "Swing #" + str(self.number_of_oscilators)
            swing = SwingOScilator(self.screen, label, 500, 200, 1)
            self.objects.append(swing)

            plot = Plot(screen, swing, 300, 500, 500)
            self.objects.append(plot)

        for o in self.objects:
            if point_in_rect(pos, o.x, o.y, o.width, o.height):
                if self.mode == self.REMOVE_MODE:
                    self.objects.remove(o)
                    break

                if self.selected_object != o:
                    self.prop_modifier = PropertiesModifier(screen, o)
                self.selected_object = o
                o.clicked((pos[0] - o.x, pos[1] - o.y))

        if self.prop_modifier is not None:
            self.prop_modifier.handle_click(pos)

    def load_resources(self):
        self.move_icon = pygame.image.load("move_icon.png")
        self.move_icon_rect = self.move_icon.get_rect()

        self.spring_icon = pygame.image.load("spring_oscilator_icon.png")
        self.spring_icon_rect = self.move_icon.get_rect()

        self.trash_icon = pygame.image.load("trash-icon.png")
        self.trash_icon_rect = self.trash_icon.get_rect()

        self.swing_icon = pygame.image.load("swing_icon.png")
        self.swing_icon_rect = self.swing_icon.get_rect()

    def draw_ui(self):
        self.screen.blit(self.move_icon, self.move_icon_rect)

        self.spring_icon_rect.left = self.move_icon_rect.right + 5
        self.screen.blit(self.spring_icon, self.spring_icon_rect)

        self.swing_icon_rect.left = self.spring_icon_rect.right + 5
        self.screen.blit(self.swing_icon, self.swing_icon_rect)

        self.trash_icon_rect.left = self.swing_icon_rect.right + 5
        self.screen.blit(self.trash_icon, self.trash_icon_rect)

        if self.mode == self.MODE_MOVE:
            pygame.draw.rect(self.screen, GREEN, self.move_icon_rect, 3)

        elif self.mode == self.REMOVE_MODE:
            pygame.draw.rect(self.screen, RED, self.trash_icon_rect, 3)

        if self.prop_modifier is not None:
            self.prop_modifier.render()


sim = Simulation(screen)
sim.start()

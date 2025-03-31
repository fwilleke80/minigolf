# @file minigolf.py
# @brief A fun and minimalist implementation of a minigolf engine
# @details Could probably also be used for pool billard.

import pygame
import json
import math
import os
from typing import List, Dict, Any, Tuple

# Constants
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 600
FPS: int = 60

COLOR_AIMLINE: Tuple[int, int, int] = (255, 255, 0)
SHOOT_STRENGTH: float = 20.0
MAX_SHOOT_STRENGTH: float = 600.0  # maximum multiplier for the shot

## @brief Load course data from a JSON file.
#  @param filename The path to the JSON file.
#  @return A dictionary containing the course data.
def load_course_data(filename: str) -> Dict[str, Any]:
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    else:
        return \
{
    "name": "Simple Course",
    "polygon": [[100, 100], [500, 100], [500, 250], [600, 250], [600, 100], [700, 100], [700, 500], [600, 500], [450, 400], [450, 300], [100, 300]],
    "damping": 0.6,
    "color_background": [50, 50, 50],
    "color_course": [40, 65, 10],
    "color_ball": [192, 192, 192],
    "color_holes": [0, 0, 0],
    "holes": [
        {
            "pos": [650, 200],
            "radius": 15
        }
    ],
    "obstacles": [
        {
            "type": "circle",
            "pos": [400, 200],
            "radius": 50,
            "damping": 0.25,
            "color": [128, 40, 20]
        }
    ],
    "ball_start": [200, 200],
    "ball_friction": 0.85,
    "ball_radius": 8.0
}

## @brief Get the nearest point on a line segment from a given point.
#  @param p The point to project.
#  @param a The start point of the segment.
#  @param b The end point of the segment.
#  @return The nearest point on the segment from p.
def get_nearest_point_on_segment(p: pygame.Vector2, a: pygame.Vector2, b: pygame.Vector2) -> pygame.Vector2:
    ab: pygame.Vector2 = b - a
    if ab.length_squared() == 0:
        return a
    t: float = (p - a).dot(ab) / ab.dot(ab)
    t = max(0, min(1, t))
    return a + ab * t

## @brief Handle collision between the ball and the edges of a polygon.
#  @param ball The ball object.
#  @param polygon_points A list of points defining the polygon.
#  @param damping The damping factor to apply on collision.
#  @return True if a collision occurred, False otherwise.
def handle_polygon_collision(ball: "Ball", polygon_points: List[pygame.Vector2], damping: float) -> bool:
    for i in range(len(polygon_points)):
        j: int = (i + 1) % len(polygon_points)
        p1: pygame.Vector2 = polygon_points[i]
        p2: pygame.Vector2 = polygon_points[j]
        nearest: pygame.Vector2 = get_nearest_point_on_segment(ball.pos, p1, p2)
        dist: float = (ball.pos - nearest).length()
        if dist < ball.radius:
            if dist == 0:
                continue
            normal: pygame.Vector2 = (ball.pos - nearest).normalize()
            # Move the ball out of the collision zone.
            ball.pos = nearest + normal * ball.radius
            # Reflect the ball's velocity off the edge.
            ball.velocity = ball.velocity.reflect(normal)
            # Apply damping factor.
            ball.velocity *= damping
            return True
    return False

## @brief Class representing the ball in the game.
class Ball:
    ## @brief Construct a new Ball object.
    #  @param pos The starting position of the ball.
    #  @param friction The friction coefficient.
    #  @param radius The radius of the ball.
    #  @param color The color of the ball.
    def __init__(self, pos: Tuple[float, float], friction: float = 0.01, radius: float = 8.0, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        self.pos: pygame.Vector2 = pygame.Vector2(pos)
        self.velocity: pygame.Vector2 = pygame.Vector2(0, 0)
        self.radius: float = radius
        self.friction: float = friction
        self.color: Tuple[int, int, int] = color
        self.prev_pos: pygame.Vector2 = self.pos.copy()

    ## @brief Update the ball's position and velocity.
    #  @param dt The time elapsed since the last update.
    def update(self, dt: float) -> None:
        self.prev_pos = self.pos.copy()  # Store the previous position.
        self.pos += self.velocity * dt
        self.velocity *= 1.0 - (1.0 - self.friction) * dt
        if self.velocity.length() < 0.1:
            self.velocity = pygame.Vector2(0, 0)

    ## @brief Draw the ball on the given screen.
    #  @param screen The pygame Surface to draw on.
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), int(self.radius))

## @brief Base class for obstacles.
class Obstacle:
    ## @brief Draw the obstacle on the screen.
    #  @param screen The pygame Surface to draw on.
    def draw(self, screen: pygame.Surface) -> None:
        raise NotImplementedError("Draw method not implemented!")

    ## @brief Handle collision with the ball.
    #  @param ball The ball object.
    #  @param dt The time elapsed since the last update.
    def collide(self, ball: Ball, dt: float) -> None:
        raise NotImplementedError("Collision method not implemented!")

## @brief Class representing a circular obstacle.
class CircleObstacle(Obstacle):
    ## @brief Construct a new CircleObstacle object.
    #  @param pos The position of the circle's center.
    #  @param radius The radius of the circle.
    #  @param damping The damping factor to apply on collision.
    #  @param color The color of the circle.
    def __init__(self, pos: Tuple[float, float], radius: float, damping: float, color: Tuple[int, int, int]) -> None:
        self.pos: pygame.Vector2 = pygame.Vector2(pos)
        self.radius: float = radius
        self.damping: float = damping
        self.color: Tuple[int, int, int] = color

    ## @brief Draw the circular obstacle.
    #  @param screen The pygame Surface to draw on.
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), int(self.radius), 2)

    ## @brief Handle collision between the ball and the circular obstacle.
    #  @param ball The ball object.
    #  @param dt The time elapsed since the last update.
    def collide(self, ball: Ball, dt: float) -> None:
        # Determine start and end of ball's travel this frame.
        start: pygame.Vector2 = ball.prev_pos if hasattr(ball, 'prev_pos') else ball.pos - ball.velocity * dt
        end: pygame.Vector2 = ball.pos
        d: pygame.Vector2 = end - start

        # If the ball hasn't moved much, do a simple static check.
        if d.length_squared() < 1e-8:
            if (ball.pos - self.pos).length() < self.radius + ball.radius:
                if (ball.pos - self.pos).length() > 0:
                    normal: pygame.Vector2 = (ball.pos - self.pos).normalize()
                    ball.pos = self.pos + normal * (self.radius + ball.radius)
                    ball.velocity = ball.velocity.reflect(normal) * self.damping
            return

        f: pygame.Vector2 = start - self.pos
        # Combined radius: obstacle radius + ball radius.
        r: float = self.radius + ball.radius

        a: float = d.dot(d)
        b: float = 2 * f.dot(d)
        c: float = f.dot(f) - r * r

        discriminant: float = b * b - 4 * a * c
        if discriminant < 0:
            return

        discriminant = math.sqrt(discriminant)
        t1: float = (-b - discriminant) / (2 * a)
        t2: float = (-b + discriminant) / (2 * a)

        t: float = -1.0
        if 0 <= t1 <= 1:
            t = t1
        elif 0 <= t2 <= 1:
            t = t2

        if 0 <= t <= 1:
            # The collision point along the ball's travel.
            collision_point: pygame.Vector2 = start + d * t
            # Calculate the collision normal from the obstacle center.
            normal: pygame.Vector2 = (collision_point - self.pos).normalize()
            # Reposition the ball so its center is at a distance of (obstacle.radius + ball.radius).
            # A small epsilon factor (1.0001) is applied to avoid sticking.
            ball.pos = self.pos + normal * (self.radius + ball.radius) * 1.0001
            # Reflect velocity and apply damping.
            ball.velocity = ball.velocity.reflect(normal) * self.damping

## @brief Class representing a polygonal obstacle.
class PolygonObstacle(Obstacle):
    ## @brief Construct a new PolygonObstacle object.
    #  @param points A list of points defining the polygon.
    def __init__(self, points: List[Tuple[float, float]]) -> None:
        self.points: List[pygame.Vector2] = [pygame.Vector2(p) for p in points]

    ## @brief Draw the polygon obstacle.
    #  @param screen The pygame Surface to draw on.
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.polygon(screen, (0, 200, 0), [(p.x, p.y) for p in self.points], 2)

    ## @brief Handle collision between the ball and the polygon obstacle.
    #  @param ball The ball object.
    #  @param dt The time elapsed since the last update.
    def collide(self, ball: Ball, dt: float) -> None:
        pass

## @brief Class representing a hole on the course.
class Hole:
    ## @brief Construct a new Hole object.
    #  @param pos The position of the hole.
    #  @param radius The radius of the hole.
    #  @param color The color of the hole.
    def __init__(self, pos: Tuple[float, float], radius: float, color: Tuple[int, int, int]) -> None:
        self.pos: pygame.Vector2 = pygame.Vector2(pos)
        self.radius: float = radius
        self.color: Tuple[int, int, int] = color

    ## @brief Draw the hole on the screen.
    #  @param screen The pygame Surface to draw on.
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), int(self.radius))

    ## @brief Check if the ball is in the hole.
    #  @param ball The ball object.
    #  @return True if the ball is in the hole, False otherwise.
    def check_ball(self, ball: Ball) -> bool:
        return (ball.pos - self.pos).length() < self.radius

## @brief Class representing the course.
class Course:
    ## @brief Construct a new Course object.
    #  @param data A dictionary containing course data.
    def __init__(self, data: Dict[str, Any]) -> None:
        self.name: str = data["name"]
        self.polygon: List[pygame.Vector2] = [pygame.Vector2(p) for p in data["polygon"]]
        self.holes: List[Hole] = [Hole(tuple(h["pos"]), h["radius"], tuple(data["color_holes"])) for h in data["holes"]]
        self.ball_start: pygame.Vector2 = pygame.Vector2(data["ball_start"])
        self.damping: float = data["damping"]
        self.color: Tuple[int, int, int] = tuple(data["color_course"])
        self.colorstroke: Tuple[int, int, int] = tuple(data["color_course_stroke"])
        self.obstacles: List[Obstacle] = [
            obstacle_types[obstacle_data["type"]](
                tuple(obstacle_data["pos"]),
                float(obstacle_data["radius"]),
                float(obstacle_data["damping"]),
                tuple(obstacle_data["color"])
            )
            for obstacle_data in data["obstacles"]
        ]

    ## @brief Draw the course on the screen.
    #  @param screen The pygame Surface to draw on.
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.polygon(screen, self.color, [(p.x, p.y) for p in self.polygon])
        pygame.draw.polygon(screen, self.colorstroke, [(p.x, p.y) for p in self.polygon], 2)
        for hole in self.holes:
            hole.draw(screen)
        for obs in self.obstacles:
            obs.draw(screen)

# Map obstacle type names to their classes.
obstacle_types: Dict[str, Any] = {
    "circle": CircleObstacle,
    "polygon": PolygonObstacle
}

## @brief Main function to run the minigolf game.
def main() -> None:
    pygame.init()
    screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Minigolf Game")
    clock: pygame.time.Clock = pygame.time.Clock()

    # Load course data.
    course_data: Dict[str, Any] = load_course_data("course.json")
    course: Course = Course(course_data)
    ball: Ball = Ball(tuple(course.ball_start), course_data["ball_friction"], course_data["ball_radius"], tuple(course_data["color_ball"]))

    # Initialize game data.
    game_data: Dict[str, Any] = {
        "course_name": course.name,
        "total_shots": 0,
        "shots_since_last_hole": 0,
        "shots_needed_last_hole": 0
    }

    # Initialize font for on-screen text.
    font: pygame.font.Font = pygame.font.SysFont(None, 24)

    aiming: bool = False
    aim_start: pygame.Vector2 = pygame.Vector2(0, 0)
    aim_end: pygame.Vector2 = pygame.Vector2(0, 0)

    running: bool = True
    while running:
        dt: float = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    aiming = True
                    aim_start = pygame.Vector2(pygame.mouse.get_pos())
            if event.type == pygame.MOUSEMOTION:
                if aiming:
                    aim_end = pygame.Vector2(pygame.mouse.get_pos())
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and aiming:
                    aiming = False
                    aim_release: pygame.Vector2 = pygame.Vector2(pygame.mouse.get_pos())
                    shoot_vector: pygame.Vector2 = aim_release - ball.pos
                    strength: float = min(shoot_vector.length() * SHOOT_STRENGTH, MAX_SHOOT_STRENGTH)
                    if shoot_vector.length() != 0:
                        ball.velocity = shoot_vector.normalize() * strength
                        # Update shot counters.
                        game_data["total_shots"] += 1
                        game_data["shots_since_last_hole"] += 1

        ball.update(dt)

        for obs in course.obstacles:
            obs.collide(ball, dt)

        # Check and handle collisions with the course polygon edges.
        handle_polygon_collision(ball, course.polygon, course.damping)

        for hole in course.holes:
            if hole.check_ball(ball):
                print("Ball in hole!")
                # Record shots needed for this hole.
                game_data["shots_needed_last_hole"] = game_data["shots_since_last_hole"]
                # Reset shots for the current hole.
                game_data["shots_since_last_hole"] = 0
                ball.pos = pygame.Vector2(course.ball_start)
                ball.velocity = pygame.Vector2(0, 0)

        screen.fill(tuple(course_data["color_background"]))
        course.draw(screen)
        ball.draw(screen)

        if aiming:
            pygame.draw.line(screen, COLOR_AIMLINE, (ball.pos.x, ball.pos.y), pygame.mouse.get_pos(), 2)

        # Render game data on screen.
        info_text: str = (
            f"{game_data['course_name']}\n\n"
            f"Total Shots: {game_data['total_shots']}\n"
            f"Current Hole Shots: {game_data['shots_since_last_hole']}\n"
            f"Last Hole: {game_data['shots_needed_last_hole']}"
        )
        text_surface: pygame.Surface = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

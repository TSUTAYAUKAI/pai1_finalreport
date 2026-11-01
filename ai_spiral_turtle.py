#!/usr/bin/env python3
"""PAI final assignment: kNN imitation learning controls ROS 2 turtlesim.

No external ML libraries are required. Training examples are generated from an
expert feedback controller; at runtime all Twist commands are predicted by kNN.

ROS:   python3 ai_spiral_turtle.py
Test:  python3 ai_spiral_turtle.py --dry-run
"""
import argparse
import heapq
import math
import random


def clamp(value, low, high):
    return max(low, min(high, value))


def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


# A progressively expanding square spiral, safely inside the turtlesim canvas.
WAYPOINTS = [
    (7.0, 5.54), (7.0, 7.0), (4.2, 7.0), (4.2, 4.2),
    (8.0, 4.2), (8.0, 8.0), (3.1, 8.0), (3.1, 3.1),
    (9.0, 3.1), (9.0, 9.0), (2.1, 9.0), (2.1, 2.1),
    (9.8, 2.1),
]


class KNNImitationPolicy:
    """kNN regression over synthetic expert demonstrations (behavior cloning)."""

    def __init__(self, n_examples=3600, neighbors=7, seed=2026):
        rng = random.Random(seed)
        self.neighbors = neighbors
        self.examples = []
        for _ in range(n_examples):
            distance = rng.uniform(0, 10)
            angle_error = rng.uniform(-math.pi, math.pi)

            # Expert demonstration: turn toward the goal, slow down near turns.
            # The expert is used to LABEL the dataset only, not at inference.
            expert_linear = min(1.3, 0.83 * distance) * max(
                0.0, math.cos(angle_error)
            ) ** 3
            expert_angular = clamp(2.9 * angle_error, -2.7, 2.7)

            feature = self.feature(distance, angle_error)
            self.examples.append((feature, expert_linear, expert_angular))

    @staticmethod
    def feature(distance, angle_error):
        # sin/cos encoding avoids a discontinuity at +/- pi.
        return (
            min(distance, 10.0) / 10.0,
            math.sin(angle_error),
            math.cos(angle_error),
        )

    def predict(self, distance, angle_error):
        x0, x1, x2 = self.feature(distance, angle_error)
        closest = heapq.nsmallest(
            self.neighbors,
            (
                (
                    (x0 - feat[0]) ** 2
                    + (x1 - feat[1]) ** 2
                    + (x2 - feat[2]) ** 2,
                    lin,
                    ang,
                )
                for feat, lin, ang in self.examples
            ),
            key=lambda sample: sample[0],
        )
        weights = [1.0 / (d2 + 0.0001) for d2, _, _ in closest]
        total = sum(weights)
        linear = sum(w * sample[1] for w, sample in zip(weights, closest)) / total
        angular = sum(w * sample[2] for w, sample in zip(weights, closest)) / total
        return linear, angular


class SpiralTask:
    def __init__(self):
        self.policy = KNNImitationPolicy()
        self.waypoint_index = 0

    @property
    def done(self):
        return self.waypoint_index >= len(WAYPOINTS)

    def update(self, x, y, theta):
        if self.done:
            return 0.0, 0.0, False
        gx, gy = WAYPOINTS[self.waypoint_index]
        distance = math.hypot(gx - x, gy - y)
        if distance < 0.24:
            self.waypoint_index += 1
            return 0.0, 0.0, True
        heading = math.atan2(gy - y, gx - x)
        angle_error = wrap_angle(heading - theta)
        linear, angular = self.policy.predict(distance, angle_error)
        return linear, angular, False


def dry_run():
    """Pure-Python unicycle simulation: check behavior before opening ROS."""
    task = SpiralTask()
    x, y, theta = 5.544445, 5.544445, 0.0
    dt = 0.1
    trail = [(x, y)]
    for step in range(3600):
        linear, angular, new_goal = task.update(x, y, theta)
        if new_goal:
            print(f"Reached waypoint {task.waypoint_index}/{len(WAYPOINTS)}")
        if task.done:
            print(f"SUCCESS: completed spiral in {step * dt:.1f} simulated seconds")
            print(f"End pose: x={x:.2f}, y={y:.2f}")
            return True, trail
        theta = wrap_angle(theta + angular * dt)
        x += linear * math.cos(theta) * dt
        y += linear * math.sin(theta) * dt
        trail.append((x, y))
        if not (0.1 < x < 10.9 and 0.1 < y < 10.9):
            print(f"FAILED: hit boundary at x={x:.2f}, y={y:.2f}")
            return False, trail
    print("FAILED: did not finish within 360 simulated seconds")
    return False, trail


def run_ros():
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import Twist
    try:
        from turtlesim.msg import Pose
    except ImportError:  # newer ROS distros expose message types separately
        from turtlesim_msgs.msg import Pose

    class AISpiralNode(Node):
        def __init__(self):
            super().__init__("ai_spiral_turtle")
            self.task = SpiralTask()
            self.pose = None
            self.finished_announced = False
            self.velocity_pub = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)
            self.pose_sub = self.create_subscription(
                Pose, "/turtle1/pose", self.on_pose, 10
            )
            self.timer = self.create_timer(0.1, self.on_timer)
            self.get_logger().info(
                "kNN imitation model ready (3600 expert examples). Starting spiral..."
            )

        def on_pose(self, msg):
            self.pose = msg

        def on_timer(self):
            if self.pose is None:
                return
            v, w, reached = self.task.update(
                self.pose.x, self.pose.y, self.pose.theta
            )
            if reached:
                self.get_logger().info(
                    f"Waypoint {self.task.waypoint_index}/{len(WAYPOINTS)} reached"
                )
            msg = Twist()
            msg.linear.x = v
            msg.angular.z = w
            self.velocity_pub.publish(msg)
            if self.task.done and not self.finished_announced:
                self.finished_announced = True
                self.get_logger().info("DONE! Stop the screen recording now.")

    rclpy.init()
    node = AISpiralNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        stop = Twist()
        node.velocity_pub.publish(stop)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="test without ROS")
    args = parser.parse_args()
    if args.dry_run:
        ok, _ = dry_run()
        raise SystemExit(0 if ok else 1)
    run_ros()

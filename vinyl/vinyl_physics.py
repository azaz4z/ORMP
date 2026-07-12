import math

class VinylPhysics:
    def __init__(self, rate, total_frames, rpm=33.3333):
        self.rpm = rpm
        self.rps = rpm / 60

        self.frames_per_rev = rate / self.rps
        self.max_angle = (
            total_frames / self.frames_per_rev
        ) * 2 * math.pi

        self.angle = 0
        self.prev_angle = 0
        self.mouse_angle = 0
        self._pending_jump = None

        self.normal_velocity = (
            1024 / self.frames_per_rev
        ) * 2 * math.pi

        self.velocity = 0

    def load_new_track(self, rate, total_frames):
        self.frames_per_rev = rate / self.rps
        self.max_angle = (
            total_frames / self.frames_per_rev
        ) * 2 * math.pi
        self.angle = 0
        self.prev_angle = 0
        self.mouse_angle = 0
        self._pending_jump = None
        self.normal_velocity = (
            1024 / self.frames_per_rev
        ) * 2 * math.pi
        self.velocity = 0

    def request_jump(self, progress):
        self._pending_jump = progress

    def get_audio_range(self):
        if self._pending_jump is not None:
            new_angle = self._pending_jump * self.max_angle
            self.angle = new_angle
            self.prev_angle = new_angle
            self.mouse_angle = new_angle
            self._pending_jump = None

        start_pos = (
            self.prev_angle /
            (2 * math.pi)
        ) * self.frames_per_rev

        end_pos = (
            self.angle /
            (2 * math.pi)
        ) * self.frames_per_rev

        self.prev_angle = self.angle
        return start_pos, end_pos

    def update(self, target):
        self.velocity = (
            self.velocity * 0.80 +
            target * 0.20
        )

        self.angle += self.velocity

        self.angle = max(
            0,
            min(self.angle, self.max_angle)
        )

    def drag_spring(self):
        distance = self.mouse_angle - self.angle

        # Spring constant (controls "heaviness" of the vinyl)
        k = 0.45
        spring_force = distance * k

        # Damping to prevent infinite oscillation
        damping = 0.6
        self.velocity = (self.velocity + spring_force) * damping
        
        # Max scratch speed (e.g. 10x normal playback speed)
        max_scratch_velocity = self.normal_velocity * 10
        self.velocity = max(-max_scratch_velocity, min(self.velocity, max_scratch_velocity))

        self.angle += self.velocity
        self.angle = max(0, min(self.angle, self.max_angle))

    def move_mouse(self, delta):
        self.mouse_angle += delta
        self.mouse_angle = max(
            0,
            min(self.mouse_angle, self.max_angle)
        )
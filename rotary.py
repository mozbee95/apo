# test
import threading

PULSE_TIMEOUT = 0.5    # s : temps max entre deux impulsions d'un même chiffre
COMPOSE_TIMEOUT = 2.0  # s : temps avant de considérer le numéro complet

PULSE_VALUES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]


class Rotary:
    def __init__(self, on_compose_start=None, on_compose_end=None):
        self.value = ""
        self.pulse_count = 0
        self.pulse_timer = None
        self.compose_timer = None
        self.on_compose_start = on_compose_start
        self.on_compose_end = on_compose_end
        self.lock = threading.Lock()
        print("Rotary init")

    def on_pulse(self):
        # réception d'une impulsion
        print("Impulse received")
        with self.lock:
            if self.pulse_count == 0 and self.value == "" and self.on_compose_start:
                self.on_compose_start()
            self.pulse_count += 1
            if self.pulse_timer:
                self.pulse_timer.cancel()
            if self.compose_timer:
                self.compose_timer.cancel()
            self.pulse_timer = threading.Timer(PULSE_TIMEOUT, self._on_pulse_timeout)
            self.pulse_timer.start()

    def _on_pulse_timeout(self):
        # dernière impulsion reçue : on stocke le chiffre
        with self.lock:
            if 1 <= self.pulse_count <= 10:
                self.value += str(PULSE_VALUES[self.pulse_count - 1])
            self.pulse_count = 0
            self.compose_timer = threading.Timer(COMPOSE_TIMEOUT, self._on_compose_timeout)
            self.compose_timer.start()

    def _on_compose_timeout(self):
        # fin de composition
        with self.lock:
            number = self.value
            self.value = ""
            self.pulse_count = 0
        if self.on_compose_end:
            self.on_compose_end(number)
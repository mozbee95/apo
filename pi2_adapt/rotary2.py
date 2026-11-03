# rotary.py
import threading

PULSE_TIMEOUT = 0.5    # s : temps max entre deux impulsions d'un même chiffre
COMPOSE_TIMEOUT = 2.0  # s : temps avant de considérer le numéro complet

# Table brute : l'index renvoie la valeur brute du nombre d'impulsions
PULSE_VALUES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]


class Rotary:
    def __init__(self, on_compose_start=None, on_compose_end=None):
        self.value = ""
        self.pulse_count = 0
        self.pulse_timer = None
        self.compose_timer = None
        self.on_compose_start = on_compose_start
        self.on_compose_end = on_compose_end
        self.lock = threading.Lock()

    def on_pulse(self):
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
        with self.lock:
            # On stocke toutes les impulsions sans exception pour permettre l'affichage complet
            if 1 <= self.pulse_count <= len(PULSE_VALUES):
                self.value += str(PULSE_VALUES[self.pulse_count - 1])
                
            self.pulse_count = 0
            self.compose_timer = threading.Timer(COMPOSE_TIMEOUT, self._on_compose_timeout)
            self.compose_timer.start()

    def _on_compose_timeout(self):
        with self.lock:
            number = self.value
            self.value = ""
            self.pulse_count = 0
            
        if number:
            # Sécurité : Si le numéro converti en entier est inférieur à 10,
            # c'est une impulsion parasite de raccrochage/décrochage. On l'ignore pour l'audio.
            try:
                if int(number) < 10:
                    print(f"[Filtre] Signal parasite de raccrochage détecté ({number}). Lecture audio bloquée.")
                    return
            except ValueError:
                pass

            # Si le numéro est supérieur ou égal à 10, on autorise la suite
            if self.on_compose_end:
                self.on_compose_end(number)

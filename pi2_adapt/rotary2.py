# rotary.py
import asyncio

PULSE_TIMEOUT = 0.5    # s : temps max entre deux impulsions d'un même chiffre
COMPOSE_TIMEOUT = 2.0  # s : temps avant de considérer le numéro complet

# Table des valeurs brutes d'impulsions
PULSE_VALUES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]

class Rotary:
    def __init__(self, loop, on_compose_start=None, on_compose_end=None):
        self.loop = loop
        self.value = ""
        self.pulse_count = 0
        self._pulse_task = None
        self._compose_task = None
        self.on_compose_start = on_compose_start
        self.on_compose_end = on_compose_end

    def on_pulse(self):
        self.loop.call_soon_threadsafe(self._handle_pulse_async)

    def _handle_pulse_async(self):
        if self.pulse_count == 0 and self.value == "" and self.on_compose_start:
            self.on_compose_start()
            
        self.pulse_count += 1
        
        if self._pulse_task and not self._pulse_task.done():
            self._pulse_task.cancel()
        if self._compose_task and not self._compose_task.done():
            self._compose_task.cancel()
            
        self._pulse_task = asyncio.create_task(self._on_pulse_timeout())

    async def _on_pulse_timeout(self):
        try:
            await asyncio.sleep(PULSE_TIMEOUT)
            if 1 <= self.pulse_count <= len(PULSE_VALUES):
                self.value += str(PULSE_VALUES[self.pulse_count - 1])
                
            self.pulse_count = 0
            self._compose_task = asyncio.create_task(self._on_compose_timeout())
        except asyncio.CancelledError:
            pass

    async def _on_compose_timeout(self):
        try:
            await asyncio.sleep(COMPOSE_TIMEOUT)
            number = self.value
            self.value = ""
            self.pulse_count = 0
              
            if number and self.on_compose_end:
                self.on_compose_end(number)
        except asyncio.CancelledError:
            pass

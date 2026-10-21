from gpiozero import Button
from signal import pause
import time

b = Button(17, pull_up=True, bounce_time=None)
last = time.monotonic()

def edge(name):
    global last
    now = time.monotonic()
    print(f"{name:6} +{(now - last) * 1000:5.0f} ms")
    last = now

print("état initial :", "fermé" if b.is_pressed else "ouvert")
b.when_pressed = lambda: edge("fermé")
b.when_released = lambda: edge("ouvert")
pause()
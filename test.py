from gpiozero import Button
import time

b = Button(17, pull_up=False, bounce_time=None)
prev = b.is_pressed
changes = 0
print("compose un chiffre... (Ctrl+C pour arrêter)")
try:
    while True:
        cur = b.is_pressed
        if cur != prev:
            changes += 1
            print(f"{changes:3} {'fermé' if cur else 'ouvert'}")
            prev = cur
        time.sleep(0.001)
except KeyboardInterrupt:
    pass
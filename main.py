from gpiozero import Button
from signal import pause
from time import sleep
print("test\n")

hangup = Button(9)  # pull-up interne activé par défaut
while True:
    print("raccroché" if hangup.is_pressed else "décroché")
    sleep(0.1)
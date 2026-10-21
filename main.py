from gpiozero import Button
from signal import pause
from time import sleep
print("test\n")

while(1):
    hangup = Button(21)  # pull-up interne activé par défaut
    hangup.when_pressed = lambda: print("Phone HANG UP")
    hangup.when_released = lambda: print("Phone PICK UP")
    sleep(100)
from gpiozero import Button
from time import pause

hangup = Button(9, pull_up=False, bounce_time=0.05)
hangup.when_pressed = lambda: print("Phone HANG UP")
hangup.when_released = lambda: print("Phone PICK UP")
pause()
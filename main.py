from gpiozero import Button
from signal import pause
from rotary import Rotary


def compose_end(number):
    print(f"Rotary COMPOSE {number}")
    # -> déclenchement du son en fonction du numéro


rotary = Rotary(on_compose_end=compose_end)

# bouton qui reçoit les impulsions du cadran
rotary_button = Button(17, pull_up=True, bounce_time=0.01)
rotary_button.when_released = rotary.on_pulse

# combiné
hangup = Button(9, pull_up=False, bounce_time=0.05)
hangup.when_pressed = lambda: print("Phone PICK UP")
hangup.when_released = lambda: print("Phone HANG UP")

pause()
from gpiozero import Button
from time import sleep

hangup = Button(9, pull_up=False)
print("démarré")
while True:
    print("fermé (3,3 V)" if hangup.is_pressed else "ouvert (0 V)")
    sleep(0.2)
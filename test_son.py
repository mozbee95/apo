import time
import pygame

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init(devicename="headphones")

print("Tentative de lecture forcée de la tonalité pendant 5 secondes...")
try:
    # Remplacez par le nom exact de votre fichier
    son = pygame.mixer.Sound("./RESSOURCES/tonalite.wav") 
    son.play(loops=-1)
    
    # Attend 5 secondes en affichant l'état
    for i in range(5):
        print(f"Busy: {pygame.mixer.get_busy()}") # Doit afficher True
        time.sleep(1)
        
except Exception as e:
    print(f"Erreur lors de la lecture : {e}")
finally:
    pygame.mixer.quit()
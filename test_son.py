import time
import pygame

pygame.mixer.pre_init(48000, -16, 2, 2048)
pygame.mixer.init()

print("Tentative de lecture forcée de la tonalité pendant 5 secondes...")
try:
    # Remplacez par le nom exact de votre fichier
    son = pygame.mixer.Sound("./RESSOURCES/tonalite.wav") 
    son.play(loops=-1)
    
    # Attend 5 secondes en affichant l'état
    while True:
        try:
            print(f"Busy: {pygame.mixer.get_busy()}") # Doit afficher True
            time.sleep(1)
        except KeyboardInterrupt:
            break
        
        
except Exception as e:
    print(f"Erreur lors de la lecture : {e}")
finally:
    pygame.mixer.quit()
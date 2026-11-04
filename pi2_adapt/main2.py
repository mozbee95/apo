import asyncio
import time
import pygame
from gpiozero import Button
from rotary import Rotary

# --- Configuration des fichiers audio (Mappage direct Exact ou avec Parasite) ---
TONALITE_AUDIO = "./RESSOURCES/tonalite.wav"
NUMEROS_AUDIO = {
    # Chiffre 1 : 1 impulsion brute OU 11 avec le parasite du décrochage
    "1": "./RESSOURCES/son1.wav",
    "11": "./RESSOURCES/son1.wav",
    
    # Chiffre 2 : 2 impulsions brutes OU 12 avec le parasite du décrochage
    "2": "./RESSOURCES/son2.wav",
    "12": "./RESSOURCES/son2.wav",
    
    # Chiffre 3 : 3 impulsions brutes OU 13 avec le parasite du décrochage
    "3": "./RESSOURCES/son3.wav",
    "13": "./RESSOURCES/son3.wav",
    
    # Chiffre 4 : 4 impulsions brutes OU 14 avec le parasite du décrochage
    "4": "./RESSOURCES/son4.wav",
    "14": "./RESSOURCES/son4.wav",
    
    # Chiffre 5 : 5 impulsions brutes OU 15 avec le parasite du décrochage
    "5": "./RESSOURCES/son5.wav",
    "15": "./RESSOURCES/son5.wav",
    
    # Chiffre 6 : 6 impulsions brutes OU 16 avec le parasite du décrochage
    "6": "./RESSOURCES/son6.wav",
    "16": "./RESSOURCES/son6.wav",

    # Chiffre 7 : 7 impulsions brutes OU 17 avec le parasite du décrochage
    "7": "./RESSOURCES/son7.wav",
    "17": "./RESSOURCES/son7.wav",
    
    # Chiffre 8 : 8 impulsions brutes OU 18 avec le parasite du décrochage
    "8": "./RESSOURCES/son8.wav",
    "18": "./RESSOURCES/son8.wav",

    # Chiffre 9 : 9 impulsions brutes OU 19 avec le parasite du décrochage
    "9": "./RESSOURCES/son9.wav",
    "19": "./RESSOURCES/son9.wav",

    # Chiffre 0 : 0 impulsions brutes OU 10 avec le parasite du décrochage
    "0": "./RESSOURCES/son0.wav",
    "10": "./RESSOURCES/son0.wav",

    "DEFAULT": "./RESSOURCES/audio_erreur.wav"
}


# --- Affectation des Broches GPIO ---
PIN_ROTARY_PULSE = 17   # Cadran rotatif
PIN_HOOK_SWITCH = 9     # Crochet du combiné (Décroché/Raccroché)

class AsyncTelephoneController:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        
        self.canal_tonalite = pygame.mixer.Channel(0)
        self.canal_audio = pygame.mixer.Channel(1)
        
        try:
            self.son_tonalite = pygame.mixer.Sound(TONALITE_AUDIO)
        except Exception:
            self.son_tonalite = None
            print(f"[Warning] Fichier tonalité absent : {TONALITE_AUDIO}")

        self.loop = asyncio.get_event_loop()
        self.est_decroche = False
        self._current_audio_task = None

        self.rotary = Rotary(
            loop=self.loop,
            on_compose_start=self._thread_safe_compose_start,
            on_compose_end=self._thread_safe_compose_end
        )

        # --- Initialisation du matériel (GPIO) ---
        self.bouton_pulse = Button(PIN_ROTARY_PULSE, pull_up=False, bounce_time=0.02)
        self.bouton_pulse.when_pressed = self._on_gpio_pulse

        self.crochet = Button(PIN_HOOK_SWITCH, pull_up=False, bounce_time=0.2)
        self.crochet.when_pressed = self._thread_safe_decrocher
        self.crochet.when_released = self._thread_safe_raccrocher
        if self.crochet.is_pressed:
            self._thread_safe_decrocher()

    def _on_gpio_pulse(self):
        if self.est_decroche:
            self.rotary.on_pulse()

    def _thread_safe_decrocher(self):
        self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.decrocher()))

    def _thread_safe_raccrocher(self):
        self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.raccrocher()))

    def _thread_safe_compose_start(self):
        self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.on_composition_start()))

    def _thread_safe_compose_end(self, numero):
        self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.on_composition_end(numero)))

    async def decrocher(self):
        if not self.est_decroche:
            print("\n[Téléphone] Combiné décroché ! Lancement de la tonalité.")
            self.est_decroche = True
            
            if self.rotary._pulse_task and not self.rotary._pulse_task.done():
                self.rotary._pulse_task.cancel()
            if self.rotary._compose_task and not self.rotary._compose_task.done():
                self.rotary._compose_task.cancel()
            self.rotary.value = ""
            self.rotary.pulse_count = 0
            
            if self.son_tonalite:
                await self.loop.run_in_executor(
                    None, 
                    lambda: self.canal_tonalite.play(self.son_tonalite, loops=-1)
                )

    async def raccrocher(self):
        if self.est_decroche:
            print("\n[Téléphone] Combiné raccroché. Extinction immédiate de tous les sons.")
            self.est_decroche = False
            
            if self._current_audio_task and not self._current_audio_task.done():
                self._current_audio_task.cancel()
                
            await self.loop.run_in_executor(None, self.canal_tonalite.stop)
            await self.loop.run_in_executor(None, self.canal_audio.stop)
            
            if self.rotary._pulse_task and not self.rotary._pulse_task.done():
                self.rotary._pulse_task.cancel()
            if self.rotary._compose_task and not self.rotary._compose_task.done():
                self.rotary._compose_task.cancel()
            self.rotary.value = ""
            self.rotary.pulse_count = 0

    async def on_composition_start(self):
        if self.est_decroche:
            print("[Cadran] Début de la rotation détecté -> Coupure de la tonalité.")
            self.canal_tonalite.stop()

    async def on_composition_end(self, numero):
        # Si le combiné est raccroché au moment où le numéro est validé,
        # ou si c'est une impulsion "1" isolée reçue pendant le raccrochage, on ignore.
        if not self.est_decroche:
            print(f"[Filtre] Numéro {numero} reçu alors que le téléphone est raccroché -> Ignoré.")
            return

        print(f"[Cadran] Composition terminée. Numéro reçu : {numero}")
        
        if self._current_audio_task and not self._current_audio_task.done():
            print("[Lecteur] Changement de numéro détecté. Interruption du média précédent...")
            self._current_audio_task.cancel()

        fichier = NUMEROS_AUDIO.get(numero, NUMEROS_AUDIO["DEFAULT"])
        self._current_audio_task = asyncio.create_task(self._jouer_audio_async(fichier))


    async def _jouer_audio_async(self, fichier_path):
        try:
            son = pygame.mixer.Sound(fichier_path)
            self.canal_audio.play(son)
            print(f"[Lecteur] Début de la lecture : {fichier_path}")
            
            # Attente asynchrone du signal de fin de piste
            while self.canal_audio.get_busy():
                await asyncio.sleep(0.1)
                
            print(f"[Lecteur] Lecture terminée naturellement : {fichier_path}")
        except asyncio.CancelledError:
            print(f"[Lecteur] Flux audio interrompu proprement par action utilisateur.")
            self.canal_audio.stop()
        except Exception as e:
            print(f"[Lecteur] Erreur lors de la lecture du fichier {fichier_path} : {e}")

async def main():
    controller = AsyncTelephoneController()
    print("==========================================================")
    print("Système 'APO' paré pour l'exposition (Mode Double Mapping).")
    print("Contrôle actif : GPIO 17 (Impulsions) & GPIO 9 (Crochet).")
    print("==========================================================")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nFermeture demandée par l'administrateur.")
    finally:
        pygame.mixer.quit()

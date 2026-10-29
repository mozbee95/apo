import asyncio
import pygame
from gpiozero import Button
from rotary import Rotary

# --- Configuration des fichiers audio ---
TONALITE_AUDIO = "./RESSOURCES/tonalite.wav"
NUMEROS_AUDIO = {
    "1": "./RESSOURCES/test1.mp3",
    "2": "./RESSOURCES/test1.mp3",
    "DEFAULT": "./RESSOURCES/audio_erreur.wav"
}

# --- Affectation des Broches GPIO ---
PIN_ROTARY_PULSE = 17   # Cadran rotatif
PIN_HOOK_SWITCH = 9     # Crochet du combiné (Décroché/Raccroché)

class AsyncTelephoneController:
    def __init__(self):
        # Initialisation robuste du mixeur audio pygame compatible Raspberry Pi OS
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

        # Instanciation de votre logique rotary.py originelle
        self.rotary = Rotary(
            on_compose_start=self._thread_safe_compose_start,
            on_compose_end=self._thread_safe_compose_end
        )

        # --- Initialisation du matériel (GPIO) ---
        # GPIO 17 : Entrée des impulsions du cadran
        self.bouton_pulse = Button(PIN_ROTARY_PULSE, pull_up=False, bounce_time=0.02)
        self.bouton_pulse.when_pressed = self._on_gpio_pulse

        # GPIO 9 : Entrée du commutateur de crochet (Hook)
        # Note : Si le comportement est inversé (tonalité au raccroché), intervertissez simplement 
        # '_thread_safe_decrocher' et '_thread_safe_raccrocher' ci-dessous.
        self.crochet = Button(PIN_HOOK_SWITCH, pull_up=False, bounce_time=0.2)
        self.crochet.when_pressed = self._thread_safe_decrocher
        self.crochet.when_released = self._thread_safe_raccrocher
        if self.crochet.is_pressed:
            # Si le bouton est déjà détecté comme activé selon votre câblage
            self._thread_safe_decrocher()

    # --- Passerelles Thread-Safe (GPIO/Rotary vers Asyncio) ---
    def _on_gpio_pulse(self):
        """Transmet l'impulsion physique à votre classe Rotary si le téléphone est décroché."""
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

    # --- Logique Métier Asynchrone ---
    async def decrocher(self):
        if not self.est_decroche:
            print("\n[Téléphone] Combiné décroché ! Lancement de la tonalité.")
            self.est_decroche = True
            
            # Forcer l'activation de la tonalité de manière synchrone via l'exécuteur
            if self.son_tonalite:
                await self.loop.run_in_executor(
                    None, 
                    lambda: self.canal_tonalite.play(self.son_tonalite, loops=-1)
                )

    async def raccrocher(self):
        if self.est_decroche:
            print("\n[Téléphone] Combiné raccroché. Extinction immédiate de tous les sons.")
            self.est_decroche = False
            
            # Annulation immédiate de la tâche asynchrone de lecture en arrière-plan
            if self._current_audio_task and not self._current_audio_task.done():
                self._current_audio_task.cancel()
                
            # Forcer l'arrêt matériel synchrone
            await self.loop.run_in_executor(None, self.canal_tonalite.stop)
            await self.loop.run_in_executor(None, self.canal_audio.stop)
            
            # Remise à zéro de la mémoire de composition de rotary.py
            with self.rotary.lock:
                self.rotary.value = ""
                self.rotary.pulse_count = 0

    async def on_composition_start(self):
        if self.est_decroche:
            print("[Cadran] Début de la rotation détecté -> Coupure de la tonalité.")
            self.canal_tonalite.stop()

    async def on_composition_end(self, numero):
        if not self.est_decroche:
            return

        print(f"[Cadran] Composition terminée. Numéro reçu : {numero}")
        
        # Interrompt l'audio précédent si l'utilisateur recompose un numéro à la volée
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
            
            # Attente asynchrone non-bloquante du signal de fin de piste
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
    print("Système 'APO' paré pour l'exposition.")
    print("Contrôle actif : GPIO 17 (Impulsions) & GPIO 9 (Crochet).")
    print("==========================================================")
    
    # Maintient le programme en arrière-plan sans bloquer les tâches
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nFermeture demandée par l'administrateur.")
    finally:
        pygame.mixer.quit()

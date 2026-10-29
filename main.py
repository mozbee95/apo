import asyncio
import pygame
from gpiozero import Button
from rotary import Rotary

# --- Configuration des fichiers audio ---
TONALITE_AUDIO = "./RESSOURCEStonalite.wav"
NUMEROS_AUDIO = {
    "1": "./RESSOURCES/test1.mp3",
    "2": "./RESSOURCES/test2.mp3",
    "DEFAULT": "./RESSOURCES/audio_erreur.wav"
}

# --- Configuration du câblage matériel (GPIO) ---
PIN_ROTARY_PULSE = 17   # Broche pour les impulsions du cadran
PIN_HOOK_SWITCH = 9     # Broche pour le crochet (décroché/raccroché)

class AsyncTelephoneController:
    def __init__(self):
        # Initialisation du mixeur audio
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

        # Liaison avec votre classe Rotary
        self.rotary = Rotary(
            on_compose_start=self._thread_safe_compose_start,
            on_compose_end=self._thread_safe_compose_end
        )

        # --- Initialisation des composants GPIO ---
        # GPIO 17 : Impulsions du cadran (Filtrage antirebond de 20ms)
        self.bouton_pulse = Button(PIN_ROTARY_PULSE, pull_up=True, bounce_time=0.02)
        self.bouton_pulse.when_pressed = self._on_gpio_pulse

        # GPIO 9 : Crochet du téléphone (Filtrage antirebond de 50ms pour éviter les faux déclenchements)
        self.crochet = Button(PIN_HOOK_SWITCH, pull_up=True, bounce_time=0.05)
        self.crochet.when_pressed = self._thread_safe_decrocher
        self.crochet.when_released = self._thread_safe_raccrocher

    # --- Gestionnaires d'interruptions matérielles (Thread-Safe) ---
    def _on_gpio_pulse(self):
        """Appelé à chaque impulsion reçue sur le GPIO 17."""
        if self.est_decroche:
            self.rotary.on_pulse()

    def _thread_safe_decrocher(self):
        """Passerelle sécurisée vers la boucle asynchrone lors du décrochage."""
        self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.decrocher()))

    def _thread_safe_raccrocher(self):
        """Passerelle sécurisée vers la boucle asynchrone lors du raccrochage."""
        self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.raccrocher()))

    def _thread_safe_compose_start(self):
        self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.on_composition_start()))

    def _thread_safe_compose_end(self, numero):
        self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.on_composition_end(numero)))

    # --- Logique Métier Asynchrone ---
    async def decrocher(self):
        if not self.est_decroche:
            print("\n[Matériel] Combiné décroché (GPIO 9) ! Tonalité lancée.")
            self.est_decroche = True
            if self.son_tonalite:
                self.canal_tonalite.play(self.son_tonalite, loops=-1)

    async def raccrocher(self):
        if self.est_decroche:
            print("\n[Matériel] Combiné raccroché (GPIO 9) ! Coup de grâce audio immédiat.")
            self.est_decroche = False
            
            # Annulation instantanée de la tâche asynchrone de lecture en arrière-plan
            if self._current_audio_task and not self._current_audio_task.done():
                self._current_audio_task.cancel()
                
            # Arrêt des sorties sonores matérielles
            self.canal_tonalite.stop()
            self.canal_audio.stop()
            
            # Réinitialisation des buffers de votre classe rotary.py
            with self.rotary.lock:
                self.rotary.value = ""
                self.rotary.pulse_count = 0

    async def on_composition_start(self):
        if self.est_decroche:
            print("[Cadran] Premier mouvement mécanique détecté -> Tonalité coupée.")
            self.canal_tonalite.stop()

    async def on_composition_end(self, numero):
        if not self.est_decroche:
            return

        print(f"[Cadran] Composition validée. Numéro traité : {numero}")
        
        # Si un message audio était déjà en train de jouer, on l'interrompt pour lancer le nouveau
        if self._current_audio_task and not self._current_audio_task.done():
            print("[Lecteur] Interruption du fichier en cours pour nouvelle composition...")
            self._current_audio_task.cancel()

        fichier = NUMEROS_AUDIO.get(numero, NUMEROS_AUDIO["DEFAULT"])
        self._current_audio_task = asyncio.create_task(self._jouer_audio_async(fichier))

    async def _jouer_audio_async(self, fichier_path):
        try:
            try:
                son = pygame.mixer.Sound(fichier_path)
                self.canal_audio.play(son)
                print(f"[Lecteur] Lecture active : {fichier_path}")
                
                # Boucle d'attente non-bloquante pour vérifier la fin du fichier
                while self.canal_audio.get_busy():
                    await asyncio.sleep(0.1)
                    
                print(f"[Lecteur] Lecture terminée naturellement : {fichier_path}")
            except Exception:
                # Fallback de simulation si vos fichiers audios finaux ne sont pas encore créés
                print(f"[Lecteur] Fichier absent : {fichier_path}. Émulation de 5s...")
                for i in range(1, 6):
                    await asyncio.sleep(1)
                print("[Lecteur] Fin d'émulation.")
                
        except asyncio.CancelledError:
            print(f"[Lecteur] Tâche de lecture annulée proprement.")
            self.canal_audio.stop()

async def main():
    controller = AsyncTelephoneController()
    print("====================================================")
    print("Application 'APO' lancée sur le Raspberry Pi.")
    print("Écoute active sur : GPIO 17 (Cadran) et GPIO 9 (Crochet).")
    print("====================================================")
    
    # Maintient le script en vie indéfiniment de façon non-bloquante
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nArrêt propre du programme.")
    finally:
        pygame.mixer.quit()
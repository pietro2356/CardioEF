import cv2
import numpy as np

class ROISelector:
    """
    Gestisce l'interazione utente per definire la regione di interesse (ROI)
    e generare la maschera di inizializzazione.
    """

    def __init__(self, window_name="Seleziona ROI (Invio per confermare)"):
        self.window_name = window_name

    def select_and_mask(self, image):
        """
        Apre una finestra GUI per la selezione.

        Args:
            image: numpy array uint8 (l'immagine su cui disegnare)

        Returns:
            mask: numpy array uint8 (binaria: 255 dentro l'ellisse, 0 fuori)
            roi_coords: tuple (x, y, w, h) del box selezionato
        """
        # Copia per non sporcare l'originale
        img_display = image.copy()

        # Se l'immagine è grayscale, la convertiamo in BGR solo per la visualizzazione
        # (altrimenti il rettangolo di selezione azzurro di OpenCV non si vede bene)
        if len(img_display.shape) == 2:
            img_display = cv2.cvtColor(img_display, cv2.COLOR_GRAY2BGR)

        print(f"[ISTRUZIONI] Trascina il mouse per selezionare il Ventricolo Sinistro.")
        print(f"[ISTRUZIONI] Premi SPACE o INVIO per confermare. Premi C per cancellare.")

        # 1. Selezione Manuale (Funzione nativa OpenCV)
        # showCrosshair=True mostra una croce per mirare meglio
        rect = cv2.selectROI(self.window_name, img_display, showCrosshair=True, fromCenter=False, printNotice=True)

        # Chiudiamo la finestra di selezione
        cv2.destroyWindow(self.window_name)

        x, y, w, h = rect

        # Controllo anti-pigrizia: se l'utente clicca senza trascinare (w=0 o h=0)
        if w == 0 or h == 0:
            raise ValueError("Selezione non valida! Devi trascinare un rettangolo.")

        print(f"[INFO] ROI selezionata: x={x}, y={y}, w={w}, h={h}")

        # 2. Creazione Maschera Ellittica
        # Creiamo un'immagine nera delle stesse dimensioni dell'input
        mask = np.zeros(image.shape[:2], dtype=np.uint8)

        # Calcoliamo centro e assi dell'ellisse
        center = (int(x + w / 2), int(y + h / 2))
        axes = (int(w / 2), int(h / 2))

        # Disegniamo l'ellisse bianca (255) piena (-1)
        # Angolo 0 perché assumiamo che il box sia dritto.
        # In ecografia apicale il cuore è spesso verticale, quindi va bene.
        cv2.ellipse(mask, center, axes, angle=0, startAngle=0, endAngle=360, color=255, thickness=-1)

        return mask, rect

class PolygonROISelector:
    def __init__(self, window_name="ROI Poligonale"):
        self.window_name = window_name
        self.points = []  # Lista per salvare i click (x, y)
        self.image_display = None  # Immagine temporanea per il disegno

    def mouse_callback(self, event, x, y, flags, param):
        """
        Funzione chiamata automaticamente da OpenCV ogni volta che il mouse si muove o clicca.
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            # 1. Aggiungi il punto alla lista
            self.points.append((x, y))
            print(f"[CLICK] Punto aggiunto: ({x}, {y})")

            # 2. Feedback Visivo immediato
            # Disegna un cerchio sul punto cliccato
            cv2.circle(self.image_display, (x, y), 3, (0, 0, 255), -1)

            # Se abbiamo almeno 2 punti, disegna la linea che li collega
            if len(self.points) > 1:
                cv2.line(self.image_display, self.points[-2], self.points[-1], (0, 255, 0), 1)

            # Aggiorna la finestra
            cv2.imshow(self.window_name, self.image_display)

    def select_and_mask(self, image):
        """
        Gestisce il loop di selezione.
        Tasti:
        - CLICK SX: Aggiungi punto
        - C: Cancella tutto e ricomincia
        - INVIO / SPAZIO: Conferma e chiudi
        """
        # Convertiamo in BGR per poter disegnare linee colorate anche se l'input è grayscale
        if len(image.shape) == 2:
            self.image_display = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            self.image_display = image.copy()

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        # Colleghiamo il mouse alla nostra funzione
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        print("-" * 30)
        print("MODALITÀ DISEGNO POLIGONO")
        print("1. Clicca col tasto SINISTRO per aggiungere punti attorno al ventricolo.")
        print("2. Premi 'c' per cancellare e ricominciare.")
        print("3. Premi SPAZIO o INVIO per terminare e chiudere il poligono.")
        print("-" * 30)

        cv2.imshow(self.window_name, self.image_display)

        # Loop di attesa
        while True:
            key = cv2.waitKey(1) & 0xFF

            # Tasto INVIO (13) o SPAZIO (32) -> Conferma
            if key == 13 or key == 32:
                if len(self.points) < 3:
                    print("[ERRORE] Servono almeno 3 punti per un poligono!")
                    continue
                break

            # Tasto 'c' -> Pulisci
            elif key == ord('c'):
                self.points = []
                # Reset immagine
                if len(image.shape) == 2:
                    self.image_display = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                else:
                    self.image_display = image.copy()
                cv2.imshow(self.window_name, self.image_display)
                print("[RESET] Punti cancellati.")

        cv2.destroyWindow(self.window_name)

        # --- GENERAZIONE MASCHERA ---
        # Creiamo una maschera nera
        mask = np.zeros(image.shape[:2], dtype=np.uint8)

        # Convertiamo i punti in un array numpy nel formato richiesto da fillPoly
        pts = np.array(self.points, np.int32)
        pts = pts.reshape((-1, 1, 2))

        # Riempiamo il poligono di bianco (255)
        cv2.fillPoly(mask, [pts], 255)

        return mask, self.points
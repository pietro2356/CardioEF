import cv2
import numpy as np

class SegmentatorWatershed:
    def __init__(self, erosion_iter=2, dilation_iter=2):
        """
        Args:
            erosion_iter: Quanto 'restringere' la maschera utente per trovare il "centro sicuro".
            dilation_iter: Quanto 'allargare' la maschera utente per trovare lo "sfondo sicuro".
        """
        self.erosion_iter = erosion_iter
        self.dilation_iter = dilation_iter

    def run(self, image, user_mask):
        """
        Esegue il Marker-Controlled Watershed.

        Args:
            image: Immagine di input (256x256 uint8).
            user_mask: Maschera binaria (poligono) fornita dall'utente.

        Returns:
            final_mask: Maschera binaria segmentata.
            markers_vis: Immagine colorata per visualizzare cosa ha fatto l'algoritmo (debugging).
        """
        # 1. Preparazione Immagine
        # cv2.watershed richiede un'immagine a 3 canali, anche se lavoriamo in scala di grigi
        if len(image.shape) == 2:
            img_color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            img_color = image.copy()

        # 2. Definizione Marker (La parte intelligente)
        kernel = np.ones((3, 3), np.uint8)

        # A. SURE FOREGROUND (Il cuore del ventricolo)
        # Erodiamo il poligono utente: rimuoviamo i bordi incerti, teniamo il centro.
        sure_fg = cv2.erode(user_mask, kernel, iterations=self.erosion_iter)

        # B. SURE BACKGROUND (Tutto ciò che è sicuramente fuori)
        # Dilatiamo il poligono utente: tutto ciò che è oltre questa linea è sfondo.
        sure_bg_area = cv2.dilate(user_mask, kernel, iterations=self.dilation_iter)
        # Invertiamo: 255 diventa la zona lontana dal cuore
        sure_bg = cv2.bitwise_not(sure_bg_area)

        # C. UNKNOWN (La zona dove cercare il bordo reale)
        # È la ciambella tra la dilatazione e l'erosione
        unknown = cv2.subtract(sure_bg_area, sure_fg)

        # 3. Creazione Mappa dei Marker (int32 per OpenCV)
        # 0 = Unknown (calcola qui)
        # 1 = Background
        # 2 = Foreground (Ventricolo)

        markers = np.zeros(image.shape[:2], dtype=np.int32)
        markers[sure_bg == 255] = 1  # Sfondo certo
        markers[sure_fg == 255] = 2  # Ventricolo certo
        markers[unknown == 255] = 0  # Zona incerta (Watershed lavorerà qui)

        # 4. Esecuzione Watershed
        # L'algoritmo modifica 'markers' in-place.
        # I confini trovati saranno segnati con -1.
        cv2.watershed(img_color, markers)

        # 5. Estrazione Risultato
        # Vogliamo solo la regione che l'algoritmo ha deciso essere "2" (Ventricolo)
        final_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        final_mask[markers == 2] = 255

        # --- Visualizzazione Debug (Opzionale ma utile per il report) ---
        markers_vis = img_color.copy()
        # Colora i confini trovati (-1) di rosso
        markers_vis[markers == -1] = [0, 0, 255]
        # Colora la regione interna trovata di verde (in trasparenza simulata)
        markers_vis[markers == 2] = [0, 255, 0]

        return final_mask, markers_vis

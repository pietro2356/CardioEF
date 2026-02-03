import cv2

class EchoPreprocessor:
    """
    Classe dedicata alla pulizia dell'immagine ecocardiografica.
    Pipeline: Bilateral Filter -> CLAHE
    """

    def __init__(self):
        # CLAHE: Contrast Limited Adaptive Histogram Equalization
        # clipLimit: soglia per evitare di amplificare troppo il rumore (2.0 - 4.0 è standard)
        # tileGridSize: dimensione della griglia locale (8x8 è standard OpenCV)
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

    def apply(self, img):
        """
        Input: Immagine uint8
        Output: Immagine filtrata uint8
        """
        # 1. Bilateral Filter
        # Mantiene i bordi (edges) ma rimuove il rumore (speckle) nelle zone piatte.
        # d=9: Diametro del pixel neighborhood.
        # sigmaColor=75: Quanto devono essere diverse le intensità per non essere mixate (alto = mantiene solo bordi forti).
        # sigmaSpace=75: Quanto distanti devono essere i pixel per influenzarsi.
        denoised = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)

        # 2. CLAHE
        # Aumenta il contrasto locale per rendere visibile il ventricolo
        enhanced = self.clahe.apply(denoised)

        return enhanced
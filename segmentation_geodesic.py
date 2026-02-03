from skimage.segmentation import morphological_geodesic_active_contour, inverse_gaussian_gradient
from skimage import img_as_float


class SegmentatorGeodesic:
    """
    Implementa il Morphological Geodesic Active Contour (MorphGAC).
    Adatto per trovare contorni in immagini rumorose (Ultrasuoni).
    """

    def __init__(self, iterations=250, smoothing=3, threshold=0.3, balloon=0):
        """
        Parametri Tattici:
        - iterations: Quanti passi fa l'algoritmo.
        - smoothing: (1-3) Quanto rendiamo rigido il contorno.
                     Alto = forma più circolare/liscia (buono per il cuore).
                     Basso = segue ogni singolo pixel (male per lo speckle).
        - threshold: "Soglia di arresto". Valori più bassi rendono il contorno
                     più sensibile ai bordi deboli.
        - balloon: (+1 o -1).
                   0: Si muove solo per curvatura e attrazione bordi (Più stabile).
                   +1: Si gonfia come un palloncino (utile se partiamo da dentro).
                   -1: Si sgonfia (utile se partiamo da fuori).
        """
        self.iterations = iterations
        self.smoothing = smoothing
        self.threshold = threshold
        self.balloon = balloon

    def compute_gimage(self, image):
        """
        Calcola la 'Stopping Function' (Inverse Gaussian Gradient).
        I bordi diventano valli scure (vicino a 0), le aree piatte diventano picchi chiari (vicino a 1).
        """
        # Convertiamo in float per calcoli precisi (range 0.0 - 1.0)
        img_float = img_as_float(image)

        # alpha: grandezza del filtro gaussiano (sigma). Più alto = ignora lo speckle fine.
        # Un valore di 100-200 è tipico per immagini mediche molto rumorose.
        gimage = inverse_gaussian_gradient(img_float, alpha=1000.0, sigma=2.0)

        return gimage

    def run(self, image, initial_mask):
        """
        Esegue la segmentazione.

        Args:
            image: Immagine di input (256x256 uint8).
            initial_mask: Maschera binaria di partenza (l'ellisse).

        Returns:
            final_mask: Maschera binaria risultante.
            evolution: Lista di maschere intermedie (per fare video/debug).
        """
        # 1. Calcolo mappa dei bordi
        gimage = self.compute_gimage(image)

        # 2. Esecuzione MorphGAC
        # init_level_set accetta la maschera booleana o binaria
        print(f"[INFO] Avvio MorphGAC per {self.iterations} iterazioni...")

        final_level_set = morphological_geodesic_active_contour(
            gimage,
            self.iterations,
            init_level_set=initial_mask,
            smoothing=self.smoothing,
            threshold=self.threshold,
            balloon=self.balloon
        )

        return final_level_set, gimage
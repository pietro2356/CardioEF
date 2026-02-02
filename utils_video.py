import cv2
import os

def extract_specific_frames(video_path, frame_indices):
    """
    Estrae frame specifici da un video .avi.

    Args:
        video_path (str): Percorso del file video.
        frame_indices (list): Lista di interi dei frame da estrarre (es. [0, 45]).
                              Attenzione: OpenCV usa indici 0-based.

    Returns:
        dict: Dizionario {frame_index: image_array}
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video non trovato: {video_path}")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise IOError(f"Impossibile aprire il video: {video_path}")

    extracted_frames = {}

    # Recuperiamo info totali per safety check
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for idx in frame_indices:
        if idx >= total_frames:
            print(f"[WARN] Frame {idx} fuori dal range (Totale: {total_frames}). Salto.")
            continue

        # SEEKING: Saltiamo direttamente al frame desiderato
        # CV_CAP_PROP_POS_FRAMES è la proprietà per impostare l'indice
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)

        ret, frame = cap.read()

        if ret:
            # Convertiamo subito in Grayscale per coerenza col progetto
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            extracted_frames[idx] = frame_gray
        else:
            print(f"[ERRORE] Impossibile leggere il frame {idx}")

    cap.release()
    return extracted_frames


def standardize_image_size(image, target_size=(256, 256)):
    """
    Ridimensiona l'immagine a una dimensione fissa per l'elaborazione.
    Usa interpolazione bicubica per mantenere la coerenza dei gradienti.

    Args:
        image: array numpy uint8 (es. 112x112)
        target_size: tuple (width, height) - Default 256x256

    Returns:
        resized_image: array numpy uint8 (256x256)
        scale_factor: tuple (scale_x, scale_y) utile per riportare la maschera alle dimensioni originali
    """
    h, w = image.shape
    target_w, target_h = target_size

    # Calcoliamo i fattori di scala (serviranno alla fine per la valutazione!)
    scale_x = target_w / w
    scale_y = target_h / h

    resized_image = cv2.resize(image, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

    return resized_image, (scale_x, scale_y)
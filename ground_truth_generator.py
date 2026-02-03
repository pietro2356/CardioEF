import pandas as pd
import numpy as np
import cv2
import matplotlib.pyplot as plt

def get_ground_truth_masks(csv_path, filename, original_shape, target_shape):
    """
    Legge VolumeTracings.csv e restituisce le maschere binarie per i frame annotati.

    Args:
        csv_path (str): Path al file VolumeTracings.csv
        filename (str): Il nome del file video (es. '0X100009310A3BD7FC.avi')
        original_shape (tuple): (112, 112) dimensione originale dei dati
        target_shape (tuple): (256, 256) dimensione su cui lavora il tuo algoritmo

    Returns:
        dict: { frame_index: mask_array_256x256 }
    """
    # 1. Caricamento e Filtro
    df = pd.read_csv(csv_path)

    # Rimuoviamo l'estensione .avi se nel CSV non c'è, o viceversa.
    # EchoNet nel CSV tracings a volte usa l'estensione, a volte no. Controlla.
    # Qui assumiamo che nel CSV ci sia 'nomefile.avi' come nel tuo esempio.
    df_file = df[df['FileName'] == filename]

    if df_file.empty:
        print(f"[WARN] Nessuna traccia trovata per {filename}")
        return {}

    # Calcoliamo i fattori di scala (es. 256/112 = 2.28)
    scale_x = target_shape[0] / original_shape[0]
    scale_y = target_shape[1] / original_shape[1]

    masks = {}

    # 2. Iteriamo sui frame unici trovati (dovrebbero essere 2: ED e ES)
    unique_frames = df_file['Frame'].unique()

    for frame_idx in unique_frames:
        # Prendiamo i punti di quel frame
        df_frame = df_file[df_file['Frame'] == frame_idx]

        # 3. Costruzione del Poligono
        # I punti X1, Y1 sono un lato. I punti X2, Y2 sono l'altro.
        # Spesso sono ordinati dall'apice alla base o viceversa.

        pts1 = df_frame[['X1', 'Y1']].values
        pts2 = df_frame[['X2', 'Y2']].values

        # Scaliamo le coordinate
        pts1[:, 0] *= scale_x
        pts1[:, 1] *= scale_y
        pts2[:, 0] *= scale_x
        pts2[:, 1] *= scale_y

        # Uniamo i punti per formare un anello chiuso.
        # Punti 1 in ordine normale + Punti 2 in ordine INVERSO (per chiudere il giro)
        polygon_pts = np.concatenate((pts1, pts2[::-1]))

        # Arrotondiamo a interi per OpenCV
        polygon_pts = polygon_pts.astype(np.int32)
        polygon_pts = polygon_pts.reshape((-1, 1, 2))

        # 4. Disegno Maschera
        mask = np.zeros(target_shape, dtype=np.uint8)
        cv2.fillPoly(mask, [polygon_pts], 255)

        masks[frame_idx] = mask

    return masks
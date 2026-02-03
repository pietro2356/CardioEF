# -------------------------------------------------------------------------
# Project: CardioEF
# Dataset Source: EchoNet-Dynamic (Stanford University)
# Reference: Ouyang et al. (2020). Video-based AI for beat-to-beat assessment of cardiac function. *Nature*, 580(7802), 252-256.
# -------------------------------------------------------------------------

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from dotenv import load_dotenv
from echo_processor import EchoPreprocessor
from ground_truth_generator import get_ground_truth_masks
from roi_selector import PolygonROISelector
from segmentation_geodesic import SegmentatorGeodesic
from segmentation_watershed import SegmentatorWatershed
from utils_video import standardize_image_size, extract_specific_frames

# --- CONFIGURAZIONE ---
load_dotenv()

BASE_PATH = os.getenv('DATASET_BASE_PATH')
VIDEOS_PATH = os.path.join(BASE_PATH, "Videos")
TRACINGS_CSV = os.path.join(BASE_PATH, "VolumeTracings.csv")
FILELIST_CSV = os.path.join(BASE_PATH, "FileList.csv")
REPORT_PATH = os.getenv('REPORT_BASE_PATH')

TARGET_SIZE = (256, 256)


def calculate_dice(mask1, mask2):
    """Calcola il DICE Score tra due maschere binarie."""
    if mask1 is None or mask2 is None: return 0.0

    m1 = mask1 > 0
    m2 = mask2 > 0
    intersection = np.logical_and(m1, m2).sum()
    if (m1.sum() + m2.sum()) == 0: return 0.0

    return 2. * intersection / (m1.sum() + m2.sum())


def calculate_volume_single_plane(mask, pixel_spacing_mm=1.0):
    """
    Stima il volume (ml) usando il metodo Area-Length (Single Plane).
    Formula: V = (8 * Area^2) / (3 * pi * Length)
    """
    if mask is None or np.sum(mask) == 0: return 0.0

    # Area in pixel
    area_pixels = np.sum(mask > 0)

    # Lunghezza (Length): Approssimiamo con l'altezza del bounding box
    # (In proiezione Apicale 4 Camere il cuore è verticale)
    x, y, w, h = cv2.boundingRect(mask)
    length_pixels = h

    # Conversione in cm (assumendo pixel_spacing, se noto. Qui usiamo unitario per confronto relativo)
    # Nota: Per volumi reali (ml) servirebbe la calibrazione esatta del pixel (cm/px).
    # Qui calcoliamo un "Volume Index" in unità arbitrarie se il pixel_spacing non è accurato.

    volume = (8.0 * (area_pixels ** 2)) / (3.0 * np.pi * length_pixels)
    return volume

def compute_ef_from_vols(vols, ref_ef_val=None):
    """
    Calcola EF (stringa) e stringa di errore a partire da una lista di volumi.
    Se ref_ef_val è None non viene calcolato l'errore.
    """
    ef_str = "N/A"
    err_str = ""
    if len(vols) >= 2:
        edv, esv = max(vols), min(vols)
        ef_val = (edv - esv) / edv if edv > 0 else 0
        ef_str = f"{ef_val * 100:.1f}%"
        if ref_ef_val is not None:
            diff = abs(ef_val * 100 - ref_ef_val)
            err_str = f"(Err: {diff:.1f}%)"
    return ef_str, err_str

def create_and_save_report(clean_name, results, ref_ef_str, ref_ef_val, ef_snake_str, err_snake, ef_ws_str, err_ws, report_base_path=REPORT_PATH):
    """
    Crea la figura di report, la salva e la mostra.
    - clean_name: nome pulito del file (senza estensione)
    - results: lista di dict con 'img','gt','snake','watershed','d_snake','d_water','frame'
    - ref_ef_str: stringa EF di riferimento (es. "55.0%" o "N/A")
    - ref_ef_val: valore numerico EF di riferimento o None
    - ef_snake_str, err_snake, ef_ws_str, err_ws: stringhe EF/errore da mostrare
    """
    fig, axes = plt.subplots(len(results), 4, figsize=(18, 10))
    if len(results) == 1:
        axes = np.array([axes])
        axes = axes.reshape(1, -1)

    title_text = (f"Paziente: {clean_name}\n"
                  f"EF CLINICA (Stanford): {ref_ef_str}\n"
                  f"EF Snake: {ef_snake_str} {err_snake}  |  EF Watershed: {ef_ws_str} {err_ws}")

    fig.suptitle(title_text, fontsize=16, fontweight='bold', y=0.98)

    for i, res in enumerate(results):
        ax_row = axes[i]

        # Col 1: Originale
        ax_row[0].imshow(res['img'], cmap='gray')
        ax_row[0].set_title(f"Frame {res['frame']}", fontsize=10)
        ax_row[0].axis('off')

        # Col 2: Ground Truth
        ax_row[1].imshow(res['img'], cmap='gray')
        if res['gt'] is not None:
            ax_row[1].contour(res['gt'], colors='lime', linewidths=2)
        ax_row[1].set_title("Ground Truth", fontsize=10, color='green')
        ax_row[1].axis('off')

        # Col 3: Snake
        ax_row[2].imshow(res['img'], cmap='gray')
        ax_row[2].contour(res['snake'], colors='red', linewidths=2)
        dice_txt = f"{res['d_snake']:.3f}"
        ax_row[2].set_title(f"Snake\nDICE: {dice_txt}", fontsize=11, fontweight='bold', color='red')
        ax_row[2].axis('off')

        # Col 4: Watershed
        ax_row[3].imshow(res['img'], cmap='gray')
        ax_row[3].contour(res['watershed'], colors='cyan', linewidths=2)
        dice_txt = f"{res['d_water']:.3f}"
        ax_row[3].set_title(f"Watershed\nDICE: {dice_txt}", fontsize=11, fontweight='bold', color='blue')
        ax_row[3].axis('off')

    plt.tight_layout()
    plt.subplots_adjust(top=0.82, hspace=0.15)

    output_dir = os.path.join(report_base_path, "Reports_Images")
    os.makedirs(output_dir, exist_ok=True)

    ef_filename_part = f"_REF{ref_ef_val:.0f}" if ref_ef_str != "N/A" and ref_ef_val is not None else ""
    save_filename = f"{clean_name}{ef_filename_part}_Report.png"
    save_path = os.path.join(output_dir, save_filename)

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"[INFO] Report salvato: {save_path}")

    plt.show()
    plt.close(fig)

def process_patient(filename):
    print(f"\n{'=' * 50}")
    print(f"PROCESSANDO PAZIENTE: {filename}")
    print(f"{'=' * 50}")

    # 1. Recupero Info Frame (ED / ES) da VolumeTracings
    try:
        df_tracings = pd.read_csv(TRACINGS_CSV)
        patient_data = df_tracings[df_tracings['FileName'] == filename]

        if patient_data.empty:
            print("[SKIP] Nessun dato di tracciamento per questo file.")
            return

        frames_to_process = patient_data['Frame'].unique()  # Es. [46, 82]
        print(f"[INFO] Frame annotati trovati: {frames_to_process}")

    except Exception as e:
        print(f"[ERRORE] Lettura CSV: {e}")
        return

    # 1.1 Recupero EF di Riferimento da FileList.csv
    ref_ef_str = "N/A"
    try:
        df_list = pd.read_csv(FILELIST_CSV)
        clean_name = os.path.splitext(filename)[0]

        # Cerchiamo la riga
        row = df_list[df_list['FileName'] == clean_name]

        if not row.empty:
            ref_ef_val = row['EF'].values[0]
            ref_ef_str = f"{ref_ef_val:.1f}%"
            print(f"[DATASET] EF Clinica di Riferimento (Stanford): {ref_ef_str}")
        else:
            print("[WARN] FileName non trovato in FileList.csv")

    except Exception as e:
        print(f"[WARN] Impossibile leggere FileList.csv: {e}")

    # 2. Estrazione Video
    video_path = os.path.join(VIDEOS_PATH, filename)
    try:
        frames_dict = extract_specific_frames(video_path, frames_to_process)
    except Exception as e:
        print(f"[ERRORE] Estrazione video: {e}")
        return

    # 3. Caricamento Ground Truth
    gt_masks = get_ground_truth_masks(
        TRACINGS_CSV,
        filename,
        (112, 112), # Original Size - Valutare se dinamico
        TARGET_SIZE
    )

    # Inizializzazione Algoritmi
    preprocessor = EchoPreprocessor()
    roi_selector = PolygonROISelector(window_name=f"Seleziona ROI - {filename}")

    # METODO A: Geodesic Active Contour
    seg_snake = SegmentatorGeodesic(iterations=500, smoothing=2, balloon=1)

    # METODO B: Watershed
    seg_watershed = SegmentatorWatershed(erosion_iter=3, dilation_iter=3)

    results = []

    # 4. Loop sui Frame (ED e ES)
    for frame_idx in frames_to_process:
        print(f"\n--- Frame {frame_idx} ---")

        # A. Preprocessing
        original = frames_dict[frame_idx]
        img_work, scale = standardize_image_size(original, TARGET_SIZE)
        img_clean = preprocessor.apply(img_work)

        # B. Interazione Utente (ROI)
        print("Seleziona il poligono attorno al ventricolo...")
        mask_roi, _ = roi_selector.select_and_mask(img_clean)

        # C. Esecuzione Algoritmi
        # 1. Snake
        mask_snake, _ = seg_snake.run(img_clean, mask_roi)
        # Convertiamo output snake (float/bool) in uint8 per coerenza
        mask_snake = mask_snake.astype(np.uint8) * 255

        # 2. Watershed
        mask_watershed, _ = seg_watershed.run(img_clean, mask_roi)

        # D. Valutazione
        gt_mask = gt_masks.get(frame_idx, None)

        dice_snake = calculate_dice(gt_mask, mask_snake)
        dice_watershed = calculate_dice(gt_mask, mask_watershed)

        print(f"--> DICE Snake: {dice_snake:.4f}")
        print(f"--> DICE Watershed: {dice_watershed:.4f}")

        # Salvataggio risultati per plot finale
        results.append({
            'frame': frame_idx,
            'img': img_clean,
            'gt': gt_mask,
            'snake': mask_snake,
            'watershed': mask_watershed,
            'd_snake': dice_snake,
            'd_water': dice_watershed
        })

        # ---------------------------------------------------------
        # 5. CALCOLO EJECTION FRACTION (EF) E PREPARAZIONE DATI
        # ---------------------------------------------------------
        vols_snake = [calculate_volume_single_plane(r['snake']) for r in results]
        vols_ws = [calculate_volume_single_plane(r['watershed']) for r in results]

        ref_val = ref_ef_val if ref_ef_str != "N/A" else None

        ef_snake_str, err_snake = compute_ef_from_vols(vols_snake, ref_val)
        ef_ws_str, err_ws = compute_ef_from_vols(vols_ws, ref_val)

        print(f"\n[RISULTATI] REF: {ref_ef_str} | Snake: {ef_snake_str} {err_snake} | Watershed: {ef_ws_str} {err_ws}")

        # ---------------------------------------------------------
        # 6. VISUALIZZAZIONE REPORT CON CONFRONTO
        # ---------------------------------------------------------
        create_and_save_report(
            clean_name,
            results,
            ref_ef_str,
            ref_val,
            ef_snake_str,
            err_snake,
            ef_ws_str,
            err_ws
        )


# --- MAIN ---
if __name__ == "__main__":
    df = pd.read_csv(FILELIST_CSV)

    print(f"[INFO] Caricato CSV con {len(df)} voci da {FILELIST_CSV}")

    row = df.iloc[5]
    filename = row['FileName'] + ".avi"

    process_patient(filename)
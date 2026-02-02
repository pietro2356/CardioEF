# CardioEF: Automated Left Ventricle Segmentation & Ejection Fraction Estimation

**CardioEF** è una pipeline di Computer Vision classica progettata per l'analisi automatica di ecocardiografie (Apical-4-Chamber view). Il progetto confronta due approcci di segmentazione semi-automatica (**Active Contours** vs **Marker-Controlled Watershed**) per isolare il ventricolo sinistro, calcolare i volumi cardiaci e stimare la Frazione di Eiezione (EF), un parametro vitale per la diagnosi di insufficienza cardiaca.

Il sistema è validato sul dataset open-source **EchoNet-Dynamic** (Stanford Medicine).

---

## 🏥 Contesto Clinico

L'ecocardiografia è la modalità di imaging più comune per valutare la funzionalità cardiaca. Il parametro chiave estratto è la **Frazione di Eiezione (EF)**, che indica la percentuale di sangue pompata fuori dal ventricolo a ogni battito.

$$EF (\%) = \frac{EDV - ESV}{EDV} \times 100$$

Dove:
* **EDV (End-Diastolic Volume):** Volume massimo (cuore rilassato/pieno).
* **ESV (End-Systolic Volume):** Volume minimo (cuore contratto).

Un'accurata segmentazione del ventricolo sinistro è fondamentale per calcolare questi volumi. CardioEF automatizza questo processo riducendo la variabilità soggettiva e confrontando i risultati con i tracciati manuali di cardiologi esperti.

---

## ⚙️ Architettura Tecnica

Il progetto implementa una pipeline modulare in Python:

### 1. Preprocessing Avanzato
Le immagini ecografiche sono affette da *speckle noise* (rumore granulare).
* **Ridimensionamento:** Standardizzazione a 256x256.
* **CLAHE (Contrast Limited Adaptive Histogram Equalization):** Per migliorare il contrasto locale delle pareti cardiache.
* **Bilateral Filter:** Per rimuovere il rumore preservando i bordi (edge-preserving smoothing).

### 2. Algoritmi di Segmentazione (Confronto)
Il software richiede un input iniziale utente (ROI poligonale) e applica due metodi in parallelo:

* **Metodo A: Geodesic Active Contours (Snakes)**
    * Utilizza curve evolutive che minimizzano un'energia interna (fluidità) ed esterna (gradiente dell'immagine).
    * *Pro:* Modella bene forme curve continue.
    * *Contro:* Sensibile all'inizializzazione e ai minimi locali.

* **Metodo B: Marker-Controlled Watershed**
    * Approccio morfologico basato sull'immersione. Utilizza la ROI utente per definire zone di "Sure Foreground" (Erosione) e "Sure Background" (Dilatazione).
    * *Pro:* Deterministico, robusto al rumore speckle, evita sovra-segmentazione grazie ai marker.

### 3. Stima Volumetrica
I volumi sono calcolati utilizzando il **Metodo Area-Length (Single Plane)**, assumendo il ventricolo come un ellissoide di rotazione.

---

## 📊 Validazione e Risultati

Il sistema confronta i risultati ottenuti con il **Ground Truth** (tracciati manuali) fornito dal dataset EchoNet-Dynamic.

Le metriche di valutazione includono:
1.  **DICE Coefficient (Geometrico):** Misura la sovrapposizione tra la maschera generata e quella del medico ($0.0 - 1.0$).
2.  **Delta EF (Clinico):** Differenza assoluta tra l'EF calcolata dall'algoritmo e l'EF clinica riportata nel dataset.

*Esempio di Output:*
> **Watershed:** DICE Score ~0.80 (Alta affidabilità geometrica)
> **Clinica:** Errore medio EF < 5% (Accettabile per screening)

---

## 🚀 Installazione e Utilizzo

### Prerequisiti
* Python 3.8+
* Dataset EchoNet-Dynamic (scaricato localmente)

### 1. Clona il repository
```bash
git clone https://github.com/pietro2356/CardioEF.git
cd CardioEF
```

### 2. Installa le dipendenze
Tutte le librerie necessarie sono elencate in requirements.txt.
```bash
pip install -r requirements.txt
```

### 3. Configurazione
Copiate il file [.env.example](.env.example) e rinominatelo in `.env`.
All'interno modificate la variabile `DATASET_BASE_PATH` impostando come valore il percorso della cartella del dataset EchoNet-Dynamic.
> La variabile `REPORT_BASE_PATH` contiene il percorso dove salvare i report.
```dotenv
DATASET_BASE_PATH='C:/Percorso/Al/Dataset/EchoNet-Dynamic'
REPORT_BASE_PATH='./reports'
```

### 4. Esecuzione
Lancia la pipeline principale. Verrà analizzato un paziente di test (o una lista).
```bash
python main.py
```
Durante l'esecuzione:
- Verrà mostrato il frame (ED o ES).
- Disegna un poligono attorno al ventricolo col mouse (Click sx per i punti, Click dx per chiudere).
- Il sistema calcolerà le maschere e mostrerà il report comparativo.

## 📂 Struttura del Progetto
- [main.py](main.py): Script principale (Orchestrazione, Calcolo EF, Report).
- [roi_selector.py](roi_selector.py): Gestione dell'interfaccia utente per la selezione ROI.
- [segmentation_geodesic.py](segmentation_geodesic.py): Implementazione Active Contours (Snake).
- [segmentation_watershed.py](segmentation_watershed.py): Implementazione Marker-Controlled Watershed.
- [ground_truth_generator.py](ground_truth_generator.py): Parsing dei file CSV e generazione maschere di riferimento.
- [utils_video.py](utils_video.py): Estrazione frame da video AVI.

## 📝 Autori
Sviluppato per il corso di Tecnologie Multimediali.
- Pietro Rocchio
- Juri Marku
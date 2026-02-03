# Panoramica Architetturale di CardioEF

## Diagramma di Flusso ad Alto Livello

Descrizione per la presentazione:

1. **Input**: Il sistema prende in ingresso il video ecocardiografico grezzo.
2. **Preprocessing**: Le immagini vengono pulite dal rumore.
3. **Input Utente**: Il medico o l'operatore seleziona approssimativamente l'area del cuore.
4. **Core**: Il sistema traccia i contorni precisi, calcola i volumi (Diastole/Sistole) e la percentuale di Eiezione (EF).
5. **Output**: Viene generato un report che confronta i dati calcolati con quelli dell'ospedale.

```mermaid
graph LR
    A[Input Video Echocardiogram] --> B(Preprocessing & Pulizia)
    B --> C{Input Utente}
    C -->|Disegno ROI| CA
    
    subgraph CA["Core Algoritmico"]
        direction TB
        D[Segmentazione Automatica] --> E[Calcolo Volumi LV]
        E --> F[Stima Ejection Fraction]
    end
    
    CA --> G[Report Finale & Confronto Clinico]
    
    style A fill:#4DB6AC,stroke:#004D40,stroke-width:2px,color:#000
    style B fill:#B0BEC5,stroke:#37474F,stroke-width:1px,color:#000
    style C fill:#FFF176,stroke:#F57F17,stroke-width:2px,color:#000
    style D fill:#64B5F6,stroke:#0D47A1,stroke-width:2px,color:#000
    style E fill:#9575CD,stroke:#311B92,stroke-width:1px,color:#000
    style F fill:#9575CD,stroke:#311B92,stroke-width:1px,color:#000
    style G fill:#F06292,stroke:#880E4F,stroke-width:2px,color:#000
```

## Diagramma di Flusso Dettagliato del Processo

1. **Acquisizione**: Incrociamo il video `.avi` con il CSV dei tracciati per estrarre solo i due frame critici: **End-Diastole (ED)** e **End-Systole (ES)**. Recuperiamo anche l'EF di riferimento da `FileList.csv`.
2. **Preprocessing (EchoPreprocessor)**:
    - Ridimensioniamo a 256x256 per standardizzare l'input.
    - Applichiamo il **Bilateral Filter** per togliere lo speckle noise mantenendo i bordi.
    - Applichiamo **CLAHE** per risaltare le pareti del ventricolo.
3. **Selezione ROI**: L'utente disegna un poligono. Da questo generiamo una maschera binaria di partenza.
4. **Segmentazione**:
    - **Snake (Active Contours)**: Calcola il gradiente inverso e fa evolvere la curva usando forze elastiche (smoothing) e forze di "palloncino" (balloon).
    - **Watershed**: Usa la ROI per creare marker sicuri (interno/esterno) e lascia all'algoritmo il compito di trovare il confine esatto nella "zona incerta".
5. **Analisi**:
    - **Geometrica**: Calcoliamo il **DICE Score** confrontando le nostre maschere con il Ground Truth (tracciati manuali nel CSV).
    - **Clinica**: Stimiamo il volume (Metodo Area-Length) e calcoliamo la **Frazione di Eiezione**.
6. **Output**: Generiamo un'immagine composita con i contorni visivi, i valori numerici e il confronto diretto con i dati di Stanford.

```mermaid
flowchart TD
    subgraph INPUT ["1. Acquisizione Dati"]
    VID[Video .AVI] --> EXT[Extract Frames ED/ES]
    CSV[VolumeTracings.csv] --> EXT
    CSV_REF[FileList.csv] --> REF_EF[EF Clinica Riferimento]
    end

    subgraph PREP ["2. Preprocessing (EchoPreprocessor)"]
    EXT --> RESIZE[Resize 256x256]
    RESIZE --> BILA[Bilateral Filter<br/> Denoising]
    BILA --> CLAHE["CLAHE<br/> (Contrast Enhancement)"]
    end

    subgraph ROI ["3. Selezione ROI"]
    CLAHE --> USER[PolygonROISelector]
    USER --> MASK_ROI[Maschera Iniziale]
    end

    subgraph SEG ["4. Segmentazione Parallela"]
    
    direction TB
    MASK_ROI --> SNAKE_PATH
    MASK_ROI --> WATER_PATH
    
        subgraph SNAKE_PATH [Path A: Active Contours]
        GRAD[Inverse Gaussian Gradient]
        MORPH["Morphological Snake<br/>(Balloon Force)"]
        GRAD --> MORPH
        end

        subgraph WATER_PATH [Path B: Watershed]
        ERO["Erosione<br/>(Sure FG)"]
        DIL["Dilatazione<br/>(Sure BG)"]
        MARK[Marker Generation]
        ERO & DIL --> MARK
        MARK --> WS_ALGO[Cv2.Watershed]
        end
    end

    subgraph ANALISYS ["5. Analisi & Validazione"]
    MORPH --> VOL_S[Calcolo Volume Snake]
    WS_ALGO --> VOL_W[Calcolo Volume Watershed]
    
    VOL_S & VOL_W --> EF_CALC["Calcolo EF %<br/>(EDV-ESV)"/EDV]
    
    GT[Ground Truth Masks] --> DICE[Calcolo DICE Score]
    MORPH & WS_ALGO --> DICE
    end

    subgraph OUTPUT ["6. Output"]
    EF_CALC & DICE & REF_EF --> REPORT[Generazione Grafico PNG]
    REPORT --> SAVE[Salvataggio su Disco]
    end

    PREP --> ROI
    ROI --> SEG
    SEG --> ANALISYS
    ANALISYS --> OUTPUT

    %% Input: Verde Lime (Visibile su scuro)
    style INPUT fill:#C5E1A5,stroke:#33691E,color:#000,stroke-width:2px
    style VID fill:#E6EE9C,stroke:#827717,color:#000
    style CSV fill:#E6EE9C,stroke:#827717,color:#000
    style CSV_REF fill:#E6EE9C,stroke:#827717,color:#000
    
    %% Preprocessing & ROI: Grigi/Bianchi luminosi
    style PREP fill:#ECEFF1,stroke:#455A64,color:#000
    style ROI fill:#ECEFF1,stroke:#455A64,color:#000

    %% Snake Path: Oro/Arancio Vibrante
    style SNAKE_PATH fill:#FFD54F,stroke:#FF6F00,color:#000,stroke-width:2px
    style GRAD fill:#FFE082,stroke:#FF8F00,color:#000
    style MORPH fill:#FFE082,stroke:#FF8F00,color:#000

    %% Watershed Path: Ciano/Azzurro Vibrante
    style WATER_PATH fill:#4DD0E1,stroke:#006064,color:#000,stroke-width:2px
    style ERO fill:#80DEEA,stroke:#00838F,color:#000
    style DIL fill:#80DEEA,stroke:#00838F,color:#000
    style MARK fill:#80DEEA,stroke:#00838F,color:#000
    style WS_ALGO fill:#80DEEA,stroke:#00838F,color:#000

    %% Output: Magenta/Rosa (Si stacca bene dal resto)
    style OUTPUT fill:#F48FB1,stroke:#880E4F,color:#000,stroke-width:2px
    style REPORT fill:#F8BBD0,stroke:#AD1457,color:#000
    style SAVE fill:#F8BBD0,stroke:#AD1457,color:#000

    %% Analisi: Viola Chiaro
    style ANALISYS fill:#CE93D8,stroke:#4A148C,color:#000
```


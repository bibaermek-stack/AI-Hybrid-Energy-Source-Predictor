# GCAITMD'25 — Proceedings abstract (ready to submit)

**Seminar:** 1st International Hybrid Seminar on “Green Chemistry and Artificial Intelligence: Towards Molecular Design” (GCAITMD'25), University of M’sila, Algeria, 21–22 October 2025  

**Suggested topics:**  
- **Topic 03** — Nanomaterials and Nanostructures for Energy and Environmental Applications  
- **Topic 04** — Valorization of Natural and Renewable Resources and Materials  
- **Topic 05** — Applications of Artificial Intelligence in Molecular Design / intelligent systems for sustainability  

**Format:** matches *Seminar Proceedings Book* oral/poster abstracts (title · authors · affiliation · abstract · keywords).

---

## English version (Oral / Poster communication)

### ARTIFICIAL INTELLIGENCE-DRIVEN OPTIMIZATION OF HYBRID RENEWABLE ENERGY SYSTEMS: A SMART EDUCATIONAL PLATFORM FOR SUSTAINABLE SOLAR–WIND DEPLOYMENT

**Author Name(s)**¹\*  
¹ *Affiliation / Laboratory / University, City, Country*  
\*Corresponding author: e-mail@domain.com  

**Abstract:**  
The transition toward low-carbon energy systems requires intelligent tools that can forecast renewable generation, detect equipment faults early, and optimize storage–grid interaction under real operating conditions. This work presents **EcoPredict AI**, an integrated artificial-intelligence platform for hybrid solar–wind energy systems with a focus on educational deployment and regional contexts such as Turkistan, Kazakhstan. The platform combines (i) classical machine-learning models for solar and wind power forecasting, (ii) computer-vision models for photovoltaic panel fault detection, (iii) multi-hour linear programming for battery–grid dispatch (profit vs. CO₂ trade-offs), (iv) a retrieval-augmented bilingual (English/Kazakh) energy advisor, and (v) sustainability metrics including avoided CO₂, LCOE, ROI and payback.  

On plant generation and weather data, Random Forest and XGBoost solar forecast models achieve **R² ≈ 99.67–99.71%**, while a sequence LSTM baseline reaches **R² ≈ 91.37%**. For panel diagnostics, YOLOv11 attains **mAP@50 up to 97.2%** (best checkpoint) and **≈ 93.1%** on a held-out test set. Transfer-learning CNN probes (ResNet50 / VGG16) on clean/dirty panel imagery reach about **81% / 78%** validation accuracy; multi-class fault labels with limited samples remain more challenging and are complemented by YOLO. Hybrid dispatch is formulated with PuLP over 24–48 h horizons (solar, wind, BESS, grid import/export). The system is exposed through a FastAPI backend and a multipage Streamlit dashboard, enabling both research evaluation and student laboratories. Overall, EcoPredict AI illustrates how green energy operations and AI methods can be unified into a reproducible, sustainability-oriented educational and decision-support platform.

**Keywords:** Artificial intelligence; hybrid solar–wind systems; power forecasting; photovoltaic fault detection; energy optimization; sustainability metrics; educational platform.

---

## French version (Résumé — style proceedings)

### OPTIMISATION PILOTÉE PAR L’INTELLIGENCE ARTIFICIELLE DES SYSTÈMES ÉNERGÉTIQUES HYBRIDES RENOUVELABLES : UNE PLATEFORME ÉDUCATIVE INTELLIGENTE POUR LE DÉPLOIEMENT SOLAIRE–ÉOLIEN DURABLE

**Nom(s) de l’auteur (des auteurs)**¹\*  
¹ *Affiliation / Laboratoire / Université, Ville, Pays*  
\*Auteur correspondant : e-mail@domain.com  

**Résumé :**  
La transition énergétique exige des outils capables de prévoir la production renouvelable, de détecter précocement les défauts des équipements et d’optimiser le couplage stockage–réseau. Nous présentons **EcoPredict AI**, une plateforme d’intelligence artificielle dédiée aux systèmes hybrides solaire–éolien, conçue à la fois pour l’aide à la décision opérationnelle et pour l’enseignement (contexte régional type Turkistan, Kazakhstan). Elle intègre des modèles de prévision (Random Forest, XGBoost, LSTM), la détection de défauts de panneaux (YOLOv11, CNN ResNet50/VGG16), l’optimisation multipériode de la batterie et du réseau (programmation linéaire PuLP, objectifs profit / CO₂), un conseiller énergétique bilingue (anglais/kazakh) fondé sur la recherche documentaire vectorielle, ainsi que des indicateurs de durabilité (CO₂ évité, LCOE, ROI, temps de retour).  

Les modèles de prévision solaire atteignent un **R² d’environ 99,7%** (RF/XGB) et **≈ 91,4%** (LSTM). La détection YOLO atteint jusqu’à **97,2%** de mAP@50. Les classifieurs CNN clean/dirty approchent **≈ 81%** (ResNet50) et **≈ 78%** (VGG16) en validation. L’architecture logicielle (FastAPI + Streamlit) rend l’ensemble reproductible pour la recherche et les travaux pratiques. EcoPredict AI montre ainsi la convergence entre chimie/énergie verte, intelligence artificielle et développement durable au sens des objectifs de GCAITMD’25.

**Mots-clés :** Intelligence artificielle ; systèmes hybrides solaire–éolien ; prévision de puissance ; détection de défauts photovoltaïques ; optimisation énergétique ; indicateurs de durabilité ; plateforme éducative.

---

## Suggested TOC line (for proceedings book)

| Type | Code (example) | Title (short) | Topic |
|------|----------------|---------------|-------|
| Oral / Poster | T3 / T5 | AI-Driven Optimization of Hybrid Renewable Energy Systems: EcoPredict AI Educational Platform | T3 Energy & Environment · T5 AI applications |

---

## Results table (for extended abstract / slides)

**Locked canonical copy:** [`docs/PAPER_METRICS_LOCKED.md`](PAPER_METRICS_LOCKED.md) (2026-07-20)

| Module | Model | Metric | Value |
|--------|--------|--------|------:|
| Solar forecast | Random Forest | R² | **99.67%** |
| Solar forecast | XGBoost | R² | **99.71%** |
| Solar forecast | LSTM | R² | **91.37%** |
| Fault detection | YOLOv11 (best checkpoint) | mAP@50 | **97.2%** |
| Fault detection | YOLOv11 (held-out test) | mAP@50 | **93.1%** |
| Fault detection | ResNet50 (clean/dirty probe) | Val accuracy | **≈ 80.9%** |
| Fault detection | VGG16 (clean/dirty probe) | Val accuracy | **≈ 78.4%** |
| Optimization | PuLP hybrid LP | Horizon | 24–48 h |
| Education | Streamlit labs | Count | **12** |

*Sources: `docs/METRICS.md`, `artifacts/model_metrics.json`, `artifacts/cnn_fault_metrics.json`.*

---

## Checklist before submission

- [ ] Insert real author names, ORCID, laboratory and university  
- [ ] Confirm oral vs poster and topic code (T3 / T4 / T5)  
- [ ] Replace e-mail and phone  
- [x] **Metrics locked** against `PAPER_METRICS_LOCKED.md` (no ad-hoc % in abstract)  
- [ ] Optional: add 1 figure (architecture) if poster template allows  
- [ ] Cite ELPV dataset if EL-cell experiments are included later  
- [ ] Align language (EN or FR) with session requirements  
- [ ] Mention educational labs (n=12) only if space allows  

---

*Prepared for GCAITMD'25 proceedings style · EcoPredict AI project · metrics locked 2026-07-20*

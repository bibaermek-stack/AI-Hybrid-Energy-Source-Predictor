const { Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle, Header, Footer, PageNumber } = require("docx");
const fs = require("fs");
const path = require("path");

const headerLine =
  "1st International Hybrid Seminar on \"Green Chemistry and Artificial Intelligence: Towards Molecular Design\" (GCAITMD'25 M'sila - Algeria)";

const children = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [
      new TextRun({
        text: headerLine,
        italics: true,
        size: 18,
        font: "Times New Roman",
        color: "333333",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 200 },
    children: [
      new TextRun({
        text: "ARTIFICIAL INTELLIGENCE-DRIVEN OPTIMIZATION OF HYBRID RENEWABLE ENERGY SYSTEMS: A SMART EDUCATIONAL PLATFORM FOR SUSTAINABLE SOLAR–WIND DEPLOYMENT",
        bold: true,
        size: 26,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60 },
    children: [
      new TextRun({
        text: "Author Name(s)¹*",
        bold: true,
        size: 22,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [
      new TextRun({
        text: "¹ Affiliation / Laboratory / University, City, Country",
        size: 20,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [
      new TextRun({
        text: "*Corresponding author: e-mail@domain.com",
        size: 20,
        font: "Times New Roman",
        italics: true,
      }),
    ],
  }),
  new Paragraph({
    spacing: { before: 120, after: 120 },
    children: [
      new TextRun({ text: "Abstract: ", bold: true, size: 22, font: "Times New Roman" }),
      new TextRun({
        text: "The transition toward low-carbon energy systems requires intelligent tools that can forecast renewable generation, detect equipment faults early, and optimize storage–grid interaction under real operating conditions. This work presents EcoPredict AI, an integrated artificial-intelligence platform for hybrid solar–wind energy systems with a focus on educational deployment and regional contexts such as Turkistan, Kazakhstan. The platform combines (i) classical machine-learning models for solar and wind power forecasting, (ii) computer-vision models for photovoltaic panel fault detection, (iii) multi-hour linear programming for battery–grid dispatch (profit vs. CO₂ trade-offs), (iv) a retrieval-augmented bilingual (English/Kazakh) energy advisor, and (v) sustainability metrics including avoided CO₂, LCOE, ROI and payback.",
        size: 22,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    spacing: { after: 120 },
    children: [
      new TextRun({
        text: "On plant generation and weather data, Random Forest and XGBoost solar forecast models achieve R² ≈ 99.67–99.71%, while a sequence LSTM baseline reaches R² ≈ 91.37%. For panel diagnostics, YOLOv11 attains mAP@50 up to 97.2% (best checkpoint) and ≈ 93.1% on a held-out test set. Transfer-learning CNN probes (ResNet50 / VGG16) on clean/dirty panel imagery reach about 81% / 78% validation accuracy; multi-class fault labels with limited samples remain more challenging and are complemented by YOLO. Hybrid dispatch is formulated with PuLP over 24–48 h horizons (solar, wind, BESS, grid import/export). The system is exposed through a FastAPI backend and a multipage Streamlit dashboard, enabling both research evaluation and student laboratories. Overall, EcoPredict AI illustrates how green energy operations and AI methods can be unified into a reproducible, sustainability-oriented educational and decision-support platform.",
        size: 22,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    spacing: { before: 160, after: 200 },
    children: [
      new TextRun({ text: "Keywords: ", bold: true, size: 22, font: "Times New Roman" }),
      new TextRun({
        text: "Artificial intelligence; hybrid solar–wind systems; power forecasting; photovoltaic fault detection; energy optimization; sustainability metrics; educational platform.",
        size: 22,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    spacing: { before: 300 },
    border: {
      top: { style: BorderStyle.SINGLE, size: 6, color: "2E75B6", space: 8 },
    },
    children: [
      new TextRun({
        text: "Suggested seminar topics: T3 (Energy & Environment) · T4 (Renewable resources) · T5 (AI applications). Format aligned with GCAITMD'25 Seminar Proceedings Book (M'sila, 21–22 Oct 2025).",
        size: 18,
        font: "Times New Roman",
        color: "555555",
        italics: true,
      }),
    ],
  }),
  new Paragraph({ spacing: { before: 400 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 200 },
    border: {
      top: { style: BorderStyle.SINGLE, size: 12, color: "999999", space: 12 },
    },
    children: [
      new TextRun({
        text: "VERSION FRANÇAISE (Résumé)",
        bold: true,
        size: 24,
        font: "Times New Roman",
        color: "1F4E79",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 200 },
    children: [
      new TextRun({
        text: "OPTIMISATION PILOTÉE PAR L’INTELLIGENCE ARTIFICIELLE DES SYSTÈMES ÉNERGÉTIQUES HYBRIDES RENOUVELABLES : UNE PLATEFORME ÉDUCATIVE INTELLIGENTE POUR LE DÉPLOIEMENT SOLAIRE–ÉOLIEN DURABLE",
        bold: true,
        size: 24,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [
      new TextRun({
        text: "Nom(s) de l’auteur (des auteurs)¹*",
        bold: true,
        size: 22,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [
      new TextRun({
        text: "¹ Affiliation / Laboratoire / Université, Ville, Pays",
        size: 20,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [
      new TextRun({
        text: "*Auteur correspondant : e-mail@domain.com",
        size: 20,
        font: "Times New Roman",
        italics: true,
      }),
    ],
  }),
  new Paragraph({
    spacing: { after: 120 },
    children: [
      new TextRun({ text: "Résumé : ", bold: true, size: 22, font: "Times New Roman" }),
      new TextRun({
        text: "La transition énergétique exige des outils capables de prévoir la production renouvelable, de détecter précocement les défauts des équipements et d’optimiser le couplage stockage–réseau. Nous présentons EcoPredict AI, une plateforme d’intelligence artificielle dédiée aux systèmes hybrides solaire–éolien, conçue pour l’aide à la décision et l’enseignement (contexte régional type Turkistan, Kazakhstan). Elle intègre des modèles de prévision (Random Forest, XGBoost, LSTM), la détection de défauts de panneaux (YOLOv11, CNN ResNet50/VGG16), l’optimisation multipériode de la batterie et du réseau (programmation linéaire PuLP), un conseiller énergétique bilingue (anglais/kazakh), ainsi que des indicateurs de durabilité (CO₂ évité, LCOE, ROI, temps de retour).",
        size: 22,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    spacing: { after: 120 },
    children: [
      new TextRun({
        text: "Les modèles de prévision solaire atteignent un R² d’environ 99,7% (RF/XGB) et ≈ 91,4% (LSTM). La détection YOLO atteint jusqu’à 97,2% de mAP@50. Les classifieurs CNN clean/dirty approchent ≈ 81% (ResNet50) et ≈ 78% (VGG16) en validation. L’architecture logicielle (FastAPI + Streamlit) rend l’ensemble reproductible pour la recherche et les travaux pratiques. EcoPredict AI montre ainsi la convergence entre énergie verte, intelligence artificielle et développement durable au sens des objectifs de GCAITMD’25.",
        size: 22,
        font: "Times New Roman",
      }),
    ],
  }),
  new Paragraph({
    spacing: { before: 160 },
    children: [
      new TextRun({ text: "Mots-clés : ", bold: true, size: 22, font: "Times New Roman" }),
      new TextRun({
        text: "Intelligence artificielle ; systèmes hybrides solaire–éolien ; prévision de puissance ; détection de défauts photovoltaïques ; optimisation énergétique ; indicateurs de durabilité ; plateforme éducative.",
        size: 22,
        font: "Times New Roman",
      }),
    ],
  }),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Times New Roman", size: 22 } } },
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({
                  text: "GCAITMD'25 · Seminar Proceedings · EcoPredict AI abstract",
                  size: 16,
                  font: "Times New Roman",
                  color: "666666",
                }),
              ],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({
                  text: "GCAITMD'25 M'sila — Algeria  ·  Page ",
                  size: 16,
                  font: "Times New Roman",
                  color: "666666",
                }),
                new TextRun({
                  children: [PageNumber.CURRENT],
                  size: 16,
                  font: "Times New Roman",
                  color: "666666",
                }),
              ],
            }),
          ],
        }),
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "GCAITMD25_EcoPredict_Abstract.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out, buf.length);
});

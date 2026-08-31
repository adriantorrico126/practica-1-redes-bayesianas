# Práctica 1 — Redes Bayesianas

**Estudiante:** Adrian Torrico  
**Materia:** Minería de Datos

Este repositorio resuelve la práctica de predicción de abandono de clientes mediante dos Redes Bayesianas discretas: una estructura propuesta y otra aprendida automáticamente con Hill Climbing.

## Abrir en Google Colab

Cuando el repositorio esté publicado, abre el notebook desde este enlace:

`https://colab.research.google.com/github/adriantorrico126/practica-1-redes-bayesianas/blob/main/Practica_1_Redes_Bayesianas_Adrian_Torrico.ipynb`

En Colab, ejecuta las celdas en orden. El notebook instala `pgmpy==0.1.25` automáticamente y lee el archivo `customers (2).csv` incluido en el repositorio.

## Contenido

- `Practica_1_Redes_Bayesianas_Adrian_Torrico.ipynb`: notebook ejecutable en Google Colab.
- `Informe_Practica_1_Redes_Bayesianas_Adrian_Torrico_Class_Notebook.docx`: informe para Class Notebook, sin resumen ejecutivo, conclusiones ni anexos.
- `Patron_y_justificacion_Adrian_Torrico.docx`: documento individual con el patrón de abandono, su evidencia y el enlace a Colab.
- `Documento_presentacion_patron_Adrian_Torrico.docx`: versión narrativa, en primera persona, para presentar el patrón y su aplicación.
- `customers (2).csv`: datos de entrada.
- `analisis_redes_bayesianas.py`: versión reproducible del análisis.
- `resultados/`: gráficos y resultados generados.
- `Práctica 1 red bayesiana 1.pdf`: enunciado original.

## Resultado destacado

Para un cliente con contrato mensual, sin soporte técnico, satisfacción baja y poca antigüedad, la red aprendida estima una probabilidad de abandono de **52.82%**.

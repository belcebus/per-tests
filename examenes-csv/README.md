# Generacion One-Shot de CSV por Provincia

Este directorio contiene un flujo one-shot para generar varios CSV a partir de los YAML de preguntas oficiales, agrupados por provincia.

## Restricciones del flujo

- No modifica ningun fichero existente del proyecto.
- Crea solo archivos nuevos dentro de `examenes-csv/`.
- No usa tests unitarios para este proceso.
- Cada ejecucion regenera el CSV completo desde cero.

## Archivos

- `generate_csv_from_yaml.py`: script one-shot de conversion.
- `preguntas_todas_convocatorias_madrid.csv`: salida para Madrid (generada por script).
- `preguntas_todas_convocatorias_murcia.csv`: salida para Murcia (generada por script).
- `ejemplo-preguntas.csv`: referencia de formato objetivo ya existente.

## Fuente de datos

Entrada leida por defecto:

- `data/exams/questions/**/*.yaml`

No se cruza con JSON de respuestas. La respuesta correcta se toma de `correct_answer` en cada YAML.

## Regla de preguntas anuladas

Si `correct_answer` es `ANULADA` o `anulada`:

- `not_influence_to_score=on`
- no se marca ninguna opcion como correcta en `answers`
- la pregunta se conserva en el CSV

## Uso

Desde la raiz del proyecto:

```bash
python3 examenes-csv/generate_csv_from_yaml.py
```

Opciones utiles:

```bash
python3 examenes-csv/generate_csv_from_yaml.py \
  --input-root data/exams/questions \
  --output examenes-csv/preguntas_todas_convocatorias.csv
```

El valor de `--output` se usa como base del nombre. Si pasas `preguntas_todas_convocatorias.csv`, el script generara:

- `preguntas_todas_convocatorias_madrid.csv`
- `preguntas_todas_convocatorias_murcia.csv`

Modo estricto (falla ante inconsistencias):

```bash
python3 examenes-csv/generate_csv_from_yaml.py --strict
```

## Validaciones incluidas en runtime

El script informa warnings y resumen:

- total de YAML procesados
- total de filas CSV generadas
- total de preguntas anuladas
- total de warnings de consistencia

Ademas valida internamente casos como:

- estructura esperada `categories -> questions`
- preguntas con menos de 2 opciones
- respuestas correctas no reconocidas

## Comprobacion manual recomendada

1. Revisar que existen los ficheros `examenes-csv/preguntas_todas_convocatorias_madrid.csv` y `examenes-csv/preguntas_todas_convocatorias_murcia.csv`.
2. Verificar cabecera y columnas esperadas en ambos.
3. Muestrear preguntas de varios YAML y comprobar categoria, enunciado y respuesta marcada.
4. Confirmar que preguntas anuladas salen con `not_influence_to_score=on`.

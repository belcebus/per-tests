# Test Fixtures

Esta carpeta contiene archivos de datos de test reutilizables para la suite de pruebas automatizadas.

## Archivos Disponibles

### `sample_exam.yaml`
Archivo de examen de muestra con la estructura estándar de preguntas organizadas por categorías. Incluye:
- 2 preguntas de ejemplo (Nomenclatura náutica y RIPA)
- Metadatos del examen (Madrid 2025)
- Estructura completa con exam_info y categories

### `sample_answers.json`
Archivo de respuestas correspondiente al examen de muestra. Contiene las respuestas correctas para las preguntas del `sample_exam.yaml`.

## Uso en Tests

Los fixtures en `tests/conftest.py` cargan automáticamente estos archivos para crear datos de test limpios y consistentes:

```python
def test_example(sample_yaml_exam):
    # sample_yaml_exam es una Path que apunta al archivo copiado en la carpeta temporal
    # Cada test obtiene una copia independiente de los datos
```

## Ventajas de este Enfoque

1. **Separación de datos**: Los datos de test están separados del código de test
2. **Reutilización**: Los mismos datos pueden usarse en múltiples tests
3. **Mantenibilidad**: Cambios en los datos de test se hacen en un solo lugar
4. **Legibilidad**: Los archivos YAML/JSON son más fáciles de leer que strings en Python
5. **Versionado**: Los datos de test se versionan junto con el código

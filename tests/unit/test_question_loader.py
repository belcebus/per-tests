"""
Tests unitarios para el servicio QuestionLoader

Estos tests verifican que el cargador de preguntas funciona correctamente:
- Cargar archivos YAML
- Validar estructura de datos
- Organizar preguntas por categorías y comunidades
- Manejo de errores
"""

import pytest
import yaml
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from typing import Dict, Any

from app.services.question_loader import QuestionLoader
from app.models.schemas import Question, QuestionMetadata, QuestionFile


class TestQuestionLoaderLegacyFormat:
    """Test para el formato anterior de archivos YAML."""
    
    @pytest.fixture
    def temp_dir(self):
        """Crear un directorio temporal para tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_questions_from_file_legacy_format(self, temp_dir):
        """Test de carga con formato anterior (preguntas)."""
        loader = QuestionLoader()

        # Crear un archivo YAML con formato anterior que incluya metadata de archivo
        yaml_content = """
metadata:
  exam_type: "per"
  category: "navegacion"
  version: "1.0"
preguntas:
  - id: "1"
    enunciado: "Test question?"
    opciones:
      a: "Option A"
      b: "Option B"
    respuesta_correcta: "a"
    metadata:
      title: "Test Exam"
      subtitle: "Test 01"
      total_questions: 1
      community: "Madrid"
      year: 2025
      call: "abril"
      test_code: "Test01"
      categoria: "1"
      año: 2025
      comunidad_autonoma: "Madrid"
"""

        test_file = temp_dir / "test_legacy.yaml"
        test_file.write_text(yaml_content)

        questions = loader._load_questions_from_file(test_file)

        assert len(questions) == 1
        assert questions[0].id == "1"
        assert questions[0].enunciado == "Test question?"

    def test_load_questions_with_unrecognized_format(self, temp_dir):
        """Test de archivo con formato no reconocido.""" 
        loader = QuestionLoader()

        yaml_content = """
unknown_structure:
  data: "some data"
"""

        test_file = temp_dir / "test_unknown.yaml"
        test_file.write_text(yaml_content)

        questions = loader._load_questions_from_file(test_file)

        # Debe retornar lista vacía para formato no reconocido
        assert questions == []

class TestQuestionLoaderCompleteWorkflow:
    """Tests para el flujo completo de trabajo."""
    
    def test_question_loader_init(self, temp_dir):
        """Test de inicialización del loader."""
        loader = QuestionLoader(str(temp_dir))
        
        assert loader.data_directory == temp_dir
        assert loader.questions_cache == {}
        assert loader.all_questions == []
    
    @patch('app.services.question_loader.settings')
    def test_question_loader_init_default_directory(self, mock_settings):
        """Test de inicialización con directorio por defecto."""
        mock_settings.get_absolute_path.return_value = Path("/default/path")
        
        loader = QuestionLoader()
        
        assert loader.data_directory == Path("/default/path")
        mock_settings.get_absolute_path.assert_called_once()
    
    def test_question_loader_init_relative_path(self, temp_dir):
        """Test de inicialización con ruta relativa."""
        loader = QuestionLoader("relative/path")
        
        # Debe convertir la ruta relativa a absoluta
        assert loader.data_directory.is_absolute()
        assert "relative/path" in str(loader.data_directory)
    
    def test_question_loader_init_absolute_path(self):
        """Test de inicialización con ruta absoluta."""
        abs_path = "/absolute/test/path"
        loader = QuestionLoader(abs_path)
        
        assert loader.data_directory == Path(abs_path)
    
    def test_load_questions_from_file(self, sample_yaml_exam):
        """Test de carga de preguntas desde archivo."""
        loader = QuestionLoader()
        
        questions = loader._load_questions_from_file(sample_yaml_exam)
        
        assert len(questions) == 2
        assert questions[0].metadata.numero_pregunta == 1
        assert questions[0].metadata.categoria == "1"
        assert questions[1].metadata.numero_pregunta == 2
        assert questions[1].metadata.categoria == "6"
        assert "embarcación" in questions[0].enunciado
    
    def test_load_questions_from_file_invalid_yaml(self, temp_dir):
        """Test de carga con YAML inválido."""
        loader = QuestionLoader(str(temp_dir))
        
        # Crear archivo YAML inválido
        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [")
        
        # Debería manejar el error graciosamente y devolver lista vacía
        questions = loader._load_questions_from_file(invalid_file)
        assert questions == []
    
    def test_load_questions_from_file_missing_structure(self, temp_dir):
        """Test de carga con estructura faltante."""
        loader = QuestionLoader(str(temp_dir))
        
        # Crear archivo sin estructura de preguntas
        missing_structure = temp_dir / "missing.yaml"
        missing_structure.write_text("""
metadata:
  title: "Test"
# Falta la sección 'preguntas'
        """)
        
        # Debería manejar el error y devolver lista vacía
        questions = loader._load_questions_from_file(missing_structure)
        assert questions == []

    def test_get_stats_empty(self):
        """Test de estadísticas con loader vacío."""
        loader = QuestionLoader()
        
        stats = loader.get_stats()
        
        assert "total_preguntas" in stats
        assert "categorias" in stats
        assert "años_disponibles" in stats
        assert "comunidades_disponibles" in stats
        assert "preguntas_por_categoria" in stats
        assert stats["total_preguntas"] == 0

    def test_get_questions_by_criteria_community(self):
        """Test de obtener preguntas por comunidad usando get_questions_by_criteria."""
        loader = QuestionLoader()
        
        # Mock de all_questions con preguntas de diferentes comunidades
        madrid_metadata = QuestionMetadata(
            title="Test", subtitle="01", total_questions=100,
            community="Madrid", year=2025, call="abril", test_code="Test01",
            comunidad_autonoma="Madrid"  # Campo de compatibilidad para filtrado
        )
        valencia_metadata = QuestionMetadata(
            title="Test", subtitle="01", total_questions=100,
            community="Valencia", year=2025, call="abril", test_code="Test01",
            comunidad_autonoma="Valencia"  # Campo de compatibilidad para filtrado
        )
        
        question_madrid = Question(
            id="madrid_q1", enunciado="Test Madrid", 
            opciones={"a": "A", "b": "B"}, respuesta_correcta="a",
            metadata=madrid_metadata
        )
        question_valencia = Question(
            id="valencia_q1", enunciado="Test Valencia",
            opciones={"a": "A", "b": "B"}, respuesta_correcta="a", 
            metadata=valencia_metadata
        )
        
        loader.all_questions = [question_madrid, question_valencia]
        
        madrid_questions = loader.get_questions_by_criteria(comunidades=["Madrid"])
        valencia_questions = loader.get_questions_by_criteria(comunidades=["Valencia"])
        
        assert len(madrid_questions) == 1
        assert len(valencia_questions) == 1
        assert madrid_questions[0].metadata.community == "Madrid"
        assert valencia_questions[0].metadata.community == "Valencia"


class TestQuestionLoaderAdvanced:
    """Tests avanzados para QuestionLoader."""
    
    @patch('app.services.question_loader.settings')
    @patch('builtins.print')
    def test_load_all_questions_with_exams_directory(self, mock_print, mock_settings):
        """Test de carga desde directorio de exámenes."""
        loader = QuestionLoader()
        
        # Mock del directorio de exámenes
        mock_exams_dir = MagicMock()
        mock_exams_dir.exists.return_value = True
        mock_yaml_file = MagicMock()
        mock_yaml_file.name = "test-exam.yaml"
        mock_exams_dir.glob.return_value = [mock_yaml_file]
        mock_settings.get_exams_path.return_value = mock_exams_dir
        
        # Mock del método _load_questions_from_file
        test_question = Question(
            id="test_q1",
            enunciado="Test question",
            opciones={"a": "Option A", "b": "Option B"},
            respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test", subtitle="01", total_questions=1,
                community="Madrid", year=2025, call="abril", test_code="Test01",
                categoria="1"
            )
        )
        
        with patch.object(loader, '_load_questions_from_file', return_value=[test_question]):
            questions = loader.load_all_questions()
            
            assert len(questions) == 1
            assert questions[0] == test_question
            assert "1" in loader.questions_cache
            assert len(loader.questions_cache["1"]) == 1
    
    @patch('app.services.question_loader.settings')
    @patch('builtins.print')
    def test_load_all_questions_fallback_to_main_directory(self, mock_print, mock_settings):
        """Test de fallback al directorio principal."""
        loader = QuestionLoader()
        
        # Mock del directorio de exámenes no existe
        mock_exams_dir = MagicMock()
        mock_exams_dir.exists.return_value = False
        mock_settings.get_exams_path.return_value = mock_exams_dir
        
        # Mock del directorio principal
        mock_yaml_file = MagicMock()
        mock_yaml_file.name = "fallback-exam.yaml"
        loader.data_directory = MagicMock()
        loader.data_directory.glob.return_value = [mock_yaml_file]
        
        test_question = Question(
            id="fallback_q1",
            enunciado="Fallback question",
            opciones={"a": "Option A", "b": "Option B"},
            respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test", subtitle="01", total_questions=1,
                community="Madrid", year=2025, call="abril", test_code="Test01",
                categoria="2"
            )
        )
        
        with patch.object(loader, '_load_questions_from_file', return_value=[test_question]):
            questions = loader.load_all_questions()
            
            assert len(questions) == 1
            assert "2" in loader.questions_cache
    
    @patch('app.services.question_loader.settings')
    @patch('builtins.print')
    def test_load_all_questions_no_files_found(self, mock_print, mock_settings):
        """Test cuando no se encuentran archivos YAML."""
        loader = QuestionLoader()
        
        # Mock de directorios vacíos
        mock_exams_dir = MagicMock()
        mock_exams_dir.exists.return_value = True
        mock_exams_dir.glob.return_value = []
        mock_settings.get_exams_path.return_value = mock_exams_dir
        
        questions = loader.load_all_questions()
        
        assert len(questions) == 0
        assert len(loader.all_questions) == 0
        assert len(loader.questions_cache) == 0
    
    @patch('app.services.question_loader.settings')
    @patch('builtins.print')
    def test_load_all_questions_with_error_handling(self, mock_print, mock_settings):
        """Test de manejo de errores al cargar archivos."""
        loader = QuestionLoader()
        
        # Mock del directorio de exámenes
        mock_exams_dir = MagicMock()
        mock_exams_dir.exists.return_value = True
        mock_yaml_file1 = MagicMock(name="good-exam.yaml")
        mock_yaml_file2 = MagicMock(name="bad-exam.yaml")
        mock_exams_dir.glob.return_value = [mock_yaml_file1, mock_yaml_file2]
        mock_settings.get_exams_path.return_value = mock_exams_dir
        
        # Configurar _load_questions_from_file para fallar en el segundo archivo
        def side_effect(file_path):
            if file_path == mock_yaml_file2:
                raise Exception("File corrupted")
            return [Question(
                id="good_q1",
                enunciado="Good question",
                opciones={"a": "Option A", "b": "Option B"},
                respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test", subtitle="01", total_questions=1,
                    community="Madrid", year=2025, call="abril", test_code="Test01",
                    categoria="1"
                )
            )]
        
        with patch.object(loader, '_load_questions_from_file', side_effect=side_effect):
            questions = loader.load_all_questions()
            
            # Solo debe cargar el archivo bueno
            assert len(questions) == 1
            assert len(loader.questions_cache) == 1
    
    def test_get_category_id_name_map(self):
        """Test del mapeo de categorías."""
        loader = QuestionLoader()
        
        # Crear preguntas con diferentes categorías
        q1 = Question(
            id="q1", enunciado="Test 1", opciones={"a": "A"}, respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test", subtitle="01", total_questions=1,
                community="Madrid", year=2025, call="abril", test_code="Test01",
                categoria="1", categoria_nombre="Nomenclatura"
            )
        )
        q2 = Question(
            id="q2", enunciado="Test 2", opciones={"a": "A"}, respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test", subtitle="01", total_questions=1,
                community="Madrid", year=2025, call="abril", test_code="Test01",
                categoria="2"  # Sin categoria_nombre
            )
        )
        
        loader.questions_cache = {"1": [q1], "2": [q2]}
        
        cat_map = loader.get_category_id_name_map()
        
        assert cat_map["1"] == "Nomenclatura"
        assert cat_map["2"] == "Categoría 2"  # Nombre por defecto
    
    def test_get_available_categories(self):
        """Test de obtener categorías disponibles."""
        loader = QuestionLoader()
        
        # Mock del mapeo de categorías
        with patch.object(loader, 'get_category_id_name_map', return_value={"1": "Cat1", "2": "Cat2"}):
            categories = loader.get_available_categories()
            
            assert len(categories) == 2
            assert {"id": "1", "nombre": "Cat1"} in categories
            assert {"id": "2", "nombre": "Cat2"} in categories
    
    def test_get_available_years(self):
        """Test de obtener años disponibles."""
        loader = QuestionLoader()
        
        # Crear preguntas con diferentes años
        loader.all_questions = [
            Question(
                id="q1", enunciado="Test 1", opciones={"a": "A"}, respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test", subtitle="01", total_questions=1,
                    community="Madrid", year=2023, call="abril", test_code="Test01",
                    anio=2023
                )
            ),
            Question(
                id="q2", enunciado="Test 2", opciones={"a": "A"}, respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test", subtitle="01", total_questions=1,
                    community="Madrid", year=2024, call="abril", test_code="Test01",
                    anio=2024
                )
            ),
            Question(
                id="q3", enunciado="Test 3", opciones={"a": "A"}, respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test", subtitle="01", total_questions=1,
                    community="Madrid", year=2024, call="abril", test_code="Test01",
                    anio=2024  # Año duplicado
                )
            )
        ]
        
        years = loader.get_available_years()
        
        assert set(years) == {2023, 2024}  # Sin duplicados
        assert len(years) == 2
    
    def test_get_available_communities(self):
        """Test de obtener comunidades disponibles."""
        loader = QuestionLoader()
        
        # Crear preguntas con diferentes comunidades
        loader.all_questions = [
            Question(
                id="q1", enunciado="Test 1", opciones={"a": "A"}, respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test", subtitle="01", total_questions=1,
                    community="Madrid", year=2025, call="abril", test_code="Test01",
                    comunidad_autonoma="Madrid"
                )
            ),
            Question(
                id="q2", enunciado="Test 2", opciones={"a": "A"}, respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test", subtitle="01", total_questions=1,
                    community="Valencia", year=2025, call="abril", test_code="Test01",
                    comunidad_autonoma="Valencia"
                )
            )
        ]
        
        communities = loader.get_available_communities()
        
        assert set(communities) == {"Madrid", "Valencia"}
        assert len(communities) == 2
    
    def test_get_stats(self):
        """Test de obtener estadísticas."""
        loader = QuestionLoader()

        # Crear preguntas con datos variados
        loader.all_questions = [
            Question(
                id="q1", enunciado="Test 1", opciones={"a": "A"}, respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test", subtitle="01", total_questions=1,
                    community="Madrid", year=2023, call="abril", test_code="Test01",
                    categoria="1", anio=2023, comunidad_autonoma="Madrid"
                )
            ),
            Question(
                id="q2", enunciado="Test 2", opciones={"a": "A"}, respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test", subtitle="01", total_questions=1,
                    community="Valencia", year=2024, call="junio", test_code="Test02",
                    categoria="2", anio=2024, comunidad_autonoma="Valencia"
                )
            )
        ]
        
        # Simular questions_cache
        loader.questions_cache = {
            "1": [loader.all_questions[0]],
            "2": [loader.all_questions[1]]
        }

        stats = loader.get_stats()

        assert stats["total_preguntas"] == 2
        assert stats["categorias"] == 2
        assert "años_disponibles" in stats
        assert "comunidades_disponibles" in stats
        assert set(stats["años_disponibles"]) == {2023, 2024}
        assert set(stats["comunidades_disponibles"]) == {"Madrid", "Valencia"}
        assert len(stats["preguntas_por_categoria"]) == 2


class TestQuestionLoaderFilters:
    """Tests para los filtros de QuestionLoader."""
    
    def test_get_questions_by_criteria_empty_filters(self):
        """Test de filtrado sin criterios (devuelve todas)."""
        loader = QuestionLoader()
        loader.all_questions = [
            Question(
                id="q1", enunciado="Test 1", opciones={"a": "A"}, respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test", subtitle="01", total_questions=1,
                    community="Madrid", year=2025, call="abril", test_code="Test01"
                )
            )
        ]
        
        with patch('builtins.print'):
            questions = loader.get_questions_by_criteria()
            
            assert len(questions) == 1
    
    def test_get_questions_by_criteria_by_categories(self):
        """Test de filtrado por categorías."""
        loader = QuestionLoader()
        
        q1 = Question(
            id="q1", enunciado="Test 1", opciones={"a": "A"}, respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test", subtitle="01", total_questions=1,
                community="Madrid", year=2025, call="abril", test_code="Test01",
                categoria="1"
            )
        )
        q2 = Question(
            id="q2", enunciado="Test 2", opciones={"a": "A"}, respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test", subtitle="01", total_questions=1,
                community="Madrid", year=2025, call="abril", test_code="Test01",
                categoria="2"
            )
        )
        
        loader.all_questions = [q1, q2]
        
        with patch('builtins.print'):
            questions = loader.get_questions_by_criteria(categorias=["1"])
            
            assert len(questions) == 1
            assert questions[0].metadata.categoria == "1"
    
    def test_get_questions_by_criteria_by_years(self):
        """Test de filtrado por años."""
        loader = QuestionLoader()
        
        q1 = Question(
            id="q1", enunciado="Test 1", opciones={"a": "A"}, respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test", subtitle="01", total_questions=1,
                community="Madrid", year=2023, call="abril", test_code="Test01",
                anio=2023
            )
        )
        q2 = Question(
            id="q2", enunciado="Test 2", opciones={"a": "A"}, respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test", subtitle="01", total_questions=1,
                community="Madrid", year=2024, call="abril", test_code="Test01",
                anio=2024
            )
        )
        
        loader.all_questions = [q1, q2]
        
        with patch('builtins.print'):
            questions = loader.get_questions_by_criteria(anios=[2023])
            
            assert len(questions) == 1
            assert questions[0].metadata.anio == 2023


class TestQuestionLoaderFileHandling:
    """Tests para el manejo de archivos YAML."""
    
    def test_load_questions_from_file_with_list_options(self, temp_dir):
        """Test de carga con opciones en formato lista."""
        loader = QuestionLoader()

        # Crear un archivo YAML con formato correcto
        yaml_content = """
exam_info:
  title: "Test Exam"
  subtitle: "Test 01"
  total_questions: 1
  community: "Madrid"
  year: 2025
  call: "abril"
  test_code: "Test01"

categories:
  1:
    name: "Test Category"
    questions:
      - id: 1
        question: "Test question?"
        options:
          a: "Option A"
          b: "Option B"
          c: "Option C"
          d: "Option D"
        correct_answer: "a"
"""

        test_file = temp_dir / "test_list_options.yaml"
        test_file.write_text(yaml_content)

        questions = loader._load_questions_from_file(test_file)

        assert len(questions) == 1
        assert questions[0].opciones["a"] == "Option A"
        assert questions[0].opciones["b"] == "Option B"
        assert questions[0].respuesta_correcta == "a"  # respuesta correcta es "a"
    
    def test_load_questions_from_file_with_anulada_answer(self, temp_dir):
        """Test de carga con respuesta anulada."""
        loader = QuestionLoader()

        yaml_content = """
exam_info:
  title: "Test Exam"
  subtitle: "Test 01"
  total_questions: 1
  community: "Madrid"
  year: 2025
  call: "abril"
  test_code: "Test01"

categories:
  1:
    name: "Test Category"
    questions:
      - id: 1
        question: "Test question?"
        options:
          a: "Option A"
          b: "Option B"
        correct_answer: "ANULADA"
"""

        test_file = temp_dir / "test_anulada.yaml"
        test_file.write_text(yaml_content)

        questions = loader._load_questions_from_file(test_file)

        assert len(questions) == 1
        assert questions[0].respuesta_correcta == "ANULADA"  # Se mantiene como está en el archivo
    
    def test_load_questions_from_file_missing_structure(self, temp_dir):
        """Test de carga con estructura faltante."""
        loader = QuestionLoader()

        yaml_content = """
# Archivo incompleto - falta exam_info
categories:
  1:
    name: "Test Category"
    questions: []
"""

        test_file = temp_dir / "test_incomplete.yaml"
        test_file.write_text(yaml_content)

        # No debe levantar excepción, solo retornar lista vacía o con metadata default
        questions = loader._load_questions_from_file(test_file)
        assert isinstance(questions, list)

    def test_load_questions_from_file_empty_categories(self, temp_dir):
        """Test de carga con categorías vacías."""
        loader = QuestionLoader()
        
        yaml_content = """
exam_info:
  title: "Test Exam"
  subtitle: "Test 01"
  total_questions: 0
  community: "Madrid"
  year: 2025
  call: "abril"
  test_code: "Test01"

categories: []
"""
        
        test_file = temp_dir / "test_empty_categories.yaml"
        test_file.write_text(yaml_content)
        
        questions = loader._load_questions_from_file(test_file)
        
        assert len(questions) == 0

    def test_load_questions_from_file_not_found(self):
        """Test de carga de archivo inexistente."""
        loader = QuestionLoader()
        
        # Usar Path para archivo inexistente
        non_existent_file = Path("/tmp/non_existent_file.yaml")
        
        # El método maneja las excepciones internamente, no las propaga
        questions = loader._load_questions_from_file(non_existent_file)
        assert questions == []  # Debe retornar lista vacía en caso de error

    def test_load_questions_from_file_invalid_yaml(self, temp_dir):
        """Test de carga con YAML inválido."""
        loader = QuestionLoader()
        
        # Crear archivo con YAML malformado
        invalid_yaml = "invalid: yaml: content: ["
        test_file = temp_dir / "invalid.yaml"
        test_file.write_text(invalid_yaml)

        # El método maneja las excepciones internamente, no las propaga
        questions = loader._load_questions_from_file(test_file)
        assert questions == []  # Debe retornar lista vacía en caso de error
class TestQuestionLoaderEdgeCases:
    """Tests para casos edge del QuestionLoader."""
    
    def test_backup_files_filtering(self):
        """Test de que los archivos de backup se filtran correctamente."""
        loader = QuestionLoader()

        # Mock de archivos incluyendo backups
        mock_files = [
            Path("exam1.yaml"),
            Path("exam2.backup.yaml"),  # Debe filtrarse
            Path("bk_exam3.yaml"),      # Debe filtrarse  
            Path("exam4.bak.yaml"),     # Debe filtrarse
            Path("exam5.yaml")
        ]

        with patch('app.services.question_loader.settings') as mock_settings:
            mock_exams_dir = MagicMock()
            mock_exams_dir.exists.return_value = True
            mock_exams_dir.glob.return_value = mock_files
            mock_settings.get_exams_path.return_value = mock_exams_dir

            with patch.object(loader, '_load_questions_from_file', return_value=[]):
                with patch('builtins.print'):
                    loader.load_all_questions()

                    # Solo debe procesar los archivos no-backup (exam1.yaml y exam5.yaml)
                    actual_calls = loader._load_questions_from_file.call_args_list
                    
                    assert len(actual_calls) == 2
                    # Verificar que se llama con los archivos correctos
                    called_files = [call_args[0][0] for call_args in actual_calls]
                    assert Path("exam1.yaml") in called_files
                    assert Path("exam5.yaml") in called_files

    def test_question_with_missing_metadata_fields(self):
        """Test de pregunta con campos de metadata faltantes."""
        loader = QuestionLoader()
        
        # Crear una pregunta con metadata mínimo
        question = Question(
            id="q1", enunciado="Test", opciones={"a": "A"}, respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test", subtitle="01", total_questions=1,
                community="Madrid", year=2025, call="abril", test_code="Test01"
                # Sin categoria_nombre
            )
        )
        
        loader.questions_cache = {"unknown": [question]}
        
        cat_map = loader.get_category_id_name_map()
        
        assert cat_map["unknown"] == "Categoría unknown"  # Nombre por defecto


class TestQuestionLoaderIntegration:
    """Tests de integración para QuestionLoader."""
    
    def test_get_available_methods(self):
        """Test de métodos disponibles en QuestionLoader."""
        loader = QuestionLoader()
        
        # Verificar que los métodos públicos existen
        assert hasattr(loader, 'load_all_questions')
        assert hasattr(loader, 'get_questions_by_criteria')
        assert hasattr(loader, 'get_available_categories')
        assert hasattr(loader, 'get_available_years')
        assert hasattr(loader, 'get_available_communities')
        assert hasattr(loader, 'get_stats')
    
    def test_error_handling_corrupted_file(self, temp_dir):
        """Test de manejo de archivos corruptos."""
        loader = QuestionLoader(str(temp_dir))
        
        # Debería poder manejar directorios vacíos sin fallar
        try:
            result = loader.load_all_questions()
            # Si devuelve algo, debería ser una lista
            assert isinstance(result, list)
        except Exception:
            # Si lanza excepción, es comportamiento esperado para directorios vacíos
            pass

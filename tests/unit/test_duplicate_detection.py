"""
Tests específicos para la funcionalidad de detección de duplicados
"""

import pytest
from unittest.mock import Mock, patch

from app.services.exam_service import ExamService
from app.models.schemas import Question, QuestionMetadata, ExamGenerationRequest


class TestDuplicateDetection:
    """Tests para la funcionalidad de detección de preguntas duplicadas."""
    
    def test_get_question_content_hash_identical_questions(self):
        """Test que preguntas idénticas generan el mismo hash."""
        service = ExamService()
        
        # Crear metadatos diferentes para simular preguntas de diferentes exámenes
        metadata1 = QuestionMetadata(
            title='Examen 1', subtitle='Test01', total_questions=10,
            community='Madrid', year=2023, call='Ordinaria', test_code='Test01'
        )
        metadata2 = QuestionMetadata(
            title='Examen 2', subtitle='Test02', total_questions=15,
            community='Barcelona', year=2024, call='Extraordinaria', test_code='Test02'
        )
        
        # Preguntas idénticas en contenido pero diferentes metadatos
        q1 = Question(
            id='exam1_q1',
            enunciado='¿Cuál es la capital de España?',
            opciones={'a': 'Madrid', 'b': 'Barcelona', 'c': 'Sevilla', 'd': 'Valencia'},
            respuesta_correcta='a',
            metadata=metadata1
        )
        
        q2 = Question(
            id='exam2_q5',
            enunciado='¿Cuál es la capital de España?',
            opciones={'a': 'Madrid', 'b': 'Barcelona', 'c': 'Sevilla', 'd': 'Valencia'},
            respuesta_correcta='a',
            metadata=metadata2
        )
        
        hash1 = service._get_question_content_hash(q1)
        hash2 = service._get_question_content_hash(q2)
        
        assert hash1 == hash2, "Preguntas con contenido idéntico deben tener el mismo hash"
    
    def test_get_question_content_hash_different_order_options(self):
        """Test que preguntas con opciones en orden diferente generan el mismo hash."""
        service = ExamService()
        
        metadata = QuestionMetadata(
            title='Test', subtitle='Test01', total_questions=10,
            community='Madrid', year=2023, call='Ordinaria', test_code='Test01'
        )
        
        q1 = Question(
            id='q1',
            enunciado='¿Cuál es la capital de España?',
            opciones={'a': 'Madrid', 'b': 'Barcelona', 'c': 'Sevilla', 'd': 'Valencia'},
            respuesta_correcta='a',
            metadata=metadata
        )
        
        # Misma pregunta con opciones en orden diferente
        q2 = Question(
            id='q2',
            enunciado='¿Cuál es la capital de España?',
            opciones={'d': 'Valencia', 'a': 'Madrid', 'c': 'Sevilla', 'b': 'Barcelona'},
            respuesta_correcta='a',
            metadata=metadata
        )
        
        hash1 = service._get_question_content_hash(q1)
        hash2 = service._get_question_content_hash(q2)
        
        assert hash1 == hash2, "Preguntas con opciones en orden diferente deben tener el mismo hash"
    
    def test_get_question_content_hash_different_questions(self):
        """Test que preguntas diferentes generan hashes diferentes."""
        service = ExamService()
        
        metadata = QuestionMetadata(
            title='Test', subtitle='Test01', total_questions=10,
            community='Madrid', year=2023, call='Ordinaria', test_code='Test01'
        )
        
        q1 = Question(
            id='q1',
            enunciado='¿Cuál es la capital de España?',
            opciones={'a': 'Madrid', 'b': 'Barcelona', 'c': 'Sevilla', 'd': 'Valencia'},
            respuesta_correcta='a',
            metadata=metadata
        )
        
        q2 = Question(
            id='q2',
            enunciado='¿Cuál es la capital de Francia?',
            opciones={'a': 'París', 'b': 'Lyon', 'c': 'Marsella', 'd': 'Niza'},
            respuesta_correcta='a',
            metadata=metadata
        )
        
        hash1 = service._get_question_content_hash(q1)
        hash2 = service._get_question_content_hash(q2)
        
        assert hash1 != hash2, "Preguntas diferentes deben tener hashes diferentes"
    
    def test_get_question_content_hash_whitespace_normalization(self):
        """Test que los espacios extra se normalizan correctamente."""
        service = ExamService()
        
        metadata = QuestionMetadata(
            title='Test', subtitle='Test01', total_questions=10,
            community='Madrid', year=2023, call='Ordinaria', test_code='Test01'
        )
        
        q1 = Question(
            id='q1',
            enunciado='¿Cuál es la capital de España?',
            opciones={'a': 'Madrid', 'b': 'Barcelona'},
            respuesta_correcta='a',
            metadata=metadata
        )
        
        # Misma pregunta con espacios extra
        q2 = Question(
            id='q2',
            enunciado=' ¿Cuál  es   la capital  de España? ',
            opciones={'a': '  Madrid  ', 'b': ' Barcelona  '},
            respuesta_correcta='a',
            metadata=metadata
        )
        
        hash1 = service._get_question_content_hash(q1)
        hash2 = service._get_question_content_hash(q2)
        
        assert hash1 == hash2, "Espacios extra deben ser normalizados para generar el mismo hash"
    
    def test_select_unique_questions_success(self):
        """Test de selección exitosa de preguntas únicas."""
        service = ExamService()
        
        metadata = QuestionMetadata(
            title='Test', subtitle='Test01', total_questions=10,
            community='Madrid', year=2023, call='Ordinaria', test_code='Test01'
        )
        
        # Crear preguntas con contenido diferente
        questions = []
        for i in range(5):
            q = Question(
                id=f'q{i}',
                enunciado=f'¿Pregunta número {i}?',
                opciones={'a': f'Respuesta {i}A', 'b': f'Respuesta {i}B'},
                respuesta_correcta='a',
                metadata=metadata
            )
            questions.append(q)
        
        selected = service._select_unique_questions(questions, 3)
        
        assert len(selected) == 3, "Debe seleccionar exactamente 3 preguntas"
        
        # Verificar que no hay duplicados
        selected_hashes = set()
        for q in selected:
            hash_val = service._get_question_content_hash(q)
            assert hash_val not in selected_hashes, "No debe haber preguntas duplicadas"
            selected_hashes.add(hash_val)
    
    def test_select_unique_questions_with_duplicates(self):
        """Test de selección cuando hay preguntas duplicadas."""
        service = ExamService()
        
        metadata = QuestionMetadata(
            title='Test', subtitle='Test01', total_questions=10,
            community='Madrid', year=2023, call='Ordinaria', test_code='Test01'
        )
        
        # Crear preguntas donde algunas son duplicadas
        questions = [
            Question(
                id='q1', enunciado='¿Pregunta A?',
                opciones={'a': 'RespA1', 'b': 'RespA2'},
                respuesta_correcta='a', metadata=metadata
            ),
            Question(
                id='q2', enunciado='¿Pregunta A?',  # Duplicada
                opciones={'a': 'RespA1', 'b': 'RespA2'},
                respuesta_correcta='a', metadata=metadata
            ),
            Question(
                id='q3', enunciado='¿Pregunta B?',
                opciones={'a': 'RespB1', 'b': 'RespB2'},
                respuesta_correcta='a', metadata=metadata
            ),
            Question(
                id='q4', enunciado='¿Pregunta A?',  # Otra duplicada
                opciones={'b': 'RespA2', 'a': 'RespA1'},  # Orden diferente
                respuesta_correcta='a', metadata=metadata
            ),
        ]
        
        selected = service._select_unique_questions(questions, 2)
        
        assert len(selected) == 2, "Debe seleccionar exactamente 2 preguntas únicas"
        
        # Verificar que no hay duplicados
        selected_hashes = set()
        for q in selected:
            hash_val = service._get_question_content_hash(q)
            assert hash_val not in selected_hashes, "No debe haber preguntas duplicadas"
            selected_hashes.add(hash_val)
    
    def test_select_unique_questions_insufficient_unique(self):
        """Test de error cuando no hay suficientes preguntas únicas."""
        service = ExamService()
        
        metadata = QuestionMetadata(
            title='Test', subtitle='Test01', total_questions=10,
            community='Madrid', year=2023, call='Ordinaria', test_code='Test01'
        )
        
        # Crear preguntas donde todas son prácticamente iguales
        questions = []
        for i in range(5):
            q = Question(
                id=f'q{i}',
                enunciado='¿Pregunta duplicada?',  # Mismo contenido
                opciones={'a': 'Respuesta A', 'b': 'Respuesta B'},
                respuesta_correcta='a',
                metadata=metadata
            )
            questions.append(q)
        
        with pytest.raises(ValueError, match="No hay suficientes preguntas únicas"):
            service._select_unique_questions(questions, 3)  # Pide 3, pero solo hay 1 única
    
    def test_select_unique_questions_empty_list(self):
        """Test de error cuando la lista de preguntas está vacía."""
        service = ExamService()
        
        with pytest.raises(ValueError, match="No hay preguntas disponibles para seleccionar"):
            service._select_unique_questions([], 1)
    
    def test_select_unique_questions_with_many_duplicates(self):
        """Test de selección con muchos duplicados para mejorar cobertura."""
        service = ExamService()
        
        metadata = QuestionMetadata(
            title='Test', subtitle='Test01', total_questions=10,
            community='Madrid', year=2023, call='Ordinaria', test_code='Test01'
        )
        
        # Crear preguntas donde todas menos 3 son duplicadas
        questions = []
        
        # Agregar 15 preguntas idénticas (duplicadas)
        for i in range(15):
            q = Question(
                id=f'dup_{i}',
                enunciado='¿Pregunta duplicada?',
                opciones={'a': 'RespA', 'b': 'RespB'},
                respuesta_correcta='a',
                metadata=metadata
            )
            questions.append(q)
        
        # Agregar 3 preguntas únicas
        for i in range(3):
            q = Question(
                id=f'unique_{i}',
                enunciado=f'¿Pregunta única {i}?',
                opciones={'a': f'Resp{i}A', 'b': f'Resp{i}B'},
                respuesta_correcta='a',
                metadata=metadata
            )
            questions.append(q)
        
        # Solicitar 3 preguntas - debe poder seleccionar exactamente las 3 únicas
        selected = service._select_unique_questions(questions, 3)
        
        assert len(selected) == 3, "Debe seleccionar exactamente 3 preguntas únicas"
        
        # Verificar que no hay duplicados en la selección
        selected_hashes = set()
        for q in selected:
            hash_val = service._get_question_content_hash(q)
            assert hash_val not in selected_hashes, "No debe haber preguntas duplicadas en la selección"
            selected_hashes.add(hash_val)
    
    def test_select_unique_questions_trace_coverage(self):
        """Test para cubrir las líneas de trazas de duplicados."""
        service = ExamService()
        
        # Test con metadatos que tengan diferentes comunidades y años
        # para cubrir las líneas de agrupación estadística
        communities = ['Madrid', 'Barcelona', 'Murcia', 'Valencia', 'Sevilla']
        years = [2020, 2021, 2022, 2023, 2024]
        
        questions = []
        
        # Crear preguntas duplicadas de diferentes fuentes (15 duplicados)
        for i in range(15):  
            community = communities[i % len(communities)]
            year = years[i % len(years)]
            
            metadata = QuestionMetadata(
                title=f'Test {community}', subtitle='Test01', total_questions=10,
                community=community, year=year, call='Ordinaria', test_code='Test01',
                categoria='1'
            )
            
            q = Question(
                id=f'dup_{i}',
                enunciado='¿Pregunta duplicada multifuente?',
                opciones={'a': 'RespA', 'b': 'RespB'},
                respuesta_correcta='a',
                metadata=metadata
            )
            questions.append(q)
        
        # Añadir 2 preguntas únicas para poder hacer selección
        for i in range(2):
            unique_metadata = QuestionMetadata(
                title='Test Único', subtitle='Test01', total_questions=10,
                community='Madrid', year=2023, call='Ordinaria', test_code='Test01',
                categoria='1'
            )
            
            unique_q = Question(
                id=f'unique_{i}',
                enunciado=f'¿Pregunta única {i}?',
                opciones={'a': f'RespUnique{i}A', 'b': f'RespUnique{i}B'},
                respuesta_correcta='a',
                metadata=unique_metadata
            )
            questions.append(unique_q)
        
        # Solicitar 2 preguntas - esto debería generar trazas de muchos duplicados
        selected = service._select_unique_questions(questions, 2)
        
        assert len(selected) == 2, "Debe seleccionar exactamente 2 preguntas únicas"
        
        # Verificar que no hay duplicados en la selección
        selected_hashes = set()
        for q in selected:
            hash_val = service._get_question_content_hash(q)
            assert hash_val not in selected_hashes, "No debe haber preguntas duplicadas en la selección"
            selected_hashes.add(hash_val)
    
    def test_generate_exam_with_duplicate_prevention(self):
        """Test de integración: generación de examen con prevención de duplicados."""
        service = ExamService()
        
        # Mock del question_loader usando patch.object
        with patch.object(service, 'question_loader') as mock_loader:
            metadata = QuestionMetadata(
                title='Test', subtitle='Test01', total_questions=10,
                community='Madrid', year=2023, call='Ordinaria', test_code='Test01'
            )
            
            # Simular preguntas con algunas duplicadas
            mock_questions = [
                Question(
                    id=f'q{i}',
                    enunciado=f'¿Pregunta única {i}?' if i < 3 else '¿Pregunta duplicada?',
                    opciones={'a': f'Resp{i}A', 'b': f'Resp{i}B'} if i < 3 else {'a': 'RespA', 'b': 'RespB'},
                    respuesta_correcta='a',
                    metadata=metadata
                ) for i in range(6)  # 3 únicas + 3 duplicadas
            ]
            
            mock_loader.get_questions_by_criteria.return_value = mock_questions
            
            request = ExamGenerationRequest(num_preguntas=3)
            result = service.generate_exam(request)
            
            assert len(result.questions) == 3, "Debe generar exactamente 3 preguntas"
            assert result.exam_id.startswith('exam_'), "Debe tener ID de examen válido"
            
            # Verificar que no hay duplicados en el examen generado
            generated_hashes = set()
            for client_q in result.questions:
                # Reconstruir la pregunta completa para calcular hash
                # (las preguntas del cliente no tienen respuesta_correcta)
                full_q = Question(
                    id=client_q.id,
                    enunciado=client_q.enunciado,
                    opciones=client_q.opciones,
                    respuesta_correcta='a',  # Dummy value para el hash
                    metadata=client_q.metadata
                )
                hash_val = service._get_question_content_hash(full_q)
                assert hash_val not in generated_hashes, "El examen no debe contener preguntas duplicadas"
                generated_hashes.add(hash_val)
    
    def test_exam_service_coverage_additional_cases(self):
        """Test adicional para mejorar cobertura de casos específicos."""
        service = ExamService()
        
        # Test para cubrir líneas en generate_simulacro_exam
        # Mock del question_loader usando patch.object
        with patch.object(service, 'question_loader') as mock_loader:
            metadata = QuestionMetadata(
                title='Test', subtitle='Test01', total_questions=10,
                community='Madrid', year=2023, call='Ordinaria', test_code='Test01',
                categoria='invalid'  # Categoría inválida para cubrir manejo de errores
            )
            
            # Simular preguntas con categorías inválidas
            mock_questions = [
                Question(
                    id=f'q{i}',
                    enunciado=f'¿Pregunta {i}?',
                    opciones={'a': f'Resp{i}A', 'b': f'Resp{i}B', 'c': f'Resp{i}C', 'd': f'Resp{i}D'},
                    respuesta_correcta='a',
                    metadata=metadata
                ) for i in range(5)
            ]
            
            mock_loader.get_questions_by_criteria.return_value = mock_questions
            
            # Usar ExamGenerationRequest ya que está disponible
            request = ExamGenerationRequest(num_preguntas=3)
            
            # Este debería funcionar sin problemas con preguntas válidas
            result = service.generate_exam(request)
            
            assert len(result.questions) == 3, "Debe generar exactamente 3 preguntas"
            assert result.exam_id.startswith('exam_'), "Debe tener ID de examen válido"
    
    def test_duplicate_traces_with_many_duplicates(self):
        """Test específico para activar las trazas de resumen estadístico (líneas 170-183)."""
        service = ExamService()
        
        # Crear EXACTAMENTE 11 preguntas idénticas para garantizar >10 duplicados
        questions = []
        
        # Todas las preguntas serán idénticas excepto por los IDs y metadatos
        base_enunciado = '¿Pregunta duplicada exacta?'
        base_opciones = {'a': 'RespA', 'b': 'RespB'}
        
        communities = ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Murcia']
        years = [2020, 2021, 2022, 2023, 2024]
        
        # Crear 11 preguntas idénticas
        for i in range(11):
            metadata = QuestionMetadata(
                title=f'Test {i}', subtitle='Test01', total_questions=10,
                community=communities[i % len(communities)],
                year=years[i % len(years)],
                call='Ordinaria', test_code='Test01',
                categoria='1'
            )
            
            q = Question(
                id=f'dup_{i}',
                enunciado=base_enunciado,
                opciones=base_opciones,
                respuesta_correcta='a',
                metadata=metadata
            )
            questions.append(q)
        
        # Agregar UNA pregunta completamente diferente
        unique_metadata = QuestionMetadata(
            title='Test Único', subtitle='Test01', total_questions=10,
            community='Madrid', year=2023, call='Ordinaria', test_code='Test01',
            categoria='1'
        )
        
        unique_q = Question(
            id='unique',
            enunciado='¿Esta es una pregunta completamente diferente?',
            opciones={'a': 'RespUniqueA', 'b': 'RespUniqueB'},
            respuesta_correcta='a',
            metadata=unique_metadata
        )
        questions.append(unique_q)
        
        # Verificar que todas las duplicadas tienen el mismo hash
        hashes = []
        for q in questions[:-1]:  # Todas excepto la última
            hash_val = service._get_question_content_hash(q)
            hashes.append(hash_val)
        
        unique_hash = service._get_question_content_hash(questions[-1])
        
        # Verificar que las duplicadas tienen el mismo hash y la única es diferente
        assert all(h == hashes[0] for h in hashes), "Todas las preguntas duplicadas deben tener el mismo hash"
        assert unique_hash != hashes[0], "La pregunta única debe tener hash diferente"
        
        # Ahora hacer la selección - deberíamos ver exactamente 10 duplicados descartados
        # (11 duplicadas - 1 seleccionada = 10 descartadas)
        selected = service._select_unique_questions(questions, 2)
        
        # Debe seleccionar exactamente 2: 1 de las duplicadas + 1 única
        assert len(selected) == 2, f"Debe seleccionar exactamente 2 preguntas, pero seleccionó {len(selected)}"
        
        # Verificar que las 2 seleccionadas tienen hashes diferentes
        selected_hashes = [service._get_question_content_hash(q) for q in selected]
        assert len(set(selected_hashes)) == 2, "Las 2 preguntas seleccionadas deben ser únicas"
    
    def test_empty_questions_coverage(self):
        """Test para cubrir la línea 109 - caso de lista vacía."""
        service = ExamService()
        
        # Test del caso donde available_questions está vacío (línea 109)
        with pytest.raises(ValueError, match="No hay preguntas disponibles para seleccionar"):
            service._select_unique_questions([], 1)

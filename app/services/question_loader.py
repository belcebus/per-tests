"""
Servicio para cargar preguntas desde archivos YAML

Este módulo se encarga de:
1. Leer archivos YAML de la carpeta 'data'
2. Validar que tienen la estructura correcta
3. Convertirlos a objetos Python que podemos usar
4. Mantener todas las preguntas cargadas en memoria para acceso rápido
"""

import os
import yaml
from typing import List, Dict
from pathlib import Path

from app.models.schemas import Question, QuestionFile, QuestionMetadata


class QuestionLoader:
    """
    Clase que maneja la carga de preguntas desde archivos YAML.
    
    Es como un "bibliotecario" que:
    - Sabe dónde están los archivos
    - Los lee cuando se lo pedimos
    - Los organiza para que sea fácil buscar preguntas
    """
    
    def __init__(self, data_directory: str = "data"):
        """
        Inicializa el cargador de preguntas.
        
        Args:
            data_directory: Carpeta donde están los archivos YAML
        """
        self.data_directory = Path(data_directory)
        self.questions_cache: Dict[str, List[Question]] = {}
        self.all_questions: List[Question] = []
        
    def load_all_questions(self) -> None:
        """
        Carga TODAS las preguntas de TODOS los archivos YAML.
        
        Este método:
        1. Busca todos los archivos .yaml en la carpeta data
        2. Los lee uno por uno
        3. Guarda todas las preguntas en memoria
        4. Las organiza por categorías para búsquedas rápidas
        """
        print("🔄 Cargando preguntas desde archivos YAML...")
        
        # Limpiar caché anterior
        self.questions_cache.clear()
        self.all_questions.clear()
        
        # Buscar todos los archivos .yaml
        yaml_files = list(self.data_directory.glob("**/*.yaml"))
        
        if not yaml_files:
            print(f"⚠️  No se encontraron archivos YAML en {self.data_directory}")
            return
            
        for yaml_file in yaml_files:
            try:
                questions = self._load_questions_from_file(yaml_file)
                self.all_questions.extend(questions)
                
                # Organizar por categoría
                for question in questions:
                    category = question.metadata.categoria
                    if category not in self.questions_cache:
                        self.questions_cache[category] = []
                    self.questions_cache[category].append(question)
                    
            except Exception as e:
                print(f"❌ Error cargando {yaml_file}: {e}")
                continue
        
        print(f"✅ Cargadas {len(self.all_questions)} preguntas de {len(yaml_files)} archivos")
        print(f"📂 Categorías encontradas: {list(self.questions_cache.keys())}")
    
    def _load_questions_from_file(self, file_path: Path) -> List[Question]:
        """
        Carga preguntas de un archivo YAML específico.
        
        Args:
            file_path: Ruta al archivo YAML
            
        Returns:
            Lista de preguntas del archivo
        """
        print(f"📖 Leyendo {file_path.name}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            questions = []
            
            # Verificar si es el nuevo formato (con categorías) o el formato anterior
            if 'categories' in yaml_data:
                # Nuevo formato: las preguntas están organizadas por categorías
                for category_id, category_data in yaml_data['categories'].items():
                    category_name = category_data.get('name', f'Categoría {category_id}')
                    
                    for question_data in category_data.get('questions', []):
                        # Convertir opciones de lista a diccionario si es necesario
                        opciones_raw = question_data.get('options', [])
                        if isinstance(opciones_raw, list):
                            # Convertir lista a diccionario {a: opcion1, b: opcion2, ...}
                            opciones = {}
                            letters = ['a', 'b', 'c', 'd']
                            for i, option in enumerate(opciones_raw[:4]):  # Máximo 4 opciones
                                if i < len(letters):
                                    opciones[letters[i]] = option
                        else:
                            opciones = opciones_raw
                        
                        # Convertir respuesta correcta de índice a letra si es necesario
                        respuesta_correcta = question_data.get('correct_answer')
                        if isinstance(respuesta_correcta, int):
                            letters = ['a', 'b', 'c', 'd']
                            if 0 <= respuesta_correcta < len(letters):
                                respuesta_correcta = letters[respuesta_correcta]
                        elif respuesta_correcta == "ANULADA":
                            respuesta_correcta = "ANULADA"
                        
                        question = Question(
                            id=str(question_data.get('id', f"{file_path.stem}_{category_id}_{len(questions)}")),
                            enunciado=question_data.get('question', ''),
                            opciones=opciones,
                            respuesta_correcta=respuesta_correcta or 'a',
                            metadata=QuestionMetadata(
                                # Usar la categoría del nodo padre, no de la pregunta individual
                                categoria=category_name,
                                convocatoria="madrid",  # Extraer del nombre del archivo
                                fuente=file_path.stem,
                                año=2025,  # Por defecto, se puede extraer del nombre del archivo
                                comunidad_autonoma="Madrid",  # Por defecto
                                numero_pregunta=question_data.get('id', 0)
                            )
                        )
                        questions.append(question)
            
            elif 'preguntas' in yaml_data:
                # Formato anterior: usar Pydantic para validar la estructura
                question_file = QuestionFile(**yaml_data)
                questions = question_file.preguntas
            
            else:
                print(f"⚠️  Formato no reconocido en {file_path}")
                return []
            
            return questions
            
        except Exception as e:
            print(f"❌ Error cargando {file_path}: {e}")
            return []
    
    def get_questions_by_criteria(
        self,
        categorias: List[str] = None,
        años: List[int] = None,
        comunidades: List[str] = None,
        tipo_examen: str = "per"
    ) -> List[Question]:
        """
        Filtra preguntas según criterios específicos.
        
        Args:
            categorias: Lista de categorías deseadas (None = todas)
            años: Lista de años deseados (None = todos)
            comunidades: Lista de comunidades deseadas (None = todas)
            tipo_examen: Tipo de examen
            
        Returns:
            Lista de preguntas que cumplen los criterios
        """
        filtered_questions = self.all_questions.copy()
        
        # Filtrar por categorías
        if categorias:
            filtered_questions = [
                q for q in filtered_questions 
                if q.metadata.categoria in categorias
            ]
        
        # Filtrar por años
        if años:
            filtered_questions = [
                q for q in filtered_questions 
                if q.metadata.año in años
            ]
        
        # Filtrar por comunidades
        if comunidades:
            filtered_questions = [
                q for q in filtered_questions 
                if q.metadata.comunidad_autonoma in comunidades
            ]
        
        print(f"🔍 Filtrado: {len(filtered_questions)} preguntas encontradas")
        return filtered_questions
    
    def get_available_categories(self) -> List[str]:
        """
        Devuelve todas las categorías disponibles.
        
        Returns:
            Lista de nombres de categorías
        """
        return list(self.questions_cache.keys())
    
    def get_available_years(self) -> List[int]:
        """
        Devuelve todos los años disponibles.
        
        Returns:
            Lista de años únicos
        """
        years = set(q.metadata.año for q in self.all_questions)
        return sorted(list(years))
    
    def get_available_communities(self) -> List[str]:
        """
        Devuelve todas las comunidades autónomas disponibles.
        
        Returns:
            Lista de comunidades únicas
        """
        communities = set(q.metadata.comunidad_autonoma for q in self.all_questions)
        return sorted(list(communities))
    
    def get_stats(self) -> Dict:
        """
        Devuelve estadísticas sobre las preguntas cargadas.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            "total_preguntas": len(self.all_questions),
            "categorias": len(self.questions_cache),
            "años_disponibles": self.get_available_years(),
            "comunidades_disponibles": self.get_available_communities(),
            "preguntas_por_categoria": {
                cat: len(questions) 
                for cat, questions in self.questions_cache.items()
            }
        }
    
    def load_yaml_file(self, file_path: Path) -> QuestionFile:
        """
        Carga un archivo YAML específico y lo convierte a objetos Python.
        
        Args:
            file_path: Ruta completa al archivo YAML
            
        Returns:
            QuestionFile con las preguntas organizadas
            
        Raises:
            Exception: Si el archivo no existe o está mal formateado
        """
        print(f"📄 Cargando archivo: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            
            # Verificar estructura básica
            if 'exam_info' not in data or 'categories' not in data:
                raise ValueError("El archivo no tiene la estructura correcta (falta exam_info o categories)")
            
            # Extraer metadatos del examen (con soporte para formato antiguo y nuevo)
            exam_info = data['exam_info']
            metadata = QuestionMetadata(
                title=exam_info.get('title', 'Título no especificado'),
                subtitle=exam_info.get('subtitle', 'Subtítulo no especificado'),
                total_questions=exam_info.get('total_questions', 0),
                # Nuevos campos con valores por defecto para compatibilidad
                community=exam_info.get('community', 'No especificada'),
                year=exam_info.get('year', 0),
                call=exam_info.get('call', 'No especificada'),
                test_code=exam_info.get('test_code', 'No especificado')
            )
            
            questions = []
            
            # Cargar preguntas (compatible con ambos formatos)
            for category_data in data['categories']:
                category_name = category_data.get('name', 'Categoría sin nombre')
                
                for question_data in category_data.get('questions', []):
                    # Convertir opciones de lista a diccionario si es necesario
                    opciones_raw = question_data.get('options', [])
                    if isinstance(opciones_raw, list):
                        # Convertir lista a diccionario {a: opcion1, b: opcion2, ...}
                        opciones = {}
                        letters = ['a', 'b', 'c', 'd']
                        for i, option in enumerate(opciones_raw[:4]):  # Máximo 4 opciones
                            if i < len(letters):
                                opciones[letters[i]] = option
                    else:
                        opciones = opciones_raw
                    
                    # Convertir respuesta correcta de índice a letra si es necesario
                    respuesta_correcta = question_data.get('correct_answer')
                    if isinstance(respuesta_correcta, int):
                        letters = ['a', 'b', 'c', 'd']
                        if 0 <= respuesta_correcta < len(letters):
                            respuesta_correcta = letters[respuesta_correcta]
                    elif respuesta_correcta == "ANULADA":
                        respuesta_correcta = "ANULADA"
                    
                    question = Question(
                        id=str(question_data.get('id', f"{file_path.stem}_{len(questions)}")),
                        enunciado=question_data.get('question', ''),
                        opciones=opciones,
                        respuesta_correcta=respuesta_correcta or 'a',
                        metadata=metadata  # Usar metadatos extraídos del archivo
                    )
                    questions.append(question)
            
            return QuestionFile(preguntas=questions)
        
        except Exception as e:
            print(f"❌ Error cargando {file_path}: {e}")
            raise e


# Instancia global del cargador de preguntas
# Esta variable se usará en toda la aplicación
question_loader = QuestionLoader()

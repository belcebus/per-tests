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

from app.models.schemas import Question, QuestionFile


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
        
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        # Usar Pydantic para validar la estructura
        question_file = QuestionFile(**yaml_data)
        
        return question_file.preguntas
    
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


# Instancia global del cargador de preguntas
# Esta variable se usará en toda la aplicación
question_loader = QuestionLoader()

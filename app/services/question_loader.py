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
from typing import List, Dict, Optional
from pathlib import Path

from app.models.schemas import Question, QuestionFile, QuestionMetadata
from config.settings import settings


class QuestionLoader:
    """
    Clase que maneja la carga de preguntas desde archivos YAML.

    Es como un "bibliotecario" que:
    - Sabe dónde están los archivos
    - Los lee cuando se lo pedimos
    - Los organiza para que sea fácil buscar preguntas
    """

    def __init__(self, data_directory: Optional[str] = None):
        """
        Inicializa el cargador de preguntas.

        Args:
            data_directory: Carpeta donde están los archivos YAML (opcional, usa configuración por defecto)
        """
        # Usar configuración centralizada si no se especifica directorio
        if data_directory is None:
            self.data_directory = settings.get_absolute_path(settings.data_dir)
        else:
            # Usar ruta absoluta basada en la ubicación de este archivo (compatibilidad)
            if not os.path.isabs(data_directory):
                # Obtener directorio del proyecto (dos niveles arriba de este archivo)
                project_root = Path(__file__).parent.parent.parent
                self.data_directory = project_root / data_directory
            else:
                self.data_directory = Path(data_directory)
        self.questions_cache: Dict[str, List[Question]] = {}
        self.all_questions: List[Question] = []

    def load_all_questions(self) -> List[Question]:
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

        # Buscar archivos .yaml solo en la carpeta exams y excluir backups
        exams_dir = settings.get_exams_path()
        yaml_files = []

        if exams_dir.exists():
            # Buscar archivos en exams/ y excluir backups
            all_yaml_files = list(exams_dir.glob("**/*.yaml"))
            yaml_files = [
                f
                for f in all_yaml_files
                if not any(x in f.name.lower() for x in ["backup", "bk_", ".bak"])
            ]
        else:
            # Fallback: buscar en el directorio principal (compatibilidad)
            all_yaml_files = list(self.data_directory.glob("*.yaml"))
            yaml_files = [
                f
                for f in all_yaml_files
                if not any(x in f.name.lower() for x in ["backup", "bk_", ".bak"])
            ]

        if not yaml_files:
            print(
                f"⚠️  No se encontraron archivos YAML válidos en {self.data_directory}"
            )
            return []

        for yaml_file in yaml_files:
            try:
                questions = self._load_questions_from_file(yaml_file)
                self.all_questions.extend(questions)

                # Organizar por categoría
                for question in questions:
                    category = question.metadata.categoria or ""
                    if category not in self.questions_cache:
                        self.questions_cache[category] = []
                    self.questions_cache[category].append(question)

            except Exception as e:
                print(f"❌ Error cargando {yaml_file}: {e}")
                continue

        print(
            f"✅ Cargadas {len(self.all_questions)} preguntas de {len(yaml_files)} archivos"
        )
        print(f"📂 Categorías encontradas: {list(self.questions_cache.keys())}")

        return self.all_questions

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
            with open(file_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            questions: List[Question] = []

            # Verificar si es el nuevo formato (con categories) o el formato anterior
            if "categories" in yaml_data:
                # Nuevo formato: las preguntas están organizadas por categorías
                print("   📁 Procesando formato con categorías...")

                for category_id, category_data in yaml_data["categories"].items():
                    category_name = category_data.get(
                        "name", f"Categoría {category_id}"
                    )
                    print(f"   📂 Procesando categoría {category_id}: {category_name}")

                    category_questions = category_data.get("questions", [])
                    print(
                        f"   📝 Preguntas en esta categoría: {len(category_questions)}"
                    )

                    for question_data in category_questions:
                        # Las opciones ya vienen como diccionario en el formato actual
                        opciones = question_data.get("options", {})
                        # La respuesta correcta ya viene como letra o "ANULADA"
                        respuesta_correcta = question_data.get("correct_answer", "a")
                        # Extraer información del examen del archivo si está disponible
                        exam_info = yaml_data.get("exam_info", {})
                        question = Question(
                            id=str(
                                question_data.get(
                                    "id",
                                    f"{file_path.stem}_{category_id}_{len(questions)}",
                                )
                            ),
                            enunciado=question_data.get("question", ""),
                            opciones=opciones,
                            respuesta_correcta=respuesta_correcta,
                            metadata=QuestionMetadata(
                                # Campos principales requeridos
                                title=exam_info.get(
                                    "title",
                                    "EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO",
                                ),
                                subtitle=exam_info.get("subtitle", "Código de Test"),
                                total_questions=exam_info.get("total_questions", 45),
                                community=exam_info.get("community", "Madrid"),
                                year=exam_info.get("year", 2025),
                                call=exam_info.get("call", "Ordinaria"),
                                test_code=exam_info.get("test_code", "Test01"),
                                # Campos de compatibilidad
                                categoria=str(category_id),
                                categoria_nombre=category_name,
                                convocatoria=exam_info.get("call", "Ordinaria"),
                                anio=exam_info.get("year", 2025),
                                comunidad_autonoma=exam_info.get("community", "Madrid"),
                                numero_pregunta=question_data.get("id", 0),
                            ),
                        )
                        questions.append(question)

                print(f"   ✅ Total preguntas procesadas del archivo: {len(questions)}")

            elif "preguntas" in yaml_data:
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
        categorias: Optional[List[str]] = None,
        anios: Optional[List[int]] = None,
        comunidades: Optional[List[str]] = None,
        tipo_examen: str = "per",
    ) -> List[Question]:
        """
        Filtra preguntas según criterios específicos.

        Args:
            categorias: Lista de categorías deseadas (None = todas)
            anios: Lista de años deseados (None = todos)
            comunidades: Lista de comunidades deseadas (None = todas)
            tipo_examen: Tipo de examen

        Returns:
            Lista de preguntas que cumplen los criterios
        """
        filtered_questions = self.all_questions.copy()

        # Normalizar argumentos a lista vacía si son None
        categorias = categorias or []
        anios = anios or []
        comunidades = comunidades or []

        # Filtrar por categorías
        if categorias:
            filtered_questions = [
                q for q in filtered_questions if q.metadata.categoria in categorias
            ]

        # Filtrar por años
        if anios:
            filtered_questions = [
                q for q in filtered_questions if q.metadata.anio in anios
            ]

        # Filtrar por comunidades
        if comunidades:
            filtered_questions = [
                q
                for q in filtered_questions
                if q.metadata.comunidad_autonoma in comunidades
            ]

        print(f"🔍 Filtrado: {len(filtered_questions)} preguntas encontradas")
        return filtered_questions

    def get_category_id_name_map(self) -> Dict[str, str]:
        """
        Devuelve un diccionario {id: nombre} de todas las categorías cargadas.
        """
        result = {}
        for cat_id, questions in self.questions_cache.items():
            # Buscar el primer nombre legible disponible
            nombre = None
            for q in questions:
                if (
                    hasattr(q.metadata, "categoria_nombre")
                    and q.metadata.categoria_nombre
                ):
                    nombre = q.metadata.categoria_nombre
                    break
            result[cat_id] = nombre or f"Categoría {cat_id}"
        return result

    def get_available_categories(self) -> list:
        """
        Devuelve todas las categorías disponibles como lista de dicts {id, nombre}.
        """
        cat_map = self.get_category_id_name_map()
        return [{"id": k, "nombre": v} for k, v in cat_map.items()]

    def get_available_years(self) -> List[int]:
        """
        Devuelve todos los años disponibles.

        Returns:
            Lista de años únicos
        """
        years = set(
            q.metadata.anio for q in self.all_questions if q.metadata.anio is not None
        )
        return sorted(list(years))

    def get_available_communities(self) -> List[str]:
        """
        Devuelve todas las comunidades autónomas disponibles.

        Returns:
            Lista de comunidades únicas
        """
        communities = set(
            q.metadata.comunidad_autonoma
            for q in self.all_questions
            if q.metadata.comunidad_autonoma is not None
        )
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
                cat: len(questions) for cat, questions in self.questions_cache.items()
            },
        }

    def get_exam_metadata(self) -> Dict:
        """
        Obtiene metadatos de todos los exámenes disponibles organizados por criterios.

        Returns:
            Diccionario con estructura jerárquica de metadatos de exámenes
        """
        exam_metadata: Dict[str, Dict[int, Dict[str, set]]] = {}

        # Agrupar por comunidad, año y convocatoria
        for question in self.all_questions:
            community = question.metadata.community
            year = question.metadata.year
            call = question.metadata.call
            test_code = question.metadata.test_code

            # Crear la estructura jerárquica
            if community not in exam_metadata:
                exam_metadata[community] = {}
            if year not in exam_metadata[community]:
                exam_metadata[community][year] = {}
            if call not in exam_metadata[community][year]:
                exam_metadata[community][year][call] = set()

            exam_metadata[community][year][call].add(test_code)

        # Convertir sets a listas ordenadas para JSON serialization
        result_metadata: Dict[str, Dict[int, Dict[str, List[str]]]] = {}
        for community in exam_metadata:
            result_metadata[community] = {}
            for year in exam_metadata[community]:
                result_metadata[community][year] = {}
                for call in exam_metadata[community][year]:
                    result_metadata[community][year][call] = sorted(
                        list(exam_metadata[community][year][call])
                    )

        return {
            "comunidades": self.get_available_communities(),
            "anios": self.get_available_years(),
            "convocatorias_por_comunidad_anio": result_metadata,
        }

    def get_available_calls_by_community_year(
        self, community: str, year: int
    ) -> List[str]:
        """
        Obtiene las convocatorias disponibles para una comunidad y año específicos.

        Args:
            community: Nombre de la comunidad autónoma
            year: Año del examen

        Returns:
            Lista de convocatorias disponibles
        """
        calls = set()
        for question in self.all_questions:
            if (
                question.metadata.community == community
                and question.metadata.year == year
            ):
                calls.add(question.metadata.call)

        return sorted(list(calls))

    def get_available_tests_by_criteria(
        self, community: str, year: int, call: str
    ) -> List[Dict]:
        """
        Obtiene los modelos de test disponibles para criterios específicos.

        Args:
            community: Nombre de la comunidad autónoma
            year: Año del examen
            call: Convocatoria del examen

        Returns:
            Lista de diccionarios con información de cada test disponible
        """
        tests = {}

        for question in self.all_questions:
            if (
                question.metadata.community == community
                and question.metadata.year == year
                and question.metadata.call == call
            ):

                test_id = (
                    f"{community.lower()}_{year}_{call}_{question.metadata.test_code}"
                )

                if test_id not in tests:
                    tests[test_id] = {
                        "id": test_id,
                        "title": question.metadata.title,
                        "subtitle": question.metadata.subtitle,
                        "community": question.metadata.community,
                        "year": question.metadata.year,
                        "call": question.metadata.call,
                        "test_code": question.metadata.test_code,
                        "total_questions": question.metadata.total_questions,
                    }

        return list(tests.values())

    def get_questions_for_specific_exam(self, exam_identifier: str) -> List[Question]:
        """
        Obtiene todas las preguntas de un examen específico.

        Args:
            exam_identifier: Identificador del examen (ej: 'madrid_2024_abril_test01')

        Returns:
            Lista de preguntas del examen específico

        Raises:
            ValueError: Si no se encuentra el examen especificado
        """
        # Parsear el identificador del examen
        parts = exam_identifier.split("_")
        if len(parts) != 4:
            raise ValueError(f"Formato de identificador inválido: {exam_identifier}")

        community, year_str, call, test_code = parts

        try:
            year = int(year_str)
        except ValueError:
            raise ValueError(f"Año inválido en identificador: {year_str}")

        # Capitalizar la primera letra de la comunidad para hacer match
        community = community.capitalize()

        # Filtrar preguntas que coincidan
        matching_questions = []
        for question in self.all_questions:
            if (
                question.metadata.community == community
                and question.metadata.year == year
                and question.metadata.call == call
                and question.metadata.test_code == test_code
            ):
                matching_questions.append(question)

        if not matching_questions:
            raise ValueError(
                f"No se encontraron preguntas para el examen: {exam_identifier}"
            )

        # Ordenar por número de pregunta si está disponible
        matching_questions.sort(key=lambda q: q.metadata.numero_pregunta or 0)

        print(
            f"🎯 Examen específico encontrado: {exam_identifier} con {len(matching_questions)} preguntas"
        )
        return matching_questions


# Instancia global del cargador de preguntas
# Esta variable se usará en toda la aplicación
question_loader = QuestionLoader()

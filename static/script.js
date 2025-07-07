/**
 * Cliente JavaScript para PER Tests
 * 
 * Este archivo maneja toda la lógica del frontend:
 * 1. Cargar información inicial del sistema
 * 2. Configurar y generar exámenes
 * 3. Mostrar preguntas y manejar respuestas
 * 4. Enviar examen para corrección
 * 5. Mostrar resultados
 */

// ================================
// VARIABLES GLOBALES
// ================================

let currentExam = null;          // Examen actual
let currentQuestionIndex = 0;    // Índice de pregunta actual
let userAnswers = {};           // Respuestas del usuario
let examStartTime = null;       // Tiempo de inicio del examen
let timerInterval = null;       // Intervalo del cronómetro
let examType = 'normal';        // 'normal' o 'simulacro'

// Mapeo global de categorías id → nombre
let categoryIdNameMap = {};

// ================================
// CONFIGURACIÓN DE LA API
// ================================

const API_BASE = '/api';

// ================================
// FUNCIONES DE UTILIDAD
// ================================

/**
 * Muestra/oculta el overlay de carga
 */
function showLoading(show = true) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.add('active');
    } else {
        loading.classList.remove('active');
    }
}

/**
 * Cambia entre pantallas
 */
function showScreen(screenId) {
    // Ocultar todas las pantallas
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Mostrar la pantalla seleccionada
    document.getElementById(screenId).classList.add('active');
}

/**
 * Realiza una petición a la API
 */
async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error en la petición');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error en API:', error);
        alert(`Error: ${error.message}`);
        throw error;
    }
}

// ================================
// INICIALIZACIÓN
// ================================

/**
 * Carga la información inicial del sistema
 */
async function loadSystemInfo() {
    try {
        // Cargar información general
        const info = await apiRequest('/exams/info');
        displaySystemInfo(info);
        
        // Cargar opciones para formularios
        const categories = await apiRequest('/exams/categories');
        populateFormOptions(categories);
        
    } catch (error) {
        console.error('Error cargando información del sistema:', error);
    }
}

/**
 * Muestra la información del sistema
 */
function displaySystemInfo(info) {
    const container = document.getElementById('system-info');
    const preguntas = info.preguntas;
    
    container.innerHTML = `
        <div class="info-grid">
            <div class="info-item">
                <strong>📚 Total de preguntas:</strong> ${preguntas.total_preguntas}
            </div>
            <div class="info-item">
                <strong>📂 Categorías:</strong> ${preguntas.categorias}
            </div>
            <div class="info-item">
                <strong>📅 Años disponibles:</strong> ${preguntas.años_disponibles.join(', ')}
            </div>
            <div class="info-item">
                <strong>🌍 Comunidades:</strong> ${preguntas.comunidades_disponibles.length}
            </div>
            <div class="info-item">
                <strong>🎯 Exámenes activos:</strong> ${info.servicio.examenes_activos}
            </div>
        </div>
    `;
}

/**
 * Rellena las opciones de los formularios
 */
function populateFormOptions(data) {
    // Construir el mapeo global de categorías
    categoryIdNameMap = {};
    data.categorias.forEach(catObj => {
        categoryIdNameMap[catObj.id] = catObj.nombre;
    });
    // Categorías
    const categoriasContainer = document.getElementById('categorias-container');
    categoriasContainer.innerHTML = data.categorias.map(catObj => `
        <div class="checkbox-item">
            <input type="checkbox" id="cat-${catObj.id}" value="${catObj.id}">
            <label for="cat-${catObj.id}">${catObj.nombre}</label>
        </div>
    `).join('');
    // Años
    const añosContainer = document.getElementById('años-container');
    añosContainer.innerHTML = data.años.map(año => `
        <div class="checkbox-item">
            <input type="checkbox" id="año-${año}" value="${año}">
            <label for="año-${año}">${año}</label>
        </div>
    `).join('');
    // Comunidades
    const comunidadesContainer = document.getElementById('comunidades-container');
    comunidadesContainer.innerHTML = data.comunidades.map(com => `
        <div class="checkbox-item">
            <input type="checkbox" id="com-${com}" value="${com}">
            <label for="com-${com}">${com}</label>
        </div>
    `).join('');
    
    // Actualizar indicadores de scroll después de llenar los contenedores
    setTimeout(() => {
        updateScrollIndicators();
    }, 100);
}

/**
 * Detecta si un contenedor checkbox tiene contenido que requiere scroll
 * y aplica la clase correspondiente
 */
function updateScrollIndicators() {
    const checkboxGroups = document.querySelectorAll('.checkbox-group');
    
    checkboxGroups.forEach((group, index) => {
        // Verificar si el contenido excede la altura del contenedor
        const hasScroll = group.scrollHeight > group.clientHeight;
        
        if (hasScroll) {
            group.classList.add('has-scroll');
            // Agregar título para indicar que se puede hacer scroll
            group.setAttribute('title', 'Desliza hacia abajo para ver más opciones');
        } else {
            group.classList.remove('has-scroll');
            group.removeAttribute('title');
        }
    });
}

// ================================
// GENERACIÓN DE EXÁMENES
// ================================

/**
 * Genera un nuevo examen
 */
async function generateExam() {
    showLoading(true);
    try {
        const config = getExamConfig();
        // Añadir tipo_examen si es simulacro
        if (examType === 'simulacro') {
            config.tipo_examen = 'simulacro';
        }
        const exam = await apiRequest('/exams/generate', {
            method: 'POST',
            body: JSON.stringify(config)
        });
        currentExam = exam;
        currentQuestionIndex = 0;
        userAnswers = {};
        startExam();
    } catch (error) {
        console.error('Error generando examen:', error);
    } finally {
        showLoading(false);
    }
}

/**
 * Obtiene la configuración del examen del formulario
 */
function getExamConfig() {
    const numPreguntasSelect = document.getElementById('num-preguntas');
    let numPreguntas;
    
    if (numPreguntasSelect.value === 'custom') {
        // Usar el valor personalizado
        numPreguntas = parseInt(document.getElementById('custom-questions').value);
        
        // Validar que sea un número válido
        if (isNaN(numPreguntas) || numPreguntas < 1 || numPreguntas > 100) {
            alert('Por favor, ingresa un número válido de preguntas (entre 1 y 100)');
            throw new Error('Número de preguntas inválido');
        }
    } else {
        // Usar el valor predefinido
        numPreguntas = parseInt(numPreguntasSelect.value);
    }
    
    // Categorías seleccionadas
    const categorias = Array.from(document.querySelectorAll('#categorias-container input:checked'))
        .map(cb => cb.value);
    
    // Años seleccionados
    const años = Array.from(document.querySelectorAll('#años-container input:checked'))
        .map(cb => parseInt(cb.value));
    
    // Comunidades seleccionadas
    const comunidades = Array.from(document.querySelectorAll('#comunidades-container input:checked'))
        .map(cb => cb.value);
    
    return {
        num_preguntas: numPreguntas,
        categorias: categorias.length > 0 ? categorias : null,
        años: años.length > 0 ? años : null,
        comunidades: comunidades.length > 0 ? comunidades : null
    };
}

// ================================
// INTERFAZ DEL EXAMEN
// ================================

/**
 * Inicia el examen
 */
function startExam() {
    showScreen('exam-screen');
    examStartTime = Date.now();
    startTimer();
    showQuestion(0);
}

/**
 * Inicia el cronómetro
 */
function startTimer() {
    timerInterval = setInterval(() => {
        const elapsed = Date.now() - examStartTime;
        const minutes = Math.floor(elapsed / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        
        document.getElementById('timer').textContent = 
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
}

/**
 * Detiene el cronómetro
 */
function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

/**
 * Muestra una pregunta específica
 */
function showQuestion(index) {
    const question = currentExam.questions[index];
    
    // Actualizar progreso
    document.getElementById('progress-text').textContent = 
        `Pregunta ${index + 1} de ${currentExam.questions.length}`;
    
    const progressPercent = ((index + 1) / currentExam.questions.length) * 100;
    document.getElementById('progress-fill').style.width = `${progressPercent}%`;
    
    // Mostrar pregunta
    const questionNumberElem = document.getElementById('question-number');
    questionNumberElem.textContent = index + 1;
    questionNumberElem.style.cursor = question.metadata ? 'pointer' : '';
    // Eliminar popover previo si existe
    let metaPopoverElem = document.getElementById('meta-popover-exam');
    if (metaPopoverElem) metaPopoverElem.remove();
    if (question.metadata) {
        // Crear popover
        const popover = document.createElement('div');
        popover.className = 'question-metadata-popover';
        popover.id = 'meta-popover-exam';
        popover.tabIndex = -1;
        popover.innerHTML = `
            <button class="close-metadata-popover" aria-label="Cerrar">&times;</button>
            <strong>Apareció en:</strong><br>
            <span><b>Comunidad:</b> ${question.metadata.community || ''}</span><br>
            <span><b>Año:</b> ${question.metadata.year || ''}</span><br>
            <span><b>Convocatoria:</b> ${question.metadata.call || ''}</span><br>
            <span><b>Modelo:</b> ${question.metadata.test_code || ''}</span><br>
            <span><b>Pregunta original:</b> ${question.metadata.numero_pregunta || 'N/A'}</span>
        `;
        popover.style.display = 'none';
        popover.style.position = 'absolute';
        popover.style.left = '50%';
        popover.style.transform = 'translateX(-50%)';
        popover.style.top = '120%';
        popover.style.zIndex = '20';
        popover.style.background = '#fff';
        popover.style.color = '#222';
        popover.style.border = '1px solid #d1d5db';
        popover.style.boxShadow = '0 2px 8px rgba(0,0,0,0.12)';
        popover.style.padding = '12px 16px 8px 16px';
        popover.style.borderRadius = '8px';
        popover.style.fontSize = '0.95em';
        popover.style.textAlign = 'left';
        // Forzar estilos para evitar herencia del span del número
        popover.querySelectorAll('span, strong, b').forEach(el => {
            el.style.background = 'none';
            el.style.color = '#222';
            el.style.borderRadius = '0';
            el.style.display = 'inline';
            el.style.padding = '0';
        });
        // Insertar popover en el mismo contenedor padre
        questionNumberElem.parentElement.style.position = 'relative';
        questionNumberElem.parentElement.appendChild(popover);
        // Evento click en el número
        questionNumberElem.onclick = function(e) {
            e.stopPropagation();
            document.querySelectorAll('.question-metadata-popover').forEach(pop => pop.style.display = 'none');
            popover.style.display = 'block';
        };
        // Cerrar al hacer click fuera
        document.addEventListener('click', function(e) {
            popover.style.display = 'none';
        }, { once: true });
        // Cerrar con aspa
        popover.querySelector('.close-metadata-popover').addEventListener('click', function(e) {
            e.stopPropagation();
            popover.style.display = 'none';
        });
        // Cerrar al perder el foco
        popover.addEventListener('blur', function() {
            setTimeout(() => { popover.style.display = 'none'; }, 100);
        });
    } else {
        questionNumberElem.onclick = null;
    }
    document.getElementById('question-text').textContent = question.enunciado;
    
    // Mostrar opciones
    const optionsContainer = document.getElementById('question-options');
    optionsContainer.innerHTML = Object.entries(question.opciones).map(([letter, text]) => `
        <div class="option" data-value="${letter}">
            <div class="option-letter">${letter.toUpperCase()}</div>
            <div class="option-text">${text}</div>
        </div>
    `).join('');
    
    // Agregar eventos a opciones
    document.querySelectorAll('.option').forEach(option => {
        option.addEventListener('click', () => selectOption(option));
    });
    
    // Mostrar respuesta previa si existe
    const previousAnswer = userAnswers[question.id];
    if (previousAnswer) {
        const selectedOption = document.querySelector(`[data-value="${previousAnswer}"]`);
        if (selectedOption) {
            selectOption(selectedOption);
        }
    }
    
    // Actualizar botones de navegación
    updateNavigationButtons(index);
}

/**
 * Inicia el examen
 */
function startExam() {
    showScreen('exam-screen');
    examStartTime = Date.now();
    startTimer();
    showQuestion(0);
}

/**
 * Inicia el examen
 */
function startExam() {
    showScreen('exam-screen');
    examStartTime = Date.now();
    startTimer();
    showQuestion(0);
}

/**
 * Selecciona una opción
 */
function selectOption(optionElement) {
    // Remover selección previa
    document.querySelectorAll('.option').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // Seleccionar nueva opción
    optionElement.classList.add('selected');
    
    // Guardar respuesta
    const questionId = currentExam.questions[currentQuestionIndex].id;
    const answer = optionElement.dataset.value;
    userAnswers[questionId] = answer;
}

/**
 * Actualiza los botones de navegación
 */
function updateNavigationButtons(index) {
    const btnAnterior = document.getElementById('btn-anterior');
    const btnSiguiente = document.getElementById('btn-siguiente');
    const btnFinalizar = document.getElementById('btn-finalizar');
    
    // Botón anterior
    btnAnterior.style.display = index > 0 ? 'inline-block' : 'none';
    
    // Botón siguiente y finalizar
    if (index < currentExam.questions.length - 1) {
        btnSiguiente.style.display = 'inline-block';
        btnFinalizar.style.display = 'none';
    } else {
        btnSiguiente.style.display = 'none';
        btnFinalizar.style.display = 'inline-block';
    }
}

/**
 * Navega a la pregunta anterior
 */
function previousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        showQuestion(currentQuestionIndex);
    }
}

/**
 * Navega a la siguiente pregunta
 */
function nextQuestion() {
    if (currentQuestionIndex < currentExam.questions.length - 1) {
        currentQuestionIndex++;
        showQuestion(currentQuestionIndex);
    }
}

// ================================
// FINALIZACIÓN Y RESULTADOS
// ================================

/**
 * Finaliza el examen y envía para corrección
 */
async function finishExam() {
    // Verificar que todas las preguntas están respondidas
    const unanswered = currentExam.questions.filter(q => !userAnswers[q.id]);
    
    if (unanswered.length > 0) {
        if (!confirm(`Tienes ${unanswered.length} preguntas sin responder. ¿Quieres continuar?`)) {
            return;
        }
    }
    
    showLoading(true);
    stopTimer();
    
    try {
        // Enviar respuestas para corrección
        const result = await apiRequest('/exams/correct', {
            method: 'POST',
            body: JSON.stringify({
                exam_id: currentExam.exam_id,
                respuestas: userAnswers
            })
        });
        
        // Mostrar resultados
        showResults(result);
        
    } catch (error) {
        console.error('Error corrigiendo examen:', error);
    } finally {
        showLoading(false);
    }
}

/**
 * Muestra los resultados del examen
 */
function showResults(result) {
    showScreen('results-screen');
    
    // Puntuación principal
    document.getElementById('score-percentage').textContent = `${result.porcentaje}%`;
    document.getElementById('score-fraction').textContent = result.puntuacion_total;
    
    const statusElement = document.getElementById('score-status');
    if (result.aprobado) {
        statusElement.textContent = '✅ APROBADO';
        statusElement.className = 'score-status aprobado';
    } else {
        statusElement.textContent = '❌ SUSPENDIDO';
        statusElement.className = 'score-status suspendido';
    }
    
    // Resultados por categoría
    const categoryContainer = document.getElementById('category-results');
    categoryContainer.innerHTML = Object.entries(result.desglose_por_categoria).map(([category, data]) => {
        // Usar el mapeo global para mostrar el nombre legible
        let categoryName = categoryIdNameMap[category] || category.replace(/_/g, ' ');
        return `
            <div class="category-result">
                <div class="category-name">${categoryName}</div>
                <div class="category-score">${data.correctas}/${data.total} (${data.porcentaje}%)</div>
            </div>
        `;
    }).join('');
    
    // Detalle de preguntas
    const questionsContainer = document.getElementById('question-details');
    questionsContainer.innerHTML = result.preguntas_detalle.map((detail, index) => {
        const meta = detail.metadata;
        const popoverId = `meta-popover-${index}`;
        // Mostrar todas las opciones para referencia
        const opcionesHtml = Object.entries(detail.opciones).map(([letra, texto]) => {
            let claseOpcion = 'option-reference';
            if (letra === detail.respuesta_correcta) {
                claseOpcion += ' correct-option';
            }
            if (letra === detail.respuesta_usuario && !detail.es_correcta) {
                claseOpcion += ' user-wrong-option';
            }
            return `
                <div class="${claseOpcion}">
                    <span class="option-letter-ref">${letra.toUpperCase()}</span>
                    <span class="option-text-ref">${texto}</span>
                    ${letra === detail.respuesta_correcta ? '<span class="correct-indicator">✓</span>' : ''}
                    ${letra === detail.respuesta_usuario && !detail.es_correcta ? '<span class="wrong-indicator">✗</span>' : ''}
                </div>
            `;
        }).join('');
        return `
            <div class="question-detail ${detail.es_correcta ? 'correct' : 'incorrect'}">
                <div class="question-detail-header">
                    <span class="question-number-detail">
                        Pregunta ${index + 1}
                        <span class="metadata-popover-container" style="position: relative; display: inline-block;">
                            <button class="question-metadata-link" tabindex="0" aria-label="Ver metadatos de la pregunta" data-popover="${popoverId}" style="margin-left: 0.4em; vertical-align: middle;">
                                ℹ️
                            </button>
                            <div class="question-metadata-popover" id="${popoverId}" tabindex="-1">
                                <button class="close-metadata-popover" aria-label="Cerrar">&times;</button>
                                <strong>Apareció en:</strong><br>
                                <span><b>Comunidad:</b> ${meta.community}</span><br>
                                <span><b>Año:</b> ${meta.year}</span><br>
                                <span><b>Convocatoria:</b> ${meta.call}</span><br>
                                <span><b>Modelo:</b> ${meta.test_code}</span><br>
                                <span><b>Pregunta original:</b> ${meta.numero_pregunta || 'N/A'}</span>
                            </div>
                        </span>
                    </span>
                    <span class="question-status ${detail.es_correcta ? 'correct' : 'incorrect'}">
                        ${detail.es_correcta ? '✅ Correcta' : '❌ Incorrecta'}
                    </span>
                </div>
                <div class="question-detail-content">
                    <div class="question-text-detail">
                        <strong>Pregunta:</strong> ${detail.enunciado}
                    </div>
                    <div class="all-options">
                        <div class="options-label">Opciones:</div>
                        <div class="options-list">
                            ${opcionesHtml}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // Lógica para mostrar/cerrar popovers de metadatos
    document.querySelectorAll('.question-metadata-link').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            // Cerrar otros popovers
            document.querySelectorAll('.question-metadata-popover').forEach(pop => pop.style.display = 'none');
            // Abrir el correspondiente
            const popover = document.getElementById(btn.dataset.popover);
            if (popover) {
                popover.style.display = 'block';
            }
        });
    });
    // Cerrar al hacer click fuera
    document.addEventListener('click', function(e) {
        document.querySelectorAll('.question-metadata-popover').forEach(pop => pop.style.display = 'none');
    });
    // Cerrar con aspa
    document.querySelectorAll('.close-metadata-popover').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            btn.parentElement.style.display = 'none';
        });
    });
    // Cerrar al perder el foco
    document.querySelectorAll('.question-metadata-popover').forEach(pop => {
        pop.addEventListener('blur', function() {
            setTimeout(() => { pop.style.display = 'none'; }, 100);
        });
    });
}

/**
 * Vuelve a la pantalla de configuración para un nuevo examen
 */
function newExam() {
    // Limpiar datos del examen anterior
    currentExam = null;
    currentQuestionIndex = 0;
    userAnswers = {};
    stopTimer();
    
    // Volver a la pantalla de configuración
    showScreen('exam-config');
    
    // Recargar información del sistema
    loadSystemInfo();
}

// ================================
// EVENT LISTENERS
// ================================

document.addEventListener('DOMContentLoaded', () => {
    // Cargar información inicial
    loadSystemInfo();
    
    // Botones principales
    document.getElementById('btn-generar').addEventListener('click', generateExam);
    document.getElementById('btn-anterior').addEventListener('click', previousQuestion);
    document.getElementById('btn-siguiente').addEventListener('click', nextQuestion);
    document.getElementById('btn-finalizar').addEventListener('click', finishExam);
    document.getElementById('btn-nuevo-examen').addEventListener('click', newExam);
    
    // Manejar cambio en el selector de número de preguntas
    document.getElementById('num-preguntas').addEventListener('change', handleQuestionNumberChange);
    
    // Validación en tiempo real para el campo personalizado
    document.getElementById('custom-questions').addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        const isValid = !isNaN(value) && value >= 1 && value <= 100;
        
        // Cambiar estilo según validación
        if (e.target.value && !isValid) {
            e.target.style.borderColor = '#dc3545';
            e.target.style.backgroundColor = '#fff5f5';
        } else {
            e.target.style.borderColor = '#e1e5e9';
            e.target.style.backgroundColor = 'white';
        }
    });
    
    // Configurar selector de tipo de examen
    setupExamTypeSelector();
    
    // Actualizar indicadores de scroll al redimensionar ventana
    window.addEventListener('resize', () => {
        setTimeout(updateScrollIndicators, 100);
    });
});

// ================================
// NUEVO: SOPORTE PARA SIMULACRO
// ================================

function setupExamTypeSelector() {
    const typeSelect = document.getElementById('tipo-examen');
    if (!typeSelect) return;
    typeSelect.addEventListener('change', function() {
        examType = this.value;
        const disable = examType === 'simulacro';
        // Deshabilitar selección de categorías y años (pero NO comunidades)
        document.querySelectorAll('#categorias-container input, #años-container input').forEach(cb => {
            cb.disabled = disable;
        });
        // Deshabilitar selector de número de preguntas
        document.getElementById('num-preguntas').disabled = disable;
        // Mostrar/ocultar aviso de simulacro
        const simulacroInfo = document.getElementById('simulacro-info');
        if (simulacroInfo) simulacroInfo.style.display = disable ? 'block' : 'none';
        // Ocultar grupo de preguntas personalizadas en simulacro
        document.getElementById('custom-questions-group').style.display = 'none';
    });
}

// OPCIONAL: MOSTRAR TIEMPO MÁXIMO EN SIMULACRO
function showMaxTimeIfSimulacro() {
    const maxTimeElem = document.getElementById('simulacro-max-time');
    if (!maxTimeElem) return;
    if (examType === 'simulacro' && currentExam && currentExam.max_time_minutes) {
        maxTimeElem.textContent = `⏱️ Tiempo máximo: ${currentExam.max_time_minutes} minutos`;
        maxTimeElem.style.display = 'block';
    } else {
        maxTimeElem.style.display = 'none';
    }
}
// Llamar a showMaxTimeIfSimulacro() en startExam()
const originalStartExam = startExam;
startExam = function() {
    originalStartExam();
    showMaxTimeIfSimulacro();
};

// ================================
// UTILIDADES ADICIONALES
// ================================

/**
 * Maneja errores de red
 */
window.addEventListener('online', () => {
    console.log('Conexión restaurada');
});

window.addEventListener('offline', () => {
    console.log('Sin conexión a internet');
    alert('Se ha perdido la conexión a internet. Algunas funciones pueden no funcionar correctamente.');
});

/**
 * Maneja el cambio en el selector de número de preguntas
 */
function handleQuestionNumberChange() {
    const select = document.getElementById('num-preguntas');
    const customGroup = document.getElementById('custom-questions-group');
    
    if (select.value === 'custom') {
        customGroup.style.display = 'block';
        // Hacer focus en el campo personalizado
        setTimeout(() => {
            document.getElementById('custom-questions').focus();
        }, 100);
    } else {
        customGroup.style.display = 'none';
    }
}

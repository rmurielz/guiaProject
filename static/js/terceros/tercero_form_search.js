document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Iniciando script TomSelect...');

    // --- CONFIGURACIÓN Y ELEMENTOS DEL DOM ---
    const form = document.getElementById('terceros-form');
    if (!form) {
        console.error('❌ No se encontró el formulario');
        return;
    }

    // --- CONFIGURACIÓN CENTRALIZADA ---
    const CONFIG = {
        minQueryLength: 2,
        debounceTime: 500,
        messages: {
            loading: 'Verificando...',
            exists: (nombre) => `¡Atención! ID ya registrado para: ${nombre}`,
            available: 'ID disponible',
            networkError: 'Error de red al verificar',
        },
        icons: { loading: 'fa-spinner fa-spin', danger: 'fa-exclamation-triangle', success: 'fa-check-circle', error: 'fa-times-circle' }
    };

    const { paisesUrl, divisionesUrl, ciudadesUrl, verificarUrl } = form.dataset;
    console.log('📡 URLs configuradas:', { paisesUrl, divisionesUrl, ciudadesUrl });

    // Campos de identificación
    const tipoIdSelect = document.getElementById('id_tipo_identificacion');
    const nroidInput = document.getElementById('id_nroid');
    const validationMessageEl = document.getElementById('id-validation-message');

    // Selectores de ubicación
    const paisSelectEl = document.getElementById('pais-select');
    const divisionSelectEl = document.getElementById('division-select');
    const ciudadSelectEl = document.getElementById('ciudad-select');

    // Campos ocultos del formulario
    const paisIdInput = document.getElementById('id_pais_geoname_id');
    const paisNombreInput = document.getElementById('id_pais_nombre');
    const paisCodigoInput = document.getElementById('id_pais_codigo_iso');
    const divisionIdInput = document.getElementById('id_division_geoname_id');
    const divisionNombreInput = document.getElementById('id_division_nombre');
    const divisionCodigoInput = document.getElementById('id_division_codigo_iso');
    const ciudadNombreInput = document.getElementById('id_ciudad_nombre');

    const submitButton = document.getElementById('submit-button');
    let debounceTimeout = null;

    // --- VERIFICACIÓN DE ID ---
    const checkTerceroExists = async () => {
        const tipoID = tipoIdSelect.value;
        const nroId = nroidInput.value.trim();
        if (!tipoID || !nroId) {
            clearValidationMessage();
            return;
        }
        showValidationMessage(CONFIG.messages.loading, 'loading', CONFIG.icons.loading);
        const url = new URL(verificarUrl, window.location.origin);
        url.searchParams.append('tipo_identificacion', tipoID);
        url.searchParams.append('nroid', nroId);

        try {
            const response = await fetch(url);
            const data = await response.json();
            if (data.existe) {
                showValidationMessage(CONFIG.messages.exists(data.nombre), 'danger', CONFIG.icons.danger);
                submitButton.disabled = true;
            } else {
                showValidationMessage(CONFIG.messages.available, 'success', CONFIG.icons.success);
                submitButton.disabled = false;
            }
        } catch (error) {
            showValidationMessage('Error de red al verificar', 'danger', 'fa-times-circle');
        }
    };

    const debouncedCheck = () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(checkTerceroExists, CONFIG.debounceTime);
    };

    const showValidationMessage = (message, type, icon) => {
        validationMessageEl.innerHTML = `<i class="fas ${icon} me-1"></i>${message}`;
        validationMessageEl.className = `validation-message ${type}`;
    };

    const clearValidationMessage = () => {
        validationMessageEl.innerHTML = '';
        validationMessageEl.className = '';
    };

    // --- CONFIGURACIÓN SIMPLE DE TOM-SELECT ---
    const createTomSelect = (element, urlBuilder, parentTomSelect = null) => {
        console.log(`🔧 Creando TomSelect para: ${element.id}`);

        // Destruir instancia previa si existe
        if (element.tomselect) {
            element.tomselect.destroy();
        }

        const tomSelect = new TomSelect(element, {
            valueField: 'id',
            labelField: 'nombre',
            searchField: 'nombre',
            create: false,
            maxOptions: 50,
            openOnFocus: true,
            closeAfterSelect: true,

            load: function(query, callback) {
                console.log(`🔍 Buscando "${query}" en ${element.id}`);

                // Exigimos 2+ caracteres SOLO si el usuario está escribiendo. Si el campo está vacío (on focus), permitimos la carga.
                if (query.length > 0 && query.length < CONFIG.minQueryLength) {
                    console.log('❌ Query muy corta, esperando más caracteres...');
                    return callback();
                }

                if (parentTomSelect && !parentTomSelect.getValue()) {
                    console.log('❌ Campo padre no tiene valor');
                    return callback();
                }

                const url = urlBuilder(query);
                console.log('📡 Fetching:', url);

                fetch(url)
                    .then(response => {
                        console.log('📨 Response status:', response.status);
                        return response.json();
                    })
                    .then(data => {
                        console.log('📊 Data received:', data);
                        const items = data.map(item => ({
                            id: String(item.id),
                            nombre: item.nombre,
                            codigo: item.codigo || ''
                        }));
                        callback(items);
                    })
                    .catch(error => {
                        console.error('❌ Error fetching:', error);
                        callback();
                    });
            },

            onInitialize: function() {
                console.log(`✅ TomSelect inicializado: ${element.id}`);
            },

            onFocus: function() {
                console.log(`👆 Focus en: ${element.id}`);
            },

            onType: function(str) {
                console.log(`⌨️ Escribiendo en ${element.id}: "${str}"`);
            }
        });

        return tomSelect;
    };

    /**
     * Maneja la lógica de cambio para un selector padre de TomSelect.
     * Limpia y actualiza los selectores dependientes y los campos ocultos.
     * @param {object} options
     * @param {TomSelect} options.sourceSelect - La instancia de TomSelect que cambió.
     * @param {TomSelect} options.dependentSelect - La instancia de TomSelect que depende de la fuente.
     * @param {object} options.hiddenInputs - Un objeto con los inputs ocultos a actualizar.
     * @param {TomSelect[]} [options.cascadingCleanup=[]] - Selectores adicionales para limpiar en cascada.
     */
    const handleParentSelectChange = ({ sourceSelect, dependentSelect, hiddenInputs, cascadingCleanup = [] }) => {
        const value = sourceSelect.getValue();

        // Limpiar y deshabilitar el selector dependiente directo
        dependentSelect.clear();
        dependentSelect.clearOptions();
        dependentSelect.disable();

        // Limpiar otros selectores en la cadena (ej. ciudad cuando cambia país)
        cascadingCleanup.forEach(select => {
            select.clear();
            select.clearOptions();
            select.disable();
        });

        // Actualizar campos ocultos
        const data = value ? sourceSelect.options[value] : null;
        hiddenInputs.id.value = data?.id || '';
        hiddenInputs.nombre.value = data?.nombre || '';
        if (hiddenInputs.codigo) hiddenInputs.codigo.value = data?.codigo || '';

        // Habilitar el selector dependiente si hay un valor
        if (value) dependentSelect.enable();
    };

    // --- INICIALIZACIÓN DE TOM-SELECT ---
    console.log('🎯 Inicializando TomSelect instances...');

    // Verificar que los elementos existan
    if (!paisSelectEl) {
        console.error('❌ No se encontró pais-select');
        return;
    }

    try {
        // Crear instancias
        const paisTomSelect = createTomSelect(
            paisSelectEl,
            (query) => `${paisesUrl}?q=${encodeURIComponent(query)}`
        );

        const divisionTomSelect = createTomSelect(
            divisionSelectEl,
            (query) => `${divisionesUrl}?geoname_id=${paisTomSelect.getValue()}&q=${encodeURIComponent(query)}`,
            paisTomSelect
        );

        const ciudadTomSelect = createTomSelect(
            ciudadSelectEl,
            (query) => `${ciudadesUrl}?geoname_id=${divisionTomSelect.getValue()}&q=${encodeURIComponent(query)}`,
            divisionTomSelect
        );

        // Estado inicial
        divisionTomSelect.disable();
        ciudadTomSelect.disable();

        // --- EVENTOS DE CAMBIO ---
        paisTomSelect.on('change', () => {
            console.log('🌍 País cambió:', paisTomSelect.getValue());
            handleParentSelectChange({
                sourceSelect: paisTomSelect,
                dependentSelect: divisionTomSelect,
                hiddenInputs: { id: paisIdInput, nombre: paisNombreInput, codigo: paisCodigoInput },
                cascadingCleanup: [ciudadTomSelect] // Al cambiar país, también se limpia ciudad
            });
        });

        divisionTomSelect.on('change', () => {
            console.log('🏛️ División cambió:', divisionTomSelect.getValue());
            handleParentSelectChange({
                sourceSelect: divisionTomSelect,
                dependentSelect: ciudadTomSelect,
                hiddenInputs: { id: divisionIdInput, nombre: divisionNombreInput, codigo: divisionCodigoInput }
            });
        });

        ciudadTomSelect.on('change', (value) => {
            console.log('🏙️ Ciudad cambió:', value);
            // Este es el último eslabón, solo actualiza su campo oculto
            if (value) {
                const data = ciudadTomSelect.options[value];
                ciudadNombreInput.value = data.nombre;
            } else {
                ciudadNombreInput.value = '';
            }
        });

        console.log('🎉 ¡TomSelect configurado exitosamente!');

    } catch (error) {
        console.error('💥 Error creando TomSelect:', error);
    }

    // --- EVENT LISTENERS PARA VALIDACIÓN ---
    if (tipoIdSelect && nroidInput) {
        tipoIdSelect.addEventListener('change', checkTerceroExists);
        nroidInput.addEventListener('input', debouncedCheck);
    }

    console.log('🏁 FIN DEL SCRIPT. Si ves esto, no hubo errores fatales en la inicialización.');
});
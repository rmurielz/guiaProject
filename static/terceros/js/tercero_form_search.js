document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Iniciando script TomSelect...');

    // --- CONFIGURACIÓN Y ELEMENTOS DEL DOM ---
    const form = document.getElementById('terceros-form');
    if (!form) {
        console.error('❌ No se encontró el formulario');
        return;
    }

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
        showValidationMessage('Verificando...', 'loading', 'fa-spinner fa-spin');
        const url = new URL(verificarUrl, window.location.origin);
        url.searchParams.append('tipo_identificacion', tipoID);
        url.searchParams.append('nroid', nroId);

        try {
            const response = await fetch(url);
            const data = await response.json();
            if (data.existe) {
                showValidationMessage(`¡Atención! ID ya registrado para: ${data.nombre}`, 'danger', 'fa-exclamation-triangle');
                submitButton.disabled = true;
            } else {
                showValidationMessage('ID disponible', 'success', 'fa-check-circle');
                submitButton.disabled = false;
            }
        } catch (error) {
            showValidationMessage('Error de red al verificar', 'danger', 'fa-times-circle');
        }
    };

    const debouncedCheck = () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(checkTerceroExists, 500);
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
                if (query.length > 0 && query.length < 2) {
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
        paisTomSelect.on('change', (value) => {
            console.log('🌍 País cambió:', value);

            // Limpiar campos dependientes
            divisionTomSelect.clear();
            divisionTomSelect.clearOptions();
            ciudadTomSelect.clear();
            ciudadTomSelect.clearOptions();
            ciudadTomSelect.disable();

            if (value) {
                const data = paisTomSelect.options[value];
                paisIdInput.value = data.id;
                paisNombreInput.value = data.nombre;
                paisCodigoInput.value = data.codigo || '';
                divisionTomSelect.enable();
            } else {
                paisIdInput.value = '';
                paisNombreInput.value = '';
                paisCodigoInput.value = '';
                divisionTomSelect.disable();
            }
        });

        divisionTomSelect.on('change', (value) => {
            console.log('🏛️ División cambió:', value);

            ciudadTomSelect.clear();
            ciudadTomSelect.clearOptions();

            if (value) {
                const data = divisionTomSelect.options[value];
                divisionIdInput.value = data.id;
                divisionNombreInput.value = data.nombre;
                divisionCodigoInput.value = data.codigo || '';
                ciudadTomSelect.enable();
            } else {
                divisionIdInput.value = '';
                divisionNombreInput.value = '';
                divisionCodigoInput.value = '';
                ciudadTomSelect.disable();
            }
        });

        ciudadTomSelect.on('change', (value) => {
            console.log('🏙️ Ciudad cambió:', value);

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
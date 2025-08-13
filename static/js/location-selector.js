document.addEventListener('DOMContentLoaded', function () {
    // El script espera un objeto global `LOCATION_SELECTOR_CONFIG` definido en la plantilla.
    if (typeof LOCATION_SELECTOR_CONFIG === 'undefined') {
        console.error('Location Selector: El objeto de configuración `LOCATION_SELECTOR_CONFIG` no fue encontrado.');
        return;
    }

    const urls = LOCATION_SELECTOR_CONFIG.urls;
    const ubicacionInicialData = LOCATION_SELECTOR_CONFIG.ubicacion_inicial;

    const hiddenFields = {
        pais: {
            id: document.getElementById('id_pais_geoname_id'),
            nombre: document.getElementById('id_pais_nombre'),
            codigo: document.getElementById('id_pais_codigo_iso')
        },
        division: {
            id: document.getElementById('id_division_geoname_id'),
            nombre: document.getElementById('id_division_nombre'),
            codigo: document.getElementById('id_division_codigo_iso')
        },
        ciudad: {
            id: document.getElementById('id_ciudad_geoname_id'),
            nombre: document.getElementById('id_ciudad_nombre')
        }
    };

    function createTomSelect(elementId, options) {
        const element = document.getElementById(elementId);
        if (!element) {
            console.error(`Location Selector: Elemento con ID "${elementId}" no encontrado.`);
            return null;
        }

        return new TomSelect(element, {
            valueField: 'id',
            labelField: 'nombre',
            searchField: 'nombre',
            create: false,
            placeholder: options.placeholder,
            preload: options.preload || false, // Carga inicial al enfocar
            load: function (query, callback) {
                let fetchUrl = `${options.url}?q=${encodeURIComponent(query)}`;
                if (options.parentField && options.parentField.getValue()) {
                    fetchUrl += `&geoname_id=${options.parentField.getValue()}`;
                }
                fetch(fetchUrl)
                    .then(response => response.json())
                    .then(json => callback(json))
                    .catch(() => callback());
            },
            onChange: function() {
                // Evita que el dropdown se cierre inmediatamente después de seleccionar
                // una opción que fue cargada dinámicamente.
                this.refreshOptions(false);
            }
        });
    }

    function updateHiddenFields(type, item) {
        const fields = hiddenFields[type];
        if (fields.id) fields.id.value = item?.id || '';
        if (fields.nombre) fields.nombre.value = item?.nombre || '';
        if (fields.codigo) fields.codigo.value = item?.codigo || '';
    }

    const tomSelectPais = createTomSelect('id_pais', { url: urls.paises, placeholder: 'Busca un país...', preload: 'focus' });
    const tomSelectDivision = createTomSelect('id_division', { url: urls.divisiones, placeholder: 'Primero selecciona un país...', parentField: tomSelectPais });
    const tomSelectCiudad = createTomSelect('id_ciudad', { url: urls.ciudades, placeholder: 'Primero selecciona un departamento...', parentField: tomSelectDivision });

    if (!tomSelectPais || !tomSelectDivision || !tomSelectCiudad) {
        console.error("Location Selector: Uno o más elementos TomSelect no pudieron ser inicializados.");
        return;
    }

    tomSelectPais.on('change', function(value){
        updateHiddenFields('pais', this.options[value]);
        tomSelectDivision.clear();
        tomSelectDivision.clearOptions();
        tomSelectDivision.enable();
        tomSelectDivision.load('');
        tomSelectCiudad.clear();
        tomSelectCiudad.disable();
        updateHiddenFields('division', null);
        updateHiddenFields('ciudad', null);
    });

    tomSelectDivision.on('change', function(value){
        updateHiddenFields('division', this.options[value]);
        tomSelectCiudad.clear();
        tomSelectCiudad.clearOptions();
        tomSelectCiudad.enable();
        tomSelectCiudad.load('');
        updateHiddenFields('ciudad', null);
    });

    tomSelectCiudad.on('change', function (value){
        updateHiddenFields('ciudad', this.options[value]);
    });

    // Cargar datos iniciales si estamos en modo de edición
    if (ubicacionInicialData && ubicacionInicialData.pais) {
        const pais = ubicacionInicialData.pais;
        const division = ubicacionInicialData.division;
        const ciudad = ubicacionInicialData.ciudad;

        tomSelectPais.addOption(pais);
        tomSelectPais.setValue(pais.id);
        updateHiddenFields('pais', pais);

        tomSelectDivision.addOption(division);
        tomSelectDivision.setValue(division.id);
        updateHiddenFields('division', division);
        tomSelectDivision.enable();

        tomSelectCiudad.addOption(ciudad);
        tomSelectCiudad.setValue(ciudad.id);
        updateHiddenFields('ciudad', ciudad);
        tomSelectCiudad.enable();
    }
});
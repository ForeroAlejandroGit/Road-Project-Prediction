let map;
let detalleMap;
let currentRoute;
let markers = [];

function initMap() {
    const mapDiv = document.getElementById('map');
    if (!mapDiv) {
        // Try again on next tick; router may not have rendered Inicio yet /
        setTimeout(initMap, 50);
        return;
    }
    map = new google.maps.Map(mapDiv, {
        center: { lat: 3.4516, lng: -76.5320 },
        zoom: 9,
        styles: [
            {
                featureType: 'poi',
                elementType: 'labels',
                stylers: [{ visibility: 'off' }]
            }
        ]
    });
}

const { createApp } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;

const Inicio = {
    template: InicioTemplate,
    inject: ['appState'],
    computed: {
        proyectos() { return this.appState.proyectos; },
        selectedProyecto() { return this.appState.selectedProyecto; }
    },
    methods: {
        selectProyecto(proyecto) {
            this.appState.selectedProyecto = proyecto;
            this.drawRoute(proyecto);
        },
        drawRoute(proyecto) {
            if (currentRoute) {
                currentRoute.setMap(null);
            }
            
            const directionsService = new google.maps.DirectionsService();
            const directionsRenderer = new google.maps.DirectionsRenderer({
                map: map,
                suppressMarkers: false,
                polylineOptions: {
                    strokeColor: '#2563eb',
                    strokeWeight: 6
                }
            });
            
            currentRoute = directionsRenderer;
            
            const request = {
                origin: { lat: proyecto.lat_inicio, lng: proyecto.lng_inicio },
                destination: { lat: proyecto.lat_fin, lng: proyecto.lng_fin },
                travelMode: 'DRIVING'
            };
            
            directionsService.route(request, (result, status) => {
                if (status === 'OK') {
                    directionsRenderer.setDirections(result);
                }
            });
            
            map.setCenter({ lat: proyecto.lat_inicio, lng: proyecto.lng_inicio });
            map.setZoom(11);
        },
        editProyecto(proyecto) {
            this.appState.editingProyecto = proyecto;
            this.appState.form = { ...proyecto };
            this.$router.push('/nuevo');
        },
        async deleteProyecto(id) {
            if (confirm('¿Está seguro de eliminar este proyecto?')) {
                await fetch(`/api/proyectos/${id}`, { method: 'DELETE' });
                await this.appState.loadProyectos();
                if (this.selectedProyecto && this.selectedProyecto.id === id) {
                    this.appState.selectedProyecto = null;
                }
            }
        },
        formatNumber(num) {
            return new Intl.NumberFormat('es-CO').format(num);
        }
    },
    mounted() {
        this.$nextTick(() => {
            const waitForMap = () => {
                if (map) {
                    this.appState.updateMapMarkers();
                } else {
                    setTimeout(waitForMap, 50);
                }
            };
            waitForMap();
        });
    }
};

const Nuevo = {
    template: NuevoTemplate,
    inject: ['appState'],
    computed: {
        editingProyecto() { return this.appState.editingProyecto; },
        form() { return this.appState.form; },
        totalCausado() {
            return this.form.items.reduce((sum, item) => sum + (item.causado || 0), 0);
        }
    },
    methods: {
        formatNumber(num) {
            return new Intl.NumberFormat('es-CO').format(num);
        },
        async saveProyecto() {
            if (this.form.unidades_funcionales.length === 0) {
                alert('Debe agregar al menos una Unidad Funcional');
                return;
            }
            
            const method = this.editingProyecto ? 'PUT' : 'POST';
            const url = this.editingProyecto 
                ? `/api/proyectos/${this.editingProyecto.id}` 
                : '/api/proyectos';
            
            const proyectoData = {
                nombre: this.form.nombre,
                codigo: this.form.codigo,
                num_ufs: this.form.num_ufs,
                longitud: this.form.longitud,
                anio_inicio: this.form.anio_inicio,
                duracion: this.form.duracion,
                fase: this.form.fase,
                ubicacion: this.form.ubicacion,
                costo: this.form.costo,
                lat_inicio: this.form.lat_inicio,
                lng_inicio: this.form.lng_inicio,
                lat_fin: this.form.lat_fin,
                lng_fin: this.form.lng_fin
            };
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(proyectoData)
            });
            
            const result = await response.json();
            const codigo = this.form.codigo;
            
            for (const uf of this.form.unidades_funcionales) {
                uf.codigo = codigo;
                await fetch('/api/unidades-funcionales', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(uf)
                });
            }
            
            for (const item of this.form.items) {
                if (item.causado > 0) {
                    item.codigo = codigo;
                    await fetch('/api/items', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(item)
                    });
                }
            }
            
            await this.appState.loadProyectos();
            this.cancelForm();
            this.$router.push('/');
        },
        cancelForm() {
            this.appState.form = this.appState.getEmptyForm();
            this.appState.editingProyecto = null;
            this.$router.push('/');
        },
        addUnidadFuncional() {
            this.form.unidades_funcionales.push({
                unidad_funcional: this.form.unidades_funcionales.length + 1,
                longitud_km: 0,
                puentes_vehiculares_und: 0,
                puentes_vehiculares_mt2: 0,
                puentes_peatonales_und: 0,
                puentes_peatonales_mt2: 0,
                tuneles_und: 0,
                tuneles_km: 0,
                alcance: 'Primera calzada',
                zona: 'Rural',
                tipo_terreno: 'Plano'
            });
        },
        removeUnidadFuncional(index) {
            this.form.unidades_funcionales.splice(index, 1);
        },
    }
};

const Detalle = {
    template: DetalleTemplate,
    inject: ['appState'],
    data() {
        return {
            unidadesFuncionales: [],
            items: []
        };
    },
    computed: {
        selectedProyecto() { return this.appState.selectedProyecto; },
        totalItems() {
            return this.items.reduce((sum, item) => sum + item.causado, 0);
        }
    },
    methods: {
        formatNumber(num) {
            return new Intl.NumberFormat('es-CO').format(num);
        },
        async loadRelatedData() {
            if (this.selectedProyecto) {
                const codigo = this.selectedProyecto.codigo;
                const [ufsRes, itemsRes] = await Promise.all([
                    fetch(`/api/unidades-funcionales/${codigo}`),
                    fetch(`/api/items/${codigo}`)
                ]);
                this.unidadesFuncionales = await ufsRes.json();
                this.items = await itemsRes.json();
            }
        }
    },
    watch: {
        selectedProyecto: {
            immediate: true,
            handler() {
                this.loadRelatedData();
                this.$nextTick(() => {
                    if (this.selectedProyecto) {
                        detalleMap = new google.maps.Map(document.getElementById('detalle-map'), {
                            center: { lat: this.selectedProyecto.lat_inicio, lng: this.selectedProyecto.lng_inicio },
                            zoom: 11
                        });
                        
                        const directionsService = new google.maps.DirectionsService();
                        const directionsRenderer = new google.maps.DirectionsRenderer({
                            map: detalleMap
                        });
                        
                        directionsService.route({
                            origin: { lat: this.selectedProyecto.lat_inicio, lng: this.selectedProyecto.lng_inicio },
                            destination: { lat: this.selectedProyecto.lat_fin, lng: this.selectedProyecto.lng_fin },
                            travelMode: 'DRIVING'
                        }, (result, status) => {
                            if (status === 'OK') {
                                directionsRenderer.setDirections(result);
                            }
                        });
                    }
                });
            }
        }
    }
};

const Historicos = {
    template: HistoricosTemplate,
    inject: ['appState'],
    computed: {
        proyectos() { return this.appState.proyectos; },
        totalInversion() {
            return this.proyectos.reduce((sum, p) => sum + p.costo, 0);
        },
        totalLongitud() {
            return this.proyectos.reduce((sum, p) => sum + p.longitud, 0);
        },
        costoPromedioKm() {
            return this.totalLongitud > 0 ? this.totalInversion / this.totalLongitud : 0;
        }
    },
    methods: {
        formatNumber(num) {
            return new Intl.NumberFormat('es-CO').format(num);
        }
    }
};

const Modelo = {
    template: ModeloTemplate,
    inject: ['appState'],
    data() {
        return {
            prediccion: {
                longitud: 0,
                num_ufs: 0
            },
            costoPredicho: null
        };
    },
    methods: {
        async predecirCosto() {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.prediccion)
            });
            const result = await response.json();
            this.costoPredicho = result.costo_predicho;
        },
        formatNumber(num) {
            return new Intl.NumberFormat('es-CO').format(num);
        }
    }
};

const routes = [
    { path: '/', component: Inicio },
    { path: '/nuevo', component: Nuevo },
    { path: '/detalle', component: Detalle },
    { path: '/historicos', component: Historicos },
    { path: '/modelo', component: Modelo }
];

const router = createRouter({
    history: createWebHashHistory(),
    routes
});

const app = createApp({
    data() {
        return {
            proyectos: [],
            selectedProyecto: null,
            editingProyecto: null,
            form: this.getEmptyForm(),
            logoUrl: LOGO_URL
        };
    },
    computed: {
        currentTitle() {
            const route = this.$route.path;
            if (route === '/') return 'Inicio';
            if (route === '/nuevo') return this.editingProyecto ? 'Editar Proyecto' : 'Nuevo Proyecto';
            if (route === '/detalle') return 'Detalle del Proyecto';
            if (route === '/historicos') return 'Análisis Histórico';
            if (route === '/modelo') return 'Modelo Predictivo';
            return 'Sistema de Predicción de Costos';
        }
    },
    methods: {
        async loadProyectos() {
            const response = await fetch('/api/proyectos');
            this.proyectos = await response.json();
            this.updateMapMarkers();
        },
        updateMapMarkers() {
            if (!map) return;
            
            markers.forEach(marker => marker.setMap(null));
            markers = [];
            
            this.proyectos.forEach(proyecto => {
                const marker = new google.maps.Marker({
                    position: { lat: proyecto.lat_inicio, lng: proyecto.lng_inicio },
                    map: map,
                    title: proyecto.nombre,
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 8,
                        fillColor: '#2563eb',
                        fillOpacity: 0.8,
                        strokeColor: '#ffffff',
                        strokeWeight: 2
                    }
                });
                
                marker.addListener('click', () => {
                    this.selectedProyecto = proyecto;
                });
                
                markers.push(marker);
            });
        },
        getEmptyForm() {
            return {
                nombre: '',
                codigo: '',
                num_ufs: 0,
                longitud: 0,
                anio_inicio: new Date().getFullYear(),
                duracion: 0,
                fase: 'Detalle',
                ubicacion: '',
                costo: 0,
                lat_inicio: 0,
                lng_inicio: 0,
                lat_fin: 0,
                lng_fin: 0,
                unidades_funcionales: [],
                items: [
                    { item: '1 - TRANSPORTE', causado: 0 },
                    { item: '2.1 - INFORMACIÓN GEOGRÁFICA', causado: 0 },
                    { item: '2.2 TRAZADO Y DISEÑO GEOMÉTRICO', causado: 0 },
                    { item: '2.3 - SEGURIDAD VIAL', causado: 0 },
                    { item: '2.4 - SISTEMAS INTELIGENTES', causado: 0 },
                    { item: '3.1 - GEOLOGÍA', causado: 0 },
                    { item: '3.2 - HIDROGEOLOGÍA', causado: 0 },
                    { item: '4 - SUELOS', causado: 0 },
                    { item: '5 - TALUDES', causado: 0 },
                    { item: '6 - PAVIMENTO', causado: 0 },
                    { item: '7 - SOCAVACIÓN', causado: 0 },
                    { item: '8 - ESTRUCTURAS', causado: 0 },
                    { item: '9 - TÚNELES', causado: 0 },
                    { item: '10 - URBANISMO Y PAISAJISMO', causado: 0 },
                    { item: '11 - PREDIAL', causado: 0 },
                    { item: '12 - IMPACTO AMBIENTA', causado: 0 },
                    { item: '13 - CANTIDADES', causado: 0 },
                    { item: '14 - EVALUACIÓN SOCIOECONÓMICA', causado: 0 },
                    { item: '15 - OTROS - MANEJO DE REDES', causado: 0 },
                    { item: '16 - DIRECCIÓN Y CORDINACIÓN', causado: 0 }
                ]
            };
        }
    },
    provide() {
        return {
            appState: this
        };
    },
    mounted() {
        this.loadProyectos();
    }
});

app.use(router);
app.mount('#app');


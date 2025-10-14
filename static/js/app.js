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
        form() { return this.appState.form; }
    },
    methods: {
        async saveProyecto() {
            const method = this.editingProyecto ? 'PUT' : 'POST';
            const url = this.editingProyecto 
                ? `/api/proyectos/${this.editingProyecto.id}` 
                : '/api/proyectos';
            
            await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.form)
            });
            
            await this.appState.loadProyectos();
            this.cancelForm();
            this.$router.push('/');
        },
        cancelForm() {
            this.appState.form = this.appState.getEmptyForm();
            this.appState.editingProyecto = null;
            this.$router.push('/');
        }
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
            form: this.getEmptyForm()
        };
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
                lng_fin: 0
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


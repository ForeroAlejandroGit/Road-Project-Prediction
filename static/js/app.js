let map;
let detalleMap;
let currentRoute;
let markers = [];

function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
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

createApp({
    data() {
        return {
            currentView: 'inicio',
            proyectos: [],
            selectedProyecto: null,
            editingProyecto: null,
            form: this.getEmptyForm(),
            prediccion: {
                longitud: 0,
                num_ufs: 0
            },
            costoPredicho: null
        };
    },
    computed: {
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
        async loadProyectos() {
            const response = await fetch('/api/proyectos');
            this.proyectos = await response.json();
            this.updateMapMarkers();
        },
        
        selectProyecto(proyecto) {
            this.selectedProyecto = proyecto;
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
        
        updateMapMarkers() {
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
                    this.selectProyecto(proyecto);
                });
                
                markers.push(marker);
            });
        },
        
        editProyecto(proyecto) {
            this.editingProyecto = proyecto;
            this.form = { ...proyecto };
            this.currentView = 'nuevo';
        },
        
        async deleteProyecto(id) {
            if (confirm('¿Está seguro de eliminar este proyecto?')) {
                await fetch(`/api/proyectos/${id}`, { method: 'DELETE' });
                await this.loadProyectos();
                if (this.selectedProyecto && this.selectedProyecto.id === id) {
                    this.selectedProyecto = null;
                }
            }
        },
        
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
            
            await this.loadProyectos();
            this.cancelForm();
            this.currentView = 'inicio';
        },
        
        cancelForm() {
            this.form = this.getEmptyForm();
            this.editingProyecto = null;
            this.currentView = 'inicio';
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
        },
        
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
    },
    watch: {
        currentView(newView) {
            if (newView === 'detalle' && this.selectedProyecto) {
                this.$nextTick(() => {
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
                });
            }
        }
    },
    mounted() {
        this.loadProyectos();
    }
}).mount('#app');


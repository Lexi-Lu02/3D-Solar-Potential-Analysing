// App entry point — creates the Vue app, plugs in the router, and mounts it on the #app div in index.html.
// MapLibre CSS is imported here so it applies globally (the map is used in two different pages).
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'maplibre-gl/dist/maplibre-gl.css'
import './style.css'

createApp(App).use(router).mount('#app')

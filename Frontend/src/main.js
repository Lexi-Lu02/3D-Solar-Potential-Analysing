// ─────────────────────────────────────────────────────────────────────────────
// main.js — The very first file that runs when the browser loads the app.
//
// Think of it as the "on switch" for the whole website:
//   1. It creates the Vue application using our root component (App.vue).
//   2. It installs the router so the app knows about the different pages (/home, /explore, etc.).
//   3. It "mounts" (attaches) the whole app to the <div id="app"> element in index.html.
//
// MapLibre CSS is imported here (globally) so the map's built-in buttons and
// popups look correct on every page that uses a map.
// ─────────────────────────────────────────────────────────────────────────────

// createApp is Vue's function that turns our code into a running application.
import { createApp } from 'vue'

// App.vue is the root (outermost) component — every other page lives inside it.
import App from './App.vue'

// The router controls which page (component) is shown based on the URL.
import router from './router'

// MapLibre GL is the library that draws the interactive 3D map.
// Its CSS file provides the default styling for map controls (zoom buttons, etc.).
import 'maplibre-gl/dist/maplibre-gl.css'

// Our own global CSS file with shared colours, fonts, and layout rules.
import './style.css'

// Put it all together:
//   createApp(App)     → create the Vue app using App.vue as the root
//   .use(router)       → tell the app which URL maps to which page
//   .mount('#app')     → attach everything to the <div id="app"> in index.html
createApp(App).use(router).mount('#app')

<template>
  <!--
    App.vue — The root (outermost) component that wraps every page.

    It does two things:
      1. Provides a "skip to main content" link for keyboard and screen-reader users
         (accessibility feature — normally invisible, but appears when you press Tab).
      2. Renders whichever page the router says should be shown right now.
  -->

  <!--
    Skip link — lets keyboard users jump past the navigation bar straight to the
    page content by pressing Tab then Enter. Hidden until focused.
  -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <!--
    RouterView is a placeholder that Vue Router swaps out for the correct page
    component based on the current URL.

    The v-slot="{ Component }" syntax lets us wrap the page in <KeepAlive>.
  -->
  <RouterView v-slot="{ Component }">
    <!--
      KeepAlive tells Vue to keep certain page components alive in memory even
      when the user navigates away from them.

      Without KeepAlive, switching from /explore to /home and back would:
        • Destroy the MapLibre map completely (expensive — takes a few seconds to reload)
        • Reset the camera position back to the starting view
        • Re-fetch all 40,000+ building records from scratch

      With KeepAlive, the map stays in memory. Only ExploreView and PrecinctsView
      (the two map pages) are kept alive — the lighter pages are recreated normally.
    -->
    <!-- Render the current page component here -->
    <KeepAlive include="ExploreView,PrecinctsView">
      <component :is="Component" />
    </KeepAlive>
  </RouterView>
</template>

<style>
/* ── Skip-to-content link ─────────────────────────────────────────────────────
   Visually hidden above the screen until the user focuses it with Tab.
   When focused it drops down to the top of the page. */
.skip-link {
  position: absolute;
  top: -100%;       /* hidden above the viewport by default */
  left: 8px;
  z-index: 9999;    /* always on top of everything else */
  background: var(--accent);
  color: var(--surface-white);
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 16px;
  border-radius: 0 0 8px 8px;
  text-decoration: none;
  transition: top 0.15s;
}
/* When the link receives keyboard focus, slide it into view */
.skip-link:focus {
  top: 0;
  outline: 3px solid var(--text-primary);
  outline-offset: 2px;
}
</style>

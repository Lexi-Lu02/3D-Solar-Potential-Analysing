<template>
  <!-- Skip link lets keyboard/screen-reader users jump straight to the page content, bypassing the navbar -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <RouterView v-slot="{ Component }">
    <!--
      KeepAlive keeps the 3D map pages alive when you navigate away.
      Without it, MapLibre would tear down and re-initialise every time you
      switch tabs, which is expensive and loses your camera position.
      Home and Password don't need this because they're lightweight.
    -->
    <KeepAlive include="ExploreView,PrecinctsView">
      <component :is="Component" />
    </KeepAlive>
  </RouterView>
</template>

<style>
/* Skip-to-content link — visible on focus for keyboard users */
.skip-link {
  position: absolute;
  top: -100%;
  left: 8px;
  z-index: 9999;
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
.skip-link:focus {
  top: 0;
  outline: 3px solid var(--text-primary);
  outline-offset: 2px;
}
</style>

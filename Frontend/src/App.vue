<template>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <RouterView v-slot="{ Component }">
    <KeepAlive include="ExploreView">
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
  background: #EA580C;
  color: #ffffff;
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
  outline: 3px solid #1C1917;
  outline-offset: 2px;
}
</style>

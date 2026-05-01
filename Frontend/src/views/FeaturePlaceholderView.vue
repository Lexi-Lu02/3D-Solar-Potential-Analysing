<template>
  <div class="placeholder-page">
    <MainNavbar />
    <section class="placeholder-content">
      <h1>{{ title }}</h1>
      <p>{{ description }}</p>
      <RouterLink class="placeholder-cta" to="/explore">Open 3D Explore</RouterLink>
    </section>
  </div>
</template>

<script setup>
// Generic placeholder shown for pages that are not built yet (currently: AI Insights).
// The router passes title and description as props, so we don't need to create a
// separate stub component for every future feature.
import MainNavbar from '../components/MainNavbar.vue'

defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
})
</script>

<style scoped>
.placeholder-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}

.placeholder-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  text-align: center;
  padding: 24px;
}

h1 {
  font-family: 'DM Serif Display', serif;
  font-size: 42px;
  color: var(--text-primary);
}

p {
  max-width: 640px;
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1.7;
}

.placeholder-cta {
  margin-top: 8px;
  display: inline-block;
  padding: 10px 18px;
  border-radius: 8px;
  text-decoration: none;
  background: var(--accent);
  color: var(--surface-white);
  font-weight: 600;
}
</style>

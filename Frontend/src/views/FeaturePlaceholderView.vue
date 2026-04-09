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
  background: #f7f5f0;
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
  color: #1c1917;
}

p {
  max-width: 640px;
  color: #6b6560;
  font-size: 16px;
  line-height: 1.7;
}

.placeholder-cta {
  margin-top: 8px;
  display: inline-block;
  padding: 10px 18px;
  border-radius: 8px;
  text-decoration: none;
  background: #ea580c;
  color: #ffffff;
  font-weight: 600;
}
</style>

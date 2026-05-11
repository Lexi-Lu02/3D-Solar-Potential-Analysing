<template>
  <!--
    FeaturePlaceholderView.vue — A generic "coming soon" page.

    Instead of creating a separate stub page for every unfinished feature,
    the router passes a `title` and `description` as props to this single
    reusable component. Currently used for the "AI Insights" page.

    What's on screen:
      • The main navigation bar (MainNavbar)
      • A large centred heading (the feature name)
      • A paragraph describing what's coming
      • A button that takes the user to the 3D Explore map
  -->
  <div class="placeholder-page">

    <!-- Shared navigation bar across the top of the page -->
    <MainNavbar />

    <section class="placeholder-content">
      <!-- {{ title }} outputs whatever text the router passed as the title prop -->
      <h1>{{ title }}</h1>

      <!-- {{ description }} outputs the description text from the router props -->
      <p>{{ description }}</p>

      <!-- A call-to-action link back to the main map page -->
      <RouterLink class="placeholder-cta" to="/explore">Explore the Map</RouterLink>
    </section>

  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// FeaturePlaceholderView.vue — Script section
//
// This component receives its content from whoever rendered it (the router).
// defineProps declares which pieces of data the component expects to receive.
//
// Because the router passes `title` and `description` as static props (see router/index.js),
// this component doesn't need to fetch anything or manage any state.
// ─────────────────────────────────────────────────────────────────────────────

// Import the shared top navigation bar.
import MainNavbar from '../components/MainNavbar.vue'

// defineProps declares the "inputs" this component accepts.
// Think of props like function arguments — the router calls this component
// and passes values for `title` and `description`.
defineProps({
  title: {
    type: String,       // must be a text string
    required: true,     // the router MUST provide this — the component won't work without it
  },
  description: {
    type: String,
    required: true,
  },
})
</script>

<style scoped>
/* Full-page layout that stretches to fill the screen */
.placeholder-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}

/* Centred content area that fills the space below the nav bar */
.placeholder-content {
  flex: 1;                     /* take up all remaining vertical space */
  display: flex;
  flex-direction: column;
  align-items: center;         /* horizontally centred */
  justify-content: center;     /* vertically centred */
  gap: 14px;
  text-align: center;
  padding: 24px;
}

/* Large serif heading */
h1 {
  font-family: 'DM Serif Display', serif;
  font-size: 42px;
  color: var(--text-primary);
}

/* Description paragraph below the heading */
p {
  max-width: 640px;
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1.7;
}

/* The "Explore the Map" button — styled as an orange pill */
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

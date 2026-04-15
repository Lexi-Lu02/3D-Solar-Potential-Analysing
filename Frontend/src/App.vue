<template>
  <RouterView v-slot="{ Component }">
    <KeepAlive include="ExploreView">
      <component :is="Component" />
    </KeepAlive>
  </RouterView>
</template>

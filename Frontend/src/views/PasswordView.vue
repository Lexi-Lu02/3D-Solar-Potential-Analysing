<template>
  <div class="pw-screen">
    <div class="pw-card">
      <div class="pw-logo">
        <div class="pw-logo-icon"><img :src="logoUrl" alt="SolarMap logo" /></div>
        <div class="pw-logo-text">SolarMap Melbourne</div>
        <div class="pw-logo-sub">3D City Solar Potential</div>
      </div>

      <form class="pw-form" @submit.prevent="submit">
        <label class="pw-label" for="pw-input">Enter access password</label>
        <div class="pw-input-row">
          <input
            id="pw-input"
            ref="inputRef"
            v-model="password"
            :type="showPw ? 'text' : 'password'"
            class="pw-input"
            :class="{ shake: shaking }"
            placeholder="Password"
            autocomplete="current-password"
          />
          <button type="button" class="pw-toggle" @click="showPw = !showPw" tabindex="-1">
            {{ showPw ? '🙈' : '👁️' }}
          </button>
        </div>
        <div v-if="errorMsg" class="pw-error">{{ errorMsg }}</div>
        <button type="submit" class="pw-btn" :disabled="!password">Enter</button>
      </form>
    </div>
    <div class="pw-footer">© City of Melbourne 2023 · Data for research purposes</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { setAuthenticated } from '../router'
import logoUrl from '../pictures/Project logo.png'

const CORRECT_PASSWORD = 'tp06888'

const password = ref('')
const showPw = ref(false)
const errorMsg = ref('')
const shaking = ref(false)
const inputRef = ref(null)
const router = useRouter()
const route = useRoute()

onMounted(() => {
  inputRef.value?.focus()
})

function submit() {
  if (password.value === CORRECT_PASSWORD) {
    setAuthenticated(true)

    const redirectPath = route.query.redirect || '/'
    router.replace(redirectPath)
  } else {
    errorMsg.value = 'Incorrect password. Please try again.'
    shaking.value = true
    password.value = ''
    setTimeout(() => { shaking.value = false }, 500)
    setTimeout(() => { errorMsg.value = '' }, 3000)
  }
}
</script>

<style scoped>
.pw-screen {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #FFF7ED 0%, #F7F5F0 50%, #EFF6FF 100%);
  padding: 24px;
}

.pw-card {
  background: #ffffff;
  border: 1px solid #E2DDD4;
  border-radius: 16px;
  padding: 40px 36px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04);
}

.pw-logo {
  text-align: center;
  margin-bottom: 32px;
}

.pw-logo-icon {
  margin-bottom: 10px;
}

.pw-logo-icon img {
  width: 72px;
  height: 72px;
  object-fit: contain;
}

.pw-logo-text {
  font-family: 'DM Serif Display', serif;
  font-size: 22px;
  color: #1C1917;
  margin-bottom: 4px;
}

.pw-logo-sub {
  font-size: 13px;
  color: #A8A29E;
}

.pw-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pw-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #6B6560;
}

.pw-input-row {
  position: relative;
  display: flex;
  align-items: center;
}

.pw-input {
  width: 100%;
  padding: 11px 40px 11px 14px;
  border: 1px solid #E2DDD4;
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: #1C1917;
  background: #FAFAF9;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.pw-input:focus {
  border-color: #EA580C;
  box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.1);
  background: #fff;
}

.pw-input.shake {
  animation: shake 0.4s ease;
  border-color: #DC2626;
}

.pw-toggle {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 2px;
  opacity: 0.6;
}

.pw-toggle:hover { opacity: 1; }

.pw-error {
  font-size: 12px;
  color: #DC2626;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 6px;
  padding: 8px 10px;
}

.pw-btn {
  margin-top: 4px;
  padding: 11px;
  background: #EA580C;
  color: white;
  border: none;
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.pw-btn:hover:not(:disabled) { background: #C2410C; }
.pw-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.pw-footer {
  margin-top: 24px;
  font-size: 11px;
  color: #A8A29E;
  text-align: center;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}
</style>

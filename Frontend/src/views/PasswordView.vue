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
            :aria-describedby="errorMsg ? 'pw-error-msg' : undefined"
            aria-required="true"
          />
          <button
            type="button"
            class="pw-toggle"
            @click="showPw = !showPw"
            :aria-label="showPw ? 'Hide password' : 'Show password'"
            :aria-pressed="showPw"
          >
            <span aria-hidden="true">{{ showPw ? '🙈' : '👁️' }}</span>
          </button>
        </div>
        <div v-if="errorMsg" id="pw-error-msg" class="pw-error" role="alert" aria-live="assertive">{{ errorMsg }}</div>
        <button type="submit" class="pw-btn" :disabled="!password" :aria-disabled="!password">Enter</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { setAuthenticated } from '../router'
import logoUrl from '../pictures/Project logo.png'
import { useRouter, useRoute } from 'vue-router'

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

    router.replace(route.query.redirect || '/')
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
  background: linear-gradient(135deg, #E8E6E0 0%, #F2F0EA 50%, #E4E2DC 100%);
  padding: 24px;
}

.pw-card {
  background: rgba(242, 240, 234, 0.88);
  border: 1px solid #C4C2BA;
  border-radius: 16px;
  padding: 40px 36px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 8px 32px rgba(26, 26, 24, 0.10);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
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
  color: #1A1A18;
  margin-bottom: 4px;
}

.pw-logo-sub {
  font-size: 13px;
  color: #6B6960;
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
  color: #4A4844;
}

.pw-input-row {
  position: relative;
  display: flex;
  align-items: center;
}

.pw-input {
  width: 100%;
  padding: 11px 40px 11px 14px;
  border: 1px solid #C4C2BA;
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: #1A1A18;
  background: rgba(255, 255, 255, 0.70);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.pw-input:focus {
  border-color: #D4743A;
  box-shadow: 0 0 0 3px rgba(212, 116, 58, 0.15);
  background: #fff;
}

.pw-input.shake {
  animation: shake 0.4s ease;
  border-color: var(--error);
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
.pw-toggle:focus-visible {
  opacity: 1;
  outline: 3px solid #D4743A;
  outline-offset: 2px;
  border-radius: 4px;
}

.pw-error {
  font-size: 12px;
  color: var(--error);
  background: var(--error-bg);
  border: 1px solid var(--error-border);
  border-radius: 6px;
  padding: 8px 10px;
}

.pw-btn {
  margin-top: 4px;
  padding: 11px;
  background: #1A1A18;
  color: #F0EFE8;
  border: none;
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.pw-btn:hover:not(:disabled) { background: #D4743A; color: #fff; }
.pw-btn:focus-visible {
  outline: 3px solid #D4743A;
  outline-offset: 2px;
}
.pw-btn:disabled { opacity: 0.4; cursor: not-allowed; }


@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}
</style>

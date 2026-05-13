<template>
  <!--
    PasswordView.vue — The login / access-gate page.

    The whole platform is protected by a single shared password.
    This is NOT per-user authentication — anyone with the correct password gets in.

    What's on screen:
      • The SolarMap logo and name
      • A password input with a show/hide toggle (eye icon)
      • An "Enter" button (disabled until something is typed)
      • A red error message that appears for 3 seconds after a wrong password
  -->
  <div class="pw-screen">
    <div class="pw-card">

      <!-- ── Logo area ── -->
      <div class="pw-logo">
        <!-- :src="logoUrl" dynamically binds the image source to our imported logo -->
        <div class="pw-logo-icon"><img :src="logoUrl" alt="SolarMap logo" /></div>
        <div class="pw-logo-text">SolarMap Melbourne</div>
        <div class="pw-logo-sub">3D City Solar Potential</div>
      </div>

      <!--
        The login form.
        @submit.prevent="submit" means:
          • When the user presses Enter or clicks Submit, call the submit() function.
          • .prevent stops the browser from reloading the page (default form behaviour).
      -->
      <form class="pw-form" @submit.prevent="submit">

        <label class="pw-label" for="pw-input">Enter access password</label>

        <div class="pw-input-row">
          <!--
            The password input field.
            v-model="password"      → two-way binding: typing updates the `password` variable,
                                       and `password` changes update what's displayed.
            :type="showPw ? 'text' : 'password'"  → toggles between visible and masked text.
            :class="{ shake: shaking }"           → adds the CSS "shake" animation class when the
                                                      password is wrong.
            :aria-describedby  → links this input to the error message for screen readers.
          -->
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

          <!--
            Show/hide password toggle button (the eye icon).
            @click="showPw = !showPw" flips the showPw boolean between true and false.
            :aria-pressed="showPw" tells screen readers whether the button is "on" or "off".
          -->
          <button
            type="button"
            class="pw-toggle"
            @click="showPw = !showPw"
            :aria-label="showPw ? 'Hide password' : 'Show password'"
            :aria-pressed="showPw"
          >
            <!-- Show a monkey emoji when password is visible, eye emoji when hidden -->
            <span aria-hidden="true">{{ showPw ? '🙈' : '👁️' }}</span>
          </button>
        </div>

        <!--
          Error message — only shown when `errorMsg` is not empty.
          v-if="errorMsg" hides the element completely when there is no error.
          role="alert" and aria-live="assertive" cause screen readers to read it immediately.
        -->
        <div v-if="errorMsg" id="pw-error-msg" class="pw-error" role="alert" aria-live="assertive">{{ errorMsg }}</div>

        <!--
          Submit button.
          :disabled="!password" disables the button when the input is empty.
          type="submit" makes pressing Enter inside the form trigger @submit on the <form> above.
        -->
        <button type="submit" class="pw-btn" :disabled="!password" :aria-disabled="!password">Enter</button>

      </form>
    </div>
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// PasswordView.vue — Script section
//
// This page checks if the entered password matches the hardcoded correct one.
// If correct → mark the session as authenticated and go to the intended page.
// If wrong   → shake the input, show an error for 3 seconds, clear the field.
// ─────────────────────────────────────────────────────────────────────────────

// ref        → creates a reactive variable (changing it updates the screen automatically)
// onMounted  → runs code once after the page is fully shown on screen
import { ref, onMounted } from 'vue'

// setAuthenticated is from the router — calling it saves the "logged in" flag.
import { setAuthenticated } from '../router'
import { clearHomeChatHistory } from '../composables/useHomeJourney.js'

// Import the logo image so we can show it in the template.
import logoUrl from '../pictures/Project logo.png'

// useRouter → lets us navigate to a different page programmatically (in code, not a link).
// useRoute  → gives us information about the current URL (e.g. query parameters).
import { useRouter, useRoute } from 'vue-router'

// The single shared password for the whole platform.
const CORRECT_PASSWORD = 'tp06888'

// ── Reactive variables ────────────────────────────────────────────────────────
// Each ref() creates a reactive variable. When you change .value on any of these,
// Vue automatically updates the relevant part of the screen.

const password = ref('')        // what the user has typed in the input field
const showPw   = ref(false)     // true = show plain text, false = show dots (masked)
const errorMsg = ref('')        // the error text shown in red (empty = no error shown)
const shaking  = ref(false)     // true triggers the CSS shake animation on the input
const inputRef = ref(null)      // a reference to the actual <input> DOM element

const router = useRouter()  // used to navigate after login
const route  = useRoute()   // used to read ?redirect=... from the URL

// ── Auto-focus the input when the page loads ──────────────────────────────────
// onMounted runs once after Vue has finished drawing the page.
// Focusing the input means users can start typing immediately without clicking first.
onMounted(() => {
  inputRef.value?.focus()  // ?. means "only if inputRef.value exists" (safe null check)
})

// ── Handle form submission ────────────────────────────────────────────────────
function submit() {
  if (password.value === CORRECT_PASSWORD) {
    // Correct password:
    // 1. Mark the session as authenticated (stores 'true' in sessionStorage).
    setAuthenticated(true)
    clearHomeChatHistory()
    // 2. Redirect to wherever the user originally wanted to go (from ?redirect=...),
    //    or fall back to the home page if they came directly to /login.
    router.replace(route.query.redirect || '/')
  } else {
    // Wrong password:
    // 1. Show an error message.
    errorMsg.value = 'Incorrect password. Please try again.'
    // 2. Trigger the shake animation.
    shaking.value = true
    // 3. Clear the input so the user can try again.
    password.value = ''
    // 4. Stop the shake animation after 500ms (matches the CSS animation duration).
    setTimeout(() => { shaking.value = false }, 500)
    // 5. Remove the error message after 3 seconds.
    setTimeout(() => { errorMsg.value = '' }, 3000)
  }
}
</script>

<style scoped>
/*
  scoped means these CSS rules only apply to elements inside THIS component.
  They won't accidentally affect other pages.
*/

/* Full-screen centred layout with a subtle gradient background */
.pw-screen {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg) 0%, var(--surface) 50%, var(--surface3) 100%);
  padding: 24px;
}

/* The white card in the centre of the screen */
.pw-card {
  background: rgba(var(--surface-rgb), 0.88);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 40px 36px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 8px 32px rgba(var(--ink-rgb), 0.10);
  backdrop-filter: blur(12px);       /* frosted glass effect */
  -webkit-backdrop-filter: blur(12px);
}

/* Logo area at the top of the card */
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
  color: var(--text-primary);
  margin-bottom: 4px;
}

.pw-logo-sub {
  font-size: 13px;
  color: var(--text-caption);
}

/* Form layout — stacks items vertically with gaps */
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
  color: var(--text-secondary);
}

/* Row that contains both the input and the eye-toggle button */
.pw-input-row {
  position: relative;  /* needed so the toggle button can be positioned inside */
  display: flex;
  align-items: center;
}

/* The password text field */
.pw-input {
  width: 100%;
  padding: 11px 40px 11px 14px;  /* right padding leaves room for the toggle button */
  border: 1px solid var(--border);
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: var(--text-primary);
  background: rgba(var(--white-rgb), 0.70);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

/* Highlight with an orange glow when the input is focused */
.pw-input:focus {
  border-color: var(--city-light);
  box-shadow: 0 0 0 3px rgba(var(--city-light-rgb), 0.15);
  background: var(--white);
}

/* Red border while the shake animation plays (wrong password) */
.pw-input.shake {
  animation: shake 0.4s ease;
  border-color: var(--error);
}

/* The eye icon button, positioned on the right edge of the input */
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
  outline: 3px solid var(--city-light);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Red error box shown below the input */
.pw-error {
  font-size: 12px;
  color: var(--error);
  background: var(--error-bg);
  border: 1px solid var(--error-border);
  border-radius: 6px;
  padding: 8px 10px;
}

/* The "Enter" submit button */
.pw-btn {
  margin-top: 4px;
  padding: 11px;
  background: var(--ink);
  color: var(--nav-text);
  border: none;
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

/* Turns orange on hover (but only when not disabled) */
.pw-btn:hover:not(:disabled) { background: var(--city-light); color: var(--white); }
.pw-btn:focus-visible {
  outline: 3px solid var(--city-light);
  outline-offset: 2px;
}
/* Faded and not-clickable when the input is empty */
.pw-btn:disabled { opacity: 0.4; cursor: not-allowed; }


/* ── Shake animation ──────────────────────────────────────────────────────────
   Applied to the input box when the password is wrong.
   The input rapidly moves left and right to signal an error (like a door rattling). */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}
</style>

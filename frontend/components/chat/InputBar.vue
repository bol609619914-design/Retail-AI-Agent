<template>
  <div class="flex items-center gap-3 rounded-full border border-white/55 bg-white/65 px-5 py-3 shadow-[0_10px_30px_rgba(148,163,184,0.10)]">
    <input
      :value="modelValue"
      type="text"
      class="flex-1 border-0 bg-transparent text-[15px] font-normal text-slate-700 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
      placeholder="比如：我希望卧室更安静柔和，适合睡前放松"
      :disabled="disabled"
      @input="handleInput"
      @keydown.enter="emit('submit')"
    >

    <button
      type="button"
      class="send-button flex h-10 w-10 items-center justify-center rounded-full text-slate-600 transition hover:bg-white/80 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
      :disabled="disabled"
      @click="emit('submit')"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="1.8"
        class="h-5 w-5"
        aria-hidden="true"
      >
        <path d="M21 3L9 15" />
        <path d="M21 3L14 21L9 15L3 10L21 3Z" />
      </svg>
      <span class="sr-only">发送</span>
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  disabled: boolean
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  submit: []
}>()

function handleInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
}
</script>

<style scoped>
.send-button {
  border: 0;
  background: transparent;
}
</style>

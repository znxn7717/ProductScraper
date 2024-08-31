<template>
  <span class="loader mr-2"></span>
</template>

<style scoped>
.loader {
  width: 0.6rem;
  height: 1.2rem;
  display: grid;
  background:
    linear-gradient(currentColor 0 0) top/100% 2px,
    radial-gradient(farthest-side at  top, #0000 calc(100% - 2px),currentColor calc(100% - 1px) ,#0000) top,
    linear-gradient(currentColor 0 0) bottom/100% 2px,
    radial-gradient(farthest-side at  bottom, #0000 calc(100% - 2px),currentColor calc(100% - 1px) ,#0000) bottom;
  background-size: 100% 1px,100% 50%; 
  background-repeat: no-repeat;
  animation: l18 4s infinite linear;
}
.loader::before,
.loader::after {
  content: "";
  grid-area: 1/1;
  background: inherit;
  border: inherit;
  animation: inherit;
}
.loader::after {
  animation-duration: 2s;
}
@keyframes l18 {
  100% {transform: rotate(1turn)}
}
</style>
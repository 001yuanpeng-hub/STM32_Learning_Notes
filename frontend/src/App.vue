<template>
  <div id="app">
    <ChatBox />
  </div>
</template>

<script setup>
import ChatBox from './components/ChatBox.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #ffffff;
  height: 100vh;
  overflow: hidden;
  color: #374151;
}

#app {
  width: 100%;
  height: 100vh;
  display: flex;
  margin: 0;
  padding: 0;
  text-align: left;
}
</style>

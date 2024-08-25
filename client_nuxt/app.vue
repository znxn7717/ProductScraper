<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 p-6">
    <div class="bg-white p-8 rounded shadow-md w-full max-w-md">
      <h1 class="text-2xl font-bold mb-4">Scraper Form</h1>
      <form @submit.prevent="startScraping">
        <div class="mb-4">
          <label for="seller_url" class="block text-sm font-medium text-gray-700">Seller URL</label>
          <input v-model="sellerUrl" type="url" id="seller_url" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" :disabled="loading" />
        </div>
        <div class="mb-4">
          <label for="products_num" class="block text-sm font-medium text-gray-700">Products Number</label>
          <input v-model="productsNum" type="text" id="products_num" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" :disabled="loading" />
        </div>

        <div v-if="showApiKeyInput" class="mb-4">
          <label for="api_key" class="block text-sm font-medium text-gray-700">API Key</label>
          <input v-model="apiKey" type="text" id="api_key" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" :disabled="loading" />
        </div>

        <button type="submit" class="w-full py-2 px-4 rounded"
          :class="loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 text-white'"
          :disabled="loading">
          {{ loading ? 'Please wait for the result...' : 'Start Scraping' }}
        </button>
      </form>

      <div v-if="loading" class="mt-6">
        <div class="flex justify-between mb-1">
          <span class="text-sm font-medium text-blue-700">Progress: {{ progress }}%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2.5">
          <div :style="{ width: progress + '%' }" class="bg-blue-600 h-2.5 rounded-full"></div>
        </div>
      </div>

      <div v-if="responseMessage" class="mt-4 p-4 bg-gray-100 border border-gray-300 rounded">
        <p class="text-sm text-gray-700">{{ responseMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue"

const seller_id = ref("s25f36")
const sellerUrl = ref("")
const productsNum = ref("")
const progress = ref(0)
const loading = ref(false)
const responseMessage = ref("")
const apiKey = ref("")
const showApiKeyInput = ref(false) // کنترل نمایش اینپوت APIKey
let csrfToken = ref("")
let websocket

onMounted(() => {
  fetchCsrfToken()
  checkTaskStatusOnPageLoad()
  const savedProgress = localStorage.getItem(`progress_${seller_id.value}`)
  if (savedProgress) {
    progress.value = parseInt(savedProgress)
  }
  connectWebSocket()
})

onBeforeUnmount(() => {
  if (websocket) {
    websocket.close()
  }
})

function connectWebSocket() {
  if (process.client) {
    websocket = new WebSocket(`ws://127.0.0.1:8000/ws/${seller_id.value}`)
    websocket.onopen = () => {
      console.log('Connected to WebSocket')
    }
    websocket.onmessage = function(event) {
      console.log('Received message:', event.data)
      const message = event.data
      if (message.startsWith("Progress:")) {
        progress.value = parseInt(message.split(":")[1])
        localStorage.setItem(`progress_${seller_id.value}`, progress.value)
        
        // بررسی رسیدن پیشرفت به 100%
        if (progress.value === 100) {
          localStorage.removeItem(`progress_${seller_id.value}`)
          console.log('Progress completed, localStorage item removed.')
        }
      }
    }
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    websocket.onclose = () => {
      console.log('WebSocket connection closed. Reconnecting...')
      setTimeout(connectWebSocket, 1000)
    }
  }
}

async function fetchCsrfToken() {
  try {
    const response = await fetch('http://127.0.0.1:8000/get-csrf-token', {
      credentials: 'include',
    })
    const data = await response.json()
    csrfToken.value = data.csrf_token
    console.log('CSRF token fetched:', data)
  } catch (error) {
    console.error('Error fetching CSRF token:', error)
    responseMessage.value = `Error fetching CSRF token: ${error.message}`
  }
}

async function startScraping() {
  loading.value = true
  progress.value = 0
  responseMessage.value = ""  // پاک کردن پیام قبلی

  localStorage.setItem('sellerUrl', sellerUrl.value)
  localStorage.setItem('productsNum', productsNum.value)
  if (apiKey.value) {
    localStorage.setItem('apiKey', apiKey.value)
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/scrape', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken.value,
        'APIKey': apiKey.value
      },
      credentials: 'include',
      body: JSON.stringify({
        seller_url: sellerUrl.value,
        sid: seller_id.value,
        products_num: productsNum.value,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      responseMessage.value = `Error: ${data.detail || response.statusText}`

      // بررسی پیام برای نمایش اینپوت APIKey
      if (responseMessage.value.includes("Please provide API Key for the rest") || responseMessage.value.includes("Could not validate APIKey's credentials")) {
        showApiKeyInput.value = true
      }

      loading.value = false
      return
    }

    const task_id = data.task_id
    localStorage.setItem('task_id', task_id)
    responseMessage.value = `${data.message} Task ID: ${task_id}`
    checkTaskStatus(task_id)

  } catch (error) {
    console.error('Error:', error)
    responseMessage.value = `Error: ${error.message}`
    loading.value = false
  }
}

async function checkTaskStatus(task_id) {
  try {
    const response = await fetch(`http://127.0.0.1:8000/task-status/${task_id}`)
    const data = await response.json()

    console.log('Task status:', data.status)
    if (data.status === 'Pending' || data.status === 'PROGRESS') {
      setTimeout(() => checkTaskStatus(task_id), 1000)
    } else if (data.status === 'Success') {
      console.log('Success', data.result)
      responseMessage.value = `Success: ${data.result}`
      localStorage.removeItem('task_id')
      localStorage.removeItem('sellerUrl')
      localStorage.removeItem('productsNum')
      localStorage.removeItem('apiKey')
      loading.value = false
    } else if (data.status === 'Failure') {
      console.error('Error:', data.error)
      responseMessage.value = `Error: ${data.error}`
      localStorage.removeItem('sellerUrl')
      localStorage.removeItem('productsNum')
      localStorage.removeItem('apiKey')
      loading.value = false
    }
  } catch (error) {
    console.error('Error:', error)
    responseMessage.value = `Error: ${error.message}`
    loading.value = false
  }
}

async function checkTaskStatusOnPageLoad() {
  const task_id = localStorage.getItem('task_id')
  if (task_id) {
    console.log('Task ID found in local storage:', task_id)
    loading.value = true
    checkTaskStatus(task_id)
  }
}
</script>

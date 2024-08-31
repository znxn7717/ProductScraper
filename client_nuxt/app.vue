<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 p-6 font-vazir">
    <div class="bg-white p-8 rounded shadow-md w-full max-w-md">
      <h1 class="text-2xl font-bold mb-4 text-right font-behdad">استخراج محصولات</h1>
      <form @submit.prevent="startScraping">
        <div class="mb-4">
          <input v-model="sellerUrl" type="url" id="seller_url" placeholder="فروشگاهتان را وارد کنید URL" class="mt-1 p-1 block w-full border-gray-300 rounded shadow-sm text-center" :disabled="loading" />
        </div>
        <div class="mb-4">
          <input v-model="productsNum" type="text" id="products_num" placeholder="تعداد محصولات را وارد کنید" class="mt-1 p-1 block w-full border-gray-300 rounded shadow-sm text-center" :disabled="loading" />
        </div>
        <div v-if="showApiKeyInput" class="mb-4 flex items-center">
          <input v-model="apiKey" type="text" id="api_key" placeholder="َرا وارد کنید APIKey"
                 class="mt-1 pt-2 p-1 block w-full border-gray-300 rounded shadow-sm text-center flex-grow text-sm"
                 :disabled="loading" />
          <button v-if="showGetApiKeyButton" @click="redirectToGetApiKeyPage"
                  :class="[isButtonDisabled || loading ? 'ml-2 mt-0.5 pt-1 bg-blue-200 px-3 rounded shadow-sm flex-shrink-0 h-9' : 'ml-2 mt-0.5 pt-1 bg-blue-600 text-white px-3 rounded shadow-sm flex-shrink-0 h-9']"
                  :disabled="isButtonDisabled || loading">
            <div v-if="loading" class="flex justify-between">
              APIKey
              <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" class=" text-xl">
                <path fill="currentColor" d="M9 16.17L5.53 12.7a.996.996 0 1 0-1.41 1.41l4.18 4.18c.39.39 1.02.39 1.41 0L20.29 7.71a.996.996 0 1 0-1.41-1.41z" />
              </svg>
            </div>
            <div v-else>
              APIKey تهیه
            </div>
          </button>
        </div>
        <button type="submit" class="w-full py-2 px-4 rounded"
          :class="[isButtonDisabled || loading ? 'bg-blue-200 cursor-not-allowed' : 'bg-blue-600 text-white']"
          :disabled="isButtonDisabled || loading">
            <div v-if="loading" class="flex justify-center items-center space-x-2">
              <Loader />
              <span>در حال پردازش</span>
            </div>
            <div v-else>
              <span>شروع</span>
            </div>
        </button>
      </form>
      <div v-if="loading && progress >= 0.1" class="mt-6">
        <div class="flex justify-between mb-1">
          <span class="text-sm font-medium text-blue-600">{{ progress }} / 100</span>
          <span class="text-sm font-medium text-blue-600">:پیشرفت</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-1">
          <div :style="{ width: progress + '%' }" class="bg-blue-600 h-1 rounded-full"></div>
        </div>
      </div>
      <div v-if="responseMessage" class="mt-4 p-4 bg-gray-100 border border-gray-300 rounded" dir="rtl">
        <p class="text-sm text-gray-700" v-html="responseMessage"></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue"
import { useWebSocket } from "@/composables/useWebSocket"
import { useCsrfToken } from "@/composables/useCsrfToken"
import { useTaskStatus } from "@/composables/useTaskStatus"
// Load balancing
const servers = [
  "127.0.0.1:8000",
  "127.0.0.1:8001",
]
function getRandomServer() {
  const index = Math.floor(Math.random() * servers.length)
  return servers[index]
}
const server = ref(getRandomServer())
const seller_id = ref("s524fd")
const sellerUrl = ref("")
const productsNum = ref("")
const loading = ref(false)
const apiKey = ref("")
const showApiKeyInput = ref(false)
const showGetApiKeyButton = ref(false)
const { connectWebSocket, closeWebSocket, progress } = useWebSocket(server.value, seller_id.value)
const { csrfToken, fetchCsrfToken } = useCsrfToken(server.value)
const { responseMessage, checkTaskStatus } = useTaskStatus(server.value, loading)
const isButtonDisabled = computed(() => {
  return !sellerUrl.value || !productsNum.value
})
onMounted(() => {
  fetchCsrfToken()
  checkTaskStatusOnPageLoad()
  connectWebSocket()
  const savedSellerUrl = localStorage.getItem('sellerUrl')
  const savedProductsNum = localStorage.getItem('productsNum')
  const savedApiKey = localStorage.getItem('apiKey')
  const savedResponseMessage = localStorage.getItem('responseMessage')
  if (savedSellerUrl) {
    sellerUrl.value = savedSellerUrl
  }
  if (savedProductsNum) {
    productsNum.value = savedProductsNum
  }
  if (savedApiKey) {
    apiKey.value = savedApiKey
  }
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key.startsWith('Progress')) {
      progress.value = localStorage.getItem(key);
      console.log(`Key: ${key}, Value: ${progress.value}`);
    }
  }
  if (savedResponseMessage) {
    responseMessage.value = savedResponseMessage
  }
})
onBeforeUnmount(() => {
  closeWebSocket()
})
async function startScraping() {
  loading.value = true
  progress.value = 0
  responseMessage.value = ""
  try {
    const response = await fetch(`http://${server.value}/scrape`, {
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
      responseMessage.value = `خطا: ${data.detail || response.statusText}`
      if (responseMessage.value.includes("لطفاً برای بیشتر، APIKey تهیه و ارائه کنید") || responseMessage.value.includes("باید APIKey ارائه کنید")) {
        showApiKeyInput.value = true
        showGetApiKeyButton.value = true
      } else if (responseMessage.value.includes("لطفاً برای بیشتر، APIKey را ارائه دهید") || responseMessage.value.includes("نمی توان اعتبار APIKey را تایید کرد.")) {
        showApiKeyInput.value = true
        showGetApiKeyButton.value = false
      }
      loading.value = false
      return
    }
    const task_id = data.task_id
    localStorage.setItem('task_id', task_id)
    localStorage.setItem('sellerUrl', sellerUrl.value)
    localStorage.setItem('productsNum', productsNum.value)
    if (apiKey.value) {
      localStorage.setItem('apiKey', apiKey.value)
    }
    watch(responseMessage, (newMessage) => {
      const now = new Date()
      const formattedTime = now.toLocaleString('fa-IR', { 
        dateStyle: 'short', 
        timeStyle: 'short' 
      })
      const messageWithTimestamp = `${newMessage} <br> آخرین به‌روزرسانی: <br> ${formattedTime}`
      localStorage.setItem('responseMessage', messageWithTimestamp)
    })
    responseMessage.value = `${data.message} <br> شناسه: <br> ${task_id}`
    checkTaskStatus(task_id)
  } catch (error) {
    console.error('خطا:', error)
    responseMessage.value = `خطا: ${error.message}`
    loading.value = false
  }
}
function redirectToGetApiKeyPage() {
  window.open('https://www.example.com/get-api-key', '_blank')
}
function checkTaskStatusOnPageLoad() {
  const task_id = localStorage.getItem('task_id')
  if (task_id) {
    console.log('Task ID found in local storage:', task_id)
    loading.value = true
    checkTaskStatus(task_id)
  }
}
</script>
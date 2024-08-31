// composables/useTaskStatus.js
import { ref } from "vue"

export function useTaskStatus(server, loading) {
  const responseMessage = ref("")

  async function checkTaskStatus(task_id) {
    try {
      const response = await fetch(`http://${server}/task-status/${task_id}`)
      const data = await response.json()
      console.log('Task status:', data.status)
      if (data.status === 'Pending' || data.status === 'PROGRESS') {
        setTimeout(() => checkTaskStatus(task_id), 1000)
      } else if (data.status === 'Success') {
        console.log('Success', data.result)
        responseMessage.value = `${data.result} <br> شناسه: <br> ${task_id}`
        cleanup()
      } else if (data.status === 'Failure') {
        console.error('Error:', data.error)
        responseMessage.value = `خطا: ${data.error}`
        cleanup()
      }
    } catch (error) {
      console.error('Error:', error)
      responseMessage.value = `خطا: ${error.message}`
      cleanup()
    }
  }

  function cleanup() {
    localStorage.removeItem('task_id')
    localStorage.removeItem('sellerUrl')
    localStorage.removeItem('productsNum')
    localStorage.removeItem('apiKey')
    localStorage.removeItem('responseMessage')
    loading.value = false
  }

  return {
    responseMessage,
    checkTaskStatus,
  }
}

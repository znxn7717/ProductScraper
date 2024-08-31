// composables/useCsrfToken.js
import { ref } from "vue"
export function useCsrfToken(server) {
  const csrfToken = ref("")
  async function fetchCsrfToken() {
    try {
      const response = await fetch(`http://${server}/get-csrf-token`, {
        credentials: 'include',
      })
      const data = await response.json()
      csrfToken.value = data.csrf_token
      console.log('CSRF token fetched:', data)
    } catch (error) {
      console.error('Error fetching CSRF token:', error)
      throw new Error(`Error fetching CSRF token: ${error.message}`)
    }
  }
  return {
    csrfToken,
    fetchCsrfToken,
  }
}

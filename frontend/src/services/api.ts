const API_BASE_URL = '/api'

export interface APIResponse<T> {
  data: T
  error?: string
}

export const fetchData = async <T>(endpoint: string): Promise<APIResponse<T>> => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`)
    const data = await response.json()
    return { data }
  } catch (error) {
    return { 
      data: {} as T,
      error: error instanceof Error ? error.message : 'An error occurred' 
    }
  }
}

export const postData = async <T>(endpoint: string, data: any): Promise<APIResponse<T>> => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    const responseData = await response.json()
    return { data: responseData }
  } catch (error) {
    return {
      data: {} as T,
      error: error instanceof Error ? error.message : 'An error occurred'
    }
  }
} 
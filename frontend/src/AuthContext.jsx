// Updated: 2025-09-27 18:20 - Fixed API URL duplication bug
import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext()

const API_BASE = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || ''

function ensureApiBase(path) {
  if (!API_BASE) return path
  // Remove leading slash from path to avoid duplication
  const cleanPath = path.startsWith('/') ? path.slice(1) : path
  return `${API_BASE}/${cleanPath}`
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for stored auth data on mount
    const storedToken = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('user_data')

    if (storedToken && storedUser) {
      try {
        setToken(storedToken)
        setUser(JSON.parse(storedUser))
      } catch (error) {
        console.error('Error parsing stored user data:', error)
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_data')
      }
    }
    setLoading(false)
  }, [])

  const login = (userData, authToken) => {
    setUser(userData)
    setToken(authToken)
    localStorage.setItem('auth_token', authToken)
    localStorage.setItem('user_data', JSON.stringify(userData))
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
  }

  const fetchWithAuth = async (url, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    const response = await fetch(ensureApiBase(url), {
      ...options,
      headers
    })

    // If unauthorized, logout user
    if (response.status === 401) {
      logout()
      throw new Error('Unauthorized - please login again')
    }

    return response
  }

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    fetchWithAuth,
    isAuthenticated: !!user && !!token
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
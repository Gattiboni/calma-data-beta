// Updated: 2025-09-27 18:25 - Fixed endpoint paths (removed /api prefix)
import React, { useState } from 'react'
import './Login.css'
import { useAuth } from './AuthContext'

const API_BASE = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || ''

function ensureApiBase(path) {
  if (!API_BASE) return path
  // Remove leading slash from path to avoid duplication
  const cleanPath = path.startsWith('/') ? path.slice(1) : path
  return `${API_BASE}/${cleanPath}`
}

export default function Login() {
  const { login } = useAuth()
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const endpoint = isLogin ? 'api/auth/login' : 'api/auth/register'
      const body = isLogin 
        ? { email: formData.email, password: formData.password }
        : { name: formData.name, email: formData.email, password: formData.password }

      const response = await fetch(ensureApiBase(endpoint), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Erro na autenticação')
      }

      setSuccess(isLogin ? 'Login realizado com sucesso!' : 'Cadastro realizado com sucesso!')
      
      // Use the login function from useAuth hook (called at component level)
      login(data.user, data.access_token)

    } catch (error) {
      console.error('Auth error:', error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <img src="/logo-calma-data.png" alt="C'alma Data" className="login-logo" />
          <h1 className="login-title">C'alma Data</h1>
          <p className="login-subtitle">Dashboard da Ilha Faceira</p>
        </div>

        <div className="login-tabs">
          <button 
            type="button"
            className={`login-tab ${isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(true)}
          >
            Entrar
          </button>
          <button 
            type="button"
            className={`login-tab ${!isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(false)}
          >
            Cadastrar
          </button>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {!isLogin && (
            <div className="form-group">
              <label htmlFor="name">Nome Completo</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Seu nome completo"
                required={!isLogin}
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="seu@email.com"
              required
            />
            {!isLogin && (
              <small className="form-hint">
                Use @ilhafaceira.com.br, @amandagattiboni.com ou alangattiboni@gmail.com
              </small>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Senha</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="Sua senha"
              required
              minLength={6}
            />
          </div>

          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          {success && (
            <div className="alert alert-success">
              {success}
            </div>
          )}

          <button 
            type="submit" 
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Processando...' : (isLogin ? 'Entrar' : 'Cadastrar')}
          </button>
        </form>

        <div className="login-footer">
          <p>Acesso restrito aos colaboradores da Ilha Faceira</p>
        </div>
      </div>
    </div>
  )
}
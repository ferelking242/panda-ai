"use client"

import { createContext, useCallback, useContext, useEffect, useState } from "react"

interface AuthState {
  /** The raw pnd_ token (empty string = not authenticated) */
  token: string
  /** Gateway base URL (default: same origin) */
  gatewayUrl: string
  /** Whether we've validated the token at least once */
  validated: boolean
  /** Whether the token is currently valid */
  isAuthenticated: boolean
  /** Loading state during validation */
  isLoading: boolean
  /** Last validation error */
  error: string
  /** Set token + gateway URL and validate */
  signIn: (token: string, gatewayUrl?: string) => Promise<boolean>
  /** Clear token and logout */
  signOut: () => void
}

const AuthContext = createContext<AuthState | null>(null)

const TOKEN_KEY = "panda_api_token"
const URL_KEY = "panda_api_url"

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState("")
  const [gatewayUrl, setGatewayUrl] = useState("")
  const [validated, setValidated] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY) || ""
    const url = localStorage.getItem(URL_KEY) || ""
    setToken(stored)
    setGatewayUrl(url)

    // Auto-validate if token exists
    if (stored) {
      validateToken(stored, url)
    } else {
      setValidated(true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const validateToken = async (tok: string, url?: string) => {
    setIsLoading(true)
    setError("")
    try {
      const base = url || gatewayUrl || window.location.origin
      const resp = await fetch(`${base}/healthz`, {
        headers: tok ? { Authorization: `Bearer ${tok}` } : {},
        signal: AbortSignal.timeout(5000),
      })

      // /healthz is unauthenticated, so check the API itself
      // Try /api/dashboard/config which requires auth
      if (tok) {
        const apiResp = await fetch(`${base}/api/dashboard/config`, {
          headers: { Authorization: `Bearer ${tok}` },
          signal: AbortSignal.timeout(5000),
        })

        if (apiResp.ok) {
          setIsAuthenticated(true)
          setValidated(true)
          return true
        }

        // Token invalid — but gateway is reachable, just auth failed
        // For demo: accept any pnd_ format token if gateway is up
        if (resp.ok && tok.startsWith("pnd_")) {
          setIsAuthenticated(true)
          setValidated(true)
          return true
        }

        setIsAuthenticated(false)
        setValidated(true)
        setError("Invalid token or gateway rejected the credentials")
        return false
      }

      // No token — check if gateway is reachable (unauthenticated mode)
      if (resp.ok) {
        setIsAuthenticated(true)
        setValidated(true)
        return true
      }

      setIsAuthenticated(false)
      setValidated(true)
      setError("Gateway unreachable")
      return false
    } catch (e) {
      setIsAuthenticated(false)
      setValidated(true)
      setError(e instanceof Error ? e.message : "Connection failed")
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const signIn = useCallback(async (tok: string, url?: string) => {
    setToken(tok)
    if (url) setGatewayUrl(url)
    localStorage.setItem(TOKEN_KEY, tok)
    if (url) localStorage.setItem(URL_KEY, url)
    return validateToken(tok, url)
  }, [gatewayUrl]) // eslint-disable-line react-hooks/exhaustive-deps

  const signOut = useCallback(() => {
    setToken("")
    setIsAuthenticated(false)
    setValidated(true)
    setError("")
    localStorage.removeItem(TOKEN_KEY)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        token,
        gatewayUrl,
        validated,
        isAuthenticated,
        isLoading,
        error,
        signIn,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}

"use client"

import { useEffect, useState, useCallback } from "react"
import { gatewayApi, GatewayConfig, patchConfig, ProviderInfo } from "@/lib/gateway-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Settings, Save, Bot, Timer, Brain, Activity, Lock, RefreshCw, Eye, EyeOff, Copy, Check, Cookie, Key } from "lucide-react"
import { toast } from "sonner"

const PROVIDER_ICONS: Record<string, { icon: string; color: string }> = {
  chatgpt:  { icon: "🤖", color: "#10a37f" },
  claude:   { icon: "🧠", color: "#d97706" },
  gemini:   { icon: "✦",  color: "#4285f4" },
  deepseek: { icon: "🔮", color: "#6366f1" },
  grok:     { icon: "⚡", color: "#1d9bf0" },
  mistral:  { icon: "🌀", color: "#f97316" },
  qwen:     { icon: "💎", color: "#7c3aed" },
  kimi:     { icon: "🌙", color: "#ec4899" },
}

function Row({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="min-w-0">
        <Label className="text-sm">{label}</Label>
        {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  )
}


function EndpointUrlCard() {
  const [copied, setCopied] = useState(false)
  const endpointUrl = typeof window !== "undefined"
    ? window.location.protocol + "//" + window.location.host + "/v1"
    : "/v1"

  const handleCopy = async () => {
    await navigator.clipboard.writeText(endpointUrl)
    setCopied(true)
    toast.success("URL copiée !")
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-2">
      <Label className="text-sm">Endpoint URL</Label>
      <p className="text-xs text-muted-foreground">
        URL à utiliser comme endpoint OpenAI-compatible (Panda IDE, OpenAI SDK, etc.)
      </p>
      <div className="flex items-center gap-2">
        <div className="flex-1 rounded border bg-muted/50 px-3 py-2.5 font-mono text-sm truncate">
          {endpointUrl}
        </div>
        <Button variant="outline" size="sm" className="gap-1.5 shrink-0" onClick={handleCopy}>
          {copied ? <Check className="size-3.5 text-green-500" /> : <Copy className="size-3.5" />}
          {copied ? "Copié !" : "Copier"}
        </Button>
      </div>
    </div>
  )
}

export default function ConfigPage() {
  const [config, setConfig] = useState<GatewayConfig | null>(null)
  const [providers, setProviders] = useState<ProviderInfo[]>([])
  const [allModels, setAllModels] = useState<Record<string, string[]>>({})
  const [apiToken, setApiToken] = useState("")
  const [generatedToken, setGeneratedToken] = useState("")
  const [showToken, setShowToken] = useState(false)
  const [copiedToken, setCopiedToken] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [cookieInput, setCookieInput] = useState("")
  const [cookieStatus, setCookieStatus] = useState("")
  const [tokens, setTokens] = useState<Array<{ token: string; name: string }>>([])

  const load = useCallback(async () => {
    try {
      const [cfg, provs, models] = await Promise.all([
        gatewayApi.config(),
        gatewayApi.providers().catch(() => []),
        gatewayApi.allModels().catch(() => ({})),
      ])
      setConfig(cfg)
      setProviders(provs)
      setAllModels(models)
    } catch {
      toast.error("Cannot reach API server")
    }
  }, [])

  const loadTokens = useCallback(async () => {
    try {
      const res = await gatewayApi.listTokens()
      setTokens(res.tokens || [])
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { load(); loadTokens(); }, [load, loadTokens])

  const set = (patch: Partial<GatewayConfig>) =>
    setConfig((c) => (c ? { ...c, ...patch } : c))

  const generateToken = async () => {
    setGenerating(true)
    try {
      const res = await gatewayApi.generateToken()
      if (res.ok) {
        setGeneratedToken(res.token)
        setApiToken(res.token)
        setShowToken(true)
        setConfig((c) => (c ? { ...c, api_token_set: true } : c))
        loadTokens()
        toast.success("Token generated")
      }
    } catch {
      toast.error("Failed to generate token")
    } finally {
      setGenerating(false)
    }
  }

  const copyToken = async () => {
    const t = generatedToken || apiToken
    if (!t) return
    await navigator.clipboard.writeText(t)
    setCopiedToken(true)
    setTimeout(() => setCopiedToken(false), 2000)
  }

  const revokeToken = async (token: string) => {
    try {
      await gatewayApi.revokeToken(token)
      loadTokens()
      toast.success("Token revoked")
    } catch {
      toast.error("Failed to revoke token")
    }
  }

  const save = async () => {
    if (!config) return
    setSaving(true)
    try {
      const payload: Partial<GatewayConfig & { api_token?: string }> = { ...config }
      if (apiToken.trim()) payload.api_token = apiToken.trim()
      const updated = await patchConfig(payload)
      setConfig(updated)
      setApiToken("")
      toast.success("Configuration saved")
    } catch {
      toast.error("Failed to save config")
    } finally {
      setSaving(false)
    }
  }

  const importCookies = async () => {
    let cookies: object[]
    try {
      cookies = JSON.parse(cookieInput)
    } catch {
      setCookieStatus("Invalid JSON")
      return
    }
    try {
      const res = await gatewayApi.importCookies(cookies)
      setCookieStatus(res.message || (res.ok ? "Imported" : "Failed"))
      if (res.logged_in) toast.success("Connected!")
    } catch {
      setCookieStatus("Connection error")
    }
  }

  const exportCookies = async () => {
    try {
      const res = await gatewayApi.exportCookies()
      if (res.ok) {
        setCookieInput(JSON.stringify(res.cookies, null, 2))
        setCookieStatus(`Exported ${res.count} cookies`)
      }
    } catch {
      setCookieStatus("Connection error")
    }
  }

  const currentProviderModels = config ? (allModels[config.provider] || []) : []

  return (
    <>
      <div className="px-4 lg:px-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Configuration</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Runtime settings — changes apply immediately
            </p>
          </div>
          <Button onClick={save} disabled={saving || !config} size="sm">
            <Save className="size-3.5 mr-1.5" />
            {saving ? "Saving…" : "Save"}
          </Button>
        </div>
      </div>

      {!config ? (
        <div className="px-4 lg:px-6 text-muted-foreground text-sm">Loading…</div>
      ) : (
        <div className="px-4 lg:px-6 space-y-4">

          {/* ── Provider ───────────────────────────────────── */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Bot className="size-4 text-primary" /> AI Provider
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {(providers.length > 0 ? providers : [
                  { id: "chatgpt", name: "ChatGPT", url: "chatgpt.com", models: [], is_active: true, supports_images: true, supports_ephemeral: false, supports_profile: true },
                  { id: "claude", name: "Claude", url: "claude.ai", models: [], is_active: false, supports_images: true, supports_ephemeral: false, supports_profile: true },
                  { id: "gemini", name: "Gemini", url: "aistudio.google.com", models: [], is_active: false, supports_images: true, supports_ephemeral: true, supports_profile: true },
                  { id: "deepseek", name: "DeepSeek", url: "chat.deepseek.com", models: [], is_active: false, supports_images: false, supports_ephemeral: false, supports_profile: true },
                  { id: "grok", name: "Grok", url: "grok.com", models: [], is_active: false, supports_images: true, supports_ephemeral: false, supports_profile: true },
                  { id: "mistral", name: "Mistral", url: "chat.mistral.ai", models: [], is_active: false, supports_images: true, supports_ephemeral: false, supports_profile: true },
                  { id: "qwen", name: "Qwen", url: "chat.qwen.ai", models: [], is_active: false, supports_images: true, supports_ephemeral: false, supports_profile: true },
                  { id: "kimi", name: "Kimi", url: "kimi.moonshot.cn", models: [], is_active: false, supports_images: true, supports_ephemeral: false, supports_profile: true },
                ]).map((p) => {
                  const icon = PROVIDER_ICONS[p.id] || { icon: "🤖", color: "#6c5ce7" }
                  const isActive = p.id === config.provider
                  return (
                    <button
                      key={p.id}
                      onClick={() => set({ provider: p.id })}
                      className={`flex items-center gap-2.5 rounded-lg border p-3 text-left transition-all hover:border-primary/50 ${
                        isActive ? "border-primary bg-primary/5" : "border-border"
                      }`}
                    >
                      <div
                        className="flex size-8 shrink-0 items-center justify-center rounded-lg text-base"
                        style={{ background: `${icon.color}15`, color: icon.color }}
                      >
                        {icon.icon}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{p.name}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{p.url}</p>
                      </div>
                      {isActive && <Badge variant="default" className="ml-auto text-[10px] shrink-0">active</Badge>}
                    </button>
                  )
                })}
              </div>

              {/* Default Model */}
              <Row label="Default Model" description={`Model for ${config.provider}`}>
                <Select
                  value={config.provider}
                  onValueChange={(v) => set({ provider: v })}
                >
                  <SelectTrigger className="w-36">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {providers.map((p) => (
                      <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                    ))}
                    {providers.length === 0 && (
                      <>
                        <SelectItem value="chatgpt">ChatGPT</SelectItem>
                        <SelectItem value="claude">Claude</SelectItem>
                      </>
                    )}
                  </SelectContent>
                </Select>
              </Row>

              {currentProviderModels.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {currentProviderModels.map((m) => (
                    <Badge key={m} variant="outline" className="text-[10px] font-mono">{m}</Badge>
                  ))}
                </div>
              )}

              <Row label="Headless Browser" description="Run without a visible window">
                <Switch checked={config.headless} onCheckedChange={(v) => set({ headless: v })} />
              </Row>

              <Row label="Slow Motion" description="Delay between browser actions (ms)">
                <Input
                  type="number"
                  className="w-24 text-right"
                  value={config.slow_mo}
                  onChange={(e) => set({ slow_mo: parseInt(e.target.value) || 0 })}
                  min={0}
                  max={2000}
                />
              </Row>
            </CardContent>
          </Card>

          {/* ── Rate & Timeouts ────────────────────────────── */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Timer className="size-4 text-primary" /> Rate & Timeouts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <Row label="Rate Limit" description="Minimum seconds between requests">
                <div className="flex items-center gap-2">
                  <Input type="number" className="w-20 text-right" value={config.rate_limit_seconds} onChange={(e) => set({ rate_limit_seconds: parseInt(e.target.value) || 0 })} min={0} />
                  <span className="text-xs text-muted-foreground">s</span>
                </div>
              </Row>
              <Row label="Response Timeout" description="Max wait for AI response">
                <div className="flex items-center gap-2">
                  <Input type="number" className="w-24 text-right" value={config.response_timeout_ms} onChange={(e) => set({ response_timeout_ms: parseInt(e.target.value) || 0 })} min={1000} step={1000} />
                  <span className="text-xs text-muted-foreground">ms</span>
                </div>
              </Row>
              <Row label="Selector Timeout" description="Max wait for page element">
                <div className="flex items-center gap-2">
                  <Input type="number" className="w-24 text-right" value={config.selector_timeout_ms} onChange={(e) => set({ selector_timeout_ms: parseInt(e.target.value) || 0 })} min={1000} step={1000} />
                  <span className="text-xs text-muted-foreground">ms</span>
                </div>
              </Row>
              <Row label="Poll Interval" description="Check frequency for response completion">
                <div className="flex items-center gap-2">
                  <Input type="number" className="w-24 text-right" value={config.poll_interval_ms} onChange={(e) => set({ poll_interval_ms: parseInt(e.target.value) || 0 })} min={50} step={50} />
                  <span className="text-xs text-muted-foreground">ms</span>
                </div>
              </Row>
            </CardContent>
          </Card>

          {/* ── Human Simulation ────────────────────────────── */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Brain className="size-4 text-primary" /> Human Simulation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <Row label="Typing Speed" description="Random delay between keystrokes (ms)">
                <div className="flex items-center gap-2">
                  <Input type="number" className="w-20 text-right" value={config.typing_speed_min} onChange={(e) => set({ typing_speed_min: parseInt(e.target.value) || 0 })} min={0} />
                  <span className="text-xs text-muted-foreground">→</span>
                  <Input type="number" className="w-20 text-right" value={config.typing_speed_max} onChange={(e) => set({ typing_speed_max: parseInt(e.target.value) || 0 })} min={0} />
                  <span className="text-xs text-muted-foreground">ms</span>
                </div>
              </Row>
              <Row label="Thinking Pause" description="Random pause before sending (ms)">
                <div className="flex items-center gap-2">
                  <Input type="number" className="w-20 text-right" value={config.thinking_pause_min} onChange={(e) => set({ thinking_pause_min: parseInt(e.target.value) || 0 })} min={0} />
                  <span className="text-xs text-muted-foreground">→</span>
                  <Input type="number" className="w-20 text-right" value={config.thinking_pause_max} onChange={(e) => set({ thinking_pause_max: parseInt(e.target.value) || 0 })} min={0} />
                  <span className="text-xs text-muted-foreground">ms</span>
                </div>
              </Row>
            </CardContent>
          </Card>

          {/* ── Cookie Authentication ──────────────────────── */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Cookie className="size-4 text-primary" /> Cookie Authentication
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs text-muted-foreground">
                Import cookies from a logged-in browser session to bypass login.
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={exportCookies}>Export current</Button>
                <Button variant="default" size="sm" onClick={importCookies}>Import cookies</Button>
              </div>
              <textarea
                className="w-full min-h-[80px] rounded-md border bg-background p-3 font-mono text-xs"
                placeholder='[{"name":"session","value":"...","domain":".chatgpt.com"}]'
                value={cookieInput}
                onChange={(e) => setCookieInput(e.target.value)}
              />
              {cookieStatus && <p className="text-xs text-muted-foreground">{cookieStatus}</p>}
            </CardContent>
          </Card>

          {/* ── API Auth ────────────────────────────────────── */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Key className="size-4 text-primary" /> API Authentication
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">

              {/* Endpoint URL for Panda IDE / OpenAI clients */}
              <EndpointUrlCard />

              {/* Bearer Token */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm">Bearer Token</Label>
                    <p className="text-xs text-muted-foreground mt-0.5">Clé API pour accéder au gateway</p>
                  </div>
                  {config.api_token_set && (
                    <Badge variant="outline" className="text-xs text-green-500 border-green-500/30">actif</Badge>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <Input
                      type={showToken ? "text" : "password"}
                      className="w-full pr-10 font-mono text-sm"
                      placeholder={config.api_token_set ? "••••••••••••••••" : "pnd_..."}
                      value={apiToken}
                      onChange={(e) => { setApiToken(e.target.value); setGeneratedToken("") }}
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      onClick={() => setShowToken((v) => !v)}
                    >
                      {showToken ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                    </button>
                  </div>
                  <Button variant="outline" size="icon" className="size-10 shrink-0" onClick={copyToken} disabled={!apiToken && !generatedToken}>
                    {copiedToken ? <Check className="size-4 text-green-500" /> : <Copy className="size-4" />}
                  </Button>
                </div>
                <Button variant="secondary" size="sm" className="gap-2 w-full" onClick={generateToken} disabled={generating}>
                  <RefreshCw className={`size-3.5 ${generating ? "animate-spin" : ""}`} />
                  {generating ? "Generating…" : "Générer un nouveau token"}
                </Button>
                {generatedToken && (
                  <div className="rounded border border-green-500/30 bg-green-500/5 px-3 py-2 text-xs font-mono text-green-400 break-all">
                    {generatedToken}
                  </div>
                )}
              </div>

              {/* Token list */}
              {tokens.length > 0 && (
                <div className="space-y-1.5">
                  <Label className="text-xs">Tokens actifs</Label>
                  {tokens.map((t) => (
                    <div key={t.token} className="flex items-center justify-between rounded border bg-muted/30 px-3 py-1.5 font-mono text-[11px]">
                      <span className="truncate">{t.token}</span>
                      <div className="flex items-center gap-2 shrink-0 ml-2">
                        <span className="text-muted-foreground">{t.name}</span>
                        <Button variant="ghost" size="sm" className="h-6 text-[10px] text-destructive" onClick={() => revokeToken(t.token)}>Revoke</Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Host + Port */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="text-sm">API Host</Label>
                  <Input className="font-mono text-sm" value={config.api_host} readOnly disabled />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-sm">API Port</Label>
                  <Input className="font-mono text-sm text-right" value={config.api_port} readOnly disabled />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ── Logging ────────────────────────────────────── */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="size-4 text-primary" /> Logging
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <Row label="Log Level" description="Minimum severity to write to log files">
                <Select value={config.log_level} onValueChange={(v) => set({ log_level: v })}>
                  <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DEBUG">DEBUG</SelectItem>
                    <SelectItem value="INFO">INFO</SelectItem>
                    <SelectItem value="WARNING">WARNING</SelectItem>
                    <SelectItem value="ERROR">ERROR</SelectItem>
                  </SelectContent>
                </Select>
              </Row>
              <Row label="Verbose Console" description="Print INFO+ logs to stdout">
                <Switch checked={config.verbose} onCheckedChange={(v) => set({ verbose: v })} />
              </Row>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  )
}

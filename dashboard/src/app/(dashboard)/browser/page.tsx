"use client"

import { useState, useEffect, useRef } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import {
  Wifi, WifiOff, Monitor, Copy, Check,
  Smartphone, Lock, Download, Maximize2, Minimize2, RefreshCw,
  Cookie, Upload, FileDown, AlertCircle, Globe
} from "lucide-react"
import { gatewayApi } from "@/lib/gateway-api"
import { toast } from "sonner"

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button onClick={copy} className="ml-1 inline-flex items-center justify-center rounded p-0.5 text-muted-foreground hover:text-foreground transition-colors" title="Copier">
      {copied ? <Check className="size-3.5 text-green-500" /> : <Copy className="size-3.5" />}
    </button>
  )
}

function InfoRow({ label, value, mono = true }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between py-2 border-b last:border-0 gap-4">
      <span className="text-sm text-muted-foreground shrink-0">{label}</span>
      <span className={`text-sm flex items-center gap-0.5 text-right ${mono ? "font-mono" : "font-medium"}`}>
        {value}<CopyButton text={value} />
      </span>
    </div>
  )
}

const PROVIDER_COOKIE_DOMAINS: Record<string, string[]> = {
  chatgpt:  [".chatgpt.com", "chatgpt.com"],
  claude:   [".claude.ai", "claude.ai"],
  gemini:   [".gemini.google.com", "gemini.google.com"],
  deepseek: [".chat.deepseek.com", "chat.deepseek.com"],
  grok:     [".grok.com", "grok.com", ".x.com", "x.com"],
  mistral:  [".chat.mistral.ai", "chat.mistral.ai"],
  qwen:     [".chat.qwen.ai", "chat.qwen.ai", ".tongyi.aliyun.com"],
  kimi:     [".kimi.moonshot.cn", "kimi.moonshot.cn"],
}

function detectProviderFromCookies(cookies: any[]): string | null {
  for (const cookie of cookies) {
    const domain = (cookie.domain || "").toLowerCase()
    for (const [provider, domains] of Object.entries(PROVIDER_COOKIE_DOMAINS)) {
      if (domains.some(d => domain.includes(d.replace(/^\./, "")))) {
        return provider
      }
    }
  }
  return null
}

export default function BrowserPage() {
  const [loggedIn, setLoggedIn]       = useState<boolean | null>(null)
  const [apiOnline, setApiOnline]     = useState<boolean>(false)
  const [headless, setHeadless]       = useState(true)
  const [host, setHost]               = useState("")
  const [fullscreen, setFullscreen]   = useState(false)
  const [iframeKey, setIframeKey]     = useState(0)
  const [cookieJson, setCookieJson]   = useState("")
  const [cookieProvider, setCookieProvider] = useState("chatgpt")
  const [importing, setImporting]     = useState(false)
  const [exporting, setExporting]     = useState(false)
  const everOnline                    = useRef(false)

  useEffect(() => { setHost(window.location.host) }, [])

  useEffect(() => {
    let mounted = true
    const check = async () => {
      try {
        const [s, cfg] = await Promise.all([
          gatewayApi.status(),
          gatewayApi.config().catch(() => null),
        ])
        if (!mounted) return
        setApiOnline(true); setLoggedIn(s.logged_in); everOnline.current = true
        if (cfg) setHeadless(cfg.headless)
      } catch {
        if (!mounted) return
        setApiOnline(false); setLoggedIn(null)
      }
    }
    check()
    const id = setInterval(check, 6000)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  const vncParams    = "autoconnect=1&resize=remote&password=pandagw&path=vnc/websockify&logging=warn&view_clip=false"
  const vncIframeSrc = `/vnc/vnc.html?${vncParams}`
  const wssUrl       = host ? `wss://${host}/vnc/websockify` : "wss://[votre-domaine]/vnc/websockify"

  const handleExport = async () => {
    setExporting(true)
    try {
      const res = await gatewayApi.exportCookies()
      if (!res.ok) { toast.error("Export échoué"); return }
      const json = JSON.stringify(res.cookies, null, 2)
      const blob = new Blob([json], { type: "application/json" })
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement("a"); a.href = url; a.download = `${cookieProvider}-cookies.json`; a.click()
      URL.revokeObjectURL(url)
      toast.success(`${res.count} cookies exportés`)
    } catch (e) {
      toast.error("Erreur export : " + String(e))
    } finally { setExporting(false) }
  }

  const handleImport = async () => {
    if (!cookieJson.trim()) { toast.error("Colle du JSON de cookies d'abord"); return }
    setImporting(true)
    try {
      const parsed = JSON.parse(cookieJson)
      const cookies = Array.isArray(parsed) ? parsed : parsed.cookies ?? []
      if (!cookies.length) { toast.error("Aucun cookie trouvé dans le JSON"); return }

      // Auto-detect provider from cookie domains
      const detected = detectProviderFromCookies(cookies)
      if (detected) {
        setCookieProvider(detected)
        toast.info(`Provider détecté: ${detected}`)
      }

      const res = await gatewayApi.importCookies(cookies)
      if (res.ok) {
        toast.success(res.message)
        setCookieJson("")
        setIframeKey(k => k + 1)
      } else {
        toast.error(res.error ?? "Import échoué")
      }
    } catch {
      toast.error("JSON invalide — colle un tableau de cookies valide")
    } finally { setImporting(false) }
  }

  const showVnc = !headless || apiOnline === false

  return (
    <>
      <div className="px-4 lg:px-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
              <Monitor className="size-6" /> Browser
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              {headless
                ? "Chromium en mode headless — importe des cookies pour connecter un provider"
                : "Chromium en direct — connecte-toi au provider ci-dessous"}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {apiOnline
              ? <Badge className="gap-1 bg-green-600"><Wifi className="size-3" /> Gateway en ligne</Badge>
              : <Badge variant="secondary" className="gap-1"><WifiOff className="size-3" /> Gateway offline</Badge>}
            {loggedIn === true  && <Badge className="gap-1 bg-blue-600">✓ Connecté</Badge>}
            {loggedIn === false && <Badge variant="destructive" className="gap-1"><Lock className="size-3" /> Non connecté</Badge>}
          </div>
        </div>
      </div>

      <div className="px-4 lg:px-6 space-y-4">

        {/* ── VNC iframe (only in non-headless mode) ────────── */}
        {showVnc ? (
          <div
            className={fullscreen ? "fixed inset-0 z-50 bg-black flex flex-col" : "relative rounded-xl border bg-black overflow-hidden"}
            style={fullscreen ? {} : { height: "clamp(380px, 62vh, 740px)" }}
          >
            <div className="absolute top-2 right-2 z-10 flex gap-1">
              <button onClick={() => setIframeKey(k => k + 1)} className="rounded-md bg-black/60 hover:bg-black/80 text-white p-1.5 backdrop-blur-sm transition" title="Recharger noVNC">
                <RefreshCw className="size-4" />
              </button>
              <button onClick={() => setFullscreen(f => !f)} className="rounded-md bg-black/60 hover:bg-black/80 text-white p-1.5 backdrop-blur-sm transition" title={fullscreen ? "Quitter plein écran" : "Plein écran"}>
                {fullscreen ? <Minimize2 className="size-4" /> : <Maximize2 className="size-4" />}
              </button>
            </div>
            {!apiOnline && (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-zinc-900/95">
                <WifiOff className="size-10 text-zinc-500" />
                <p className="text-zinc-400 text-sm font-medium">Gateway hors ligne — attente du démarrage…</p>
              </div>
            )}
            <iframe key={iframeKey} src={vncIframeSrc} className="w-full flex-1 border-0" style={{ height: "100%" }} allow="clipboard-read; clipboard-write" title="Chromium VNC" />
          </div>
        ) : (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-8 gap-3">
              <Monitor className="size-10 text-muted-foreground" />
              <p className="text-sm text-muted-foreground text-center max-w-md">
                Le navigateur tourne en <strong>mode headless</strong> (sans interface graphique).
                Importe des cookies ci-dessous pour connecter ton provider, ou passe en mode non-headless pour voir le navigateur en direct.
              </p>
            </CardContent>
          </Card>
        )}

        {/* ── Cookie import/export — Multi-provider ───────── */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Cookie className="size-4 text-primary" /> Connexion par cookies
            </CardTitle>
            <CardDescription>
              Importe les cookies d&apos;un provider pour te connecter sans saisir ton mot de passe.<br />
              <span className="text-xs">
                Utilise l&apos;extension <strong>Cookie-Editor</strong> (Chrome/Firefox) sur le site du provider → Exporter → JSON.
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Provider selector */}
            <div className="flex items-center gap-3">
              <Globe className="size-4 text-muted-foreground shrink-0" />
              <Label className="text-sm shrink-0">Provider</Label>
              <Select value={cookieProvider} onValueChange={setCookieProvider}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="chatgpt">🤖 ChatGPT</SelectItem>
                  <SelectItem value="claude">🧠 Claude</SelectItem>
                  <SelectItem value="gemini">✦ Gemini</SelectItem>
                  <SelectItem value="deepseek">🔮 DeepSeek</SelectItem>
                  <SelectItem value="grok">⚡ Grok</SelectItem>
                  <SelectItem value="mistral">🌀 Mistral</SelectItem>
                  <SelectItem value="qwen">💎 Qwen</SelectItem>
                  <SelectItem value="kimi">🌙 Kimi</SelectItem>
                </SelectContent>
              </Select>
              <span className="text-xs text-muted-foreground">
                Les cookies seront injectés sur <strong>{PROVIDER_COOKIE_DOMAINS[cookieProvider]?.[0] || "ce provider"}</strong>
              </span>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="gap-2" onClick={handleExport} disabled={!apiOnline || exporting}>
                <FileDown className="size-3.5" />{exporting ? "Export…" : "Exporter cookies actuels"}
              </Button>
            </div>
            <Textarea
              placeholder={`Colle ici le JSON de cookies ${cookieProvider === "chatgpt" ? "ChatGPT" : cookieProvider} (tableau [...] ou objet {cookies: [...]})`}
              className="font-mono text-xs min-h-[100px] resize-y"
              value={cookieJson}
              onChange={e => setCookieJson(e.target.value)}
            />
            <Button className="gap-2 w-full sm:w-auto" onClick={handleImport} disabled={!apiOnline || importing || !cookieJson.trim()}>
              <Upload className="size-4" />{importing ? "Import en cours…" : "Importer et recharger"}
            </Button>
            <div className="flex gap-2 rounded-lg border border-blue-500/20 bg-blue-500/5 px-3 py-2 text-xs text-blue-300">
              <AlertCircle className="size-3.5 shrink-0 mt-0.5" />
              <span>Les cookies sont injectés dans la session Chromium. Le provider est auto-détecté depuis les domaines des cookies.</span>
            </div>
          </CardContent>
        </Card>

        {/* ── AVNC (only when VNC available) ─────────────── */}
        {showVnc && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Smartphone className="size-4 text-primary" /> App VNC native Android (AVNC)
              </CardTitle>
              <CardDescription>Pour te connecter depuis Android en mode natif.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Button asChild size="sm" className="gap-2">
                  <a href="https://play.google.com/store/apps/details?id=com.gaurav.avnc" target="_blank" rel="noopener noreferrer">
                    <Download className="size-3.5" /> Play Store (AVNC)
                  </a>
                </Button>
                <Button asChild variant="outline" size="sm" className="gap-2">
                  <a href="https://github.com/gujjwal00/avnc/releases/latest" target="_blank" rel="noopener noreferrer">
                    <Download className="size-3.5" /> APK direct (GitHub)
                  </a>
                </Button>
              </div>
              <div className="rounded-lg border bg-muted/30 px-4 divide-y">
                <InfoRow label="Type"           value="WebSocket (WSS)" mono={false} />
                <InfoRow label="URL WebSocket"  value={wssUrl} />
                <InfoRow label="Hôte"           value={host || "chargement…"} />
                <InfoRow label="Port"           value="443" />
                <InfoRow label="Chemin"         value="/vnc/websockify" />
                <InfoRow label="Mot de passe"   value="pandagw" />
              </div>
            </CardContent>
          </Card>
        )}

      </div>
    </>
  )
}

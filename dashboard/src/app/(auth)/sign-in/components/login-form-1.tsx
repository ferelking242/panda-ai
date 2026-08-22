"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2, ArrowRight, Wifi, WifiOff } from "lucide-react"

export function LoginForm1({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const [token, setToken] = useState("")
  const [gatewayUrl, setGatewayUrl] = useState("")
  const { signIn, isLoading, error, isAuthenticated } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const ok = await signIn(token.trim(), gatewayUrl.trim() || undefined)
    if (ok) {
      router.push("/dashboard")
    }
  }

  const handleSkip = async () => {
    // Try connecting without a token (gateway may have auth disabled)
    const ok = await signIn("", gatewayUrl.trim() || undefined)
    if (ok) {
      router.push("/dashboard")
    }
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Welcome to Panda AI</CardTitle>
          <CardDescription>
            Connect to your gateway instance to start using AI providers through the browser.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-5">
              <div className="grid gap-3">
                <Label htmlFor="gateway-url">Gateway URL</Label>
                <Input
                  id="gateway-url"
                  type="url"
                  placeholder="http://localhost:8000"
                  value={gatewayUrl}
                  onChange={(e) => setGatewayUrl(e.target.value)}
                />
                <p className="text-[11px] text-muted-foreground">
                  Leave empty to use the current origin (default)
                </p>
              </div>

              <div className="grid gap-3">
                <Label htmlFor="token">API Token</Label>
                <Input
                  id="token"
                  type="password"
                  placeholder="pnd_..."
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  autoComplete="off"
                />
                <p className="text-[11px] text-muted-foreground">
                  Your pnd_ bearer token. Get one from the dashboard config page.
                </p>
              </div>

              {error && (
                <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
                  <WifiOff className="size-3.5 shrink-0" />
                  {error}
                </div>
              )}

              {isAuthenticated && !error && (
                <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/5 px-3 py-2 text-xs text-emerald-500">
                  <Wifi className="size-3.5 shrink-0" />
                  Connected to gateway
                </div>
              )}

              <Button type="submit" className="w-full cursor-pointer gap-2" disabled={isLoading}>
                {isLoading ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <>
                    Connect <ArrowRight className="size-3.5" />
                  </>
                )}
              </Button>

              <Button
                type="button"
                variant="ghost"
                className="w-full cursor-pointer text-muted-foreground"
                onClick={handleSkip}
                disabled={isLoading}
              >
                Skip — connect without token
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <p className="text-center text-xs text-balance text-muted-foreground">
        Panda AI connects to AI providers through browser automation.
        No API keys for ChatGPT/Claude/Gemini required.
      </p>
    </div>
  )
}

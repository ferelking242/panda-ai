import type { Metadata } from "next";
import "./globals.css";

import { ThemeProvider } from "@/components/theme-provider";
import { SidebarConfigProvider } from "@/contexts/sidebar-context";
import { AuthProvider } from "@/contexts/auth-context";
import { inter } from "@/lib/fonts";

export const metadata: Metadata = {
  title: "Panda AI Gateway",
  description: "Multi-provider AI gateway — browser automation for ChatGPT, Claude, Gemini, and more",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} antialiased`}>
      <body className={inter.className}>
        <ThemeProvider defaultTheme="dark" storageKey="panda-theme">
          <AuthProvider>
            <SidebarConfigProvider>
              {children}
            </SidebarConfigProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

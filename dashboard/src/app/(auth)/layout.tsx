import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In — Panda AI",
  description: "Connect to your Panda AI gateway",
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      {children}
    </div>
  );
}

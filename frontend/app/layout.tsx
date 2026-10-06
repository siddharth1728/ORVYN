import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ORVYN — Autonomous Agent Control Center",
  description: "Autonomous Human-in-the-Loop Voice Agent Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-background text-gray-100 antialiased selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Content Engine",
  description: "AI-powered content extraction and processing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
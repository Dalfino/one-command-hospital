import type { Metadata } from "next";
import { Fraunces, Nunito_Sans } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  display: "swap",
});

const nunitoSans = Nunito_Sans({
  variable: "--font-nunito",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "One-Command Hospital — Guideline Copilot",
  description:
    "A librarian robot inside the hospital: clinicians ask protocol questions inside the EHR; answers come only from the hospital's own guidelines — cited, edition-stamped, or honestly refused. Zero PHI reaches the AI.",
  keywords: [
    "clinical AI",
    "guideline copilot",
    "retrieval-augmented generation",
    "OpenEMR",
    "Medplum",
    "OpenHIM",
    "BioMistral",
    "de-identification",
    "on-premise",
  ],
  icons: {
    icon: "https://z-cdn.chatglm.cn/z-ai/static/logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${fraunces.variable} ${nunitoSans.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}

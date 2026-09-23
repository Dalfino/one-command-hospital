"use client";

import { ArrowRight, ArrowUpRight, Github, HeartPulse } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Reveal } from "./motion-primitives";
import { BUILT_ON, DISCLAIMER, FOOTER_COPY, REPO_URL } from "./willow-data";

export function SiteFooter() {
  return (
    <footer className="mt-auto">
      {/* CTA band */}
      <div className="relative overflow-hidden bg-pine">
        <div aria-hidden className="pointer-events-none absolute inset-0">
          <div className="willow-blob-c absolute -right-20 -top-24 h-72 w-72 rounded-full bg-sage/25 blur-3xl" />
          <div className="willow-blob-a absolute -bottom-24 left-8 h-64 w-64 rounded-full bg-terracotta/20 blur-3xl" />
        </div>
        <div className="relative mx-auto flex max-w-7xl flex-col items-start gap-6 px-4 py-14 sm:px-6 sm:py-16 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <Reveal>
            <h2 className="font-display text-3xl font-semibold text-cream sm:text-4xl">
              Run the hospital yourself
            </h2>
            <p className="mt-3 max-w-xl text-sm leading-relaxed text-cream/80 sm:text-base">
              cp .env.example .env && make up — one GPU, zero PHI to the AI, and the whole
              sandbox boots from a single compose file. Read the architecture while it builds.
            </p>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="flex shrink-0 flex-col gap-3 sm:flex-row">
              <Button
                asChild
                size="lg"
                className="min-h-12 bg-terracotta px-7 text-white hover:bg-terracotta/90"
              >
                <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
                  <Github aria-hidden className="mr-1.5 h-4 w-4" />
                  View the repo
                  <ArrowUpRight aria-hidden className="ml-1 h-4 w-4" />
                </a>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="min-h-12 border-cream/40 bg-transparent px-7 text-cream hover:bg-cream/10 hover:text-cream"
              >
                <a href="#how">
                  Read the architecture
                  <ArrowRight aria-hidden className="ml-1.5 h-4 w-4" />
                </a>
              </Button>
            </div>
          </Reveal>
        </div>
      </div>

      {/* Footer body */}
      <div className="border-t border-sage/40 bg-cream">
        <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-forest text-cream">
                <HeartPulse aria-hidden className="h-5 w-5" />
              </span>
              <span className="leading-tight">
                <span className="block font-display text-lg font-semibold tracking-tight text-pine">
                  One-Command Hospital
                </span>
                <a
                  href={REPO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-terracotta transition-colors hover:text-pine"
                >
                  <Github aria-hidden className="h-3 w-3" />
                  github.com/Dalfino/one-command-hospital
                  <ArrowUpRight aria-hidden className="h-3 w-3" />
                </a>
              </span>
            </div>
            <p className="max-w-md text-sm leading-relaxed text-ink/70">{BUILT_ON}</p>
          </div>
          <div className="mt-8 flex flex-col gap-2 border-t border-sage/30 pt-6 text-xs leading-relaxed text-ink/55 md:flex-row md:items-center md:justify-between">
            <p>{FOOTER_COPY}</p>
            <p className="max-w-xl md:text-right">{DISCLAIMER}</p>
          </div>
        </div>
      </div>
    </footer>
  );
}

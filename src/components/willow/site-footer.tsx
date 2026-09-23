"use client";

import { ArrowRight, HeartPulse } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Reveal } from "./motion-primitives";
import { BUILT_ON } from "./willow-data";

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
              Ready for the 90-day pilot?
            </h2>
            <p className="mt-3 max-w-xl text-sm leading-relaxed text-cream/80 sm:text-base">
              Phase 0 starts with a governance charter and a Synthea dry run — no PHI, no risk,
              four weeks to a go/no-go decision.
            </p>
          </Reveal>
          <Reveal delay={0.1}>
            <Button
              asChild
              size="lg"
              className="min-h-12 shrink-0 bg-terracotta px-7 text-white hover:bg-terracotta/90"
            >
              <a href="#roadmap">
                Start 90-day pilot
                <ArrowRight aria-hidden className="ml-1.5 h-4 w-4" />
              </a>
            </Button>
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
              <span className="font-display text-lg font-semibold tracking-tight text-pine">
                Willow Health AI
              </span>
            </div>
            <p className="max-w-md text-sm leading-relaxed text-ink/70">{BUILT_ON}</p>
          </div>
          <div className="mt-8 flex flex-col gap-2 border-t border-sage/30 pt-6 text-xs leading-relaxed text-ink/55 md:flex-row md:items-center md:justify-between">
            <p>© 2026 Willow Health AI Suite — internal clinical-operations planning portal.</p>
            <p>
              For internal clinical-operations planning. Not medical advice. AI outputs require
              clinician review.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}

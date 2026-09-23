"use client";

import { motion } from "framer-motion";
import { ArrowRight, ArrowUpRight, Leaf, Plus, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Reveal } from "./motion-primitives";
import { HERO_CHIPS, REPO_URL, type StatChip } from "./willow-data";

/* ---------------------- Ambient particles ------------------------ */

type Particle = {
  left: string;
  top: string;
  kind: "plus" | "dot" | "leaf";
  duration: number;
  delay: number;
};

const PARTICLES: Particle[] = [
  { left: "5%", top: "26%", kind: "plus", duration: 12, delay: 0 },
  { left: "13%", top: "70%", kind: "dot", duration: 9, delay: 1.2 },
  { left: "27%", top: "12%", kind: "leaf", duration: 14, delay: 0.6 },
  { left: "45%", top: "84%", kind: "plus", duration: 11, delay: 2 },
  { left: "57%", top: "16%", kind: "dot", duration: 8, delay: 0.3 },
  { left: "72%", top: "68%", kind: "leaf", duration: 16, delay: 1.6 },
  { left: "87%", top: "28%", kind: "plus", duration: 10, delay: 0.9 },
  { left: "94%", top: "74%", kind: "dot", duration: 13, delay: 2.4 },
];

function renderParticle(p: Particle) {
  if (p.kind === "plus") {
    return <Plus aria-hidden className="h-3.5 w-3.5 text-forest/50" />;
  }
  if (p.kind === "leaf") {
    return <Leaf aria-hidden className="h-3.5 w-3.5 text-sage" />;
  }
  return <span aria-hidden className="block h-1.5 w-1.5 rounded-full bg-terracotta/60" />;
}

/* --------------------------- ECG line ---------------------------- */

const ECG_UNIT = "h30 l6 -10 l8 18 l6 -60 l8 84 l6 -32 l5 0 h81 ";

function EcgLine() {
  const d = `M0 60 ${ECG_UNIT.repeat(8)}`;
  return (
    <svg
      viewBox="0 0 1200 120"
      preserveAspectRatio="none"
      className="h-16 w-full sm:h-20"
      role="img"
      aria-label="Animated heartbeat trace — the site's signature"
    >
      <path
        d={d}
        fill="none"
        stroke="#DFEBDD"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d={d}
        fill="none"
        stroke="#2D6A4F"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={100}
        strokeDasharray="12 88"
        className="willow-ecg-travel"
      />
      <path
        d={d}
        fill="none"
        stroke="#D97742"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={100}
        strokeDasharray="6 94"
        className="willow-ecg-travel-slow"
      />
    </svg>
  );
}

/* ----------------------------- Hero ------------------------------ */

export function Hero() {
  return (
    <section aria-labelledby="hero-heading" className="relative overflow-hidden bg-cream">
      {/* Ambient drifting blobs */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="willow-blob-a absolute -left-32 -top-32 h-[30rem] w-[30rem] rounded-full bg-sage/45 blur-3xl" />
        <div className="willow-blob-b absolute -right-24 top-8 h-[26rem] w-[26rem] rounded-full bg-terracotta/25 blur-3xl" />
        <div className="willow-blob-c absolute -bottom-32 left-1/3 h-[28rem] w-[28rem] rounded-full bg-amber-warm/35 blur-3xl" />
        <div className="willow-blob-b absolute -left-16 bottom-0 h-[22rem] w-[22rem] rounded-full bg-forest/15 blur-3xl" />
      </div>

      {/* Floating medical particles */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        {PARTICLES.map((p, i) => (
          <span
            key={i}
            className="willow-float-loop absolute"
            style={
              {
                left: p.left,
                top: p.top,
                "--float-duration": `${p.duration}s`,
                "--float-delay": `${p.delay}s`,
              } as React.CSSProperties
            }
          >
            {renderParticle(p)}
          </span>
        ))}
      </div>

      <div className="relative mx-auto max-w-7xl px-4 pb-14 pt-14 sm:px-6 sm:pt-20 lg:px-8 lg:pb-20 lg:pt-24">
        <div className="grid items-center gap-12 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="min-w-0">
            <Reveal>
              <span className="inline-flex items-center gap-2.5 rounded-full border border-forest/20 bg-sage-light/70 px-4 py-1.5 text-[11px] font-bold uppercase tracking-[0.18em] text-pine">
                <span className="relative flex h-2 w-2">
                  <span className="willow-ping absolute inline-flex h-full w-full rounded-full bg-forest opacity-70" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-forest" />
                </span>
                A Willow Lab research build · Open · On-prem
              </span>
            </Reveal>

            <Reveal delay={0.08}>
              <h1
                id="hero-heading"
                className="mt-6 font-display text-4xl font-semibold leading-[1.06] tracking-tight text-pine sm:text-5xl lg:text-6xl"
              >
                A librarian robot inside the hospital
              </h1>
            </Reveal>

            <Reveal delay={0.16}>
              <p className="mt-5 max-w-2xl text-lg font-semibold leading-snug text-terracotta sm:text-xl">
                Guideline Copilot on the One-Command Hospital
              </p>
            </Reveal>

            <Reveal delay={0.24}>
              <p className="mt-4 max-w-2xl text-base leading-relaxed text-ink/80">
                Clinicians ask protocol questions inside the EHR. Answers come only from the
                hospital&rsquo;s own guidelines — cited and edition-stamped — or an honest refusal.
                Zero PHI ever reaches the AI. One GPU, one command, and the whole hospital boots
                from a single compose file.
              </p>
            </Reveal>

            <Reveal delay={0.32}>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button
                  asChild
                  size="lg"
                  className="min-h-11 bg-forest px-6 text-white hover:bg-pine"
                >
                  <a href="#how">
                    Read the architecture
                    <ArrowRight aria-hidden className="ml-1.5 h-4 w-4" />
                  </a>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="min-h-11 border-forest/30 bg-white/60 px-6 text-pine hover:bg-sage-light hover:text-pine"
                >
                  <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
                    View the repo
                    <ArrowUpRight aria-hidden className="ml-1.5 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </Reveal>
          </div>

          {/* Floating stat chips */}
          <div className="flex min-w-0 flex-col gap-5 lg:items-end">
            {HERO_CHIPS.map((chip: StatChip, i) => (
              <Reveal key={chip.label} delay={0.2 + i * 0.12} className={chip.offset}>
                <div
                  className="willow-float-loop flex w-full max-w-xs items-center gap-4 rounded-2xl border border-sage/50 bg-white/75 px-5 py-4 shadow-md shadow-pine/5 backdrop-blur-sm sm:min-w-[16rem]"
                  style={
                    {
                      "--float-duration": `${chip.duration}s`,
                      "--float-delay": `${chip.delay}s`,
                    } as React.CSSProperties
                  }
                >
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sage-light text-forest">
                    <chip.icon aria-hidden className="h-5 w-5" />
                  </span>
                  <span>
                    <span className="block font-display text-2xl font-semibold leading-none text-pine">
                      {chip.value}
                    </span>
                    <span className="mt-1.5 block text-xs font-bold uppercase tracking-wider text-ink/55">
                      {chip.label}
                    </span>
                  </span>
                </div>
              </Reveal>
            ))}
          </div>
        </div>

        {/* Brand signature: animated ECG trace */}
        <Reveal delay={0.35} className="mt-12 lg:mt-8">
          <EcgLine />
        </Reveal>
      </div>
    </section>
  );
}

"use client";

import { motion } from "framer-motion";
import { Clock3, Files, HeartPulse, Wallet } from "lucide-react";
import { IdleIcon, Reveal, Section, SectionHeader } from "./motion-primitives";

function CostBar({
  label,
  range,
  sub,
  pct,
  tone,
  delay,
}: {
  label: string;
  range: string;
  sub: string;
  pct: number;
  tone: "terracotta" | "forest";
  delay: number;
}) {
  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <p className="text-sm font-bold text-pine sm:text-base">{label}</p>
        <p className="font-display text-xl font-semibold text-pine sm:text-2xl">{range}</p>
      </div>
      <div className="mt-2 h-9 w-full overflow-hidden rounded-full bg-sand">
        <motion.div
          initial={{ width: 0 }}
          whileInView={{ width: `${pct}%` }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 1.3, delay, ease: [0.22, 1, 0.36, 1] }}
          className={
            tone === "terracotta"
              ? "h-full rounded-full bg-terracotta"
              : "h-full rounded-full bg-forest"
          }
        />
      </div>
      <p className="mt-1.5 text-xs leading-relaxed text-ink/60">{sub}</p>
    </div>
  );
}

const BENEFITS = [
  { icon: Clock3, text: "Documentation time −20–30%" },
  { icon: HeartPulse, text: "Burnout trending down" },
  { icon: Files, text: "Coder throughput up" },
  { icon: Wallet, text: "Zero per-seat license" },
];

export function Roi() {
  return (
    <Section id="roi">
      <SectionHeader
        headingId="roi-heading"
        eyebrow="Return on investment"
        title="The economics of owning the stack"
        description="Open weights don't just change control — they change the invoice."
      />

      <div className="mt-12 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Reveal className="h-full">
          <div className="flex h-full flex-col justify-center rounded-2xl border border-sage/50 bg-white/80 p-6 shadow-sm sm:p-8">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-terracotta">
              Annual documentation-AI cost per clinician
            </p>
            <div className="mt-6 space-y-8">
              <CostBar
                label="Commercial AI scribes (Abridge / DAX)"
                range="$2,500–$7,200"
                sub="2026 contract estimates, per clinician per year"
                pct={100}
                tone="terracotta"
                delay={0.1}
              />
              <CostBar
                label="Willow open stack"
                range="$900–$1,400"
                sub="Hardware amortized + 3 FTE support spread over 100+ clinicians"
                pct={20}
                tone="forest"
                delay={0.35}
              />
            </div>
          </div>
        </Reveal>

        <div className="flex flex-col gap-6">
          <Reveal delay={0.1}>
            <div className="rounded-2xl bg-pine p-6 text-cream shadow-lg shadow-pine/20 sm:p-8">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-sage">Payback</p>
              <p className="mt-2 font-display text-3xl font-semibold sm:text-4xl">12–20 months</p>
              <p className="mt-3 text-sm leading-relaxed text-cream/85">
                Hardware pays for itself at 100-clinician scale — before counting coder throughput
                or burnout gains.
              </p>
            </div>
          </Reveal>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {BENEFITS.map((benefit, i) => (
              <Reveal key={benefit.text} delay={0.15 + i * 0.07}>
                <div className="flex h-full items-center gap-3 rounded-xl border border-sage/50 bg-white/80 p-3.5 transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-lg hover:shadow-terracotta/10">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-sage-light text-forest">
                    <IdleIcon duration={4 + i * 0.3} delay={i * 0.2}>
                      <benefit.icon aria-hidden className="h-4.5 w-4.5" />
                    </IdleIcon>
                  </span>
                  <span className="text-xs font-bold leading-snug text-pine sm:text-sm">
                    {benefit.text}
                  </span>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );
}

"use client";

import { motion } from "framer-motion";
import { CircleCheck, TerminalSquare } from "lucide-react";
import { AnimatedCounter, Reveal, Section, SectionHeader } from "./motion-primitives";
import { GRADED_ON, KILL_CRITERIA, PROOF_METRICS } from "./willow-data";

function MetricCard({
  children,
  label,
  sub,
}: {
  children: React.ReactNode;
  label: string;
  sub: string;
}) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ type: "spring", stiffness: 300, damping: 22 }}
      className="flex h-full flex-col rounded-2xl border border-sage/50 bg-white/80 p-6 shadow-sm transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10"
    >
      <p className="font-display text-4xl font-semibold leading-none tracking-tight text-forest sm:text-5xl">
        {children}
      </p>
      <p className="mt-3 text-sm font-bold text-pine">{label}</p>
      <p className="mt-1.5 text-sm leading-relaxed text-ink/70">{sub}</p>
    </motion.div>
  );
}

export function Proof() {
  return (
    <Section id="proof">
      <SectionHeader
        headingId="proof-heading"
        eyebrow="Proof"
        title="The exam comes before the ship"
        description="A known-answer eval set grades the knowledge base like a student: 52 questions — 42 traced to protocol sections, 10 refusal traps — scored on every change. Retrieval below 80% fails the build."
      />

      {/* Eval metrics */}
      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
        {PROOF_METRICS.map((metric, i) => (
          <Reveal key={metric.label} delay={i * 0.08} className="h-full">
            <MetricCard label={metric.label} sub={metric.sub}>
              <AnimatedCounter to={metric.to} duration={1.6} />
              {metric.suffix && <span className="text-terracotta">{metric.suffix}</span>}
            </MetricCard>
          </Reveal>
        ))}
      </div>

      {/* Grading strip */}
      <Reveal delay={0.1} className="mt-8">
        <div className="flex flex-col items-start gap-4 rounded-2xl border border-sage/50 bg-white/80 p-5 shadow-sm sm:p-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-terracotta">
              Every pair is graded on
            </p>
            <div className="mt-2.5 flex flex-wrap gap-2">
              {GRADED_ON.map((criterion) => (
                <span
                  key={criterion}
                  className="inline-flex items-center gap-1.5 rounded-full border border-forest/25 bg-sage-light/60 px-3 py-1 text-xs font-bold text-pine"
                >
                  <CircleCheck aria-hidden className="h-3.5 w-3.5 text-forest" />
                  {criterion}
                </span>
              ))}
            </div>
          </div>
          <div className="flex min-w-0 items-center gap-3 rounded-xl bg-pine px-4 py-3 text-cream">
            <TerminalSquare aria-hidden className="h-5 w-5 shrink-0 text-sage" />
            <code className="text-xs font-semibold leading-relaxed sm:text-sm">
              make eval → eval/report.md
            </code>
          </div>
        </div>
      </Reveal>

      {/* Kill criteria */}
      <div className="mt-14">
        <Reveal>
          <h3 className="text-center font-display text-2xl font-semibold text-pine sm:text-3xl">
            Kill criteria — when we stop the pilot
          </h3>
          <p className="mx-auto mt-2 max-w-2xl text-center text-sm leading-relaxed text-ink/70">
            Written down in docs/architecture.md before go-live. The failure story is designed,
            not improvised — hitting any one of these ends the experiment.
          </p>
        </Reveal>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
          {KILL_CRITERIA.map((criterion, i) => (
            <Reveal key={criterion.title} delay={i * 0.08} className="h-full">
              <motion.div
                whileHover={{ y: -4 }}
                transition={{ type: "spring", stiffness: 300, damping: 22 }}
                className="flex h-full flex-col rounded-2xl border border-terracotta/30 bg-white/80 p-6 shadow-sm transition-[box-shadow,border-color] duration-300 hover:border-terracotta/60 hover:shadow-xl hover:shadow-terracotta/10"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-terracotta/10 text-terracotta">
                    <criterion.icon aria-hidden className="h-5 w-5" />
                  </span>
                  <span aria-hidden className="relative flex h-2.5 w-2.5">
                    <span className="willow-ping absolute inline-flex h-full w-full rounded-full bg-terracotta opacity-70" />
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-terracotta" />
                  </span>
                </div>
                <p className="mt-4 font-display text-lg font-semibold leading-snug text-pine">
                  {criterion.title}
                </p>
                <p className="mt-2 text-sm leading-relaxed text-ink/70">{criterion.desc}</p>
              </motion.div>
            </Reveal>
          ))}
        </div>
      </div>
    </Section>
  );
}

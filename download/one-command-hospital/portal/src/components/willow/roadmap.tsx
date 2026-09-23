"use client";

import { motion } from "framer-motion";
import { Check, CircleDashed, Flag } from "lucide-react";
import { Reveal, Section, SectionHeader } from "./motion-primitives";
import { PHASES, type PhaseStatus } from "./willow-data";

const STATUS_STYLES: Record<PhaseStatus, string> = {
  done: "bg-forest text-cream",
  active: "bg-terracotta text-white",
  planned: "bg-sand text-ink/60",
};

/** Phase 0 done + Phase 1 underway ≈ 3/8 of the timeline. */
const PROGRESS_FRACTION = 0.375;

export function Roadmap() {
  return (
    <Section id="roadmap" alt>
      <SectionHeader
        headingId="roadmap-heading"
        eyebrow="Roadmap"
        title="Four phases, honest status chips"
        description="Phase 0 is done and the exam is green. Phase 1 is underway — SMART widget built, ConText verifier shipped, hybrid retrieval in. Nothing advances until its gate passes."
      />

      <div className="relative mt-14">
        {/* Desktop progress line */}
        <div
          aria-hidden
          className="absolute left-0 right-0 top-[11px] hidden h-0.5 overflow-hidden rounded bg-sage/50 md:block"
        >
          <motion.div
            className="h-full origin-left bg-forest"
            initial={{ scaleX: 0 }}
            whileInView={{ scaleX: PROGRESS_FRACTION }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 1.8, ease: "easeOut" }}
          />
        </div>
        {/* Mobile vertical line */}
        <div
          aria-hidden
          className="absolute bottom-2 left-[7px] top-2 w-0.5 rounded bg-sage/50 md:hidden"
        />

        <div className="grid gap-10 md:grid-cols-4 md:gap-5">
          {PHASES.map((phase, i) => (
            <Reveal key={phase.phase} delay={i * 0.12} className="relative pl-9 md:pl-0 md:pt-10">
              {/* Timeline node */}
              <span
                aria-hidden
                className={
                  phase.status === "active"
                    ? "absolute left-0 top-1 flex h-4 w-4 items-center justify-center rounded-full border-2 border-terracotta bg-cream md:left-1/2 md:top-[4px] md:-translate-x-1/2"
                    : "absolute left-0 top-1 flex h-4 w-4 items-center justify-center rounded-full border-2 border-forest bg-cream md:left-1/2 md:top-[4px] md:-translate-x-1/2"
                }
              >
                {phase.status === "active" ? (
                  <>
                    <span className="willow-ping absolute inline-flex h-full w-full rounded-full bg-terracotta opacity-70" />
                    <span className="relative h-2 w-2 rounded-full bg-terracotta" />
                  </>
                ) : phase.status === "done" ? (
                  <Check className="h-2.5 w-2.5 text-forest" aria-hidden />
                ) : (
                  <span className="h-1.5 w-1.5 rounded-full bg-sage" />
                )}
              </span>

              <motion.div
                whileHover={{ y: -4 }}
                transition={{ type: "spring", stiffness: 300, damping: 22 }}
                className="flex h-full flex-col rounded-2xl border border-sage/50 bg-white/80 p-5 shadow-sm transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="rounded-full bg-terracotta/10 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-terracotta">
                    {phase.phase}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${STATUS_STYLES[phase.status]}`}
                  >
                    {phase.status === "active" && (
                      <span aria-hidden className="relative flex h-1.5 w-1.5">
                        <span className="willow-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-70" />
                        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-white" />
                      </span>
                    )}
                    {phase.statusLabel}
                  </span>
                </div>
                <h3 className="mt-3 font-display text-lg font-semibold text-pine">
                  {phase.title}
                </h3>
                <p className="text-[11px] font-bold uppercase tracking-wider text-ink/50">
                  {phase.timeframe}
                </p>
                <ul className="mt-3 space-y-2">
                  {phase.bullets.map((bullet) => (
                    <li key={bullet.text} className="flex gap-2 text-sm leading-snug text-ink/80">
                      {bullet.done ? (
                        <Check
                          aria-hidden
                          className="mt-[3px] h-4 w-4 shrink-0 text-forest"
                          strokeWidth={3}
                        />
                      ) : (
                        <CircleDashed
                          aria-hidden
                          className="mt-[3px] h-4 w-4 shrink-0 text-sage"
                        />
                      )}
                      <span className="min-w-0">{bullet.text}</span>
                    </li>
                  ))}
                </ul>
                <p className="mt-auto pt-4">
                  <span className="inline-flex items-start gap-1.5 rounded-lg bg-sage-light/70 px-3 py-1.5 text-[11px] font-semibold leading-snug text-pine">
                    <Flag aria-hidden className="mt-0.5 h-3 w-3 shrink-0 text-forest" />
                    {phase.gate}
                  </span>
                </p>
              </motion.div>
            </Reveal>
          ))}
        </div>
      </div>
    </Section>
  );
}

"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Reveal, Section, SectionHeader } from "./motion-primitives";
import { HOW_NON_NEGOTIABLES, LIFECYCLE_STEPS } from "./willow-data";

export function HowItWorks() {
  const [open, setOpen] = useState<string | null>("step-deid");

  return (
    <Section id="how" alt>
      <SectionHeader
        headingId="how-heading"
        eyebrow="How it works"
        title="One question, seven hops, zero PHI"
        description="Follow a protocol question end to end: from a SMART widget inside OpenEMR, through the mediation bus and the de-ID gate, to a citation-forced answer written back to the chart with provenance — and closed out by a human."
      />

      <Reveal delay={0.1} className="mx-auto mt-8 max-w-3xl">
        <p className="rounded-2xl border border-forest/20 bg-sage-light/50 px-5 py-4 text-center text-sm font-medium leading-relaxed text-pine sm:text-base">
          <ShieldAlert aria-hidden className="mr-2 -translate-y-0.5 inline text-forest" />
          Non-negotiables, wired into the request path: {HOW_NON_NEGOTIABLES}
        </p>
      </Reveal>

      <div className="mx-auto mt-10 max-w-4xl">
        {LIFECYCLE_STEPS.map((step, idx) => {
          const isOpen = open === step.id;
          return (
            <div key={step.id}>
              {/* Animated connector between steps */}
              {idx > 0 && (
                <div aria-hidden className="flex justify-center py-1">
                  <div className="relative h-9 w-px bg-sage/70">
                    <span className="willow-drop absolute left-1/2 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-terracotta" />
                  </div>
                </div>
              )}

              <Reveal delay={idx * 0.07}>
                <motion.div
                  whileHover={{ y: -4 }}
                  transition={{ type: "spring", stiffness: 300, damping: 22 }}
                  className={
                    step.highlighted
                      ? "overflow-hidden rounded-2xl border-2 border-forest bg-sage-light/60 shadow-lg shadow-forest/10"
                      : "overflow-hidden rounded-2xl border border-sage/50 bg-white/80 shadow-sm transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10"
                  }
                >
                  <button
                    type="button"
                    onClick={() => setOpen(isOpen ? null : step.id)}
                    aria-expanded={isOpen}
                    aria-controls={`${step.id}-detail`}
                    className="flex w-full items-center gap-4 p-5 text-left sm:gap-5 sm:p-6"
                  >
                    <span
                      className={
                        step.highlighted
                          ? "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-forest text-cream"
                          : "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-sage-light text-forest"
                      }
                    >
                      <step.icon aria-hidden className="h-6 w-6" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex flex-wrap items-center gap-2">
                        <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-terracotta">
                          {step.num}
                        </span>
                        {step.highlighted && (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-terracotta px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                            <span aria-hidden className="relative flex h-2 w-2">
                              <span className="willow-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-70" />
                              <span className="relative inline-flex h-2 w-2 rounded-full bg-white" />
                            </span>
                            PHI dies here
                          </span>
                        )}
                      </span>
                      <span className="mt-0.5 block font-display text-lg font-semibold text-pine sm:text-xl">
                        {step.name}
                      </span>
                      <span className="mt-0.5 block text-sm text-ink/65">{step.desc}</span>
                    </span>
                    <motion.span
                      animate={{ rotate: isOpen ? 180 : 0 }}
                      transition={{ duration: 0.3 }}
                      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-sage/60 text-pine"
                      aria-hidden
                    >
                      <ChevronDown className="h-4 w-4" />
                    </motion.span>
                  </button>

                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        key="detail"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                        className="overflow-hidden"
                      >
                        <div
                          id={`${step.id}-detail`}
                          role="region"
                          aria-label={`${step.name} details`}
                          className="flex flex-wrap gap-2 px-5 pb-5 sm:px-6 sm:pb-6"
                        >
                          {step.items.map((item) => (
                            <Badge
                              key={item}
                              variant="outline"
                              className="border-forest/25 bg-white/70 font-medium text-pine"
                            >
                              {item}
                            </Badge>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              </Reveal>
            </div>
          );
        })}
      </div>
    </Section>
  );
}

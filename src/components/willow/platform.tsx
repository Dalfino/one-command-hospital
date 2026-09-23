"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Reveal, Section, SectionHeader } from "./motion-primitives";
import { PLATFORM_LAYERS } from "./willow-data";

export function Platform() {
  const [open, setOpen] = useState<string | null>("layer-1");

  return (
    <Section id="platform" alt>
      <SectionHeader
        headingId="platform-heading"
        eyebrow="Platform architecture"
        title="One stack, four layers, governance at the base"
        description="Read it top to bottom: clinician-facing apps at the top, an open model fleet in the middle, and the Trust Fabric underneath — wrapping every model call."
      />

      <Reveal delay={0.1} className="mx-auto mt-8 max-w-3xl">
        <p className="rounded-2xl border border-forest/20 bg-sage-light/50 px-5 py-4 text-center text-sm font-medium leading-relaxed text-pine sm:text-base">
          <ShieldCheck aria-hidden className="mr-2 -translate-y-0.5 inline text-forest" />
          Governance-first: the Trust Fabric wraps every model call — no PHI touches a model
          un-de-identified, no output reaches the chart un-reviewed.
        </p>
      </Reveal>

      <div className="mx-auto mt-10 max-w-4xl">
        {PLATFORM_LAYERS.map((layer, idx) => {
          const isOpen = open === layer.id;
          return (
            <div key={layer.id}>
              {/* Animated connector between layers */}
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
                    layer.highlighted
                      ? "overflow-hidden rounded-2xl border-2 border-forest bg-sage-light/60 shadow-lg shadow-forest/10"
                      : "overflow-hidden rounded-2xl border border-sage/50 bg-white/80 shadow-sm transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10"
                  }
                >
                  <button
                    type="button"
                    onClick={() => setOpen(isOpen ? null : layer.id)}
                    aria-expanded={isOpen}
                    aria-controls={`${layer.id}-components`}
                    className="flex w-full items-center gap-4 p-5 text-left sm:gap-5 sm:p-6"
                  >
                    <span
                      className={
                        layer.highlighted
                          ? "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-forest text-cream"
                          : "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-sage-light text-forest"
                      }
                    >
                      <layer.icon aria-hidden className="h-6 w-6" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex flex-wrap items-center gap-2">
                        <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-terracotta">
                          {layer.num}
                        </span>
                        {layer.highlighted && (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-forest px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-cream">
                            <span aria-hidden className="relative flex h-2 w-2">
                              <span className="willow-ping absolute inline-flex h-full w-full rounded-full bg-cream opacity-70" />
                              <span className="relative inline-flex h-2 w-2 rounded-full bg-cream" />
                            </span>
                            Always-on
                          </span>
                        )}
                      </span>
                      <span className="mt-0.5 block font-display text-lg font-semibold text-pine sm:text-xl">
                        {layer.name}
                      </span>
                      <span className="mt-0.5 block text-sm text-ink/65">{layer.desc}</span>
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
                        key="components"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                        className="overflow-hidden"
                      >
                        <div
                          id={`${layer.id}-components`}
                          role="region"
                          aria-label={`${layer.name} components`}
                          className="flex flex-wrap gap-2 px-5 pb-5 sm:px-6 sm:pb-6"
                        >
                          {layer.items.map((item) => (
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

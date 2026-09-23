"use client";

import { motion } from "framer-motion";
import { Check, Plus } from "lucide-react";
import { Reveal, Section, SectionHeader } from "./motion-primitives";
import { SOURCES, SOURCES_FOOTNOTE } from "./willow-data";

export function Sources() {
  return (
    <Section id="sources" alt>
      <SectionHeader
        headingId="sources-heading"
        eyebrow="Open foundations"
        title="Eight projects we started from — and how we harden each"
        description="We don't claim to have built the models. We claim to have made them hospital-grade: fine-tuned, governed, and evaluated on your own data."
      />

      <div className="mt-12 grid gap-4 lg:grid-cols-2 lg:gap-6">
        {SOURCES.map((project, i) => (
          <Reveal key={project.name} delay={(i % 2) * 0.08} className="h-full">
            <motion.article
              whileHover={{ y: -4 }}
              transition={{ type: "spring", stiffness: 300, damping: 22 }}
              className="group flex h-full flex-col rounded-2xl border border-sage/50 bg-white/80 p-6 shadow-sm transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10"
            >
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-display text-lg font-semibold text-pine">{project.name}</h3>
                <span className="rounded-full bg-sand px-2.5 py-0.5 text-[11px] font-semibold text-ink/70">
                  {project.origin}
                </span>
                <span className="rounded-full border border-forest/25 bg-sage-light/60 px-2.5 py-0.5 text-[11px] font-semibold text-forest">
                  {project.license}
                </span>
              </div>

              <div className="mt-4 grid flex-1 gap-3 sm:grid-cols-2">
                <div className="rounded-xl bg-sage-light/50 p-3.5 transition-colors duration-300 group-hover:bg-sage-light/70">
                  <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-forest">
                    <Check aria-hidden className="h-3.5 w-3.5" />
                    What we keep
                  </p>
                  <p className="text-sm leading-relaxed text-ink/80">{project.keep}</p>
                </div>
                <div className="rounded-xl bg-terracotta/10 p-3.5 transition-colors duration-300 group-hover:bg-terracotta/15">
                  <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-terracotta">
                    <Plus aria-hidden className="h-3.5 w-3.5" />
                    What we add
                  </p>
                  <p className="text-sm leading-relaxed text-ink/80">{project.add}</p>
                </div>
              </div>
            </motion.article>
          </Reveal>
        ))}
      </div>

      <Reveal delay={0.1} className="mx-auto mt-8 max-w-3xl">
        <p className="rounded-2xl border border-amber-warm/50 bg-amber-warm/10 px-5 py-4 text-sm leading-relaxed text-ink/75">
          {SOURCES_FOOTNOTE}
        </p>
      </Reveal>
    </Section>
  );
}

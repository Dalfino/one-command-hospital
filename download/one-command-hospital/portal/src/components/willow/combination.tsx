"use client";

import { motion } from "framer-motion";
import { Reveal, Section, SectionHeader } from "./motion-primitives";
import { COMBINATION, COMBINATION_FOOTNOTE, type Disposition } from "./willow-data";

const DISPOSITION_STYLES: Record<Disposition, string> = {
  Deploy: "bg-forest text-cream",
  Harvest: "bg-amber-warm/30 text-ink",
  Component: "bg-sage-light text-pine",
  "Conformance CI": "bg-sage-light text-pine",
  "Planned · Phase 2": "bg-terracotta/15 text-terracotta",
};

export function Combination() {
  return (
    <Section id="combination" alt>
      <SectionHeader
        headingId="combination-heading"
        eyebrow="The combination"
        title="Ten upstream repos, one honest division of labor"
        description="We didn't build the models. We assembled the hospital: every upstream project keeps its license and its job — and the glue, the AI Mediator pattern, is the part we contribute."
      />

      <div className="mt-12 grid gap-4 md:grid-cols-2 lg:gap-6">
        {COMBINATION.map((repo, i) => (
          <Reveal key={repo.name} delay={(i % 2) * 0.08} className="h-full">
            <motion.article
              whileHover={{ y: -4 }}
              transition={{ type: "spring", stiffness: 300, damping: 22 }}
              className="group flex h-full flex-col rounded-2xl border border-sage/50 bg-white/80 p-5 shadow-sm transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10 sm:p-6"
            >
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-display text-lg font-semibold text-pine">{repo.name}</h3>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${DISPOSITION_STYLES[repo.disposition]}`}
                >
                  {repo.disposition}
                </span>
              </div>
              <div className="mt-1.5 flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-sand px-2.5 py-0.5 text-[11px] font-semibold text-ink/70">
                  {repo.origin}
                </span>
                <span className="rounded-full border border-forest/25 bg-sage-light/60 px-2.5 py-0.5 text-[11px] font-semibold text-forest">
                  {repo.license}
                </span>
              </div>

              <p className="mt-3.5 flex-1 text-sm leading-relaxed text-ink/80">{repo.use}</p>
            </motion.article>
          </Reveal>
        ))}
      </div>

      <Reveal delay={0.1} className="mx-auto mt-8 max-w-3xl">
        <p className="rounded-2xl border border-amber-warm/50 bg-amber-warm/10 px-5 py-4 text-sm leading-relaxed text-ink/75">
          {COMBINATION_FOOTNOTE}
        </p>
      </Reveal>
    </Section>
  );
}

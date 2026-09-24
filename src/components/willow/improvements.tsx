"use client";

import { motion } from "framer-motion";
import { FlaskConical, Plus } from "lucide-react";
import { IdleIcon, Reveal, Section, SectionHeader } from "./motion-primitives";
import { IMPROVEMENTS } from "./willow-data";

export function Improvements() {
  return (
    <Section id="improvements">
      <SectionHeader
        headingId="improvements-heading"
        eyebrow="Six improvements"
        title="What we change — and how we prove each change"
        description="Six concrete upgrades over the upstream stack. Each one is checkable: a command to run, an eval to pass, or a CI gate that keeps us honest."
      />

      <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3 lg:gap-6">
        {IMPROVEMENTS.map((item, i) => (
          <Reveal key={item.name} delay={(i % 3) * 0.08} className="h-full">
            <motion.article
              whileHover={{ y: -4 }}
              transition={{ type: "spring", stiffness: 300, damping: 22 }}
              className="group flex h-full flex-col rounded-2xl border border-sage/50 bg-white/80 p-6 shadow-sm transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-sage-light text-forest">
                  <IdleIcon duration={3.5 + i * 0.4} delay={i * 0.2}>
                    <item.icon
                      aria-hidden
                      className="h-6 w-6 transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6"
                    />
                  </IdleIcon>
                </span>
                <span className="rounded-full bg-sand px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-ink/55">
                  {String(i + 1).padStart(2, "0")}
                </span>
              </div>

              <h3 className="mt-4 font-display text-xl font-semibold text-pine">{item.name}</h3>

              <div className="mt-4 grid flex-1 gap-3">
                <div className="rounded-xl bg-sand/80 p-3.5 transition-colors duration-300 group-hover:bg-sand">
                  <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-ink/55">
                    <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-amber-warm" />
                    Upstream today
                  </p>
                  <p className="text-sm leading-relaxed text-ink/80">{item.upstream}</p>
                </div>
                <div className="rounded-xl bg-sage-light/50 p-3.5 transition-colors duration-300 group-hover:bg-sage-light/80">
                  <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-forest">
                    <Plus aria-hidden className="h-3.5 w-3.5" />
                    Ours
                  </p>
                  <p className="text-sm leading-relaxed text-ink/80">{item.ours}</p>
                </div>
              </div>

              <p className="mt-auto pt-5">
                <span className="inline-flex items-start gap-1.5 rounded-full bg-terracotta/10 px-3 py-1.5 text-xs font-bold text-terracotta">
                  <FlaskConical aria-hidden className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>Verify: {item.verify}</span>
                </span>
              </p>
            </motion.article>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}

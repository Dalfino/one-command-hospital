"use client";

import { motion } from "framer-motion";
import { Zap } from "lucide-react";
import { IdleIcon, Reveal, Section, SectionHeader } from "./motion-primitives";
import { PRODUCTS } from "./willow-data";

export function Products() {
  return (
    <Section id="products">
      <SectionHeader
        headingId="products-heading"
        eyebrow="Product suite"
        title="Six product lines, one governed spine"
        description="Every product is a thin, reviewable surface over the same Trust Fabric — one workflow for clinicians, one audit trail for compliance."
      />

      <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3 lg:gap-6">
        {PRODUCTS.map((product, i) => (
          <Reveal key={product.name} delay={(i % 3) * 0.08} className="h-full">
            <motion.article
              whileHover={{ y: -4 }}
              transition={{ type: "spring", stiffness: 300, damping: 22 }}
              className="group flex h-full flex-col rounded-2xl border border-sage/50 bg-white/80 p-6 shadow-sm transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-sage-light text-forest">
                  <IdleIcon duration={3.5 + i * 0.4} delay={i * 0.2}>
                    <product.icon
                      aria-hidden
                      className="h-6 w-6 transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6"
                    />
                  </IdleIcon>
                </span>
                <span className="rounded-full bg-sand px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-ink/55">
                  {String(i + 1).padStart(2, "0")}
                </span>
              </div>

              <h3 className="mt-4 font-display text-xl font-semibold text-pine">{product.name}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink/75">{product.promise}</p>

              <p className="mt-4 text-[11px] font-bold uppercase tracking-wider text-ink/45">
                Built from
              </p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {product.builtFrom.map((src) => (
                  <span
                    key={src}
                    className="rounded-full border border-sage/60 bg-sage-light/40 px-2.5 py-0.5 text-[11px] font-semibold text-pine/85"
                  >
                    {src}
                  </span>
                ))}
              </div>

              <ul className="mt-4 space-y-2">
                {product.bullets.map((bullet) => (
                  <li key={bullet} className="flex gap-2.5 text-sm leading-snug text-ink/80">
                    <span
                      aria-hidden
                      className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-terracotta/70"
                    />
                    {bullet}
                  </li>
                ))}
              </ul>

              <p className="mt-auto pt-5">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-terracotta/10 px-3 py-1.5 text-xs font-bold text-terracotta">
                  <Zap aria-hidden className="h-3.5 w-3.5" />
                  {product.kpi}
                </span>
              </p>
            </motion.article>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}

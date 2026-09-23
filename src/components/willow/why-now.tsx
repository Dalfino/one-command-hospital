"use client";

import { motion } from "framer-motion";
import { BadgeCheck, CircleDollarSign, Timer, TrendingDown, type LucideIcon } from "lucide-react";
import { AnimatedCounter, Reveal, Section, SectionHeader } from "./motion-primitives";

function StatCard({
  icon: Icon,
  children,
  label,
  desc,
  source,
}: {
  icon: LucideIcon;
  children: React.ReactNode;
  label: string;
  desc: string;
  source: string;
}) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ type: "spring", stiffness: 300, damping: 22 }}
      className="group flex h-full flex-col rounded-2xl border border-sage/50 bg-white/80 p-6 shadow-sm transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10"
    >
      <div className="flex items-start justify-between">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-sage-light text-forest transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6">
          <Icon aria-hidden className="h-5 w-5" />
        </span>
      </div>
      <p className="mt-4 font-display text-[1.7rem] font-semibold leading-tight tracking-tight text-forest sm:text-4xl">
        {children}
      </p>
      <p className="mt-2 text-sm font-bold text-pine">{label}</p>
      <p className="mt-1 text-sm leading-relaxed text-ink/70">{desc}</p>
      <p className="mt-auto pt-3 text-[11px] font-semibold uppercase tracking-wider text-ink/45">
        {source}
      </p>
    </motion.div>
  );
}

export function WhyNow() {
  return (
    <Section id="why">
      <SectionHeader
        headingId="why-heading"
        eyebrow="Why now"
        title="The evidence is in — and the pricing is broken"
        description="Clinical operations are drowning in documentation while clinicians burn out — and the tools that demonstrably help are priced like luxury software. Commercial ambient AI works, but it closes around your data at thousands of dollars per clinician per year. Meanwhile, open medical models — MedGemma, BioMistral, OpenBioLLM — now sit at or near GPT-4-class benchmarks on clinical tasks. What has been missing is governance. That is the piece Willow builds."
      />

      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
        <Reveal delay={0} className="h-full">
          <StatCard
            icon={TrendingDown}
            label="Clinician burnout"
            desc="after 30 days with ambient AI documentation"
            source="JAMA Network, 2025"
          >
            51.9% <span className="text-terracotta">→</span>{" "}
            <AnimatedCounter from={51.9} to={38.8} duration={1.8} format={(n) => n.toFixed(1)} />%
          </StatCard>
        </Reveal>

        <Reveal delay={0.08} className="h-full">
          <StatCard
            icon={Timer}
            label="Documentation time"
            desc="reduction with AI scribes"
            source="Multi-site pilot studies, 2025–2026"
          >
            20–<AnimatedCounter from={0} to={30} duration={1.6} />%
          </StatCard>
        </Reveal>

        <Reveal delay={0.16} className="h-full">
          <StatCard
            icon={CircleDollarSign}
            label="Commercial scribe cost"
            desc="per clinician, per year"
            source="Abridge / DAX contract estimates, 2026"
          >
            $2.5k–<AnimatedCounter from={0} to={7.2} duration={1.6} format={(n) => n.toFixed(1)} />
            k
          </StatCard>
        </Reveal>

        <Reveal delay={0.24} className="h-full">
          <StatCard
            icon={BadgeCheck}
            label="FDA-authorized AI devices"
            desc="AI-enabled medical devices through 2024"
            source="U.S. FDA"
          >
            <AnimatedCounter
              from={0}
              to={1016}
              duration={1.8}
              format={(n) => Math.round(n).toLocaleString("en-US")}
            />
          </StatCard>
        </Reveal>
      </div>
    </Section>
  );
}

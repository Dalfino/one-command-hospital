"use client";

import { motion } from "framer-motion";
import { BadgeCheck, CircleDollarSign, Clock3, Timer, TrendingDown, type LucideIcon } from "lucide-react";
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
        title="It's 2 a.m. and the protocol is on a shared drive somewhere"
        description="A junior doctor needs the warfarin-bridging protocol for a morning procedure. Today that means hunting shared drives, opening stale PDF editions of unknown vintage, and falling back to a WhatsApp guess. The industry numbers below are general, but the pain they point at is specific: documentation friction burns clinicians out, and guideline lookup hasn't moved in a decade. That's the gap a Guideline Copilot closes."
      />

      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
        <Reveal delay={0} className="h-full">
          <StatCard
            icon={Clock3}
            label="When the question lands"
            desc="Post-op patient on warfarin, theatre in the morning — and the protocol lives in a stale PDF on a shared drive. This repo is built for that moment."
            source="The scenario this project serves"
          >
            2<span className="text-terracotta">:</span>00{" "}
            <span className="text-lg sm:text-2xl">a.m.</span>
          </StatCard>
        </Reveal>

        <Reveal delay={0.08} className="h-full">
          <StatCard
            icon={TrendingDown}
            label="Clinician burnout"
            desc="after 30 days with ambient AI documentation — documentation friction is a leading driver"
            source="JAMA Network, 2025 — general industry finding"
          >
            51.9% <span className="text-terracotta">→</span>{" "}
            <AnimatedCounter from={51.9} to={38.8} duration={1.8} format={(n) => n.toFixed(1)} />%
          </StatCard>
        </Reveal>

        <Reveal delay={0.16} className="h-full">
          <StatCard
            icon={Timer}
            label="Documentation time"
            desc="reduction reported with AI scribes — the same friction that buries guideline lookup"
            source="Multi-site pilot studies, 2025–2026 — general industry finding"
          >
            20–<AnimatedCounter from={0} to={30} duration={1.6} />%
          </StatCard>
        </Reveal>

        <Reveal delay={0.24} className="h-full">
          <StatCard
            icon={CircleDollarSign}
            label="Commercial scribe cost"
            desc="per clinician, per year — while the answers clinicians actually need sit in unversioned PDFs"
            source="Abridge / DAX contract estimates, 2026 — general industry finding"
          >
            $2.5k–<AnimatedCounter from={0} to={7.2} duration={1.6} format={(n) => n.toFixed(1)} />
            k
          </StatCard>
        </Reveal>
      </div>

      <Reveal delay={0.1} className="mx-auto mt-8 max-w-3xl">
        <p className="rounded-2xl border border-forest/20 bg-sage-light/50 px-5 py-4 text-center text-sm font-medium leading-relaxed text-pine sm:text-base">
          <BadgeCheck aria-hidden className="mr-2 -translate-y-0.5 inline text-forest" />
          The fix isn&rsquo;t another generic chatbot. It&rsquo;s a copilot that answers only from
          the hospital&rsquo;s own guidelines — with citations and editions — and refuses when
          they don&rsquo;t cover it.
        </p>
      </Reveal>
    </Section>
  );
}

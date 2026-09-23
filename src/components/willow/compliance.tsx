"use client";

import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Reveal, Section, SectionHeader } from "./motion-primitives";
import { COMPLIANCE_TABS } from "./willow-data";

export function Compliance() {
  return (
    <Section id="compliance">
      <SectionHeader
        headingId="compliance-heading"
        eyebrow="Compliance"
        title="The hard part, taken seriously"
        description="Four regulatory workstreams, one documentation spine. Every product ships with the evidence pack your compliance team asks for — before it asks."
      />

      <Reveal delay={0.1} className="mt-10">
        <Tabs defaultValue={COMPLIANCE_TABS[0].id} className="w-full">
          <TabsList className="grid h-auto w-full grid-cols-2 gap-1.5 rounded-2xl bg-sand p-1.5 lg:grid-cols-4">
            {COMPLIANCE_TABS.map((tab) => (
              <TabsTrigger
                key={tab.id}
                value={tab.id}
                className="min-h-11 rounded-xl px-3 py-2.5 text-xs font-bold text-ink/65 transition-colors hover:text-pine data-[state=active]:bg-white data-[state=active]:text-pine data-[state=active]:shadow-sm sm:text-sm"
              >
                <tab.icon aria-hidden className="mr-1.5 h-4 w-4 shrink-0" />
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>

          {COMPLIANCE_TABS.map((tab) => (
            <TabsContent key={tab.id} value={tab.id} className="mt-6 focus-visible:outline-none">
              <div className="rounded-2xl border border-sage/50 bg-white/80 p-5 shadow-sm sm:p-6">
                <p className="max-w-3xl text-sm leading-relaxed text-ink/80 sm:text-base">
                  {tab.intro}
                </p>
                <ul className="mt-5 grid gap-2.5 lg:grid-cols-2">
                  {tab.items.map((item, i) => (
                    <motion.li
                      key={item}
                      initial={{ opacity: 0, x: -14 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.06 + i * 0.05, duration: 0.4 }}
                      className="flex items-start gap-3 rounded-xl border border-sage/30 bg-sage-light/30 p-3.5 transition-colors hover:bg-sage-light/60"
                    >
                      <CheckCircle2
                        aria-hidden
                        className="mt-0.5 h-5 w-5 shrink-0 text-forest"
                      />
                      <span className="text-sm leading-relaxed text-ink/85">{item}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </Reveal>
    </Section>
  );
}

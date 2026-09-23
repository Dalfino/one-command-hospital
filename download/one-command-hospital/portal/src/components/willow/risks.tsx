"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Reveal, Section, SectionHeader } from "./motion-primitives";
import { RISKS, type RiskLevel } from "./willow-data";

const LEVEL_STYLES: Record<RiskLevel, string> = {
  Low: "bg-sage-light text-pine",
  Med: "bg-amber-warm/25 text-ink",
  High: "bg-terracotta/15 text-terracotta",
  Critical: "bg-terracotta text-white",
};

function LevelBadge({ level }: { level: RiskLevel }) {
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-bold ${LEVEL_STYLES[level]}`}
    >
      {level}
    </span>
  );
}

export function Risks() {
  return (
    <Section id="risks">
      <SectionHeader
        headingId="risks-heading"
        eyebrow="Risk register"
        title="Named risks, owned mitigations"
        description="Aligned with the kill criteria: if these mitigations fail, the pilot stops. A register, not a disclaimer — the failure story is designed."
      />

      <Reveal delay={0.1} className="mt-10">
        <div className="overflow-x-auto rounded-2xl border border-sage/50 bg-white/80 shadow-sm">
          <Table className="min-w-[680px]">
            <TableHeader>
              <TableRow className="border-sage/40 hover:bg-transparent">
                <TableHead className="w-[24%] text-ink/60">Risk</TableHead>
                <TableHead className="w-[11%] text-ink/60">Likelihood</TableHead>
                <TableHead className="w-[11%] text-ink/60">Impact</TableHead>
                <TableHead className="text-ink/60">Mitigation</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {RISKS.map((row) => (
                <TableRow key={row.risk} className="border-sage/30">
                  <TableCell className="font-semibold text-pine">{row.risk}</TableCell>
                  <TableCell>
                    <LevelBadge level={row.likelihood} />
                  </TableCell>
                  <TableCell>
                    <LevelBadge level={row.impact} />
                  </TableCell>
                  <TableCell className="text-ink/80">{row.mitigation}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </Reveal>
    </Section>
  );
}

"use client";

import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { IdleIcon, Reveal, Section, SectionHeader } from "./motion-primitives";
import { GPU_ROWS, REFERENCE_STACK, SCENARIOS } from "./willow-data";

export function Deployment() {
  return (
    <Section id="deployment" alt>
      <SectionHeader
        headingId="deployment-heading"
        eyebrow="Deployment"
        title="Runs inside your walls"
        description="A reference architecture your infrastructure team can price this quarter — commodity GPUs, pinned containers, and security zones that map to your existing network policy."
      />

      <div className="mt-12 grid gap-6 lg:grid-cols-2">
        {/* Reference stack */}
        <Reveal className="h-full min-w-0">
          <div className="h-full rounded-2xl border border-sage/50 bg-white/80 p-6 shadow-sm">
            <h3 className="font-display text-xl font-semibold text-pine">
              On-prem reference stack
            </h3>
            <p className="mt-1 text-sm text-ink/65">Six building blocks, all self-hosted.</p>
            <ul className="mt-5 space-y-4">
              {REFERENCE_STACK.map((item, i) => (
                <li key={item.title} className="flex items-start gap-3.5">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sage-light text-forest">
                    <IdleIcon duration={4 + i * 0.3} delay={i * 0.25}>
                      <item.icon
                        aria-hidden
                        className="h-5 w-5 transition-transform duration-300 group-hover:scale-110"
                      />
                    </IdleIcon>
                  </span>
                  <span>
                    <span className="block text-sm font-bold text-pine">{item.title}</span>
                    <span className="mt-0.5 block text-sm leading-relaxed text-ink/70">
                      {item.desc}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>

        {/* GPU sizing table */}
        <Reveal delay={0.1} className="h-full min-w-0">
          <div className="h-full rounded-2xl border border-sage/50 bg-white/80 p-6 shadow-sm">
            <h3 className="font-display text-xl font-semibold text-pine">GPU sizing</h3>
            <p className="mt-1 text-sm text-ink/65">
              Throughput measured with vLLM, batch inference.
            </p>
            <div className="mt-5 overflow-x-auto">
              <Table className="min-w-[560px]">
                <TableHeader>
                  <TableRow className="border-sage/40 hover:bg-transparent">
                    <TableHead className="text-ink/60">Workload</TableHead>
                    <TableHead className="text-ink/60">GPU footprint</TableHead>
                    <TableHead className="text-right text-ink/60">Throughput</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {GPU_ROWS.map((row) => (
                    <TableRow key={row.workload} className="border-sage/30">
                      <TableCell className="font-semibold text-pine">{row.workload}</TableCell>
                      <TableCell className="text-ink/80">{row.gpu}</TableCell>
                      <TableCell className="whitespace-nowrap text-right font-semibold text-terracotta">
                        {row.throughput}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <p className="mt-4 text-xs leading-relaxed text-ink/55">
              All serving nodes sit inside the model security zone; no ingress from the DMZ, no
              egress to the internet.
            </p>
          </div>
        </Reveal>
      </div>

      {/* Scenario cards */}
      <div className="mt-8 grid gap-4 md:grid-cols-3 lg:gap-6">
        {SCENARIOS.map((scenario, i) => (
          <Reveal key={scenario.beds} delay={i * 0.1} className="h-full">
            <Card className="h-full border-sage/50 bg-white/80 transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10">
              <CardHeader className="pb-3">
                <CardTitle className="font-display text-lg font-semibold text-pine">
                  {scenario.beds}
                </CardTitle>
                <CardDescription className="font-semibold text-forest">
                  {scenario.gpus}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <span className="inline-block rounded-full bg-terracotta/10 px-3 py-1 text-xs font-bold text-terracotta">
                  {scenario.capex}
                </span>
                <p className="mt-3 text-sm leading-relaxed text-ink/70">{scenario.desc}</p>
              </CardContent>
            </Card>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}

"use client";

import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { IdleIcon, Reveal, Section, SectionHeader } from "./motion-primitives";
import {
  COMPOSE_PROFILES,
  DEPLOY_FACTS,
  MAKE_VERBS,
  PORT_ROWS,
} from "./willow-data";

export function Deployment() {
  return (
    <Section id="deployment">
      <SectionHeader
        headingId="deployment-heading"
        eyebrow="Deployment"
        title="One command, one GPU, no internet required"
        description="cp .env.example .env && make up — the EHR, the FHIR spine, the bus, and the four AI services on a coherent port block, with three optional profiles for GPU serving, synthetic patients, and conformance."
      />

      <div className="mt-12 grid gap-6 lg:grid-cols-2">
        {/* The one command */}
        <Reveal className="h-full min-w-0">
          <div className="h-full rounded-2xl border border-sage/50 bg-white/80 p-6 shadow-sm">
            <h3 className="font-display text-xl font-semibold text-pine">The one command</h3>
            <p className="mt-1 text-sm text-ink/65">Fresh machine to running hospital.</p>
            <div className="mt-5 overflow-x-auto rounded-xl bg-pine px-4 py-3.5 shadow-md shadow-pine/10">
              <code className="whitespace-nowrap font-mono text-sm font-semibold text-cream">
                cp .env.example .env <span className="text-sage">&&</span> make up
              </code>
            </div>

            <p className="mt-6 text-xs font-bold uppercase tracking-[0.2em] text-terracotta">
              Makefile verbs
            </p>
            <ul className="mt-3 space-y-2.5">
              {MAKE_VERBS.map((verb, i) => (
                <li key={verb.verb} className="flex items-start gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-sage-light text-forest">
                    <IdleIcon duration={4 + i * 0.3} delay={i * 0.25}>
                      <CheckCircle2 aria-hidden className="h-4 w-4" />
                    </IdleIcon>
                  </span>
                  <span className="min-w-0 text-sm leading-relaxed text-ink/75">
                    <code className="font-bold text-pine">make {verb.verb}</code> — {verb.desc}
                  </span>
                </li>
              ))}
            </ul>

            <p className="mt-6 text-xs font-bold uppercase tracking-[0.2em] text-terracotta">
              Compose profiles
            </p>
            <div className="mt-2.5 flex flex-wrap gap-2">
              {COMPOSE_PROFILES.map((profile) => (
                <span
                  key={profile}
                  className="rounded-full border border-forest/25 bg-sage-light/60 px-3 py-1 text-xs font-bold text-pine"
                >
                  --profile {profile}
                </span>
              ))}
            </div>
          </div>
        </Reveal>

        {/* Port map */}
        <Reveal delay={0.1} className="h-full min-w-0">
          <div className="h-full rounded-2xl border border-sage/50 bg-white/80 p-6 shadow-sm">
            <h3 className="font-display text-xl font-semibold text-pine">Port map</h3>
            <p className="mt-1 text-sm text-ink/65">
              One coherent block — nothing collides, everything is findable.
            </p>
            <div className="mt-5 overflow-x-auto">
              <Table className="min-w-[520px]">
                <TableHeader>
                  <TableRow className="border-sage/40 hover:bg-transparent">
                    <TableHead className="text-ink/60">Service</TableHead>
                    <TableHead className="text-right text-ink/60">Port</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {PORT_ROWS.map((row) => (
                    <TableRow key={row.service} className="border-sage/30">
                      <TableCell className="font-semibold text-pine">{row.service}</TableCell>
                      <TableCell className="whitespace-nowrap text-right font-mono text-sm font-semibold text-terracotta">
                        {row.port}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <p className="mt-4 text-xs leading-relaxed text-ink/55">
              OpenHIM console note: after first boot, point its core-API target at
              localhost:8085 — Medplum owns 8080 on the host (documented in docs/architecture.md).
            </p>
          </div>
        </Reveal>
      </div>

      {/* Facts: GPU / air-gap / time */}
      <div className="mt-8 grid gap-4 md:grid-cols-3 lg:gap-6">
        {DEPLOY_FACTS.map((fact, i) => (
          <Reveal key={fact.title} delay={i * 0.1} className="h-full min-w-0">
            <Card className="h-full border-sage/50 bg-white/80 transition-[box-shadow,border-color] duration-300 hover:border-terracotta/40 hover:shadow-xl hover:shadow-terracotta/10">
              <CardHeader className="pb-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-sage-light text-forest">
                  <IdleIcon duration={4 + i * 0.3} delay={i * 0.2}>
                    <fact.icon aria-hidden className="h-5 w-5" />
                  </IdleIcon>
                </span>
                <CardTitle className="mt-3 text-xs font-bold uppercase tracking-[0.2em] text-ink/55">
                  {fact.title}
                </CardTitle>
                <CardDescription className="font-display text-2xl font-semibold text-pine">
                  {fact.big}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed text-ink/70">{fact.desc}</p>
              </CardContent>
            </Card>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}

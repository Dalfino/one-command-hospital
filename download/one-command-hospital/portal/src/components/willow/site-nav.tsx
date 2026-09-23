"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, HeartPulse, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { NAV_LINKS, REPO_URL } from "./willow-data";

export function SiteNav() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-sage/40 bg-cream/70 backdrop-blur-md supports-[backdrop-filter]:bg-cream/60">
      <nav
        aria-label="Main navigation"
        className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8"
      >
        <a
          href="#top"
          className="flex min-w-0 items-center gap-2.5 rounded-full"
          aria-label="One-Command Hospital — back to top"
        >
          <motion.span
            aria-hidden
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-forest text-cream"
            animate={{ scale: [1, 1.14, 1] }}
            transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
          >
            <HeartPulse className="h-5 w-5" />
          </motion.span>
          <span className="min-w-0 leading-tight">
            <span className="block truncate font-display text-lg font-semibold tracking-tight text-pine">
              One-Command Hospital
            </span>
            <span className="hidden text-[10px] font-bold uppercase tracking-[0.16em] text-ink/50 sm:block">
              Guideline Copilot · a Willow Lab build
            </span>
          </span>
        </a>

        <div className="hidden items-center gap-0.5 lg:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="inline-flex min-h-11 items-center rounded-full px-3 text-sm font-semibold text-ink/75 transition-colors hover:bg-sage-light hover:text-pine"
            >
              {link.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Button
            asChild
            className="hidden min-h-11 bg-terracotta text-white hover:bg-terracotta/90 md:inline-flex"
          >
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
              View the repo
              <ArrowUpRight aria-hidden className="ml-1.5 h-4 w-4" />
            </a>
          </Button>

          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="min-h-11 min-w-11 border-sage/60 text-pine lg:hidden"
                aria-label="Open navigation menu"
              >
                <Menu aria-hidden className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent
              side="right"
              aria-describedby={undefined}
              className="w-80 border-sage/40 bg-cream"
            >
              <SheetTitle className="font-display text-lg font-semibold text-pine">
                One-Command Hospital
              </SheetTitle>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink/50">
                Guideline Copilot · a Willow Lab build
              </p>
              <nav aria-label="Mobile navigation" className="mt-4 flex flex-col">
                {NAV_LINKS.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    onClick={() => setOpen(false)}
                    className="border-b border-sage/30 py-3.5 text-base font-semibold text-ink/85 transition-colors hover:text-terracotta"
                  >
                    {link.label}
                  </a>
                ))}
                <a
                  href={REPO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => setOpen(false)}
                  className="py-3.5 text-base font-semibold text-terracotta transition-colors hover:text-pine"
                >
                  View the repo ↗
                </a>
              </nav>
              <Button
                asChild
                className="mt-6 min-h-11 w-full bg-terracotta text-white hover:bg-terracotta/90"
              >
                <a href={REPO_URL} target="_blank" rel="noopener noreferrer" onClick={() => setOpen(false)}>
                  View the repo
                  <ArrowUpRight aria-hidden className="ml-1.5 h-4 w-4" />
                </a>
              </Button>
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </header>
  );
}

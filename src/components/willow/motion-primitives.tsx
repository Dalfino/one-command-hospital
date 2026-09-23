"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

/* ------------------------- Scroll reveal ------------------------- */

type RevealProps = {
  children: ReactNode;
  className?: string;
  delay?: number;
  y?: number;
};

export function Reveal({ children, className, delay = 0, y = 26 }: RevealProps) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduce ? { opacity: 0 } : { opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

/* --------------------------- Section ----------------------------- */

type SectionProps = {
  id: string;
  alt?: boolean;
  className?: string;
  children: ReactNode;
};

export function Section({ id, alt = false, className, children }: SectionProps) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-heading`}
      className={cn("scroll-mt-20 py-16 sm:py-20 lg:py-24", alt ? "bg-sand" : "bg-cream", className)}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">{children}</div>
    </section>
  );
}

/* ------------------------ Section header ------------------------- */

type SectionHeaderProps = {
  headingId: string;
  eyebrow: string;
  title: string;
  description?: string;
};

export function SectionHeader({ headingId, eyebrow, title, description }: SectionHeaderProps) {
  return (
    <Reveal className="mx-auto max-w-3xl text-center">
      <p className="mb-3 text-xs font-bold uppercase tracking-[0.22em] text-terracotta">{eyebrow}</p>
      <h2
        id={headingId}
        className="font-display text-3xl font-semibold tracking-tight text-balance text-pine sm:text-4xl lg:text-[2.75rem] lg:leading-[1.15]"
      >
        {title}
      </h2>
      {description ? (
        <p className="mt-4 text-base leading-relaxed text-ink/75 sm:text-lg">{description}</p>
      ) : null}
    </Reveal>
  );
}

/* ------------------------ Animated counter ----------------------- */

type CounterProps = {
  from?: number;
  to: number;
  duration?: number;
  format?: (n: number) => string;
  className?: string;
};

export function AnimatedCounter({
  from = 0,
  to,
  duration = 1.6,
  format = (n: number) => String(Math.round(n)),
  className,
}: CounterProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const reduce = useReducedMotion();
  const [value, setValue] = useState(from);

  useEffect(() => {
    if (!inView) return;
    if (reduce) {
      setValue(to);
      return;
    }
    let raf = 0;
    const started = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - started) / (duration * 1000));
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(from + (to - from) * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, reduce, from, to, duration]);

  return (
    <span ref={ref} className={cn("tabular-nums", className)}>
      {format(value)}
    </span>
  );
}

/* --------------------------- Idle icon --------------------------- */

type IdleIconProps = {
  children: ReactNode;
  className?: string;
  variant?: "float" | "sway";
  duration?: number;
  delay?: number;
};

/** Wraps a lucide icon with a gentle, tasteful idle loop (3–6s). */
export function IdleIcon({
  children,
  className,
  variant = "float",
  duration = 4,
  delay = 0,
}: IdleIconProps) {
  const reduce = useReducedMotion();
  return (
    <motion.span
      className={cn("inline-flex", className)}
      animate={
        reduce ? undefined : variant === "float" ? { y: [0, -4, 0] } : { rotate: [-5, 5, -5] }
      }
      transition={{ duration, delay, repeat: Infinity, ease: "easeInOut" }}
    >
      {children}
    </motion.span>
  );
}

/* --------------------------- Pulsing dot ------------------------- */

export function PulsingDot({ className }: { className?: string }) {
  return (
    <span aria-hidden className={cn("relative flex h-2.5 w-2.5 shrink-0", className)}>
      <span className="willow-ping absolute inline-flex h-full w-full rounded-full bg-forest opacity-70" />
      <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-forest" />
    </span>
  );
}

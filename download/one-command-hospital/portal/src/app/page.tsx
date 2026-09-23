import { SiteNav } from "@/components/willow/site-nav";
import { Hero } from "@/components/willow/hero";
import { WhyNow } from "@/components/willow/why-now";
import { HowItWorks } from "@/components/willow/how-it-works";
import { Combination } from "@/components/willow/combination";
import { Improvements } from "@/components/willow/improvements";
import { Proof } from "@/components/willow/proof";
import { Compliance } from "@/components/willow/compliance";
import { Deployment } from "@/components/willow/deployment";
import { Roadmap } from "@/components/willow/roadmap";
import { Risks } from "@/components/willow/risks";
import { SiteFooter } from "@/components/willow/site-footer";

export default function Home() {
  return (
    <div id="top" className="flex min-h-screen flex-col bg-cream font-sans text-ink">
      <SiteNav />
      <main className="flex-1">
        <Hero />
        <WhyNow />
        <HowItWorks />
        <Combination />
        <Improvements />
        <Proof />
        <Compliance />
        <Deployment />
        <Roadmap />
        <Risks />
      </main>
      <SiteFooter />
    </div>
  );
}

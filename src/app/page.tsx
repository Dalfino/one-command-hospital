import { SiteNav } from "@/components/willow/site-nav";
import { Hero } from "@/components/willow/hero";
import { WhyNow } from "@/components/willow/why-now";
import { Platform } from "@/components/willow/platform";
import { Products } from "@/components/willow/products";
import { Sources } from "@/components/willow/sources";
import { Compliance } from "@/components/willow/compliance";
import { Deployment } from "@/components/willow/deployment";
import { Roi } from "@/components/willow/roi";
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
        <Platform />
        <Products />
        <Sources />
        <Compliance />
        <Deployment />
        <Roi />
        <Roadmap />
        <Risks />
      </main>
      <SiteFooter />
    </div>
  );
}

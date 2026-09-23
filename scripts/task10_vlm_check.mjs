import { readFileSync, writeFileSync } from "fs";
import ZAI from "z-ai-web-dev-sdk";

const IMAGES = [
  { name: "desktop-full-1366", path: "/tmp/task10-desktop-full2.png" },
  { name: "mobile-full-375", path: "/tmp/task10-mobile-full2.png" },
];

const PROMPT = `You are a meticulous UI QA reviewer for a marketing portal page (warm cream/green palette, serif display font). Inspect the FULL-PAGE screenshot end to end and report:
1. Any overlapping text/elements, clipped or truncated text, broken layout, misaligned cards, or elements touching viewport edges.
2. Any horizontal overflow symptoms (content cut off at right edge).
3. Any empty/broken sections or missing images/icons (e.g., empty boxes).
4. Contrast problems that make text unreadable.
Answer with a short verdict line first: "VERDICT: NO ISSUES" if none of the above are found, otherwise "VERDICT: ISSUES" followed by a numbered list with the section name (Hero, Why now, How it works, The combination, Six improvements, Proof, Compliance, Deployment, Roadmap, Risks, Footer) and what you see.`;

async function main() {
  const zai = await ZAI.create();
  const results = [];
  for (const img of IMAGES) {
    const b64 = readFileSync(img.path).toString("base64");
    const completion = await zai.chat.completions.createVision({
      messages: [
        {
          role: "user",
          content: [
            { type: "text", text: PROMPT },
            {
              type: "image_url",
              image_url: { url: `data:image/png;base64,${b64}` },
            },
          ],
        },
      ],
      thinking: { type: "disabled" },
    });
    const out = (completion.choices?.[0]?.message?.content ?? "NO RESPONSE").trim();
    results.push(`===== ${img.name} =====\n${out}`);
    console.log(`===== ${img.name} =====`);
    console.log(out);
  }
  writeFileSync("/tmp/task10-vlm-report.txt", results.join("\n\n"));
}

main().catch((e) => {
  console.error("VLM inspection failed:", e.message);
  process.exit(1);
});

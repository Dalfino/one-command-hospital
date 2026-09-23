import { readFileSync } from "fs";
import ZAI from "z-ai-web-dev-sdk";
const PROMPT = `This is a 375px-wide mobile screenshot of a website hero section (cream background, green serif headline). Answer precisely:
1. Is any text clipped/cut off (top, sides)? 
2. Are the two buttons fully visible with readable labels, or clipped?
3. Are the three floating stat chips fully visible with readable labels?
4. Overall verdict: "MOBILE HERO: OK" or list issues.`;
const zai = await ZAI.create();
const b64 = readFileSync("/tmp/task10-mob-hero.png").toString("base64");
const r = await zai.chat.completions.createVision({
  messages: [{ role: "user", content: [
    { type: "text", text: PROMPT },
    { type: "image_url", image_url: { url: "data:image/png;base64," + b64 } },
  ]}],
  thinking: { type: "disabled" },
});
console.log(r.choices?.[0]?.message?.content);

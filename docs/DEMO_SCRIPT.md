# SafeNet AI — Video Demo Script
## AMD Developer Hackathon: ACT II | Track 3 — Unicorn Track

> Target length: **4 minutes 30 seconds**
> Format: screen recording with voiceover
> Tone: confident, product-pitch style — not a tutorial

---

## SLIDE 1 — Hook (0:00 – 0:20)

**[Show: India map with fraud heatmap overlaid. Text: "₹11,000 crore lost to digital fraud in India in 2024."]**

> "Every 60 seconds, an Indian citizen is targeted by a scam call, a fake currency note, or a UPI fraud attempt. Law enforcement can't act fast enough. SafeNet AI changes that."

---

## SCENE 1 — Landing Page (0:20 – 0:35)

**[Show: Landing page with Galaxy animation loading]**

> "SafeNet AI is a unified digital public-safety intelligence platform — five AI modules, one orchestration layer, one dashboard. Built on AMD Developer Cloud with Fireworks AI."

**[Point to hero text: "One intelligence layer. Five threat surfaces."]**

---

## SCENE 2 — Dashboard + AMD Status Panel (0:35 – 1:00)

**[Navigate to /dashboard. Point to the top-bar AMD Status Panel showing green "AMD GPU" badge]**

> "The dashboard connects directly to a Fireworks AI inference cluster running on AMD Instinct GPUs. You can see the active model — Gemma 2 — confirmed live right here in the status panel."

**[Click the AMD panel to expand. Show task routing: chat → gemma2-9b-it, etc.]**

> "Every severity tier routes to a different model — Gemma 2 27B for critical events, 9B for warnings, Llama 8B for lightweight summaries. Cheapest sufficient model, every time."

---

## SCENE 3 — Simulate Scenario (1:00 – 1:55)

**[Click "Simulate Scenario" button]**

> "Let me trigger a coordinated attack simulation — this is what makes SafeNet AI different from any single-module tool."

**[Watch first event appear in Risk Feed: "Scam Call Intercepted — CBI Impersonation", CRS ~35]**

> "Step 1: A spoofed call is detected. CBI impersonation, arrest-warrant threat. CRS starts at 35 — the system flags it as medium."

**[Watch second event: "Fraud Ring Linked to Call Entity", CRS ~65]**

> "Step 2: The same phone number resolves to a money-mule ring in our fraud graph. Three flagged transactions. CRS climbs to 65 — HIGH."

**[Watch third event: "COORDINATED ATTACK — All Signals Converged", CRS ~87, CRITICAL badge]**

> "Step 3: Geospatial hotspot data matches the same location. All signals converge. CRS hits 87. The system auto-escalates, generates a PDF incident report, and composes a citizen alert."

**[Point to the event description — the Gemma-generated narrative summary]**

> "That description? Written by Gemma 2 on AMD hardware — a natural-language summary of the compound threat, generated in under a second."

---

## SCENE 4 — Evidence Panel (1:55 – 2:20)

**[Click the CRITICAL event in the Risk Feed]**

> "Clicking any event opens the Evidence Panel — a full case package ready for law enforcement."

**[Walk through: Compound Risk Score 87.3, Key Evidence items, Linked Entities, Recommended Action]**

> "Transaction evidence, call transcripts, shared device fingerprints, connected mule accounts — all cross-referenced automatically. The recommended action is specific: freeze these accounts, file a SAR."

**[Click "Generate Incident Report" button]**

> "One click generates a PDF incident report with full CRS breakdown and audit trail."

---

## SCENE 5 — Citizen Shield / Gemma Demo (2:20 – 3:00)

**[Click the chat bubble bottom-right. Citizen Shield opens.]**

> "Now let's show the citizen-facing side. Same fraud — different user."

**[Type: "Someone called saying they are from CBI and I have an arrest warrant. They asked me to transfer ₹50,000."]**

> "A citizen gets this call. They open SafeNet AI and describe it."

**[Wait for Gemma response to appear]**

> "Gemma 2 — running on AMD — recognises the CBI impersonation, urgency, and money-transfer request. It gives specific, actionable advice — not a generic warning."

**[Show the risk badge: HIGH. Show the next-steps section.]**

> "Block the number. Report to 1930. Tell a family member. Concise, specific, in their language."

**[Optional: switch language dropdown to Hindi, resend]**

> "And it works in six Indian languages — Hindi, Tamil, Telugu, Bengali, Marathi — all translated by Mixtral on AMD hardware."

---

## SCENE 6 — Note Checker (3:00 – 3:30)

**[Navigate to /note-checker]**

> "Module 2 — Counterfeit Vision. Every denomination of the Indian Rupee, from ₹10 to ₹2000."

**[Upload a test note image]**

> "Upload a photo. MobileNetV3 classifies it, Gemini verifies the security features, and Grad-CAM highlights exactly which region of the note drove the verdict."

**[Show the heatmap overlay and verdict card]**

> "Real or fake, confidence score, denomination detected, actionable recommendation. Works offline with rule-based fallback if the ML model isn't available."

---

## SCENE 7 — Number Checker (3:30 – 3:50)

**[Navigate to /number-checker. Type +916511361582]**

> "Citizens can check any number before picking up or transferring money."

**[Show result: HIGH risk, fraud graph hit, blocklist match, 3 reasons listed]**

> "Three independent signals — fraud graph, pattern analysis, synthetic blocklist — all cited explicitly. No black box. Every reason is traceable."

---

## SCENE 8 — Architecture close (3:50 – 4:15)

**[Switch to architecture diagram slide]**

> "Under the hood: LangGraph orchestrates five modules in a typed state machine. Each module exposes both a REST endpoint and a direct Python function — no HTTP hops in the hot path."

> "Fireworks AI provides AMD-native inference. The model router picks the cheapest Fireworks model that can handle each task — this is the same routing intelligence that Track 1 teams are building, but applied to real-world public safety."

---

## SCENE 9 — Closing (4:15 – 4:30)

**[Show landing page again]**

> "SafeNet AI is fully containerised, deployable on AMD Developer Cloud in one command, and ready to scale. This isn't a demo toy — it's the beginning of a real safety layer for 1.4 billion people."

> "SafeNet AI. One intelligence layer. Five threat surfaces."

---

## POST-RECORDING CHECKLIST

- [ ] AMD Status Panel shows green "AMD GPU" badge throughout
- [ ] CRS values visible during simulate: ~35 → ~65 → ~87
- [ ] Gemma model name visible in AMD panel expand
- [ ] Note checker heatmap clearly visible
- [ ] Number checker shows 3 traceable reasons
- [ ] Language switch demo (optional but impressive)
- [ ] Total runtime ≤ 5 minutes (hard limit per lablab.ai rules)

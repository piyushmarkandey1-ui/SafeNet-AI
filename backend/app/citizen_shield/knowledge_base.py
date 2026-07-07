"""
SafeNet AI — Citizen Shield: Knowledge Base

Seeds a ChromaDB collection with three document types:

1. SCAM_PATTERN  — phrase-level descriptions of every tactic from Module A's
                   classifier, written as plain-language "what to watch for"
                   paragraphs so RAG retrieval finds them from natural queries.

2. BLOCKLIST     — synthetic (clearly labelled) phone numbers and UPI IDs
                   that have been reported for fraud in the SafeNet demo system.
                   ⚠️  SYNTHETIC DATA — None of these are real numbers or IDs.

3. REPORTING_GUIDE — plain-language "how to report" guide authored by the
                     SafeNet AI team.  NOT an official NCRB document and not
                     claimed as such.  Every entry carries that disclaimer.

Module contract (safenet.md §3):
  search_knowledge_base(query, top_k) is the plain Python function.
  The /ask endpoint calls it via agent.py without an HTTP hop.
"""

from __future__ import annotations

import os
from typing import Optional

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# ── Singleton state ────────────────────────────────────────────────────────────
_client = None
_collection = None
_embedder = None
_index_built = False

COLLECTION_NAME = "citizen_shield_kb"
EMBED_MODEL = "all-MiniLM-L6-v2"


# ── Raw knowledge corpus ───────────────────────────────────────────────────────

# 1. Scam-pattern knowledge (sourced from Module A's TACTIC_PATTERNS + WEIGHTS)
SCAM_PATTERN_DOCS = [
    {
        "id": "sp-impersonation",
        "text": (
            "Impersonation scams: Callers pretend to be officials from the police, "
            "CBI, customs department, FedEx, Interpol, narcotics bureau, your bank "
            "manager, or a fraud department. They claim you have a pending arrest "
            "warrant, a parcel held at customs, or unusual activity on your account. "
            "Legitimate government agencies and banks never make unsolicited calls "
            "demanding immediate action or personal information."
        ),
        "doc_type": "SCAM_PATTERN",
        "tactic": "IMPERSONATION",
        "risk_weight": 25,
    },
    {
        "id": "sp-urgency",
        "text": (
            "Urgency and threat tactics: Scammers create panic by saying you must "
            "act immediately, within the next few hours, or your account will be "
            "frozen, suspended, or that legal action will begin. Phrases like "
            "'your account has been frozen', 'penalty payment required', or "
            "'legal action will start right now' are classic pressure tactics. "
            "Real institutions give written notice and time to respond."
        ),
        "doc_type": "SCAM_PATTERN",
        "tactic": "URGENCY_THREAT",
        "risk_weight": 20,
    },
    {
        "id": "sp-isolation",
        "text": (
            "Isolation instructions: A major red flag is when a caller instructs "
            "you to stay on the line, not tell anyone — including family members — "
            "or go to a quiet room alone. This is designed to cut you off from "
            "people who could warn you. Any caller who says 'do not tell anyone' "
            "or 'don't disconnect, stay on the call' is almost certainly a scammer."
        ),
        "doc_type": "SCAM_PATTERN",
        "tactic": "ISOLATION",
        "risk_weight": 30,
    },
    {
        "id": "sp-action-request",
        "text": (
            "Action requests that compromise security: Scammers ask you to "
            "download remote-access software (AnyDesk, TeamViewer, QuickSupport), "
            "share an OTP, PIN, or password, read back a verification code, "
            "transfer money via crypto, Bitcoin, or gift cards, or join a video "
            "call and show your face or screen. No legitimate bank or government "
            "agency will ever ask you to install software or share a one-time code."
        ),
        "doc_type": "SCAM_PATTERN",
        "tactic": "ACTION_REQUEST",
        "risk_weight": 35,
    },
    {
        "id": "sp-upi-fraud",
        "text": (
            "UPI fraud patterns: Fraudsters send fake payment requests disguised "
            "as 'receive money' notifications. They ask you to enter your UPI PIN "
            "to 'collect' a refund — but entering your PIN approves a payment TO "
            "them, not FROM them. Other UPI scams involve QR codes at fake shops, "
            "phishing links mimicking Google Pay, PhonePe, or Paytm, and social "
            "engineering via OLX or classifieds where a 'buyer' sends a collect "
            "request instead of a payment."
        ),
        "doc_type": "SCAM_PATTERN",
        "tactic": "UPI_FRAUD",
        "risk_weight": 35,
    },
    {
        "id": "sp-counterfeit",
        "text": (
            "Counterfeit currency indicators: Genuine Indian Rupee notes have a "
            "security thread that glows green under UV, colour-shifting ink on the "
            "denomination numeral, micro-lettering 'भारत' and 'RBI', raised print "
            "you can feel, and a watermark portrait of Gandhi visible when held "
            "to light. Fake notes often feel smoother, have blurry security "
            "features, or the colour-shift ink does not change angle. If you "
            "receive a suspect note, do not fold it and report to your bank or "
            "the nearest police station."
        ),
        "doc_type": "SCAM_PATTERN",
        "tactic": "COUNTERFEIT_CURRENCY",
        "risk_weight": 30,
    },
    {
        "id": "sp-job-scam",
        "text": (
            "Job and investment scams: Offers of high-paying work-from-home jobs "
            "that require an upfront registration fee, equipment deposit, or "
            "training payment are almost always fraud. Similarly, 'stock tip' "
            "groups on WhatsApp or Telegram that promise guaranteed returns, "
            "or apps that show fake growing balances and then demand a 'tax "
            "payment' before you can withdraw, are investment scams. Never pay "
            "to get paid."
        ),
        "doc_type": "SCAM_PATTERN",
        "tactic": "JOB_INVESTMENT_SCAM",
        "risk_weight": 25,
    },
]

# 2. Synthetic blocklist
# ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.
BLOCKLIST_DOCS = [
    {
        "id": "bl-phone-001",
        "text": (
            "⚠️ SYNTHETIC BLOCKLIST ENTRY. "
            "Phone number +91-98001-00001 has been reported 47 times in the SafeNet "
            "demo system for CBI impersonation scams. Callers claim arrest warrants "
            "and demand immediate bank transfers."
        ),
        "doc_type": "BLOCKLIST",
        "entity_type": "phone",
        "entity_value": "+91-98001-00001",
        "report_count": 47,
    },
    {
        "id": "bl-phone-002",
        "text": (
            "⚠️ SYNTHETIC BLOCKLIST ENTRY. "
            "Phone number +91-98002-00002 has been reported 31 times for tech-support "
            "scams. Callers claim to be from Microsoft or Apple and ask victims to "
            "install AnyDesk or TeamViewer."
        ),
        "doc_type": "BLOCKLIST",
        "entity_type": "phone",
        "entity_value": "+91-98002-00002",
        "report_count": 31,
    },
    {
        "id": "bl-phone-003",
        "text": (
            "⚠️ SYNTHETIC BLOCKLIST ENTRY. "
            "Phone number +91-98003-00003 has been reported 19 times for customs "
            "parcel scams. Callers claim a package is held at customs and demand "
            "a clearance fee via UPI."
        ),
        "doc_type": "BLOCKLIST",
        "entity_type": "phone",
        "entity_value": "+91-98003-00003",
        "report_count": 19,
    },
    {
        "id": "bl-upi-001",
        "text": (
            "⚠️ SYNTHETIC BLOCKLIST ENTRY. "
            "UPI ID scam-demo@fakebank has been flagged 23 times in the SafeNet "
            "demo system for OLX refund fraud. The operator poses as a buyer, "
            "sends a collect-payment QR and claims it is a 'send money' link."
        ),
        "doc_type": "BLOCKLIST",
        "entity_type": "upi",
        "entity_value": "scam-demo@fakebank",
        "report_count": 23,
    },
    {
        "id": "bl-upi-002",
        "text": (
            "⚠️ SYNTHETIC BLOCKLIST ENTRY. "
            "UPI ID fraud-test@demopay has been reported 15 times for fake refund "
            "requests. Victims are told they will receive a cashback and asked to "
            "enter their UPI PIN to 'accept' the payment."
        ),
        "doc_type": "BLOCKLIST",
        "entity_type": "upi",
        "entity_value": "fraud-test@demopay",
        "report_count": 15,
    },
]

# 3. Reporting guide
# NOT an official NCRP/NCRB document. Written by SafeNet AI team for demo purposes.
REPORTING_GUIDE_DOCS = [
    {
        "id": "rg-cybercrime-portal",
        "text": (
            "HOW TO REPORT CYBER FRAUD IN INDIA (SafeNet AI Guide — not an official "
            "government document). "
            "Step 1: Visit the National Cyber Crime Reporting Portal at "
            "cybercrime.gov.in. This is India's official online platform for "
            "reporting cybercrime including UPI fraud, phishing, and online scams. "
            "Step 2: Click 'Report Other Cyber Crimes' for financial fraud or "
            "'Report Women/Child Related Crime' for specific cases. "
            "Step 3: Fill in the complaint form with: date and time of the incident, "
            "the fraudster's phone number or UPI ID, transaction IDs if money was "
            "transferred, and any screenshots or call recordings you have. "
            "Step 4: You will receive a complaint acknowledgement number — save it. "
            "Step 5: For urgent cases (money transferred in last 24 hours), also "
            "call the National Cyber Crime Helpline: 1930."
        ),
        "doc_type": "REPORTING_GUIDE",
        "topic": "cybercrime_portal",
    },
    {
        "id": "rg-bank-fraud",
        "text": (
            "HOW TO REPORT BANK AND UPI FRAUD (SafeNet AI Guide). "
            "If money has been deducted from your account without your authorisation: "
            "1. Call your bank's 24-hour fraud helpline immediately (number on the "
            "back of your debit/credit card). Request a temporary freeze on your account. "
            "2. File a complaint at cybercrime.gov.in or call 1930. "
            "3. Visit your nearest bank branch with your passbook, a government ID, "
            "and a written complaint. Ask for a 'chargeback' or 'dispute' form. "
            "4. If UPI was used, also report to the National Payments Corporation of "
            "India (NPCI) via your UPI app's Help section. "
            "5. File an FIR at your local police station — you will need it for "
            "insurance claims and legal proceedings."
        ),
        "doc_type": "REPORTING_GUIDE",
        "topic": "bank_upi_fraud",
    },
    {
        "id": "rg-do-not-share",
        "text": (
            "WHAT NEVER TO SHARE (SafeNet AI Safety Guide). "
            "Never share the following with anyone, including people claiming to be "
            "from your bank, the government, or tech support: "
            "• OTP (one-time password) — sharing an OTP is the same as handing over "
            "your account. No bank or government body will ever ask for it. "
            "• UPI PIN or ATM PIN — these are yours alone. "
            "• CVV number on the back of your card. "
            "• Full debit/credit card number. "
            "• Internet banking password or username. "
            "• Aadhaar number combined with OTP (can be used for biometric fraud). "
            "If you have already shared any of these, contact your bank immediately "
            "to block your card and change your passwords."
        ),
        "doc_type": "REPORTING_GUIDE",
        "topic": "what_not_to_share",
    },
    {
        "id": "rg-counterfeit-note",
        "text": (
            "HOW TO REPORT A SUSPECT COUNTERFEIT CURRENCY NOTE (SafeNet AI Guide). "
            "1. Do not fold, staple, or write on the suspect note — preserve it as is. "
            "2. Note where and when you received it. "
            "3. Hand it to your bank teller and ask them to check it — banks have "
            "UV verification equipment and are required by RBI to impound fakes. "
            "4. Ask the bank to give you a receipt acknowledging they received it. "
            "5. File a complaint at your local police station. "
            "6. You can also report online at cybercrime.gov.in under 'Other Cybercrime'. "
            "You will NOT be penalised for having received a fake note in good faith."
        ),
        "doc_type": "REPORTING_GUIDE",
        "topic": "counterfeit_currency",
    },
]

# Full corpus
ALL_DOCS = SCAM_PATTERN_DOCS + BLOCKLIST_DOCS + REPORTING_GUIDE_DOCS


# ── ChromaDB helpers ───────────────────────────────────────────────────────────

def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def _get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb
        _client = chromadb.EphemeralClient()
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def build_kb(force: bool = False) -> int:
    """
    Embeds all knowledge-base documents and loads them into ChromaDB.

    Args:
        force: Rebuild even if already seeded.

    Returns:
        Number of documents in the collection.
    """
    global _index_built
    coll = _get_collection()

    if _index_built and not force:
        return coll.count()

    texts = [d["text"] for d in ALL_DOCS]
    ids = [d["id"] for d in ALL_DOCS]
    metas = [
        {k: v for k, v in d.items() if k not in ("text",) and isinstance(v, (str, int, float, bool))}
        for d in ALL_DOCS
    ]

    embedder = _get_embedder()
    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

    coll.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metas)
    _index_built = True
    return coll.count()


def search_knowledge_base(
    query: str,
    top_k: int = 3,
    doc_type_filter: Optional[str] = None,
) -> list[dict]:
    """
    Semantic search over the knowledge base.

    Args:
        query:          Natural-language query string.
        top_k:          Number of results to return.
        doc_type_filter: If set, only return docs matching this doc_type
                         (SCAM_PATTERN | BLOCKLIST | REPORTING_GUIDE).

    Returns:
        List of result dicts: { id, text, metadata, similarity }
    """
    build_kb()
    coll = _get_collection()
    embedder = _get_embedder()

    q_emb = embedder.encode([query], show_progress_bar=False).tolist()[0]

    where = {"doc_type": doc_type_filter} if doc_type_filter else None
    kwargs = dict(
        query_embeddings=[q_emb],
        n_results=min(top_k, max(coll.count(), 1)),
        include=["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where

    res = coll.query(**kwargs)

    results = []
    for doc, meta, dist in zip(
        res["documents"][0],
        res["metadatas"][0],
        res["distances"][0],
    ):
        results.append({
            "id": meta.get("id", ""),
            "text": doc,
            "metadata": meta,
            "similarity": round(1 - dist, 4),
        })
    return results


def check_blocklist(identifier: str) -> Optional[dict]:
    """
    Looks up a phone number or UPI ID in the synthetic blocklist.

    Exact-match first; falls back to semantic search if no exact hit.

    Args:
        identifier: Phone number or UPI ID string to look up.

    Returns:
        Matching blocklist entry dict, or None if not found.
    """
    identifier = identifier.strip()

    # Exact match scan
    for entry in BLOCKLIST_DOCS:
        if entry["entity_value"].lower() == identifier.lower():
            return entry

    # Semantic fallback — useful when query has slight formatting differences
    results = search_knowledge_base(identifier, top_k=1, doc_type_filter="BLOCKLIST")
    if results and results[0]["similarity"] > 0.85:
        return results[0]["metadata"]

    return None

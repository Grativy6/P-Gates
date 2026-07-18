from datetime import UTC, datetime

from app.schemas import AnalysisResult, Finding, Panel, TraceItem


EXAMPLE_TEXT = '''A blurry gas-station image is processed by several AI models.

Facial-recognition result: “Possible candidate: Jordan Reed — 93% similarity. Identity unverified.”

Later report: “Jordan Reed identified as suspect.”'''


def analyze(source_text: str) -> AnalysisResult:
    lowered = source_text.lower()
    promoted = "Jordan Reed identified as suspect." if "identified" in lowered else source_text.strip()[:180]
    trace = [
        TraceItem(
            original_phrase=promoted,
            detected_problem="Candidate status is promoted to identification and uncertainty is lost.",
            safer_wording="A facial-recognition search returned Jordan Reed as a possible candidate; identity remains unverified.",
            layer="PAL",
        ),
        TraceItem(
            original_phrase=promoted,
            detected_problem="A consequential claim lacks independent corroboration and cannot be strengthened by later copied records or actions.",
            safer_wording="Treat this as an unverified lead requiring independent corroboration before consequential action.",
            layer="PECAN",
        ),
    ]
    return AnalysisResult(
        source_text=source_text,
        analysis_timestamp=datetime.now(UTC),
        pal=Panel(
            summary="The text contains a similarity-based candidate signal, not a verified identity or guilt finding.",
            findings=[
                Finding(category="Observation", phrase="93% similarity", issue="A model returned a similarity score from a blurry image.", safer_wording="The system returned a similarity-ranked candidate."),
                Finding(category="Inference boundary", phrase=promoted, issue="Identity and suspect status exceed the stated observation.", safer_wording="Identity is unverified; candidate status does not establish involvement or guilt."),
                Finding(category="Unresolved remainder", phrase="blurry gas-station image", issue="Image quality, threshold, database quality, and independent evidence remain unresolved.", safer_wording="Record limits and seek independent evidence if further review is considered."),
            ],
        ),
        pecan=Panel(
            summary="Consequential use begins when the candidate description is used to route suspicion, investigation, detention, accusation, or another burden.",
            findings=[
                Finding(category="Wording compression", phrase=promoted, issue="Possible-candidate and unverified qualifiers are lost.", safer_wording="Unverified facial-recognition candidate; not an identification."),
                Finding(category="Provenance", phrase="later report", issue="A later report must preserve the original output and its limits.", safer_wording="Link the report to source output, image conditions, and review history."),
                Finding(category="Corroboration / backflow", phrase="identified as suspect", issue="Copied reports are not independent corroboration; later action cannot strengthen the original weak premise.", safer_wording="Require independent corroboration; do not treat later warrants or arrests as retroactive proof."),
            ],
        ),
        pea=Panel(
            summary="The affected person bears serious privacy, reputation, liberty, and contest burdens if a candidate match is promoted into accusation.",
            findings=[
                Finding(category="Affected people", phrase="Jordan Reed", issue="The candidate, family, victim, public, and responders may be affected.", safer_wording="Keep affected standing visible rather than treating one objective as sufficient."),
                Finding(category="Proportionality", phrase="93% similarity", issue="The claimed evidence does not by itself justify high-burden action.", safer_wording="Match follow-up to uncertainty, reversibility, and safeguards."),
                Finding(category="Contest and remedy", phrase=promoted, issue="The text gives no correction, refusal, contest, or reopening route.", safer_wording="Provide human review, correction, and record reopening routes."),
            ],
        ),
        seed=Panel(
            summary="Offer a bounded explanation that helps without presenting a model output as a human decision or eliminating room to contest it.",
            findings=[
                Finding(category="Responsible release", phrase=promoted, issue="The language implies certainty not supported by the source.", safer_wording="A facial-recognition search returned this person as a possible candidate. The result was not an identification. Independent corroboration is required before consequential action."),
                Finding(category="Minimum disclosure", phrase="Jordan Reed", issue="Do not disclose a candidate identity beyond the minimum necessary review context.", safer_wording="Limit disclosure, preserve privacy, and explain how to request correction or review."),
                Finding(category="Stopping point", phrase="suspect", issue="The report prematurely closes human judgment.", safer_wording="Stop at the bounded lead; leave the next decision to an accountable human or institution."),
            ],
        ),
        trace=trace,
        disclaimer="P-Gates is a mock analysis and drafting aid. It does not make decisions, create legal or ethical authority, replace due process, or substitute for accountable human judgment.",
    )

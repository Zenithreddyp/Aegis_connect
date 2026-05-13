from agents.Investigator import analyze_logs as analyze_logs_invest
from agents.sentry import analyze_logs

from .state import auditstate


def sentry_node(state: auditstate):
    state.status = "ANALYSING"

    print(f"[ENGINE] Node: Sentry processing {state.logid}...")

    report = analyze_logs(state.logs)

    state.severity = report.get("severity")
    state.confidence = report.get("confidence_score")
    state.sentry_notes = report.get("explanation")

    return state


def investigator_node(state: auditstate):
    if state.severity not in ["HIGH", "CRITICAL"]:
        return state

    state.status = "INVESTIGATING"

    print(f"[ENGINE] Node: Investigator deep-diving into {state.logid}...")

    report = analyze_logs_invest(state.logs)
    state.severity = report.get("severity")
    state.confidence = report.get("confidence_score")
    state.enforcer_instructions = report.get("recommended_actions", "")
    state.investigator_report = report

    return state


def finalize_node(state: auditstate):
    state.status = "COMPLETED"
    print(state)

    return state

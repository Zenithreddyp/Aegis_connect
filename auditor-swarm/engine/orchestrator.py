from .nodes import finalize_node, investigator_node, sentry_node
from .router import threat_router
from .state import auditstate


def analyze_logs(raw_logs: str):

    try:
        audit = auditstate(raw_logs)

        sentry_node(audit)

        if threat_router(audit) == "investigate":
            investigator_node(audit)

        finalize_node(audit)

        print(audit)

    except Exception as e:
        print(f"Error :{e}")

from .state import auditstate


def threat_router(state: auditstate):

    if state.severity in ["HIGH", "CRITICAL"]:
        return "investigate"

    return ""

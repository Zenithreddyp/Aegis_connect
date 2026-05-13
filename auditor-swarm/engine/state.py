import uuid

PURPLE = "\033[95m"
CYAN = "\033[96m"
DARKCYAN = "\033[36m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


class auditstate:
    def __init__(self, logs):
        self.logid = str(uuid.uuid4())[:8]
        self.logs = logs
        self.severity = None
        self.confidence = 0
        self.sentry_notes = None
        self.investigator_report = None
        self.enforcer_instructions = None  # For future settings
        self.status = "WAITING"

    def __str__(self):
        if self.status == "COMPLETED":
            if self.severity == "CRITICAL":
                color = PURPLE
            elif self.severity == "HIGH":
                color = RED
            elif self.severity == "MEDIUM":
                color = YELLOW
            else:
                color = GREEN
            return f"Log batch {CYAN}[{self.logid}]{RESET} has {color}{self.severity}{RESET} severity"
        return f"Log batch {CYAN}[{self.logid}]{RESET} is under process"

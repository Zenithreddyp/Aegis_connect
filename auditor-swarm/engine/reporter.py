import os
import threading
from datetime import datetime, timezone

from fpdf import FPDF

from .state import auditstate

# ── Configuration ────────────────────────────────────────────────────────────
REPORTS_DIR = os.environ.get(
    "AEGIS_REPORTS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports"),
)

# Severity → RGB colour mapping used for threat cards in the PDF
SEVERITY_COLOURS = {
    "CRITICAL": (148, 0, 211),   # purple
    "HIGH":     (220, 53, 69),   # red
    "MEDIUM":   (255, 193, 7),   # amber
    "LOW":      (40, 167, 69),   # green
    "SAFE":     (108, 117, 125), # grey
}


# ── PDF Builder ──────────────────────────────────────────────────────────────
class AegisReport(FPDF):
    """Custom FPDF subclass with Aegis branding."""

    def __init__(self, generated_at: str):
        super().__init__()
        self.generated_at = generated_at

    @staticmethod
    def _safe(text) -> str:
        """Encode text to latin-1, replacing unsupported Unicode chars."""
        text = str(text) if text is not None else ""
        return text.encode("latin-1", errors="replace").decode("latin-1")

    def _full_width(self) -> float:
        """Return the full usable width between margins."""
        return self.w - self.l_margin - self.r_margin

    def _reset_cursor(self):
        """Reset X to left margin to prevent cursor drift."""
        self.set_x(self.l_margin)

    def _safe_multi_cell(self, h, text, indent=0):
        """
        Wrapper around multi_cell that always resets X and uses an
        explicit width, preventing the 'Not enough horizontal space' error.
        """
        self._reset_cursor()
        w = self._full_width()
        if indent > 0 and indent < w - 20:
            self.set_x(self.l_margin + indent)
            w = w - indent
        # Safety clamp — never go below 20mm
        w = max(w, 20)
        self.multi_cell(w, h, self._safe(text))
        # Always reset X after multi_cell to prevent drift
        self._reset_cursor()

    # ── Header / Footer ──────────────────────────────────────────────────
    def header(self):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(30, 30, 30)
        self._reset_cursor()
        self.cell(self._full_width(), 10, "AEGIS-CONNECT", ln=True, align="L")

        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self._reset_cursor()
        self.cell(self._full_width(), 5, "Security Audit Report", ln=True, align="L")
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(160, 160, 160)
        self.cell(95, 10, self._safe(f"Generated: {self.generated_at}"), align="L")
        self.cell(95, 10, self._safe(f"Page {self.page_no()}/{{nb}}"), align="R")

    # ── Helpers ──────────────────────────────────────────────────────────
    def _section_title(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(40, 40, 40)
        self._reset_cursor()
        self.cell(self._full_width(), 10, self._safe(title), ln=True)
        self.ln(1)

    def _label_value(self, label: str, value, bold_value: bool = False):
        # Label on its own line
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(80, 80, 80)
        self._reset_cursor()
        self.cell(self._full_width(), 6, self._safe(f"{label}:"), ln=True)

        # Value indented slightly below
        self.set_font("Helvetica", "B" if bold_value else "", 10)
        self.set_text_color(30, 30, 30)
        self._safe_multi_cell(5, value, indent=5)

    def _severity_badge(self, severity: str):
        """Draw a coloured severity badge."""
        sev = self._safe(severity) if severity else "UNKNOWN"
        r, g, b = SEVERITY_COLOURS.get(sev, (108, 117, 125))
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        badge_w = self.get_string_width(f"  {sev}  ") + 4
        self._reset_cursor()
        self.cell(badge_w, 8, f"  {sev}  ", fill=True, ln=True)
        self.set_text_color(30, 30, 30)
        self.ln(3)

    def _horizontal_rule(self):
        y = self.get_y()
        self.set_draw_color(200, 200, 200)
        self.line(10, y, 200, y)
        self.ln(4)

    def _sub_heading(self, text: str):
        """Render a sub-heading label."""
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(80, 80, 80)
        self._reset_cursor()
        self.cell(self._full_width(), 6, self._safe(text), ln=True)

    # ── High-level sections ──────────────────────────────────────────────
    def add_executive_summary(self, audits: list):
        self._section_title("Executive Summary")
        total = len(audits)
        counts = {}
        for a in audits:
            sev = a.severity if a.severity else "UNKNOWN"
            counts[sev] = counts.get(sev, 0) + 1

        self._label_value("Total Findings", str(total))
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "SAFE", "UNKNOWN"):
            if sev in counts:
                self._label_value(f"  {sev}", str(counts[sev]))
        self.ln(3)
        self._horizontal_rule()

    def add_finding(self, idx: int, audit: auditstate):
        """Render a single finding card."""
        # ── Check if enough space, otherwise new page ────────────────────
        if self.get_y() > 230:
            self.add_page()

        self._section_title(f"Finding #{idx} -- Log Batch [{audit.logid}]")
        self._severity_badge(audit.severity)

        self._label_value("Confidence", f"{audit.confidence}%")
        self._label_value("Status", audit.status)

        # Sentry notes
        if audit.sentry_notes:
            self.ln(2)
            self._sub_heading("Sentry Analysis:")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(50, 50, 50)
            self._safe_multi_cell(5, audit.sentry_notes)
            self.ln(2)

        # Investigator deep-dive (only for HIGH / CRITICAL)
        if audit.investigator_report and isinstance(audit.investigator_report, dict):
            report = audit.investigator_report

            self._sub_heading("Investigator Deep-Dive:")

            # Thought trace
            if report.get("thought_trace"):
                self._label_value("Thought Trace", report["thought_trace"])

            # Root cause
            if report.get("root_cause_hypothesis"):
                self._label_value("Root Cause Hypothesis", report["root_cause_hypothesis"])

            # MITRE ATT&CK mapping
            mitre = report.get("mitre_attack_mapping")
            if mitre and isinstance(mitre, dict):
                tactic = mitre.get("tactic", "N/A")
                tech   = mitre.get("technique_id", "N/A")
                self._label_value("MITRE ATT&CK", f"{tactic}  ({tech})")

            # Suspicious log lines
            entries = report.get("suspicious_entries", [])
            if entries:
                self.ln(1)
                self._sub_heading("Suspicious Entries:")
                self.set_font("Courier", "", 8)
                self.set_text_color(60, 60, 60)
                if isinstance(entries, list):
                    for entry in entries:
                        self._safe_multi_cell(4, f"  > {entry}")
                else:
                    self._safe_multi_cell(4, f"  > {entries}")
                self.ln(1)

            # Recommended actions
            actions = report.get("recommended_actions", [])
            if actions:
                self._sub_heading("Recommended Actions:")
                self.set_font("Helvetica", "", 9)
                self.set_text_color(50, 50, 50)
                if isinstance(actions, list):
                    for action in actions:
                        self._safe_multi_cell(5, f"  - {action}")
                else:
                    self._safe_multi_cell(5, str(actions))
                self.ln(1)

        # Enforcer instructions
        if audit.enforcer_instructions:
            self._sub_heading("Enforcer Instructions:")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(50, 50, 50)
            if isinstance(audit.enforcer_instructions, list):
                for instr in audit.enforcer_instructions:
                    self._safe_multi_cell(5, f"  - {instr}")
            else:
                self._safe_multi_cell(5, str(audit.enforcer_instructions))
            self.ln(1)

        # Raw logs excerpt (truncated for readability)
        if audit.logs:
            self.ln(1)
            self._sub_heading("Raw Log Excerpt:")
            self.set_font("Courier", "", 7)
            self.set_text_color(100, 100, 100)
            excerpt = str(audit.logs)[:600]
            if len(str(audit.logs)) > 600:
                excerpt += "\n  ... [truncated]"
            self._safe_multi_cell(4, excerpt)

        self.ln(4)
        self._horizontal_rule()


# ── Report Bundler ───────────────────────────────────────────────────────────
class ReportBundler:
    """
    Thread-safe collector that batches completed audit states and
    generates a professional PDF report once the bundle threshold is met.
    """

    def __init__(self, bundle_size: int = 3):
        self.results: list[auditstate] = []
        self.lock = threading.Lock()
        self.bundle_size = bundle_size

    def add_result(self, audit: auditstate):
        with self.lock:
            self.results.append(audit)

            if len(self.results) >= self.bundle_size:
                chunk = self.results[: self.bundle_size]
                self.results = self.results[self.bundle_size :]
                self._generate_pdf(chunk)

    def flush(self):
        """Force-generate a report for any remaining findings."""
        with self.lock:
            if self.results:
                self._generate_pdf(list(self.results))
                self.results.clear()

    # ── Internal ─────────────────────────────────────────────────────────
    def _generate_pdf(self, audits: list[auditstate]):
        os.makedirs(REPORTS_DIR, exist_ok=True)

        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%dT%H-%M-%SZ")
        generated_at = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        filename = f"aegis_report_{timestamp}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        try:
            pdf = AegisReport(generated_at)
            pdf.alias_nb_pages()
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.add_page()

            # ── Title page info ──────────────────────────────────────────
            pdf.set_font("Helvetica", "B", 22)
            pdf.set_text_color(30, 30, 30)
            pdf._reset_cursor()
            pdf.cell(pdf._full_width(), 12, "Threat Analysis Report", ln=True, align="C")
            pdf.ln(2)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(100, 100, 100)
            pdf._reset_cursor()
            pdf.cell(pdf._full_width(), 6, pdf._safe(f"Report ID: {timestamp}"), ln=True, align="C")
            pdf._reset_cursor()
            pdf.cell(pdf._full_width(), 6, pdf._safe(f"Findings: {len(audits)}"), ln=True, align="C")
            pdf.ln(6)
            pdf._horizontal_rule()

            # ── Executive summary ────────────────────────────────────────
            pdf.add_executive_summary(audits)

            # ── Individual findings ──────────────────────────────────────
            for i, audit in enumerate(audits, start=1):
                try:
                    pdf.add_finding(i, audit)
                except Exception as finding_err:
                    print(f"[REPORTER] Warning: Could not render finding #{i} [{audit.logid}]: {finding_err}")
                    pdf._section_title(f"Finding #{i} -- [{audit.logid}] (render error)")
                    pdf._horizontal_rule()

            pdf.output(filepath)
            print(f"[REPORTER] PDF report saved -> {filepath}")

        except Exception as e:
            print(f"[REPORTER] Failed to generate PDF: {e}")

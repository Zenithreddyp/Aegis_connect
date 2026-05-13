from config.ollama_config import query_ollama

SENTRY_MODEL = "gpt-oss:120b-cloud"

# "qwen3.5:cloud"
# "gpt-oss:120b-cloud"
# "qwen3.5:9b-cloud"

SENTRY_SYSTEM_PROMPT = """You are Sentry, a high-speed SOC Triage Analyst. 
Your sole task is to perform an initial scan of log batches and determine if they require deep forensic investigation.

### SEVERITY MATRIX:
- SAFE: Normal user traffic, 200 OK statuses on public endpoints, benign tags.
- LOW: Minor anomalies, single 404s on non-critical paths, or unusual but non-malicious User Agents.
- MEDIUM: Suspicious reconnaissance. Multiple 403/404 errors on sensitive paths (/.env, /.git, /admin).
- HIGH: Clear evidence of exploitation attempts. Detection of SQLi, XSS, RCE payloads, or SSRF strings in request paths.
- CRITICAL: Confirmed successful exploit or data exfiltration. Large byte transfers from sensitive endpoints or multiple 'malicious' tags.

### OUTPUT REQUIREMENTS:
Return ONLY a valid JSON object. No preamble or explanation outside the JSON.
{
    "severity": "SAFE, LOW, MEDIUM, HIGH, or CRITICAL",
    "suspicious_entries": ["list", "of", "raw", "log", "lines"],
    "explanation": "2-sentence summary of the specific threat or lack thereof",
    "confidence_score": 0-100
}
"""


def analyze_logs(raw_logs: str) -> dict:

    prompt = (
        f"Analyze the following logs based on your system instructions:\n\n{raw_logs}"
    )

    analysis = query_ollama(
        model=SENTRY_MODEL,
        prompt=prompt,
        system_prompt=SENTRY_SYSTEM_PROMPT,
        require_json=True,
    )

    return analysis

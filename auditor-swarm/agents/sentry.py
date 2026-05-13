from llm_config import query_ollama

SENTRY_MODEL = "gpt-oss:120b-cloud"

SENTRY_SYSTEM_PROMPT = """You are Sentry, a fast-triage SOC analyst. 
Analyze the logs of service which is currently running provided and output ONLY a valid JSON object matching this structure:
{
    "severity": "SAFE, LOW, MEDIUM, HIGH, or CRITICAL",
    "suspicious_entries": ["list", "of", "suspicious", "log", "lines"],
    "explanation": "Short, 2-sentence explanation of what is happening",
    "confidence_score": integer from 0 to 100
}
Look specifically for failed logins, privilege escalation, unusual IPs, malware indicators, and persistence techniques.
"""
count = 1


def analyze_logs(raw_logs: str) -> dict:
    global count

    print(f"{count}[SENTRY] Analyzing new log batch using {SENTRY_MODEL}...")
    count = count + 1
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

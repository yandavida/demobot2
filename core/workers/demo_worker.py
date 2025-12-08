from __future__ import annotations

import os
import time


def main() -> None:
    """
    Worker דמו:
    כרגע לא עושה הרבה – רק רושם לוגים כל כמה שניות.
    בהמשך נחליף אותו ל-RQ/Celery עם Redis לתורים אמיתיים.
    """
    env = os.getenv("DEMOBOT_ENV", "dev")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

    print(f"[worker] Starting DemoBot worker in env={env}")
    print(f"[worker] Connected (logically) to Redis at: {redis_url}")
    print("[worker] Waiting for jobs... (demo loop)")

    try:
        while True:
            # פה בעתיד: poll לתור, עיבוד backtests וכו'
            time.sleep(10)
            print("[worker] still alive, no real jobs yet...")
    except KeyboardInterrupt:
        print("[worker] Shutting down gracefully.")


if __name__ == "__main__":
    main()

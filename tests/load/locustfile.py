"""Basic load test for the FAR Notes API. Run against a throwaway server, never port 3000.

    FAR_NOTES_DB=.test-data/load.sqlite FAR_NOTES_DISABLE_RATE_LIMIT=1 PORT=3200 npm start
    .venv/bin/locust -f tests/load/locustfile.py --host http://127.0.0.1:3200
"""
import random
import uuid

from locust import HttpUser, between, task

PASSWORD = "load-test-password-123"  # 15+ characters, like the app requires


class StudyUser(HttpUser):
    # Each simulated user waits 1-3 seconds between actions, like a real person.
    wait_time = between(1, 3)

    def on_start(self):
        """Runs once per simulated user: create an account, sign in, remember subsection ids."""
        name = f"load_{uuid.uuid4().hex[:12]}"
        self.client.post("/api/auth/register",
                         json={"username": name, "email": f"{name}@example.test", "password": PASSWORD})
        # Locust keeps cookies, so the study_session cookie is sent on every later request.
        self.client.post("/api/auth/login", json={"username": name, "password": PASSWORD})

        sections = self.client.get("/api/regulations?part=91").json()
        self.subsection_ids = [sub["id"] for section in sections for sub in section["subsections"]]

    # Weights add up to 10, so each pick is 50% Part 91, 20% Part 61, 30% saving.
    @task(5)
    def view_part_91(self):
        self.client.get("/api/regulations?part=91")

    @task(2)
    def view_part_61(self):
        self.client.get("/api/regulations?part=61")

    @task(3)
    def mark_subsection_covered(self):
        sub_id = random.choice(self.subsection_ids)
        self.client.patch(f"/api/subsections/{sub_id}?part=91",
                          json={"covered": True},
                          name="/api/subsections/[id]")  # group all ids into one row in the report

# SKILL: core-workflow (Backend & Docker Updates)

**Trigger:** Whenever you modify, refactor, or create backend code (Python, Flask, Node.js) or any script that runs inside a Docker container or a persistent local server.

**Rules:**
1. **Never assume code is live upon saving:** Modifying a file is only step one.
2. **Mandatory Rebuild/Restart:** You MUST autonomously execute the necessary terminal commands to apply the changes. 
   - If using Docker: run `docker compose up -d --build` or restart the specific container.
   - If using a local dev server (e.g., Flask/Gunicorn): restart the service or process.
3. **Log Verification:** After the rebuild/restart, wait 3 seconds and check the container/server logs to ensure the app booted successfully without syntax errors or crash loops.
4. **Test Execution:** If you modified a specific script or endpoint (e.g., a scraper), run a quick test command (e.g., `python script.py` or a `curl` request) inside the environment to verify the logic works with the new live code.
5. **Report:** End your response by confirming: "Code updated, container rebuilt, and logs verified successfully."
"""
Server Entrypoint
Ad-to-Sale Attribution System (Python Native)
"""

import uvicorn
from app.config import SERVER_HOST, SERVER_PORT

def start():
    print("=" * 65)
    print(" STARTING AD-TO-SALE ATTRIBUTION SERVER (PYTHON NATIVE)")
    print(f" Listening on: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f" Endpoints:")
    print(f"   - Dashboard:   http://localhost:{SERVER_PORT}/dashboard")
    print(f"   - Creator Sync: http://localhost:{SERVER_PORT}/api/sync-zoho-creator")
    print(f"   - Click Webhook: http://localhost:{SERVER_PORT}/webhook/click-log")
    print(f"   - Health Check: http://localhost:{SERVER_PORT}/health")
    print(f" Interactive Docs: http://localhost:{SERVER_PORT}/docs")
    print("=" * 65)
    uvicorn.run("app.server:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)

if __name__ == "__main__":
    start()

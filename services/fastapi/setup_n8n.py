"""
n8n Workflow Setup Script
Creates all required workflows via the n8n REST API.
Run inside the Docker network: docker exec jarvis-fastapi python setup_n8n.py
"""
import httpx
import json
import sys
import os
import uuid

N8N_URL = os.getenv("N8N_URL", "http://n8n:5678")
API_KEY = os.getenv("N8N_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

HEADERS = {
    "X-N8N-API-KEY": API_KEY,
    "Content-Type": "application/json",
}

WORKFLOWS = [
    # ──────────── 1. Reminder Scheduler (CRON every 1 min) ────────────
    {
        "name": "Jarvis - Reminder Scheduler",
        "nodes": [
            {
                "parameters": {
                    "rule": {"interval": [{"field": "minutes", "minutesInterval": 1}]}
                },
                "id": "cron-reminder",
                "name": "Every Minute",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "url": "http://jarvis-fastapi:8000/tools/reminders/due",
                    "options": {}
                },
                "id": "fetch-due",
                "name": "Fetch Due Reminders",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [470, 300]
            },
            {
                "parameters": {
                    "conditions": {
                        "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                        "conditions": [
                            {
                                "id": "cond-1",
                                "leftValue": "={{ $json.reminders.length }}",
                                "rightValue": "0",
                                "operator": {"type": "number", "operation": "gt"}
                            }
                        ],
                        "combinator": "and"
                    },
                    "options": {}
                },
                "id": "check-any",
                "name": "Any Due?",
                "type": "n8n-nodes-base.if",
                "typeVersion": 2.2,
                "position": [690, 300]
            },
            {
                "parameters": {
                    "fieldToSplitOut": "reminders",
                    "options": {}
                },
                "id": "split-reminders",
                "name": "Split Reminders",
                "type": "n8n-nodes-base.splitOut",
                "typeVersion": 1,
                "position": [910, 200]
            },
            {
                "parameters": {
                    "url": "=https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={\"chat_id\": \"{{ $json.chat_id }}\", \"text\": \"⏰ Reminder: {{ $json.message }}\"}"
                },
                "id": "send-telegram",
                "name": "Send Telegram",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [1130, 200]
            },
            {
                "parameters": {
                    "url": "=http://jarvis-fastapi:8000/tools/reminders/{{ $json.id }}/sent",
                    "sendBody": True,
                    "options": {}
                },
                "id": "mark-sent",
                "name": "Mark Sent",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [1350, 200]
            }
        ],
        "connections": {
            "Every Minute": {
                "main": [[{"node": "Fetch Due Reminders", "type": "main", "index": 0}]]
            },
            "Fetch Due Reminders": {
                "main": [[{"node": "Any Due?", "type": "main", "index": 0}]]
            },
            "Any Due?": {
                "main": [
                    [{"node": "Split Reminders", "type": "main", "index": 0}],
                    []
                ]
            },
            "Split Reminders": {
                "main": [[{"node": "Send Telegram", "type": "main", "index": 0}]]
            },
            "Send Telegram": {
                "main": [[{"node": "Mark Sent", "type": "main", "index": 0}]]
            }
        },
        "settings": {"executionOrder": "v1"}
    },

    # ──────────── 2. Note Saver ────────────
    {
        "name": "Jarvis - Note Saver",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "note-save",
                    "responseMode": "responseNode",
                    "options": {}
                },
                "id": str(uuid.uuid4()),
                "name": "Webhook - Note",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [250, 300],
                "webhookId": str(uuid.uuid4())
            },
            {
                "parameters": {
                    "url": "=http://jarvis-fastapi:8000/tools/memory_write",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={\"user_id\": \"{{ $json.body.user_id }}\", \"content\": \"{{ $json.body.text }}\", \"tags\": [], \"embed\": true}"
                },
                "id": "store-note",
                "name": "Store Note",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [470, 300]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ JSON.stringify($json) }}"
                },
                "id": "resp-note",
                "name": "Respond",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [690, 300]
            }
        ],
        "connections": {
            "Webhook - Note": {
                "main": [[{"node": "Store Note", "type": "main", "index": 0}]]
            },
            "Store Note": {
                "main": [[{"node": "Respond", "type": "main", "index": 0}]]
            }
        },
        "settings": {"executionOrder": "v1"}
    },

    # ──────────── 3. Health Check (every 30 min) ────────────
    {
        "name": "Jarvis - Health Check",
        "nodes": [
            {
                "parameters": {
                    "rule": {"interval": [{"field": "minutes", "minutesInterval": 30}]}
                },
                "id": "cron-health",
                "name": "Every 30 Minutes",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "url": "http://jarvis-fastapi:8000/diagnostics",
                    "options": {}
                },
                "id": "check-health",
                "name": "Check FastAPI Health",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [470, 300]
            }
        ],
        "connections": {
            "Every 30 Minutes": {
                "main": [[{"node": "Check FastAPI Health", "type": "main", "index": 0}]]
            }
        },
        "settings": {"executionOrder": "v1"}
    },

    # ──────────── 4. Telegram Intake ────────────
    {
        "name": "Jarvis - Telegram Intake",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "telegram-intake",
                    "responseMode": "responseNode",
                    "options": {}
                },
                "id": str(uuid.uuid4()),
                "name": "Webhook - Telegram",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [250, 300],
                "webhookId": str(uuid.uuid4())
            },
            {
                "parameters": {
                    "url": "http://jarvis-fastapi:8000/orchestrate",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={\"user_id\": \"{{ $json.body.user_id }}\", \"text\": \"{{ $json.body.text }}\"}"
                },
                "id": "call-fastapi",
                "name": "Call FastAPI",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [470, 300]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ JSON.stringify($json) }}"
                },
                "id": "resp-telegram",
                "name": "Respond",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [690, 300]
            }
        ],
        "connections": {
            "Webhook - Telegram": {
                "main": [[{"node": "Call FastAPI", "type": "main", "index": 0}]]
            },
            "Call FastAPI": {
                "main": [[{"node": "Respond", "type": "main", "index": 0}]]
            }
        },
        "settings": {"executionOrder": "v1"}
    },

    # ──────────── 5. RAG Ingest from Telegram ────────────
    {
        "name": "Jarvis - Ingest Handler",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "ingest",
                    "responseMode": "responseNode",
                    "options": {}
                },
                "id": str(uuid.uuid4()),
                "name": "Webhook - Ingest",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [250, 300],
                "webhookId": str(uuid.uuid4())
            },
            {
                "parameters": {
                    "url": "http://jarvis-fastapi:8000/rag/ingest",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={\"chunks\": {{ JSON.stringify($json.body.chunks || [$json.body.text]) }}, \"collection\": \"knowledge\", \"metadata\": {\"user_id\": \"{{ $json.body.user_id }}\", \"source\": \"telegram\"}}"
                },
                "id": "call-ingest",
                "name": "Ingest to Qdrant",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [470, 300]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ JSON.stringify($json) }}"
                },
                "id": "resp-ingest",
                "name": "Respond",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [690, 300]
            }
        ],
        "connections": {
            "Webhook - Ingest": {
                "main": [[{"node": "Ingest to Qdrant", "type": "main", "index": 0}]]
            },
            "Ingest to Qdrant": {
                "main": [[{"node": "Respond", "type": "main", "index": 0}]]
            }
        },
        "settings": {"executionOrder": "v1"}
    },

    # ──────────── 6. Error Catcher Template ────────────
    {
        "name": "Jarvis - Error Catcher",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "error-catch",
                    "responseMode": "responseNode",
                    "options": {}
                },
                "id": str(uuid.uuid4()),
                "name": "Webhook - Error",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [250, 300],
                "webhookId": str(uuid.uuid4())
            },
            {
                "parameters": {
                    "url": "http://jarvis-fastapi:8000/diagnose",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={\"workflow_name\": \"{{ $json.body.workflow_name }}\", \"error\": {{ JSON.stringify($json.body.error || {}) }}}"
                },
                "id": "call-diagnose",
                "name": "Diagnose Error",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [470, 300]
            },
            {
                "parameters": {
                    "url": "=https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={\"chat_id\": \"{{ $json.body.alert_chat_id || '' }}\", \"text\": \"🚨 Workflow Error\\nWorkflow: {{ $json.workflow_name }}\\nDiagnosis: {{ $json.diagnosis }}\"}"
                },
                "id": "alert-telegram",
                "name": "Alert via Telegram",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [690, 200]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ JSON.stringify($json) }}"
                },
                "id": "resp-error",
                "name": "Respond",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [690, 400]
            }
        ],
        "connections": {
            "Webhook - Error": {
                "main": [[{"node": "Diagnose Error", "type": "main", "index": 0}]]
            },
            "Diagnose Error": {
                "main": [
                    [
                        {"node": "Alert via Telegram", "type": "main", "index": 0},
                        {"node": "Respond", "type": "main", "index": 0}
                    ]
                ]
            }
        },
        "settings": {"executionOrder": "v1"}
    }
]


def main():
    client = httpx.Client(timeout=15)

    # Check connectivity
    try:
        resp = client.get(f"{N8N_URL}/api/v1/workflows", headers=HEADERS)
        existing = resp.json().get("data", [])
        existing_names = {w["name"] for w in existing}
        print(f"✅ Connected to n8n. {len(existing)} existing workflows.")
    except Exception as e:
        print(f"❌ Cannot connect to n8n: {e}")
        sys.exit(1)

    # Create workflows
    created = 0
    for wf in WORKFLOWS:
        if wf["name"] in existing_names:
            print(f"⏭️  Skipping '{wf['name']}' (already exists)")
            continue

        try:
            resp = client.post(
                f"{N8N_URL}/api/v1/workflows",
                headers=HEADERS,
                json=wf,
            )
            if resp.status_code == 200:
                wf_id = resp.json().get("id", "?")
                print(f"✅ Created '{wf['name']}' (ID: {wf_id})")

                # Activate the workflow
                activate_resp = client.post(
                    f"{N8N_URL}/api/v1/workflows/{wf_id}/activate",
                    headers=HEADERS,
                )
                if activate_resp.status_code == 200:
                    print(f"   ✅ Activated")
                else:
                    print(f"   ⚠️  Activation failed: {activate_resp.text[:100]}")
                created += 1
            else:
                print(f"❌ Failed to create '{wf['name']}': {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"❌ Error creating '{wf['name']}': {e}")

    print(f"\n🎉 Done! Created {created} new workflows.")


if __name__ == "__main__":
    main()

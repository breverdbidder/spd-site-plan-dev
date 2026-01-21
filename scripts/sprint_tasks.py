#!/usr/bin/env python3
"""
Sprint Task Manager CLI
Add, list, and manage tasks for Ralphy execution
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)

# Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mocerqjnksmhcjzxrewo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def add_task(
    title: str,
    description: str = "",
    priority: int = 5,
    complexity: int = 5,
    domain: str = "BUSINESS",
    context: Optional[dict] = None,
    tags: Optional[list] = None,
) -> dict:
    """Add a new task to the sprint queue."""
    
    payload = {
        "title": title,
        "description": description,
        "priority": priority,
        "complexity": complexity,
        "domain": domain,
        "context": context or {},
        "tags": tags or [],
        "status": "pending",
        "source": "cli",
    }
    
    response = httpx.post(
        f"{SUPABASE_URL}/rest/v1/sprint_tasks",
        headers={**HEADERS, "Prefer": "return=representation"},
        json=payload,
    )
    
    if response.status_code == 201:
        task = response.json()[0]
        print(f"✅ Task created: {task['id']}")
        print(f"   Title: {task['title']}")
        print(f"   Priority: {task['priority']}")
        return task
    else:
        print(f"❌ Failed to create task: {response.text}")
        return {}


def list_tasks(status: str = "pending", limit: int = 10) -> list:
    """List tasks by status."""
    
    url = f"{SUPABASE_URL}/rest/v1/sprint_tasks"
    params = {
        "status": f"eq.{status}",
        "order": "priority.desc,created_at.asc",
        "limit": limit,
    }
    
    response = httpx.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        tasks = response.json()
        print(f"\n📋 {status.upper()} Tasks ({len(tasks)}):\n")
        for task in tasks:
            print(f"  [{task['priority']}] {task['title']}")
            print(f"      ID: {task['id'][:8]}... | Domain: {task.get('domain', 'N/A')}")
            if task.get('description'):
                print(f"      {task['description'][:60]}...")
            print()
        return tasks
    else:
        print(f"❌ Failed to list tasks: {response.text}")
        return []


def get_stats() -> dict:
    """Get task statistics."""
    
    response = httpx.post(
        f"{SUPABASE_URL}/rest/v1/rpc/get_task_stats",
        headers=HEADERS,
    )
    
    if response.status_code == 200:
        stats = response.json()[0] if response.json() else {}
        print("\n📊 Sprint Task Statistics:\n")
        print(f"  Total Tasks:      {stats.get('total_tasks', 0)}")
        print(f"  Pending:          {stats.get('pending_tasks', 0)}")
        print(f"  In Progress:      {stats.get('in_progress_tasks', 0)}")
        print(f"  Completed:        {stats.get('completed_tasks', 0)}")
        print(f"  Failed:           {stats.get('failed_tasks', 0)}")
        print(f"  Avg Iterations:   {stats.get('avg_iterations', 'N/A')}")
        print(f"  Completion Rate:  {stats.get('completion_rate', 'N/A')}%")
        return stats
    else:
        print(f"❌ Failed to get stats: {response.text}")
        return {}


def update_status(task_id: str, new_status: str) -> bool:
    """Update task status."""
    
    valid_statuses = ["pending", "in_progress", "completed", "failed", "blocked", "deferred"]
    if new_status not in valid_statuses:
        print(f"❌ Invalid status. Must be one of: {valid_statuses}")
        return False
    
    payload = {"status": new_status}
    if new_status == "pending":
        payload["started_at"] = None
        payload["completed_at"] = None
    
    response = httpx.patch(
        f"{SUPABASE_URL}/rest/v1/sprint_tasks?id=eq.{task_id}",
        headers={**HEADERS, "Prefer": "return=minimal"},
        json=payload,
    )
    
    if response.status_code == 204:
        print(f"✅ Task {task_id[:8]}... status updated to: {new_status}")
        return True
    else:
        print(f"❌ Failed to update task: {response.text}")
        return False


def bulk_add(file_path: str) -> int:
    """Add multiple tasks from a JSON file."""
    
    with open(file_path, 'r') as f:
        tasks = json.load(f)
    
    if not isinstance(tasks, list):
        tasks = [tasks]
    
    created = 0
    for task in tasks:
        result = add_task(
            title=task['title'],
            description=task.get('description', ''),
            priority=task.get('priority', 5),
            complexity=task.get('complexity', 5),
            domain=task.get('domain', 'BUSINESS'),
            context=task.get('context'),
            tags=task.get('tags'),
        )
        if result:
            created += 1
    
    print(f"\n✅ Created {created}/{len(tasks)} tasks")
    return created


def main():
    parser = argparse.ArgumentParser(description="Sprint Task Manager for Ralphy")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Add task
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", help="Task title")
    add_parser.add_argument("-d", "--description", default="", help="Task description")
    add_parser.add_argument("-p", "--priority", type=int, default=5, help="Priority 1-10 (default: 5)")
    add_parser.add_argument("-c", "--complexity", type=int, default=5, help="Complexity 1-10 (default: 5)")
    add_parser.add_argument("--domain", choices=["BUSINESS", "MICHAEL", "FAMILY", "PERSONAL"], default="BUSINESS")
    add_parser.add_argument("--context", type=json.loads, help="JSON context object")
    add_parser.add_argument("--tags", nargs="+", help="Tags for the task")
    
    # List tasks
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("-s", "--status", default="pending", help="Status filter (default: pending)")
    list_parser.add_argument("-n", "--limit", type=int, default=10, help="Max tasks to show")
    
    # Stats
    subparsers.add_parser("stats", help="Show task statistics")
    
    # Update status
    update_parser = subparsers.add_parser("update", help="Update task status")
    update_parser.add_argument("task_id", help="Task ID")
    update_parser.add_argument("status", help="New status")
    
    # Bulk add
    bulk_parser = subparsers.add_parser("bulk", help="Bulk add tasks from JSON file")
    bulk_parser.add_argument("file", help="JSON file with tasks")
    
    args = parser.parse_args()
    
    if not SUPABASE_KEY:
        print("❌ SUPABASE_KEY environment variable not set")
        sys.exit(1)
    
    if args.command == "add":
        add_task(
            title=args.title,
            description=args.description,
            priority=args.priority,
            complexity=args.complexity,
            domain=args.domain,
            context=args.context,
            tags=args.tags,
        )
    elif args.command == "list":
        list_tasks(status=args.status, limit=args.limit)
    elif args.command == "stats":
        get_stats()
    elif args.command == "update":
        update_status(args.task_id, args.status)
    elif args.command == "bulk":
        bulk_add(args.file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

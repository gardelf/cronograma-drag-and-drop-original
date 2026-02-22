"""
Complete Todoist Demo - Show all tasks organized by labels, projects, and priorities
"""

from config import get_config
from todoist_client import TodoistClient
import json
from collections import defaultdict

config = get_config()
todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])

print("="*80)
print("📋 TODOIST COMPLETE DEMO - ALL TASKS EXTRACTION")
print("="*80)

# Get ALL active tasks (not just today)
print("\n🔍 Fetching ALL active tasks from Todoist...")
all_tasks = todoist_client.get_all_active_tasks()
formatted_tasks = todoist_client.format_tasks_for_display(all_tasks)

print(f"✅ Found {len(formatted_tasks)} total active tasks\n")

# Organize by different criteria
tasks_by_label = defaultdict(list)
tasks_by_priority = defaultdict(list)
tasks_by_project = defaultdict(list)

for task in formatted_tasks:
    # By priority
    priority = task['priority']
    tasks_by_priority[priority].append(task)
    
    # By project
    project_id = task.get('project_id', 'No Project')
    tasks_by_project[project_id].append(task)
    
    # By labels
    labels = task.get('labels', [])
    if labels:
        for label in labels:
            tasks_by_label[label].append(task)
    else:
        tasks_by_label['Sin etiqueta'].append(task)

# Display organized results
print("="*80)
print("📊 TASKS ORGANIZED BY PRIORITY")
print("="*80)

priority_order = ['Urgente', 'Alta', 'Media', 'Baja']
for priority in priority_order:
    tasks = tasks_by_priority.get(priority, [])
    if tasks:
        print(f"\n🔴 {priority.upper()} ({len(tasks)} tasks):")
        for task in tasks:
            due_info = f" [Due: {task['due_date']}]" if task['due_date'] else ""
            labels_info = f" {task['labels']}" if task['labels'] else ""
            print(f"  • {task['content']}{due_info}{labels_info}")

print("\n" + "="*80)
print("🏷️  TASKS ORGANIZED BY LABELS")
print("="*80)

for label, tasks in sorted(tasks_by_label.items()):
    print(f"\n📌 {label} ({len(tasks)} tasks):")
    for task in tasks:
        due_info = f" [Due: {task['due_date']}]" if task['due_date'] else ""
        print(f"  • {task['content']} - Priority: {task['priority']}{due_info}")

print("\n" + "="*80)
print("📁 TASKS ORGANIZED BY PROJECT")
print("="*80)

for project_id, tasks in tasks_by_project.items():
    print(f"\n📂 Project ID: {project_id} ({len(tasks)} tasks):")
    for task in tasks:
        due_info = f" [Due: {task['due_date']}]" if task['due_date'] else ""
        labels_info = f" {task['labels']}" if task['labels'] else ""
        print(f"  • {task['content']} - {task['priority']}{due_info}{labels_info}")

print("\n" + "="*80)
print("📈 SUMMARY STATISTICS")
print("="*80)

print(f"\n📊 Total Tasks: {len(formatted_tasks)}")
print(f"🏷️  Unique Labels: {len([l for l in tasks_by_label.keys() if l != 'Sin etiqueta'])}")
print(f"📁 Projects: {len(tasks_by_project)}")
print(f"\nPriority Breakdown:")
for priority in priority_order:
    count = len(tasks_by_priority.get(priority, []))
    print(f"  • {priority}: {count} tasks")

# Show detailed JSON of first task as example
print("\n" + "="*80)
print("🔍 DETAILED DATA EXAMPLE (First Task)")
print("="*80)

if formatted_tasks:
    print("\nFormatted Task Data:")
    print(json.dumps(formatted_tasks[0], indent=2, ensure_ascii=False))
    
    print("\nRaw API Data:")
    print(json.dumps(all_tasks[0], indent=2, ensure_ascii=False))

print("\n" + "="*80)
print("✅ DEMO COMPLETE")
print("="*80)
print("\nThis shows ALL the data that can be extracted from Todoist:")
print("  ✓ Task content and description")
print("  ✓ Priority levels (1-4)")
print("  ✓ Due dates and times")
print("  ✓ Labels/tags")
print("  ✓ Project IDs")
print("  ✓ Task URLs")
print("  ✓ Creation dates")
print("  ✓ Recurring status")

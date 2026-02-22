"""
Todoist API Client
Handles fetching tasks from Todoist API
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime


class TodoistClient:
    """Client for interacting with Todoist REST API v2"""
    
    BASE_URL = "https://api.todoist.com/api/v1"
    
    def __init__(self, api_token: str):
        """
        Initialize Todoist client
        
        Args:
            api_token: Todoist API token
        """
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def get_today_tasks(self) -> List[Dict]:
        """
        Get all tasks due today
        
        Returns:
            List of task dictionaries
        """
        try:
            url = f"{self.BASE_URL}/tasks"
            params = {"filter": "today"}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            # New API returns {"results": [...]}
            tasks = data.get('results', data) if isinstance(data, dict) else data
            return tasks
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tasks from Todoist: {e}")
            return []
    
    def get_all_active_tasks(self) -> List[Dict]:
        """
        Get all active (non-completed) tasks with pagination support
        
        Returns:
            List of task dictionaries
        """
        try:
            all_tasks = []
            url = f"{self.BASE_URL}/tasks"
            cursor = None
            
            # Paginate through all tasks
            while True:
                params = {}
                if cursor:
                    params['cursor'] = cursor
                
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                # New API returns {"results": [...]}
                tasks = data.get('results', data) if isinstance(data, dict) else data
                
                if isinstance(tasks, list):
                    all_tasks.extend(tasks)
                else:
                    all_tasks.append(tasks)
                
                # Check if there are more pages
                next_cursor = data.get('next_cursor') if isinstance(data, dict) else None
                if not next_cursor:
                    break
                cursor = next_cursor
            
            print(f"✅ Fetched {len(all_tasks)} tasks from Todoist (with pagination)")
            return all_tasks
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tasks from Todoist: {e}")
            return []
    
    def format_tasks_for_display(self, tasks: List[Dict]) -> List[Dict]:
        """
        Format tasks for display in the agenda
        
        Args:
            tasks: List of raw task dictionaries from API
            
        Returns:
            List of formatted task dictionaries
        """
        formatted_tasks = []
        
        for task in tasks:
            formatted_task = {
                "id": task.get("id"),
                "content": task.get("content", "Sin título"),
                "description": task.get("description", ""),
                "priority": self._get_priority_label(task.get("priority", 1)),
                "priority_value": task.get("priority", 1),
                "labels": task.get("labels", []),
                "due_date": self._format_due_date(task.get("due")),
                "due_time": self._extract_due_time(task.get("due")),
                "project_id": task.get("project_id"),
                "url": task.get("url", "")
            }
            formatted_tasks.append(formatted_task)
        
        return formatted_tasks
    
    def _get_priority_label(self, priority: int) -> str:
        """Convert priority number to label"""
        priority_map = {
            4: "Urgente",
            3: "Alta",
            2: "Media",
            1: "Baja"
        }
        return priority_map.get(priority, "Baja")
    
    def _format_due_date(self, due: Optional[Dict]) -> Optional[str]:
        """Extract and format due date"""
        if not due:
            return None
        return due.get("date")
    
    def _extract_due_time(self, due: Optional[Dict]) -> Optional[str]:
        """Extract time from due datetime"""
        if not due:
            return None
        
        datetime_str = due.get("datetime")
        if datetime_str:
            try:
                dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
                return dt.strftime("%H:%M")
            except:
                pass
        
        return None
    
    def complete_task(self, task_id: str) -> bool:
        """
        Mark a task as completed in Todoist
        
        Args:
            task_id: ID of the task to complete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/tasks/{task_id}/close"
            
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            
            print(f"✅ Task {task_id} marked as completed in Todoist")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error completing task {task_id}: {e}")
            return False


if __name__ == "__main__":
    # Test the client
    from config import get_config
    
    config = get_config()
    token = config['TODOIST_API_TOKEN']
    if token:
        client = TodoistClient(token)
        tasks = client.get_today_tasks()
        formatted = client.format_tasks_for_display(tasks)
        
        print(f"Found {len(formatted)} tasks for today:")
        for task in formatted:
            print(f"- {task['content']} (Priority: {task['priority']})")
    else:
        print("TODOIST_API_TOKEN not found in environment")

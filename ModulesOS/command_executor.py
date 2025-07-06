import subprocess
import json
import time
from typing import Optional

class CommandExecutor:
    """Handles command execution and task management."""

    MAIN_PY_PATH = "/opt/utils/cwmCLI/main.py"

    @staticmethod
    def run_command(command: str) -> Optional[str]:
        """
        Runs a shell command and captures the output.
        Logs errors if the command fails.
        """
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, text=True)
            return result.stdout.strip()
        except Exception as e:
            print(f"Error running command: {e}")
            return None

    @classmethod
    def wait_queue(cls, task_id: str, timeout: Optional[int] = None, interval: Optional[int] = None) -> str:
        """
        Waits for a task in the queue to complete and checks if exitCode is 0.
        """
        try:
            print(f"Waiting for queue task {task_id} to complete...\n")
            command = f"{cls.MAIN_PY_PATH} queue wait -id {task_id}"
            if timeout:
                command += f" -t {timeout}"
            if interval:
                command += f" -i {interval}"
            result = cls.run_command(command)
            if not result:
                print(f"Error: No result from queue wait for task {task_id}")
                return "❌"

            try:
                task_data = json.loads(result)
                exit_code = task_data.get("exitCode", -1)
                if exit_code == 0:
                    print(f"Task {task_id} completed successfully.\n")
                    return "✅"
                else:
                    print(f"Task {task_id} failed with exitCode: {exit_code}.")
                    return "❌"
            except json.JSONDecodeError:
                print(f"Error: Task {task_id} returned a non-JSON response: {result}")
                return "❌"
        except Exception as e:
            print(f"Error in wait_queue for task {task_id}: {e}")
            return "❌"

    @staticmethod
    def extract_task_id(command_output: str) -> Optional[str]:
        """
        Extracts a task ID directly from the command output.
        Handles JSON with a single 'cmdId', a list of task IDs, or plain integer strings.
        Returns the first valid task ID as a string.
        """
        try:
            print(f"Command Results: {command_output}")
            if command_output.startswith("{") or command_output.startswith("["):
                try:
                    tasks_data = json.loads(command_output)
                    if isinstance(tasks_data, dict):
                        task_id = tasks_data.get("cmdId")
                        if task_id:
                            print(f"Extracted Task ID: {task_id}\n")
                            return str(task_id)
                    elif isinstance(tasks_data, list):
                        for task_id in tasks_data:
                            if isinstance(task_id, int):
                                print(f"Extracted Task ID: {task_id}\n")
                                return str(task_id)
                    print("No valid Task ID found in JSON response.")
                    return None
                except json.JSONDecodeError:
                    print(f"Error decoding JSON: {command_output}")
            task_id = str(command_output.strip())
            if task_id.isdigit():
                print(f"Extracted Task ID: {task_id}")
                return task_id
            raise ValueError("Could not extract Task ID.")
        except Exception as e:
            print(f"Error extracting task ID: {e}")
            return None

    @classmethod
    def extract_clone_task_id(cls, machine_name: str, index: int, timeout: int = 120, interval: int = 10) -> Optional[str]:
        """
        Waits for the task ID to appear in the queue by filtering with the specific cloned service name.
        Constructs the service name as `{machine_name}{index}-clone` to match the queue output.
        """
        start_time = time.time()
        expected_service_name = f"{machine_name}{index}-clone"
        print(f"Expected service name: {expected_service_name}\n")
        while time.time() - start_time < timeout:
            print(f"Checking queue for task with service name '{expected_service_name}'...\n")
            queue_output = cls.run_command(f"{cls.MAIN_PY_PATH} queue list")
            if not queue_output:
                print("Error: No output from queue list command.")
                time.sleep(interval)
                continue
            try:
                queue_data = json.loads(queue_output)
                if isinstance(queue_data, list):
                    for task in queue_data:
                        service_name = task.get("serviceName", "")
                        task_id = task.get("id")
                        if service_name == expected_service_name and task_id:
                            print(f"Found task ID {task_id} for service name '{expected_service_name}'.\n")
                            return str(task_id)
                    print(f"No matching task found for service name '{expected_service_name}'. Retrying in {interval} seconds...")
                else:
                    print(f"Unexpected queue data format: {queue_data}")
            except json.JSONDecodeError as e:
                print(f"Error parsing queue list JSON: {queue_output}, Error: {e}")
            time.sleep(interval)
        print(f"Timeout reached: Task with service name '{expected_service_name}' not found within {timeout} seconds.")
        return None

    @classmethod
    def execute_task(cls, command: str) -> str:
        """
        Executes a command, extracts the task ID, and waits for the task to complete.
        """
        result = cls.run_command(command)
        if result is None:
            return "❌"
        task_id = cls.extract_task_id(result)
        if task_id:
            return cls.wait_queue(task_id)
        return "❌"

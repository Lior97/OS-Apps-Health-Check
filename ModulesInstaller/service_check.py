import requests
import logging
import urllib3
from rich.logging import RichHandler
from typing import Any, Dict, List

# Configure logging with RichHandler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)

# Suppress only the Insecure Request Warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ServiceChecker:
    def __init__(self, ssh_manager):
        self.ssh = ssh_manager

    def check_service_installed(self, service_name: str) -> bool:
        command = f"dpkg -l | grep {service_name}"
        output = self.ssh.exec_command(command)
        return bool(output)

    def check_service_status(self, service_name: str) -> bool:
        command = f"systemctl is-active {service_name}"
        output = self.ssh.exec_command(command)
        return output.strip() == "active"

    def check_open_ports_v4(self) -> list:
        command = "ufw status | grep -v 'v6' | grep -i 'allow' | awk '{printf(\"%s\\n\", $1)}'"
        open_ports_v4 = self.ssh.exec_command(command)
        logging.info(f"Getting V4 Ports from Firewall")
        return open_ports_v4.strip().splitlines()
    
    def check_open_ports_v6(self) -> list:
        command = "ufw status | grep 'v6' | grep -i 'allow' | awk '{printf(\"%s\\n\", $1)}'"
        open_ports_v6 = self.ssh.exec_command(command)
        logging.info(f"Getting V6 ports from Firewall")
        return open_ports_v6.strip().splitlines()
    
    def check_listening_port(self, port: int) -> str:
        command = f"ss -ltn | grep :{port}"
        output = self.ssh.exec_command(command)
        return "Listening" if output else "Not Listening"

    def check_web_access(self, host: str, ports: List[int]) -> Dict[int, Dict[str, str]]:
        protocols = ["http", "https"]
        connectivity_results = {}

        for port in ports:
            connectivity_results[port] = {protocol: "❌" for protocol in protocols}

            for protocol in protocols:
                url = f"{protocol}://{host}:{port}"
                try:
                    logging.info(f"Checking {url}...")
                    response = requests.get(url, timeout=5, verify=False)
                    if response.status_code == 200:
                        connectivity_results[port][protocol] = "✅"
                except requests.RequestException as e:
                    logging.debug(f"Failed to connect to {url}: {e}")

        return connectivity_results

    
    def process_service(self, service: Dict[str,Any], report: Any) -> None:
        service_name = service["name"]
        installed = self.check_service_installed(service_name)
        enabled = self.check_service_status(service_name)

        # Check listening status for each port defined in the service
        listeners: List[str] = []
        for port_info in service.get("ports", []):
            port = port_info.get("port")
            if port:  # Ensure the port is defined
                listener_status = self.check_listening_port(port)
                listeners.append(f"{port} ({listener_status})")

        # Add information to the report with "V"/"X"
        report.add_installer_row(service_name, "✅" if installed else "❌", "✅" if enabled else "❌", listeners)

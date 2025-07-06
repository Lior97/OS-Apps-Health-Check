from rich.console import Console
from rich.table import Table
from enum import Enum

class TableType(Enum):
    INSTALLER = 1
    WEB = 2 
    OS = 3

class ReportGenerator:
    def __init__(self, app_or_os: TableType):
        self.console = Console()
        self.app_or_os = app_or_os
        self.table = Table(show_header=True, header_style="bold red")

        # Set up tables for all types
        self._setup_tables(app_or_os)

    def _setup_tables(self, app_or_os: TableType):
        columns = []
        if app_or_os == TableType.INSTALLER:
            columns = ["Service Name", "Installed", "Enabled", "Listeners"]
        elif app_or_os == TableType.WEB:
            columns = ["Services Ports", "UFW V4 Ports", "UFW V6 Ports", "HTTP", "HTTPS"]
        elif app_or_os == TableType.OS:
            columns = ["Rename", "Change Password", "Add IP", "Remove IP", "Add NIC", "Remove NIC", "Add HD", "Resize HD", "Remove HD"]

        for column in columns:
            self.table.add_column(column)

    def add_installer_row(self, service_name: str, installed: str, enabled: str, listeners: list) -> None:
        self.table.add_row(service_name, installed, enabled, ", ".join(listeners))

    def add_web_row(self, port: str, v4_ports: list, v6_ports: list, http_status: str, https_status: str) -> None:
        # Extract relevant V4 and V6 ports to avoid duplicating entries
        v4_port_display = v4_ports.pop(0) if v4_ports else None
        v6_port_display = v6_ports.pop(0) if v6_ports else None
        self.table.add_row(str(port), v4_port_display, v6_port_display, http_status, https_status)

    def add_os_row(self, rename: str, change_password: str, add_ip: str, remove_ip: str, add_nic: str, remove_nic: str, add_hd: str, resize_hd: str, remove_hd: str) -> None:
        self.table.add_row(rename, change_password, add_ip, remove_ip, add_nic, remove_nic, add_hd, resize_hd, remove_hd)

    def display_tables(self):
        self.console.print(self.table)

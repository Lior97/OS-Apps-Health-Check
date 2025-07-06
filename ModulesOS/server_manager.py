import random
import csv
from typing import Optional
from Modules.ssh import SSHManager
from .rdp import RDPManager
from .command_executor import CommandExecutor

class ServerManager:
    def __init__(self, executor: CommandExecutor):
        self.executor = executor
        self.ssh_manager = None
        self.rdp_manager = None
        self.os_type = None
        self.network_path = None
        self.dns_path = "/etc/resolv.conf"
        self.new_password = None
        self.index = 1
        self.size = 50
        self.auto_ip = "auto"
        self.get_random_ip()

    def set_connection_managers(self, ip: str, password: str, os_type: Optional[str] = None) -> bool:
        """Set up connection managers with initial password and prepare for updates."""
        print("Setting up connection managers...")
        self.new_password = f"{password}{self.index}"

        if os_type == "windows":
            self.os_type = "windows"
            if not self._update_connection(ip, password):
                print("Error: Failed to establish RDP connection with initial password.")
                self.os_type = "unknown"
                return False
        else:
            print("Attempting OS detection via SSH with initial password...")
            if not self._update_connection(ip, password) or not self.ssh_manager:
                print("Error: Failed to establish SSH connection with initial password.")
                self.os_type = "unknown"
                return False
            os_id = self.ssh_manager.exec_command("grep -i '^ID=' /etc/os-release | cut -d= -f2 | tr -d '\"'").strip().lower()
            self.os_type = os_id if os_id else "unknown"

        self.network_path = {
            "ubuntu": "/etc/netplan/50-cloud-init.yaml",
            "archlinux": "/etc/netplan/50-cloud-init.yaml",
            "linuxmint": "/etc/netplan/50-cloud-init.yaml",
            "debian": "/etc/network/interfaces",
            "rhel": "/etc/sysconfig/network-scripts/ifcfg-*",
            "centos": "/etc/NetworkManager/system-connections/*.nmconnection",
            "almalinux": ["/etc/sysconfig/network-scripts/ifcfg-*","/etc/NetworkManager/system-connections/*.nmconnection"],
            "rocky": ["/etc/sysconfig/network-scripts/ifcfg-*","/etc/NetworkManager/system-connections/*.nmconnection"],
            "freebsd": "/etc/rc.net.conf",
        }.get(self.os_type)

        if not self.network_path and self.os_type != "windows":
            print(f"Warning: No network config path for OS '{self.os_type}'")

        print(f"Connection setup successful for {self.os_type} with initial password.")
        print(f"Detected OS: {self.os_type}")
        print(f"Network Path: {self.network_path}")
        return True

    def _update_connection(self, ip: str, password: str) -> bool:
            """Establishes or reuses the connection with the specified password."""
            if self.os_type == "windows":
                if self.rdp_manager and self.rdp_manager.is_connected():
                    # Verify the RDP connection is still usable
                    try:
                        test_result = self.rdp_manager.run_ps("Write-Output 'x'")
                        if test_result and "x" in test_result.strip():
                            return True
                        else:
                            print("RDP connection active but test failed, re-establishing...")
                    except:
                        print(f"Establishing new RDP connection...")
                self.rdp_manager = RDPManager(ip, "Administrator", password)
                self.ssh_manager = None
                if not self.rdp_manager.is_connected():
                    print("RDP connection failed, attempting to re-establish...")
                    self.rdp_manager = RDPManager(ip, "Administrator", password)
                return self.rdp_manager.is_connected()
            else:
                if self.ssh_manager and self.ssh_manager.is_connected():
                    try:
                        test_result = self.ssh_manager.exec_command("echo x")
                        if test_result and "x" in test_result.strip():
                            return True
                        else:
                            print("SSH connection active but test failed, re-establishing...")
                    except:
                        print(f"Establishing new SSH connection...")
                self.ssh_manager = SSHManager(ip, "root", password)
                self.rdp_manager = None
                if not self.ssh_manager.is_connected():
                    print("SSH connection failed, attempting to re-establish...")
                    self.ssh_manager = SSHManager(ip, "root", password)
                return self.ssh_manager.is_connected()

    def get_random_ip(self) -> str:
        """Sets self.lan_ip to a random IP. """
        third_octet = random.randint(0, 255)
        fourth_octet = random.randint(1, 254)
        self.lan_ip = f"172.16.{third_octet}.{fourth_octet}"
        return self.lan_ip

    def save_results_to_csv(self, filename: str, results: dict) -> None:
        """Save the results to a CSV file."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(results.keys())
            writer.writerow(results.values())

    def _exec_command(self, command: str) -> Optional[str]:
        """Helper method to execute a command using the established connection."""
        if self.os_type is None:
            print("Error: OS type not determined yet.")
            return None
        if self.os_type == "windows" and self.rdp_manager:
            return self.rdp_manager.run_ps(command)
        elif self.ssh_manager:
            try:
                return self.ssh_manager.exec_command(command)
            except ConnectionResetError as e:
                print(f"Connection reset during command execution (error: {e}), connection likely dropped.")
                return None
        print("Error: No valid connection established.")
        return None

    def poweroff_server(self, machine_uuid: str) -> str:
        """Power off the server."""
        print("Powering off the server...\n")
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" power --state off'
        return self.executor.execute_task(command)

    def poweron_server(self, machine_uuid: str) -> str:
        """Power on the server."""
        print("Powering on the server...\n")
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" power --state on'
        return self.executor.execute_task(command)

    def rename_server(self, machine_uuid: str, machine_name: str) -> str:
        """Rename the server."""
        print("Renaming the server\n")
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid {machine_uuid} rename -n {machine_name}{self.index}'
        return self.executor.execute_task(command)

    def change_password(self, machine_uuid: str, ip_address: str) -> str:
        """Change the server password."""
        if not self.new_password:
            print("Error: New password has not been set.")
            return "❌"

        print("Changing the server password\n")
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" password -p {self.new_password}'
        res = self.executor.execute_task(command)
        if res == "✅":
            if not self._update_connection(ip_address, self.new_password):
                print("Error: Failed to update connection with new password.")
                return "❌"
            return "✅"
        return "❌"

    def add_ip(self, machine_uuid: str, mac_address: str, ip_address: str, dns: str, gateway: str, subnet: str) -> str:
        """Add IP to the server."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        print("Adding IP to the server\n")
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" network nic add --ip {self.auto_ip} --mac {mac_address}'
        res = self.executor.execute_task(command)

        command2 = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" network list | jq -r \'.nics[].ips[] | select(. != "{ip_address}")\''
        new_ip = self.executor.run_command(command2)
        if new_ip is None:
            print("Error: Failed to get new IP address.")
            return "❌"

        if res == "✅":
            if not self._update_connection(ip_address, self.new_password):
                print("Error: Failed to update connection after adding IP.")
                return "❌"
            ip_exists = self.check_ip_exists(new_ip, ip_address)
            network_configuration = self.check_network_configuration(ip_address, subnet, gateway, dns)
            return "✅" if ip_exists == "✅" and network_configuration == "✅" else "❌"
        return "❌"

    def remove_ip(self, machine_uuid: str, mac_address: str, ip_address: str, dns: str, gateway: str, subnet: str) -> str:
        """Remove IP from the server."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        print("Removing IP from the server\n")
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" network list | jq -r \'.nics[].ips[] | select(. != "{ip_address}")\''
        new_ip = self.executor.run_command(command)
        if new_ip is None:
            print("Error: Failed to get new IP address.")
            return "❌"

        command2 = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" network nic remove-ip --ip {new_ip} --mac {mac_address}'
        res = self.executor.execute_task(command2)
        if res == "✅":
            if not self._update_connection(ip_address, self.new_password):
                print("Error: Failed to update connection after removing IP.")
                return "❌"
            ip_exists = self.check_ip_exists(new_ip, ip_address)
            network_configuration = self.check_network_configuration(ip_address, subnet, gateway, dns)
            return "✅" if ip_exists == "❌" and network_configuration == "✅" else "❌"
        return "❌"

    def remove_nic(self, machine_uuid: str, mac_address: str, ip_address: str, dns: str, gateway: str, subnet: str) -> str:
        """Remove NIC from the server."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        print("Removing NIC from the server\n")
        self.poweroff_server(machine_uuid)
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" network list | jq -r \'.nics[] | select(.mac != "{mac_address}") | .mac\''
        new_mac = self.executor.run_command(command)
        if new_mac is None:
            print("Error: Failed to get new MAC address.")
            return "❌"
        command2 = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" network nic remove --mac {new_mac}'
        res = self.executor.execute_task(command2)
        if res == "✅":
            self.poweron_server(machine_uuid)
            if not self._update_connection(ip_address, self.new_password):
                print("Error: Failed to update connection after removing NIC.")
                return "❌"
            nic_exists = self.check_nic_exists(new_mac)
            network_configuration = self.check_network_configuration(ip_address, subnet, gateway, dns)
            return "✅" if nic_exists == "❌" and network_configuration == "✅" else "❌"
        return "❌"

    def add_nic(self, machine_uuid: str, ip_address: str, mac_address: str, dns: str, gateway: str, subnet: str, lan: str) -> str:
        """Add NIC to the server."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        print("Adding NIC to the server\n")
        self.poweroff_server(machine_uuid)
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" network add --ip {self.lan_ip} --network {lan}'
        res = self.executor.execute_task(command)
        command2 = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" network list | jq -r \'.nics[] | select(.mac != "{mac_address}") | .mac\''
        new_mac = self.executor.run_command(command2)
        if new_mac is None:
            print("Error: Failed to get new MAC address.")
            return "❌"
        if res == "✅":
            self.poweron_server(machine_uuid)
            if not self._update_connection(ip_address, self.new_password):
                print("Error: Failed to update connection after adding NIC.")
                return "❌"
            nic_exists = self.check_nic_exists(new_mac)
            network_configuration = self.check_network_configuration(ip_address, subnet, gateway, dns)
            return "✅" if nic_exists == "✅" and network_configuration == "✅" else "❌"
        return "❌"

    def add_hd(self, machine_uuid: str, ip_address: str, disk_size: int) -> str:
        """Add HD to the server."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        print("Adding HD to the server\n")
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" disk add --size {self.size}'
        res = self.executor.execute_task(command)
        if res == "✅":
            if not self._update_connection(ip_address, self.new_password):
                print("Error: Failed to update connection after adding HD.")
                return "❌"
            disk_exists = self.check_disk_exists(ip_address, self.size, disk_size)
            return "✅" if disk_exists == "✅" else "❌"
        return "❌"

    def remove_hd(self, machine_uuid: str, ip_address: str, disk_size: int) -> str:
        """Remove HD from the server."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        print("Removing HD from the server\n")
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" disk remove -i {self.index}'
        res = self.executor.execute_task(command)
        if res == "✅":
            if not self._update_connection(ip_address, self.new_password):
                print("Error: Failed to update connection after removing HD.")
                return "❌"
            disk_exists = self.check_disk_exists(ip_address, 0, disk_size)
            return "✅" if disk_exists == "✅" else "❌"
        return "❌"

    def resize_hd(self, machine_uuid: str, ip_address: str, disk_size: int) -> str:
        """Resize HD on the server."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        print("Resizing HD on the server\n")
        size = 100
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" disk resize -i {self.index} --size {size}'
        res = self.executor.execute_task(command)
        if res == "✅":
            if not self._update_connection(ip_address, self.new_password):
                print("Error: Failed to update connection after resizing HD.")
                return "❌"
            disk_exists = self.check_disk_exists(ip_address, size, disk_size)
            return "✅" if disk_exists == "✅" else "❌"
        return "❌"

    def clone_server(self, machine_uuid: str, password: str, machine_name: str) -> str:
        """Clone the server."""
        print("Cloning the server\n")
        command = f'{CommandExecutor.MAIN_PY_PATH} server --uuid "{machine_uuid}" clone --password {password}'
        result = self.executor.run_command(command)
        print(f"Clone command output: {result}")

        if result is None:
            print("Error: Clone command failed.")
            return "❌"

        clone_task_id = self.executor.extract_clone_task_id(machine_name, self.index, timeout=120, interval=10)
        if clone_task_id:
            return self.executor.wait_queue(clone_task_id, timeout=900, interval=10)

        print("Error: Failed to extract clone task ID.")
        return "❌"

    def check_network_configuration(self, ip_address: str, subnet: str, gateway: str, dns: str) -> str:
        """Checks if the network configuration matches the given parameters."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        if self.os_type is None:
            print("Error: OS type not determined yet.")
            return "❌"

        if not self._update_connection(ip_address, self.new_password):
            print("Error: Failed to update connection for network check.")
            return "❌"

        cidr = sum(bin(int(octet)).count('1') for octet in subnet.split('.'))
        if self.os_type == "windows":
            command = f"Get-NetIPAddress | Where-Object {{ $_.PrefixLength -eq '{cidr}' }}"
            command2 = f"Get-NetIPConfiguration | Where-Object {{ $_.IPv4DefaultGateway.NextHop -eq '{gateway}' }}"
            command3 = f"Get-DnsClientServerAddress | Where-Object {{ $_.ServerAddresses -contains '{dns}' }}"
        else:
            if isinstance(self.network_path, list):
                command = f"grep -i /{cidr} {' '.join(self.network_path)} ; grep -i {subnet} {' '.join(self.network_path)}"
                command2 = f"grep -i {gateway} {' '.join(self.network_path)}"
            else: 
                command = f"grep -i /{cidr} {self.network_path} ; grep -i {subnet} {self.network_path}"
                command2 = f"grep -i {gateway} {self.network_path}"

            command3 = f"resolvectl status | grep -i {dns} ; grep -i {dns} {self.dns_path}"

        result = self._exec_command(command)
        result2 = self._exec_command(command2)
        result3 = self._exec_command(command3)

        if result is None or result2 is None or result3 is None:
            print("Error: Failed to execute network check commands.")
            return "❌"
        print(f"Matched!" if result and result2 and result3 else "No match.")
        return "✅" if result and result2 and result3 else "❌"

    def check_ip_exists(self, new_ip: str, ip_address: str) -> str:
        """Checks if the given IP address exists."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        if self.os_type is None:
            print("Error: OS type not determined yet.")
            return "❌"

        if not self._update_connection(ip_address, self.new_password):
            print("Error: Failed to update connection for IP check.")
            return "❌"

        if self.os_type == "windows":
            command = f"Get-NetIPAddress | Where-Object {{ $_.IPAddress -eq '{new_ip}' }}"
        else:
            if isinstance(self.network_path, list):
                command = f"grep -i '{new_ip}' {' '.join(self.network_path)}"
            else:
                command = f"grep -i '{new_ip}' {self.network_path}"

        result = self._exec_command(command)
        if result is None:
            print("Error: Command execution failed.")
            return "❌"
        print(f"Matched!" if result.strip() else "No match.")
        return "✅" if result else "❌"

    def check_nic_exists(self, new_mac: str) -> str:
        """Checks if the given MAC address exists."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        if self.os_type is None:
            print("Error: OS type not determined yet.")
            return "❌"

        if self.os_type == "windows":
            new_mac = new_mac.strip().upper().replace(":", "-")
            command = f"Get-NetAdapter | Where-Object {{ $_.MacAddress -eq '{new_mac}' }} | Select-Object Name, MacAddress"
        else:
            if isinstance(self.network_path, list):
                command = f"grep -i '{new_mac}' {' '.join(self.network_path)}"
            else:
                command = f"grep -i '{new_mac}' {self.network_path}"

        result = self._exec_command(command)
        if result is None:
            print("Error: Failed to execute command.")
            return "❌"
        print(f"Matched!" if result else "No match.")
        return "✅" if result else "❌"

    def check_disk_exists(self, ip_address: str, size: int, disk_size: int) -> str:
        """Checks disk size matches expected total in GB."""
        if not self.new_password:
            print("Error: New password is not set.")
            return "❌"

        if self.os_type is None:
            print("Error: OS type not determined yet.")
            return "❌"

        if not self._update_connection(ip_address, self.new_password):
            print("Error: Failed to update connection for disk checking.")
            return "❌"

        total_gb = 0
        if self.os_type in ["ubuntu", "debian", "rhel", "centos", "almalinux", "rocky", "linuxmint", "archlinux"]:
            command = "lsblk -dnbo SIZE"
            result = self._exec_command(command)
            if result is None:
                print("Error: Failed to execute lsblk.")
                return "❌"
            stdout = result.strip()
            if not stdout:
                print("Error: No output received from lsblk.")
                return "❌"
            try:
                total_gb = sum(int(size) for size in stdout.split()) // (1024 ** 3)
            except Exception as e:
                print(f"Error processing lsblk output: {e}")
                return "❌"

        elif self.os_type == "freebsd":
            command = "geom disk list"
            result = self._exec_command(command)
            if result is None:
                print("Error: Failed to execute geom disk list.")
                return "❌"
            stdout = result.strip()
            if not stdout:
                print("Error: No output received from geom disk list.")
                return "❌"
            total_gb = 0
            lines = stdout.splitlines()
            current_disk = None
            for line in lines:
                line = line.strip()
                if "Geom name:" in line:
                    current_disk = line.split(":")[1].strip()
                if "Mediasize:" in line and current_disk and not current_disk.startswith("cd"):
                    try:
                        size_str = line.split(":")[1].strip().split()[0]
                        size_bytes = int(size_str)
                        disk_gb = size_bytes // (1024 ** 3)
                        total_gb += disk_gb
                    except Exception as e:
                        print(f"Error processing geom output: {e}")
                        return "❌"

        elif self.os_type == "windows":
            command = "(Get-PhysicalDisk | ForEach-Object { $_.Size } | Measure-Object -Sum).Sum"
            result = self._exec_command(command)
            if result is None or not result.strip():
                print("Error: Failed to execute PowerShell command for disk checking.")
                return "❌"
            try:
                total_gb = int(result.strip()) // (1024 ** 3)
            except ValueError as e:
                print(f"Error processing PowerShell result: {e}")
                return "❌"

        else:
            print(f"OS type {self.os_type} not supported for disk checking.")
            return "❌"

        expected_total_gb = int(disk_size) + int(size)
        print(f"Actual total partition size: {total_gb} GB; Expected total: {expected_total_gb} GB")
        return "✅" if abs(total_gb - expected_total_gb) <= 1 else "❌"

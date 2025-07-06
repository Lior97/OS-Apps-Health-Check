#!/usr/bin/env python3

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s',
    datefmt='[%H:%M:%S]'
)
import sys
from ModulesOS.args_parser import parse_arguments
from ModulesOS.command_executor import CommandExecutor
from ModulesOS.server_manager import ServerManager
from Modules.report import ReportGenerator, TableType

def main():

    args = parse_arguments()
    args.mac = args.mac.lower()
    executor = CommandExecutor()
    server_manager = ServerManager(executor)

    connection_success = server_manager.set_connection_managers(args.ip, args.password, args.ostype)
    if not connection_success:
        print("Error: Failed to establish connection to the server.")
        sys.exit(1)

    results = {
        "Rename": server_manager.rename_server(args.uuid, args.machine_name),
        "Change Password": server_manager.change_password(args.uuid, args.ip),
        "Add IP": server_manager.add_ip(args.uuid, args.mac, args.ip, args.dns, args.gateway, args.subnet),
        "Remove IP": server_manager.remove_ip(args.uuid, args.mac, args.ip, args.dns, args.gateway, args.subnet),
        "Add NIC": server_manager.add_nic(args.uuid, args.ip, args.mac, args.dns, args.gateway, args.subnet, args.lan),
        "Remove NIC": server_manager.remove_nic(args.uuid, args.mac, args.ip, args.dns, args.gateway, args.subnet),
        "Add HD": server_manager.add_hd(args.uuid, args.ip, args.disks),
        "Resize HD": server_manager.resize_hd(args.uuid, args.ip, args.disks),
        "Remove HD": server_manager.remove_hd(args.uuid, args.ip, args.disks),
    }

    report = ReportGenerator(TableType.OS)
    report.add_os_row(*results.values())
    report.display_tables()

    result_filename = f"{args.machine_name}_results.csv"
    server_manager.save_results_to_csv(result_filename, results)

if __name__ == "__main__":
    main()

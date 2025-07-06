#!/usr/bin/env python3

from ModulesInstaller import ServiceChecker, parse_config_args, load_app_config
from Modules import SSHManager, ReportGenerator, TableType
import logging
import sys

def main():
    # Parse command-line arguments or environment variables
    config = parse_config_args()

    logging.info("Starting the main process")

    # Initialize SSHManager with parsed configuration
    ssh_manager = SSHManager(config.host, config.user, config.password)

    if not ssh_manager.is_connected():
        logging.error("SSH connection failed")
        return
    logging.info("SSH connection established successfully")

    # Load the JSON configuration
    config_data = load_app_config(config.name)

    if config_data is None:
        logging.error("Config is None, check the JSON loading function.")
        sys.exit(1)

    logging.info("JSON file loaded successfully")

    # Initialize service checker
    service_checker = ServiceChecker(ssh_manager)

    # Create report generators
    installer_report = ReportGenerator(TableType.INSTALLER)
    web_report = ReportGenerator(TableType.WEB)

    # Process each service for the INSTALLER table
    for service in config_data.get("services", []):
        service_checker.process_service(service, installer_report)

    # Process each service for the WEB table
    v4_ports = service_checker.check_open_ports_v4()
    v6_ports = service_checker.check_open_ports_v6()

    for service in config_data.get("services", []):
        for port_info in service.get("ports", []):
            port = port_info.get("port")
            if port:  # Ensure the port is defined
                connectivity_results = service_checker.check_web_access(config.host, [port])
                http_status = connectivity_results.get(port, {}).get("http", "❌")
                https_status = connectivity_results.get(port, {}).get("https", "❌")
                web_report.add_web_row(port, v4_ports, v6_ports, http_status, https_status)

    # Display the reports
    installer_report.display_tables()
    web_report.display_tables()

    # Close the SSH connection
    ssh_manager.close()

if __name__ == "__main__":
    main()

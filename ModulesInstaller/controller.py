#!/usr/bin/env python3

import sys
import logging
from .service_check import ServiceChecker
from Modules.report import ReportGenerator, TableType
from .json_loader import load_app_config
from Modules.ssh import SSHManager

class Controller:
    def __init__(self):
        # Initialize report generators as None (they will be set in processing)
        self.installer_report = None
        self.web_report = None
        self.os_report = None
        self.ssh_manager = None
        self.config = None
        self.app_or_os = None
        self.config_data = None

    def proccessing(self, config):
        """
        Initialize the Controller with the provided configuration.
        """
        self.config = config
        self.ssh_manager = SSHManager(config.host, config.user, config.password)

        # Establish SSH connection
        if not self.ssh_manager.is_connected():
            logging.error("SSH connection failed")
            sys.exit(1)  # Exit if connection fails

        logging.info("SSH connection established successfully")

        # Determine the type of table (Installer or OS)
        self.config_data = load_app_config(config.name)

        if self.config_data is None:
            logging.error("Config is None, check the JSON loading function.")
            sys.exit(1)

        logging.info("JSON file loaded successfully")

        # Initialize service checker
        service_checker = ServiceChecker(self.ssh_manager)

        # Initialize and store report attributes
        self.installer_report = ReportGenerator(TableType.INSTALLER)
        self.web_report = ReportGenerator(TableType.WEB)
        self.os_report = ReportGenerator(TableType.OS)

        # Process each service for the INSTALLER table
        for service in self.config_data.get("services", []):
            service_checker.process_service(service, self.installer_report)

        # Check open ports and web access
        v4_ports = service_checker.check_open_ports_v4()
        v6_ports = service_checker.check_open_ports_v6()

        for service in self.config_data.get("services", []):
            for port_info in service.get("ports", []):
                port = port_info.get("port")
                if port:  # Ensure the port is defined
                    connectivity_results = service_checker.check_web_access(self.config.host, [port])
                    http_status = connectivity_results.get(port, {}).get("http", "❌")
                    https_status = connectivity_results.get(port, {}).get("https", "❌")
                    self.web_report.add_web_row(port, v4_ports, v6_ports, http_status, https_status)

        logging.info("Processing completed")


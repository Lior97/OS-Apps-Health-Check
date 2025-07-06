# Server Management Automation

This Python-based project automates server management tasks for Windows (via WinRM) and Linux (via SSH) servers. It handles operations like renaming servers, changing passwords, adding/removing IPs and NICs, managing disk sizes, and cloning servers. Additionally, it monitors service installation, status, and port connectivity (IPv4/IPv6, HTTP/HTTPS), generating CSV reports and formatted tables for results.

---

## Table of Contents

- [Overview](#overview)  
- [Features](#features)  
---

## Overview

This Python-based project automates server management tasks for Windows (via WinRM) and Linux (via SSH) servers. It streamlines operations such as renaming servers, changing passwords, managing network interfaces and disks, and cloning servers. The tool also monitors service installation, status, and network connectivity, producing CSV reports and formatted tables for easy tracking.

---

## Features

- **Server Operations**  
  Rename servers, update passwords, add/remove IPs and NICs, manage disk sizes, and clone servers.

- **Connection Management**  
  Supports SSH for Linux and WinRM for Windows with retry logic for reliable connections.

- **Service Monitoring**  
  Checks service installation, status, and port connectivity (IPv4/IPv6, HTTP/HTTPS).

- **OS Detection**  
  Auto-detects Linux distributions or uses specified OS for Windows.

- **Reporting**  
  Generates CSV files and formatted tables for task and service results.

- **Task Queuing**  
  Executes commands via a task queue, ensuring completion and validation.



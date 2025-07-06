import argparse

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for server management.

    Returns:
        argparse.Namespace: Parsed arguments with all required and optional parameters.
    """
    parser = argparse.ArgumentParser(description="Server Management")
    parser.add_argument("--machine_name", "-mn", required=True, help="Machine Name")
    parser.add_argument("--uuid", "-id", required=True, help="Machine UUID")
    parser.add_argument("--ip", "-ip", required=True, help="Machine IP Address")
    parser.add_argument("--mac", "-m", required=True, help="Machine MAC Address")
    parser.add_argument("--network", "-n", required=True, help="Network Name")
    parser.add_argument("--password", "-p", required=True, help="Machine Password")
    parser.add_argument("--subnet", "-sb", required=True, help="Machine Subnet")
    parser.add_argument("--gateway", "-gw", required=True, help="Machine Gateway")
    parser.add_argument("--dns", "-dns", required=True, help="Machine DNS")
    parser.add_argument("--disks", "-d", required=True, type=int, help="Disk Size (in GB)")
    parser.add_argument("--ostype", "-os", required=False, help="OS Type (optional, auto-detected if not specified)")
    parser.add_argument("--lan", "-l", required=True, help="LAN Name")

    args = parser.parse_args()
    return args

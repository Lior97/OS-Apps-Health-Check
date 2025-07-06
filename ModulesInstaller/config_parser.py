import argparse
import os

def parse_config_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configuration settings for Installer and OS Monitoring.")
    
    parser.add_argument('--host', type=str, default=os.getenv("HOST"), 
                      help="IP address of the target machine.", required=True)
    parser.add_argument('--user', type=str, default=os.getenv("USER"), 
                      help="Username for authentication.", required=True)
    parser.add_argument('--password', type=str, default=os.getenv("PASSWORD"), 
                      help="Password for authentication.", required=True)
    parser.add_argument('--name', type=str, default=os.getenv("IMAGE_NAME"), 
                      help="Name of the installation instance.", required=True)

    args = parser.parse_args()
    args.host = args.host.strip()
    return args


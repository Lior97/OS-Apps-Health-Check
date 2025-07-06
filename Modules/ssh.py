import paramiko
import logging
import time
from typing import Optional

class SSHManager:
    def __init__(self, host: str, user: str, password: str, retries: int = 10, retry_timeout: int = 10) -> None:
        """
        Initializes the SSHManager and tries to establish a connection to the host.
        :param host: The hostname or IP of the server.
        :param user: The username for SSH.
        :param password: The password for SSH.
        :param retries: Number of retries for connection attempts.
        :param retry_timeout: Time (in seconds) to wait between retries.
        """
        self.client = self._create_client(host, user, password, retries, retry_timeout)

    def _create_client(self, host: str, user: str, password: str, retries: int, retry_timeout: int) -> Optional[paramiko.SSHClient]:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        for attempt in range(1, retries + 1):
            try:
                logging.info(f"Attempt {attempt} to connect to {host}...")
                client.connect(host, username=user, password=password, allow_agent=False, look_for_keys=False)
                logging.info("Connected successfully.")
                return client
            except Exception as e:
                logging.warning(f"Attempt {attempt} failed: {e}")
                if attempt < retries:
                    logging.info(f"Retrying in {retry_timeout} seconds...")
                    time.sleep(retry_timeout)
                else:
                    logging.error(f"All {retries} attempts failed. Could not connect to {host}.")
                    return None

    def close(self):
        """
        Closes the SSH connection if it is open.
        """
        if self.client:
            self.client.close()
            logging.info("Connection closed.")

    def exec_command(self, command: str) -> str:
        """
        Executes a command on the remote server.
        :param command: The command to execute.
        :return: The output of the command as a string.
        """
        if self.client is None:
            raise ConnectionError("SSH client is not connected.")

        _, stdout, stderr = self.client.exec_command(command)
        stderr_output = stderr.read().decode()
        if stderr_output:
            logging.error(f"Error: {stderr_output}")
        return stdout.read().decode().strip()

    def is_connected(self) -> bool:
        """
        Checks if the SSH connection is active.
        :return: True if connected, False otherwise.
        """
        return self.client is not None

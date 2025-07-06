import winrm
import logging
import time

class RDPManager:
    def __init__(self, host, user, password, retries=10, retry_timeout=10):
        """
        Initializes the RDPManager and tries to establish a WinRM connection to the host.
        :param host: The hostname or IP of the server.
        :param user: The username for WinRM.
        :param password: The password for WinRM.
        :param retries: Number of retries for connection attempts.
        :param retry_timeout: Time (in seconds) to wait between retries.
        """
        self.host = host
        self.user = user
        self.password = password
        self.retries = retries
        self.retry_timeout = retry_timeout
        self.session = None
        self.connected = self._create_session()

    def _create_session(self):
        """
        Creates a WinRM session and attempts to connect to the host.
        """
        for attempt in range(1, self.retries + 1):
            try:
                logging.info(f"Attempt {attempt}: Connecting to {self.host} via WinRM...")
                self.session = winrm.Session(
                    self.host, auth=(self.user, self.password), transport="ntlm"
                )
                # Test the connection
                result = self.session.run_ps("Write-Output 'WinRM Connection Successful'")
                if result.status_code == 0:
                    logging.info(f"WinRM connection established successfully to {self.host}.")
                    return True
                else:
                    logging.error(f"Connection test failed: {result.std_err.decode()}")
            except Exception as e:
                logging.error(f"Attempt {attempt} failed: {e}")

            if attempt < self.retries:
                logging.info(f"Retrying in {self.retry_timeout} seconds...")
                time.sleep(self.retry_timeout)
            else:
                logging.error(f"All {self.retries} attempts failed. Could not connect to {self.host} via WinRM.")
                return False

        return False

    def run_ps(self, command):
        """
        Executes a PowerShell command on the remote server.
        :param command: The PowerShell command to execute.
        :return: The output of the command as a string.
        """
        if not self.connected or not self.session:
            raise ConnectionError("WinRM session is not connected.")

        try:
            result = self.session.run_ps(command)
            if result.status_code != 0:
                logging.error(f"PowerShell execution error: {result.std_err.decode()}")
                return ""
            return result.std_out.decode().strip()
        except Exception as e:
            logging.error(f"Failed to execute PowerShell command: {e}")
            return ""

    def is_connected(self):
        """
        Checks if the WinRM session is active.
        :return: True if connected, False otherwise.
        """
        return self.connected

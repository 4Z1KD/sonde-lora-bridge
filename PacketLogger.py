import json
from datetime import datetime
from pathlib import Path


class PacketLogger:
    """
    Handles logging of sonde telemetry packets to daily JSONL files.
    Creates a separate log file for each day with format: packets_YYYY-MM-DD.jsonl
    """
    
    def __init__(self, log_dir: str = "packet_logs"):
        """
        Initialize the packet logger.
        
        Args:
            log_dir (str): Directory to store log files (default: "packet_logs")
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self._last_log_date = None
        self._log_file = None
    
    def _get_log_file(self) -> Path:
        """
        Get the current log file, creating a new one if the date has changed.
        Creates separate log files for each day in YYYY-MM-DD format.
        
        Returns:
            Path: Path to the current log file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # If date has changed, update to new log file
        if today != self._last_log_date:
            self._last_log_date = today
            log_filename = f"packets_{today}.jsonl"
            self._log_file = self.log_dir / log_filename
        
        return self._log_file
    
    def log_packet(self, packet_data: dict):
        """
        Append a packet to the daily log file as a JSON line.
        
        Args:
            packet_data (dict): The packet data to log
        """
        try:
            log_file = self._get_log_file()
            
            # Add timestamp if not present
            if "logged_at" not in packet_data:
                packet_data["logged_at"] = datetime.now().isoformat()
            
            # Append as JSON line
            with open(log_file, "a") as f:
                f.write(json.dumps(packet_data) + "\n")
                
        except Exception as e:
            print(f"Error logging packet: {e}")
    
    def get_log_dir(self) -> Path:
        """
        Get the log directory path.
        
        Returns:
            Path: Path to the log directory
        """
        return self.log_dir

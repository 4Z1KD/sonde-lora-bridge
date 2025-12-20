import time


class WorkloadManager:
    """
    Manages data buffering with time and count thresholds.
    Executes a callback when either threshold is reached.
    """

    def __init__(self, count_threshold=10, time_threshold=5.0, callback=None):
        """
        Initialize the threshold manager.

        Args:
            count_threshold (int): Number of data items to buffer before triggering callback
            time_threshold (float): Time in seconds before triggering callback
            callback (callable): Function to call when thresholds are met. 
                                 Receives single data item.
        """
        self.count_threshold = count_threshold
        self.time_threshold = time_threshold
        self.callback = callback
        self.counter = 0
        self.start_time = None
        self.data_buffer = []

    def receive(self, data):
        """
        Receive data and check thresholds.

        Args:
            data: The data to buffer
        """
        # Initialize timer on first data
        if self.start_time is None:
            self.start_time = time.time()

        # Add data to buffer
        self.data_buffer.append(data)
        self.counter += 1

        # Check thresholds
        elapsed_time = time.time() - self.start_time
        
        if (self.counter >= self.count_threshold or 
            elapsed_time >= self.time_threshold):
            self._trigger_callback()

    def _trigger_callback(self):
        """Execute callback for the last buffered data item and reset."""
        if self.callback and self.data_buffer:
            self.callback(self.data_buffer[-1])
        
        # Reset state
        self.counter = 0
        self.start_time = None
        self.data_buffer = []

    def flush(self):
        """Manually trigger callback with any remaining data."""
        if self.counter > 0:
            self._trigger_callback()


if __name__ == "__main__":
    def process_data(data):
        print(f"Processing: {data}")

    manager = WorkloadManager(count_threshold=10, time_threshold=10.0, callback=process_data)
    
    # Example usage
    for i in range(15):
        manager.receive(f"data_{i}")
        time.sleep(2)
    
    manager.flush()

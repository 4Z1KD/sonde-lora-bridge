
import time
import threading


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
        self._timer_thread = None
        self._stop_event = threading.Event()

    def addWork(self, data):
        """
        Receive data and check thresholds.

        Args:
            data: The data to buffer
        """
        # Add data to buffer
        self.data_buffer.append(data)
        self.counter += 1

        # Start timer if this is the first item
        if self.counter == 1:
            self.start_time = time.time()
            self._start_timer()

        # check counter threshold
        self._check_counter_threshold()

    def _check_counter_threshold(self):
        """Check if count threshold is reached."""
        if self.counter >= self.count_threshold:
            self._trigger_callback()

    def _trigger_callback(self):
        """Execute callback for the last buffered data item and reset."""
        if self.callback and self.data_buffer:
            self.callback(self.data_buffer[-1])

        # Reset state
        self.counter = 0
        self.start_time = None
        self.data_buffer = []
        self._stop_timer()

    def flush(self):
        """Manually trigger callback with any remaining data."""
        if self.counter > 0:
            self._trigger_callback()

    def _start_timer(self):
        self._stop_event.clear()
        if self._timer_thread is None or not self._timer_thread.is_alive():
            self._timer_thread = threading.Thread(target=self._timer_check, daemon=True)
            self._timer_thread.start()

    def _stop_timer(self):
        self._stop_event.set()
        # Avoid joining the current thread to prevent RuntimeError
        if (
            self._timer_thread
            and self._timer_thread.is_alive()
            and threading.current_thread() != self._timer_thread
        ):
            self._timer_thread.join(timeout=0.1)
        self._timer_thread = None

    def _timer_check(self):
        while not self._stop_event.is_set():
            if self.start_time is not None:
                elapsed = time.time() - self.start_time
                if elapsed >= self.time_threshold:
                    self._trigger_callback()
                    break
            time.sleep(0.1)


if __name__ == "__main__":
    def process_data(data):
        print(f"Processing: {data}")

    manager = WorkloadManager(count_threshold=10, time_threshold=10.0, callback=process_data)
    
    # Example usage
    for i in range(2):
        print(f"Receiving: data_{i}")
        manager.addWork(f"data_{i}")
        time.sleep(1)
    
    time.sleep(20)
    #manager.flush()

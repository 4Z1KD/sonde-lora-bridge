import threading
import time

class LEDController:
    """
    Controls an LED on a Raspberry Pi GPIO pin.
    Provides blinking functionality when packets arrive.
    """

    def __init__(self, gpio_pin=17, blink_duration=0.2):
        """
        Initialize the LED controller.

        Args:
            gpio_pin (int): GPIO pin number (BCM numbering). Default is 17.
            blink_duration (float): How long to blink in seconds. Default is 0.2s.
        """
        self.gpio_pin = gpio_pin
        self.blink_duration = blink_duration
        self.gpio = None
        self.is_initialized = False
        self._init_gpio()

    def _init_gpio(self):
        """Initialize GPIO. Safe to call even if not on RPi."""
        try:
            import RPi.GPIO as GPIO
            self.gpio = GPIO
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setup(self.gpio_pin, self.gpio.OUT)
            self.gpio.output(self.gpio_pin, self.gpio.LOW)
            self.is_initialized = True
            print(f"LED initialized on GPIO pin {self.gpio_pin}")
        except (ImportError, RuntimeError) as e:
            print(f"Warning: Could not initialize GPIO. Running in simulation mode. ({e})")
            self.is_initialized = False

    def blink(self):
        """
        Blink the LED once (non-blocking).
        Runs in a separate thread to avoid blocking the main loop.
        """
        if not self.is_initialized:
            return
        
        thread = threading.Thread(target=self._blink_thread, daemon=True)
        thread.start()

    def _blink_thread(self):
        """Internal thread function for blinking."""
        try:
            self.gpio.output(self.gpio_pin, self.gpio.HIGH)
            time.sleep(self.blink_duration)
            self.gpio.output(self.gpio_pin, self.gpio.LOW)
        except Exception as e:
            print(f"Error blinking LED: {e}")

    def cleanup(self):
        """Clean up GPIO resources."""
        if self.is_initialized and self.gpio:
            try:
                self.gpio.output(self.gpio_pin, self.gpio.LOW)
                self.gpio.cleanup()
                self.is_initialized = False
                print("LED GPIO cleaned up")
            except Exception as e:
                print(f"Error cleaning up GPIO: {e}")

    def __del__(self):
        """Ensure cleanup on object deletion."""
        self.cleanup()


if __name__ == "__main__":
    # Test the LED controller
    led = LEDController(gpio_pin=17, blink_duration=0.2)
    
    print("Blinking LED 5 times...")
    for i in range(5):
        print(f"Blink {i+1}")
        led.blink()
        time.sleep(0.5)
    
    print("Done")
    led.cleanup()

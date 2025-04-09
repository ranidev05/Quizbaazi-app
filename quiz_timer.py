# quiz_timer.py
import asyncio
from datetime import datetime

class QuizTimer:
    """Handle timing for quiz questions"""
    
    def __init__(self, timeout_seconds, on_timeout_callback):
        self.timeout_seconds = timeout_seconds
        self.on_timeout_callback = on_timeout_callback
        self.task = None
        self.start_time = None
    
    def start(self):
        """Start the timer"""
        self.start_time = datetime.now()
        self.task = asyncio.create_task(self._timer_task())
    
    def cancel(self):
        """Cancel the timer if needed"""
        if self.task and not self.task.done():
            self.task.cancel()
    
    async def _timer_task(self):
        """Timer task to wait and then call the callback"""
        try:
            await asyncio.sleep(self.timeout_seconds)
            await self.on_timeout_callback()
        except asyncio.CancelledError:
            # Timer was cancelled
            pass
    
    def get_elapsed_time(self):
        """Get elapsed time since timer started"""
        if not self.start_time:
            return 0
        return (datetime.now() - self.start_time).total_seconds()

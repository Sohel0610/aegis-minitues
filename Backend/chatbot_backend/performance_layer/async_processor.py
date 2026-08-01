"""
Async Processor - Asynchronous processing for heavy operations
Provides non-blocking execution for chart generation and large queries
"""

import asyncio
from typing import Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor
import time


class AsyncProcessor:
    """
    Asynchronous processor for heavy operations
    Prevents blocking on chart generation and large dataset processing
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize async processor
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_async(
        self,
        func: Callable,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Execute function asynchronously
        
        Args:
            func: Function to execute
            *args: Positional arguments
            timeout: Timeout in seconds (None = no timeout)
            **kwargs: Keyword arguments
            
        Returns:
            Result of function execution
        """
        loop = asyncio.get_event_loop()
        
        try:
            if timeout:
                result = await asyncio.wait_for(
                    loop.run_in_executor(self.executor, func, *args),
                    timeout=timeout
                )
            else:
                result = await loop.run_in_executor(self.executor, func, *args)
            
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Operation timed out after {timeout} seconds")
    
    def shutdown(self):
        """Shutdown executor"""
        self.executor.shutdown(wait=True)


# Global instance
_async_processor = None

def get_async_processor() -> AsyncProcessor:
    """Get singleton instance of AsyncProcessor"""
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncProcessor()
    return _async_processor

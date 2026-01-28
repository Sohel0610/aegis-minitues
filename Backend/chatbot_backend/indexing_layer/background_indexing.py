"""
Background Indexing Job
A background job that reads from DailyLogs and builds full-text and vector indexes
"""
import time
import threading
from indexing_layer.embedding_index import initialize_embedding_index

class BackgroundIndexingJob:
    """
    Background job for maintaining indexes
    """
    
    def __init__(self, interval_minutes: int = 60):
        """
        Initialize the background indexing job
        """
        self.interval_minutes = interval_minutes
        self.running = False
        self.thread = None
    
    def start(self):
        """
        Start the background indexing job
        """
        if self.running:
            print("Background indexing job is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"Background indexing job started with interval {self.interval_minutes} minutes")
    
    def stop(self):
        """
        Stop the background indexing job
        """
        if not self.running:
            print("Background indexing job is not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join()
        print("Background indexing job stopped")
    
    def _run(self):
        """
        Main run loop for the background job
        """
        while self.running:
            try:
                print("Running background indexing job...")
                # Reinitialize the embedding index
                initialize_embedding_index()
                print("Background indexing job completed")
            except Exception as e:
                print(f"Error in background indexing job: {e}")
            
            # Wait for the next interval
            for _ in range(self.interval_minutes * 60):  # Convert minutes to seconds
                if not self.running:
                    break
                time.sleep(1)
    
    def run_once(self):
        """
        Run the indexing job once
        """
        print("Running indexing job once...")
        try:
            initialize_embedding_index()
            print("Indexing job completed")
        except Exception as e:
            print(f"Error in indexing job: {e}")

# Global instance
background_indexing_job = BackgroundIndexingJob()

def start_background_indexing(interval_minutes: int = 60):
    """
    Start the background indexing job
    """
    background_indexing_job.interval_minutes = interval_minutes
    background_indexing_job.start()

def stop_background_indexing():
    """
    Stop the background indexing job
    """
    background_indexing_job.stop()

def run_indexing_once():
    """
    Run the indexing job once
    """
    background_indexing_job.run_once()

# Example usage
if __name__ == "__main__":
    # Run indexing once
    run_indexing_once()
    
    # Start background job (for testing - in real usage, this would run in a separate process)
    # start_background_indexing(30)  # Run every 30 minutes
    # time.sleep(5)  # Let it run for a bit
    # stop_background_indexing()
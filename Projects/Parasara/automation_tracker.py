import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RunbookTracker(FileSystemEventHandler):
    def on_modified(self, event):
        self.log_change(event)

    def on_created(self, event):
        self.log_change(event)

    def log_change(self, event):
        if not event.is_directory and event.src_path.endswith(".py"):
            with open("PROJECT_RUNBOOK.md", "a") as f:
                f.write(f"\n| {time.strftime('%Y-%m-%d')} | {event.src_path} | Modified/Added | In-Progress |")

if __name__ == "__main__":
    event_handler = RunbookTracker()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True) # ఇక్కడ True చేయండి
    observer.start()
    print("Tracker Started... మార్పుల కోసం గమనిస్తున్నాను.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
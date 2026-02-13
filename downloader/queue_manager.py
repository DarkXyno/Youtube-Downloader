import threading
from queue import Queue
from downloader.download import download_video
from downloader.download import get_video_info

class DownloadQueueManager:
    def __init__(self, signals):
        self.queue = Queue()
        self.signals = signals
        self.is_downloading = False

    def add(self, url, output_path, format_type):
        """ADD ITEM TO QUEUE AND START IF IDLE."""
        try:
            info = get_video_info(url)
            title = info.get("title", url)
        except Exception as e:
            title = url

        self.queue.put((url, output_path, format_type, title))
        self.signals.queue_update.emit("Queued", title)

        if not self.is_downloading:
            self._start_next()

    def _start_next(self):
        if self.queue.empty():
            self.is_downloading = False
            self.signals.status.emit("Idle")
            return
        
        self.is_downloading = True

        url, output_path, format_type, title = self.queue.get()

        self.signals.queue_update.emit("Starting", title)

        thread = threading.Thread(
            target=self._download_worker,
            args=(url, output_path, format_type, title),
            daemon=True
        )
        thread.start()

    def _download_worker(self, url, output_path, format_type, title):
        try:
            download_video(
                url,
                output_path,
                format_type,
                progress_callback=lambda p:self.signals.progress.emit(title, p),
            )

            self.signals.finished.emit(title, None, None)
        except Exception as e:
            self.signals.status.emit(f"Error: {str(e)}")

        finally:
            self._start_next()
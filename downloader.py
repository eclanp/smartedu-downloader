import os
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
import click
import signal
from typing import Iterable
import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from threading import Event

progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
)

done_event = Event()

def handle_sigint(signum, frame):
    done_event.set()

signal.signal(signal.SIGINT, handle_sigint)

@click.command(context_settings={"help_option_names": ["-h", "--help"]}, help="从国家智慧教育公共服务平台下载教材")
@click.option("-s", "--save_path", default=os.getcwd(), help="下载文件保存路径，默认为当前目录下")
@click.option("-u", "--urls", required=True, multiple=True, help="下载地址，支持多个")
def executor(save_path: str, urls: Iterable[str]):
    with progress:
        with ThreadPoolExecutor(max_workers=5) as pool:
            for url in urls:
                pool.submit(download, save_path, url)

def download(save_path: str, url: str):
    ret = urlparse(url)
    q = parse_qs(ret.query)

    filename = q.get('file')[0].split("/")[-1]
    headers = eval(q.get("headers")[0])

    task_id = progress.add_task("download", filename=filename, start=False)
    with requests.get(q.get('file')[0], headers=headers, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        progress.update(task_id, total=total_size)

        with open(os.path.join(save_path, filename), 'wb') as f:
            progress.start_task(task_id)
            for chunk in response.iter_content(1024):
                f.write(chunk)
                progress.update(task_id, advance=len(chunk))
                if done_event.is_set():
                    return

        progress.console.log(f"{filename} 下载完成")
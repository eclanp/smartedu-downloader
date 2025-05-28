import os
import pathlib
from urllib.parse import urlparse, parse_qs
import click
import requests
from tqdm import tqdm

@click.command(context_settings={"help_option_names": ["-h", "--help"]}, help="从国家智慧教育公共服务平台下载教材")
@click.option("-s", "--save_path", default=os.getcwd(), help="下载文件保存路径，默认为当前目录下")
@click.option("-u", "--urls", required=True, multiple=True, help="下载地址，支持多个")
def download(save_path, urls):
    for url in urls:
        parse_url(save_path, url)

def parse_url(save_path, url):
    ret = urlparse(url)
    q = parse_qs(ret.query)

    filename = q.get('file')[0].split("/")[-1]
    headers = eval(q.get("headers")[0])
    #
    with requests.get(q.get('file')[0], headers=headers, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))

        with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
            with open(os.path.join(save_path, filename), 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
                    pbar.update(len(chunk))
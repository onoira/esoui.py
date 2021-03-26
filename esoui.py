
import os
import random
import re
import time

from bs4 import BeautifulSoup
from requests import (Response, request)

BASE_URI = "https://esoui.com/downloads"
DEFAULT_VERSION = (0, 0, 0)


class Mod():

    TRANSLATION_TABLE = str.maketrans({
        '-': None,
        ' ': None
    })

    @property
    def is_outdated(self) -> bool:
        return self._version == DEFAULT_VERSION

    @property
    def filename(self) -> str:
        if self.is_outdated:
            return str()
        return f"{self.id}_{self.name.translate(self.TRANSLATION_TABLE)}-{self.version}.zip"

    @property
    def version(self) -> str:
        return '.'.join(map(str, self._version))

    def __init__(self, id:int, name:str, version:tuple):
        self.id = id
        self.name = name
        self._version = version


def _request(method:str, url:str, **kwargs):
    response = request(method, url, **kwargs)
    response.raise_for_status()
    return response


def download(mod:Mod) -> bytes:
    prompt_resp:Response = _request('GET', f"{BASE_URI}/download{mod.id}")
    cup = BeautifulSoup(prompt_resp.content, 'html5lib')

    url:str = cup.find('a', text="Click here")['href']
    dl_resp = _request('GET', url)
    return dl_resp.content


def fetch(id:int) -> Mod:
    resp:Response = _request('GET', f"{BASE_URI}/info{id}")
    cup = BeautifulSoup(resp.content, 'html5lib')

    name:str = cup.find('meta', property='og:title')['content']

    # Category 157 "Discontinued & Outdated"
    if cup.find('a', href="cat157.html"):
        return Mod(id, name, DEFAULT_VERSION)

    version_field:str = cup.find('div', id='version').text
    version_text = re.match(r'Version: ((?:\d+[.-])+\d+)', version_field).group(1)
    version = tuple(map(int, version_text.split('.')))

    return Mod(id, name, version)


def main():
    ids = list()
    with open('ids', 'r') as fp:
        for line in fp:
            ids.append(int(re.sub(r'#.+', '', line).strip()))

    print(f"Processing {len(ids)} mods...")

    if not os.path.exists('mods'):
        os.makedirs('mods')

    for id in ids:
        print(f"Fetching {id}...")
        mod:Mod = fetch(id)
        if mod.is_outdated:
            print(f"Skipping '{mod.name}' (outdated)")
            continue

        path = os.path.abspath(f"mods/{mod.filename}")
        if os.path.exists(path):
            print(f"Skipping '{mod.name}' (already exists @ {path})")

        print(f"Downloading {mod.name} (v{mod.version})...")
        content:bytes = download(mod)

        print(f"Writing content (-> {path})")
        with open(path, 'wb') as fp:
            fp.write(content)

        time.sleep(3 + random.random())


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

"""
Image downloader and processor worker threads.

This module contains worker threads for:
- Downloading all images from web pages
- Processing images from Excel files or URL lists
- Compressing downloaded or existing images
"""

import os
import asyncio
import aiohttp
import pandas as pd
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from PIL import Image
from openpyxl import Workbook
from PyQt6.QtCore import QThread, pyqtSignal

# Import from our modules
from config import HEADERS
from utils.helpers import sanitize_filename


class AllImagesDownloaderThread(QThread):
    """
    Worker thread to scrape all images from URLs, download them, create metadata Excel files,
    and optionally compress the downloaded images.
    """
    progress = pyqtSignal(int, str)  # Percentage, status_text
    finished = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, urls, save_folder, auth, compress_options):
        super().__init__()
        self.urls = urls
        self.save_folder = save_folder
        self.auth = auth
        self.compress_options = compress_options
        self.is_stopped = False

    def stop(self):
        self.log.emit("Stopping process...")
        self.is_stopped = True

    def run(self):
        try:
            asyncio.run(self.main_downloader())
        except Exception as e:
            self.log.emit(f"An unexpected error occurred: {e}")
        self.finished.emit("Completed" if not self.is_stopped else "Stopped")

    async def main_downloader(self):
        async with aiohttp.ClientSession(headers=HEADERS, auth=self.auth) as session:
            total_urls = len(self.urls)
            for i, url in enumerate(self.urls):
                if self.is_stopped:
                    break
                status = f"Processing URL {i+1}/{total_urls}: {url}"
                self.progress.emit(int((i / total_urls) * 100), status)
                await self.process_url(session, url.strip())
        
        if not self.is_stopped:
            self.progress.emit(100, "All URLs processed.")
            self.log.emit("Download and extraction completed.")

    async def process_url(self, session, url):
        try:
            async with session.get(url, ssl=False, timeout=30) as response:
                if response.status != 200:
                    self.log.emit(f"Failed to fetch {url}: Status {response.status}")
                    return

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                page_title = sanitize_filename(soup.title.string if soup.title else "Untitled")
                url_folder = os.path.join(self.save_folder, page_title)
                originals_folder = os.path.join(url_folder, "Originals")
                os.makedirs(originals_folder, exist_ok=True)

                workbook = Workbook()
                ws = workbook.active
                ws.title = "Image Data"
                ws.append(["Image URL", "Alt Text", "Title", "Local Filename"])

                img_sources = self._extract_img_sources(soup, url)
                self.log.emit(f"Found {len(img_sources)} images on {url}")

                download_tasks = []
                for src, img_name, alt, title in img_sources:
                    if self.is_stopped:
                        break
                    local_path = os.path.join(originals_folder, img_name)
                    ws.append([src, alt, title, img_name])
                    download_tasks.append(self._download_image(session, src, local_path))
                
                await asyncio.gather(*download_tasks)

                excel_path = os.path.join(url_folder, f"{page_title}_Image_Data.xlsx")
                workbook.save(excel_path)
                self.log.emit(f"Metadata saved to {excel_path}")
                
                # --- Compression Step ---
                if self.compress_options['enabled'] and not self.is_stopped:
                    self.log.emit(f"Starting compression for images from {url}...")
                    self._compress_images(
                        source_dir=originals_folder,
                        output_dir=os.path.join(url_folder, "Compressed"),
                        fmt=self.compress_options['format'],
                        quality=self.compress_options['quality']
                    )

        except Exception as e:
            self.log.emit(f"Error processing {url}: {e}")

    def _extract_img_sources(self, soup, base_url):
        sources = set()
        for tag in soup.find_all(['img', 'source']):
            alt = tag.get('alt', '').strip()
            title = tag.get('title', '').strip()
            
            src_attrs = [tag.get('src'), tag.get('data-src')]
            if tag.get('srcset'):
                src_attrs.extend([s.strip().split(' ')[0] for s in tag.get('srcset').split(',')])

            for src in src_attrs:
                if src:
                    resolved_url = urljoin(base_url, src.strip())
                    img_name = sanitize_filename(os.path.basename(urlparse(resolved_url).path))
                    if img_name and '.' in img_name:
                         sources.add((resolved_url, img_name, alt, title))
        return list(sources)

    async def _download_image(self, session, url, local_path):
        try:
            async with session.get(url, ssl=False) as response:
                if response.status == 200:
                    with open(local_path, "wb") as f:
                        f.write(await response.read())
                    self.log.emit(f"Downloaded: {os.path.basename(local_path)}")
                else:
                    self.log.emit(f"Failed download for {url}: Status {response.status}")
        except Exception as e:
            self.log.emit(f"Error downloading {url}: {e}")

    def _compress_images(self, source_dir, output_dir, fmt, quality):
        os.makedirs(output_dir, exist_ok=True)
        supported = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.avif')
        format_map = {'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 'webp': 'WEBP', 'gif': 'GIF', 'avif': 'AVIF'}
        save_format = format_map.get(fmt.lower(), 'JPEG')

        for filename in os.listdir(source_dir):
            if self.is_stopped:
                break
            if not filename.lower().endswith(supported):
                continue

            img_path = os.path.join(source_dir, filename)
            self.log.emit(f"Compressing {filename}")
            try:
                with Image.open(img_path) as img:
                    base_name = os.path.splitext(filename)[0]
                    output_path = os.path.join(output_dir, f"{base_name}.{fmt.lower()}")
                    
                    if img.mode in ('P', 'RGBA') and save_format not in ['PNG', 'WEBP', 'AVIF']:
                        img = img.convert('RGB')
                    
                    save_options = {'format': save_format, 'optimize': True}
                    if save_format in ['JPEG', 'WEBP']:
                        save_options['quality'] = quality
                    img.save(output_path, **save_options)
            except Exception as e:
                self.log.emit(f"Could not compress {filename}: {e}")


class ImageProcessorThread(QThread):
    """
    A worker thread for downloading (from Excel/URL list) and/or compressing images.
    """
    download_progress = pyqtSignal(int)
    compress_progress = pyqtSignal(int)
    status_update = pyqtSignal(str)
    finished_processing = pyqtSignal(str)

    def __init__(self, mode, excel_path, urls, source_folder, output_folder, image_format, quality):
        super().__init__()
        self.mode = mode
        self.excel_path = excel_path
        self.urls = urls
        self.source_folder = source_folder
        self.output_folder = output_folder
        self.image_format = image_format
        self.quality = quality
        self.stop_processing_flag = False

    def stop(self):
        self.status_update.emit("Stopping process...")
        self.stop_processing_flag = True

    def run(self):
        try:
            download_dir = os.path.join(self.output_folder, 'Originals')
            if self.mode == "excel":
                self.status_update.emit("Starting download from Excel file...")
                self._download_from_excel(download_dir)
            elif self.mode == "url":
                self.status_update.emit("Starting download from URLs...")
                self._download_from_urls(download_dir)
            
            if self.stop_processing_flag:
                self.finished_processing.emit("Stopped")
                return

            source_dir = self.source_folder if self.mode == "local" else download_dir
            if os.path.isdir(source_dir):
                 self.status_update.emit("Starting image compression...")
                 self._compress_images(source_dir)
            else:
                self.status_update.emit("Source directory for compression not found. Skipping compression.")

            if not self.stop_processing_flag:
                self.finished_processing.emit("Completed")
            else:
                self.finished_processing.emit("Stopped")

        except Exception as e:
            self.status_update.emit(f"An error occurred: {str(e)}")
            self.finished_processing.emit("Error")

    def _download_from_excel(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        df = pd.read_excel(self.excel_path, sheet_name=0)
        if df.empty:
            return
        
        url_column = df.columns[0]
        total = len(df)
        for i, row in df.iterrows():
            if self.stop_processing_flag:
                break
            url = str(row[url_column]).strip()
            if not url:
                continue
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            self._download_file(url, output_dir)
            self.download_progress.emit(int((i + 1) / total * 100))

    def _download_from_urls(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        total = len(self.urls)
        for i, url in enumerate(self.urls):
            if self.stop_processing_flag:
                break
            self._download_file(url, output_dir)
            self.download_progress.emit(int((i + 1) / total * 100))

    def _download_file(self, url, output_dir):
        try:
            filename = sanitize_filename(os.path.basename(urlparse(url).path))
            if not filename:
                return
            
            self.status_update.emit(f"Downloading: {filename}")
            response = requests.get(url, stream=True, verify=False, timeout=10)
            if response.status_code == 200:
                with open(os.path.join(output_dir, filename), 'wb') as f:
                    for chunk in response.iter_content(8192):
                        if self.stop_processing_flag:
                            return
                        f.write(chunk)
            else:
                self.status_update.emit(f"Failed to download {filename} (status: {response.status_code})")
        except Exception as e:
            self.status_update.emit(f"Error downloading {url}: {e}")

    def _compress_images(self, source_dir):
        compressed_folder = os.path.join(self.output_folder, 'Compressed')
        os.makedirs(compressed_folder, exist_ok=True)
        
        supported = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.avif')
        format_map = {'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 'webp': 'WEBP', 'gif': 'GIF', 'avif': 'AVIF'}
        save_format = format_map.get(self.image_format.lower(), 'JPEG')

        files_to_process = [os.path.join(r, f) for r, _, files in os.walk(source_dir) for f in files if f.lower().endswith(supported)]
        total = len(files_to_process)
        if total == 0:
            self.status_update.emit("No images found to compress.")
            return

        for i, img_path in enumerate(files_to_process):
            if self.stop_processing_flag:
                break
            filename = os.path.basename(img_path)
            self.status_update.emit(f"Compressing {filename}")
            
            try:
                with Image.open(img_path) as img:
                    base_name = os.path.splitext(filename)[0]
                    output_path = os.path.join(compressed_folder, f"{base_name}.{self.image_format.lower()}")
                    
                    if img.format == 'GIF' and save_format == 'GIF':
                        img.save(output_path, save_all=True, append_images=img.n_frames > 1, optimize=False, loop=0)
                        continue

                    if img.mode in ('P', 'RGBA') and save_format not in ['PNG', 'WEBP', 'AVIF']:
                        img = img.convert('RGB')
                    
                    save_options = {'format': save_format, 'optimize': True}
                    if save_format in ['JPEG', 'WEBP']:
                        save_options['quality'] = self.quality
                    
                    img.save(output_path, **save_options)
            except Exception as e:
                self.status_update.emit(f"Could not process {filename}: {e}")
            self.compress_progress.emit(int((i + 1) / total * 100))

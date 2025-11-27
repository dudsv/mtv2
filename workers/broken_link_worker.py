"""
BrokenLinkWorker for checking broken links on pages or sitemaps.
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from PyQt6.QtCore import QThread, pyqtSignal

from config import HEADERS, TIMEOUT_STANDARD, TIMEOUT_SHORT


class BrokenLinkWorker(QThread):
    """
    Worker for 'Broken Link Inspector':
    - mode: 'single' (single page checkup) or 'sitemap'
    - root_url: Base URL (page or sitemap.xml)
    - same_domain_only: If True, filters only same-domain links (single page)
    """
    progress_update = pyqtSignal(int)
    log_update = pyqtSignal(str)
    finished = pyqtSignal(list)  # list of results

    def __init__(self, mode: str, root_url: str, same_domain_only: bool = True, max_concurrency: int = 10):
        super().__init__()
        self.mode = mode
        self.root_url = root_url.strip()
        self.same_domain_only = same_domain_only
        self.max_concurrency = max_concurrency
        self._stop_requested = False
        self.results = []

    def stop(self):
        self._stop_requested = True

    def run(self):
        try:
            asyncio.run(self.main())
        except asyncio.CancelledError:
            self.log_update.emit("[WARN] Task was cancelled")
        except Exception as e:
            self.log_update.emit(f"[ERROR] BrokenLinkWorker crashed: {e}")
        finally:
            self.finished.emit(self.results)

    async def main(self):
        self.log_update.emit(f"[INIT] Broken Link Inspector mode = {self.mode}, URL = {self.root_url}")

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            if self.mode == "single":
                urls = await self._collect_links_from_page(self.root_url, session)
            elif self.mode == "sitemap":
                urls = await self._collect_from_sitemap(self.root_url, session)
            else:
                self.log_update.emit(f"[ERROR] Unknown mode: {self.mode}")
                urls = []

            urls = list(dict.fromkeys(urls))  # dedupe preserving order
            total = len(urls)
            if total == 0:
                self.log_update.emit("[INFO] No URLs to check.")
                self.progress_update.emit(100)
                return

            self.log_update.emit(f"[INFO] {total} URL(s) to check.")
            sem = asyncio.Semaphore(self.max_concurrency)

            async def runner():
                done = 0
                tasks = [
                    self._check_one(url, session, sem)
                    for url in urls
                ]
                for coro in asyncio.as_completed(tasks):
                    if self._stop_requested:
                        self.log_update.emit("[WARN] Stop requested. Aborting remaining checks.")
                        break
                    result = await coro
                    if result is not None:
                        self.results.append(result)
                    done += 1
                    progress = int(done * 100 / total)
                    self.progress_update.emit(progress)

            await runner()
            self.progress_update.emit(100)
            self.log_update.emit("[DONE] Broken Link Inspector finished.")

    async def _collect_links_from_page(self, page_url: str, session: aiohttp.ClientSession):
        urls = []
        try:
            self.log_update.emit(f"[FETCH] Loading page: {page_url}")
            async with session.get(page_url, ssl=False, timeout=TIMEOUT_STANDARD) as resp:
                html = await resp.text(errors="ignore")
        except aiohttp.ClientError as e:
            self.log_update.emit(f"[ERROR] Network error loading page: {page_url} – {e}")
            return urls
        except asyncio.TimeoutError:
            self.log_update.emit(f"[ERROR] Timeout loading page: {page_url}")
            return urls
        except Exception as e:
            self.log_update.emit(f"[ERROR] Could not load page: {page_url} – {e}")
            return urls

        base = urlparse(page_url)
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("javascript:") or href.startswith("#"):
                continue
            full_url = urljoin(page_url, href)
            parsed = urlparse(full_url)
            if parsed.scheme not in ("http", "https"):
                continue
            if self.same_domain_only and parsed.netloc != base.netloc:
                continue
            urls.append(full_url)

        self.log_update.emit(f"[INFO] Found {len(urls)} links on page (after filtering).")
        return urls

    async def _collect_from_sitemap(self, sitemap_url: str, session: aiohttp.ClientSession):
        urls = []
        submaps = []

        self.log_update.emit(f"[FETCH] Loading sitemap root: {sitemap_url}")
        xml_root = await self._fetch_xml(sitemap_url, session)
        if not xml_root:
            return urls

        try:
            root = ET.fromstring(xml_root)
        except ET.ParseError as e:
            self.log_update.emit(f"[ERROR] Could not parse root sitemap XML: {e}")
            return urls

        root_tag = root.tag.split('}')[-1].lower()

        if root_tag == "sitemapindex":
            self.log_update.emit("[INFO] Root is <sitemapindex> (has sub-sitemaps).")
            for sm_loc in root.iterfind(".//{*}sitemap/{*}loc"):
                if sm_loc.text:
                    sm_url = sm_loc.text.strip()
                    submaps.append(sm_url)

            self.log_update.emit(f"[INFO] Found {len(submaps)} sub-sitemaps.")
            for i, sm in enumerate(submaps, 1):
                if self._stop_requested:
                    break
                self.log_update.emit(f"[FETCH] ({i}/{len(submaps)}) {sm}")
                xml_sub = await self._fetch_xml(sm, session)
                if not xml_sub:
                    continue
                try:
                    r = ET.fromstring(xml_sub)
                    for loc in r.iterfind(".//{*}url/{*}loc"):
                        if loc.text:
                            urls.append(loc.text.strip())
                except ET.ParseError as e:
                    self.log_update.emit(f"[PARSE ERROR] Could not parse sub-sitemap {sm}: {e}")

        elif root_tag == "urlset":
            self.log_update.emit("[INFO] Root is <urlset> (single sitemap).")
            for loc in root.iterfind(".//{*}url/{*}loc"):
                if loc.text:
                    urls.append(loc.text.strip())
        else:
            self.log_update.emit(f"[WARN] Unknown sitemap root tag '{root_tag}', using generic <loc>.")
            for loc in root.iterfind(".//{*}loc"):
                if loc.text:
                    urls.append(loc.text.strip())

        self.log_update.emit(f"[INFO] Collected {len(urls)} URL(s) from sitemap.")
        return urls

    async def _fetch_xml(self, url: str, session: aiohttp.ClientSession):
        try:
            async with session.get(url, ssl=False, timeout=TIMEOUT_STANDARD) as r:
                if r.status != 200:
                    self.log_update.emit(f"[ERROR] {url} – status {r.status}")
                    return None
                return await r.text()
        except aiohttp.ClientError as e:
            self.log_update.emit(f"[ERROR] Network error fetching {url} – {e}")
            return None
        except asyncio.TimeoutError:
            self.log_update.emit(f"[ERROR] Timeout fetching {url}")
            return None
        except Exception as e:
            self.log_update.emit(f"[ERROR] {url} – {e}")
            return None

    async def _check_one(self, url: str, session: aiohttp.ClientSession, sem: asyncio.Semaphore):
        async with sem:
            if self._stop_requested:
                return None

            status = None
            final_url = ""
            error = ""
            try:
                # Try HEAD first
                try:
                    async with session.head(url, ssl=False, allow_redirects=False, timeout=TIMEOUT_SHORT) as resp:
                        status = resp.status
                        final_url = str(resp.url)
                except Exception:
                    # Fallback to GET
                    async with session.get(url, ssl=False, allow_redirects=False, timeout=TIMEOUT_STANDARD) as resp:
                        status = resp.status
                        final_url = str(resp.url)
            except aiohttp.ClientError as e:
                error = f"Network error: {str(e)}"
            except asyncio.TimeoutError:
                error = "Timeout"
            except Exception as e:
                error = str(e)

            category = "network_error"
            if status is not None:
                if 200 <= status < 300:
                    category = "ok"
                elif 300 <= status < 400:
                    category = "redirect"
                elif 400 <= status < 500:
                    category = "client_error"
                elif status >= 500:
                    category = "server_error"

            return {
                "url": url,
                "status": status,
                "final_url": final_url,
                "error": error,
                "category": category,
            }

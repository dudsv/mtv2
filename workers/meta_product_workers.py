"""
MetaCheckWorker and ProductSheetWorker for checking metadata and product information.
"""

import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from PyQt6.QtCore import QThread, pyqtSignal

from config import HEADERS, TIMEOUT_HEAVY, MAX_CONCURRENCY_META, MAX_CONCURRENCY_PRODUCT
from utils.helpers import norm_text, norm_title, norm_num


class MetaCheckWorker(QThread):
    """
    Worker for 'Meta Checker':
    - items: list of dicts {url, expected: {meta_title, meta_description, og_title, og_description, h1}}
    """
    progress_update = pyqtSignal(int)
    log_update = pyqtSignal(str)
    finished = pyqtSignal(list)  # list of results

    def __init__(self, items, max_concurrency: int = MAX_CONCURRENCY_META):
        super().__init__()
        self.items = items or []
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
            self.log_update.emit(f"[ERROR] MetaCheckWorker crashed: {e}")
        finally:
            self.finished.emit(self.results)

    async def main(self):
        total = len(self.items)
        if total == 0:
            self.progress_update.emit(100)
            self.log_update.emit("[INFO] No items to check.")
            return

        self.log_update.emit(f"[INIT] Meta Checker – {total} page(s) to check.")

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            sem = asyncio.Semaphore(self.max_concurrency)

            async def runner():
                done = 0
                # Each task carries the original index
                tasks = [
                    self._process_item_indexed(idx, item, session, sem)
                    for idx, item in enumerate(self.items)
                ]

                temp_results = []

                for coro in asyncio.as_completed(tasks):
                    if self._stop_requested:
                        self.log_update.emit("[WARN] Stop requested. Aborting remaining checks.")
                        break

                    idx, result = await coro
                    if result is not None:
                        temp_results.append((idx, result))

                    done += 1
                    self.progress_update.emit(int(done * 100 / total))

                # Ensure results are in same order as spreadsheet
                temp_results.sort(key=lambda x: x[0])
                self.results = [r for (_, r) in temp_results]

            await runner()

        self.progress_update.emit(100)
        self.log_update.emit("[DONE] Meta Checker finished.")

    async def _process_item(self, item, session: aiohttp.ClientSession, sem: asyncio.Semaphore):
        async with sem:
            if self._stop_requested:
                return None

            url = item.get("url", "").strip()
            expected = item.get("expected", {}) or {}
            current = {
                "meta_title": "",
                "meta_description": "",
                "og_title": "",
                "og_description": "",
                "h1": "",
            }
            match = {
                "meta_title": None,
                "meta_description": None,
                "og_title": None,
                "og_description": None,
                "h1": None,
            }

            if not url:
                return None

            html = None
            try:
                self.log_update.emit(f"[FETCH] {url}")
                async with session.get(url, ssl=False, timeout=TIMEOUT_HEAVY) as resp:
                    if resp.status != 200:
                        self.log_update.emit(f"[WARN] {url} – HTTP {resp.status}")
                    html = await resp.text(errors="ignore")
            except aiohttp.ClientError as e:
                self.log_update.emit(f"[ERROR] Network error fetching {url}: {e}")
            except asyncio.TimeoutError:
                self.log_update.emit(f"[ERROR] Timeout fetching {url}")
            except Exception as e:
                self.log_update.emit(f"[ERROR] Could not fetch {url}: {e}")

            if html:
                try:
                    soup = BeautifulSoup(html, "html.parser")

                    # <title>
                    title_tag = soup.find("title")
                    if title_tag and title_tag.text:
                        current["meta_title"] = title_tag.text

                    # <meta name="description">
                    md = soup.find("meta", attrs={"name": "description"})
                    if md and md.get("content"):
                        current["meta_description"] = md["content"]

                    # <meta property="og:title">
                    ogt = soup.find("meta", attrs={"property": "og:title"})
                    if ogt and ogt.get("content"):
                        current["og_title"] = ogt["content"]

                    # <meta property="og:description">
                    ogd = soup.find("meta", attrs={"property": "og:description"})
                    if ogd and ogd.get("content"):
                        current["og_description"] = ogd["content"]

                    # <h1> (first H1 on page)
                    h1_tag = soup.find("h1")
                    if h1_tag:
                        current["h1"] = h1_tag.get_text(separator=" ", strip=True)

                except Exception as e:
                    self.log_update.emit(f"[ERROR] Parsing HTML from {url}: {e}")

            # ---------- Comparison ----------
            # Normalize fields
            exp_mt = norm_title(expected.get("meta_title", ""))
            cur_mt = norm_title(current["meta_title"])

            exp_md = norm_text(expected.get("meta_description", ""))
            cur_md = norm_text(current["meta_description"])

            exp_ot = norm_title(expected.get("og_title", ""))
            cur_ot = norm_title(current["og_title"])

            exp_od = norm_text(expected.get("og_description", ""))
            cur_od = norm_text(current["og_description"])

            # H1 uses simple text normalization
            exp_h1 = norm_text(expected.get("h1", ""))
            cur_h1 = norm_text(current["h1"])

            # meta title
            if exp_mt:
                current["meta_title"] = cur_mt
                match["meta_title"] = (exp_mt == cur_mt)
            # meta description
            if exp_md:
                current["meta_description"] = cur_md
                match["meta_description"] = (exp_md == cur_md)
            # og title
            if exp_ot:
                current["og_title"] = cur_ot
                match["og_title"] = (exp_ot == cur_ot)
            # og description
            if exp_od:
                current["og_description"] = cur_od
                match["og_description"] = (exp_od == cur_od)
            # h1
            if exp_h1:
                current["h1"] = cur_h1
                match["h1"] = (exp_h1 == cur_h1)

            return {
                "url": url,
                "expected": {
                    "meta_title": exp_mt,
                    "meta_description": exp_md,
                    "og_title": exp_ot,
                    "og_description": exp_od,
                    "h1": exp_h1,
                },
                "current": current,
                "match": match,
            }

    async def _process_item_indexed(self, idx, item, session: aiohttp.ClientSession, sem: asyncio.Semaphore):
        result = await self._process_item(item, session, sem)
        return idx, result


class ProductSheetWorker(QThread):
    """
    Worker to check Product ID / GTIN from a standard spreadsheet.
    Reads URL, fetches the page, captures:
      - HTTP Status (with redirect detection)
      - Product ID (JSON-LD "@id")
      - GTIN/EAN ("sku" field)
    Compares with expected values and returns list of results.
    """
    progress_update = pyqtSignal(int)
    log_update = pyqtSignal(str)
    finished = pyqtSignal(list)  # list of dicts with result per row

    def __init__(self, items, max_concurrency: int = MAX_CONCURRENCY_PRODUCT):
        super().__init__()
        self.items = items or []
        self.max_concurrency = max_concurrency
        self._stop_requested = False
        self.results = []

    def stop(self):
        self._stop_requested = True

    @staticmethod
    def _extract_product_id(html: str) -> str:
        if not html:
            return ""
        # Look for any "@id":"<digits only>"
        m = re.search(r'"@id"\s*:\s*"(\d+)"', html)
        return m.group(1) if m else ""

    @staticmethod
    def _extract_gtin(html: str) -> str:
        if not html:
            return ""
        # Look for first "sku":"<digits only>"
        m = re.search(r'"sku"\s*:\s*"(\d+)"', html)
        return m.group(1) if m else ""

    async def main(self):
        total = len(self.items)
        if total == 0:
            self.progress_update.emit(100)
            self.log_update.emit("[INFO] No rows to process.")
            return

        self.log_update.emit(f"[INIT] ProductSheetWorker – {total} row(s) to check.")

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            sem = asyncio.Semaphore(self.max_concurrency)

            async def runner():
                done = 0
                tasks = [self._process_item(item, session, sem) for item in self.items]
                for coro in asyncio.as_completed(tasks):
                    if self._stop_requested:
                        self.log_update.emit("[WARN] Stop requested. Aborting remaining checks.")
                        break
                    result = await coro
                    if result is not None:
                        self.results.append(result)
                    done += 1
                    self.progress_update.emit(int(done * 100 / total))

            await runner()

        self.progress_update.emit(100)
        self.log_update.emit("[DONE] ProductSheetWorker finished.")

    async def _process_item(self, item, session: aiohttp.ClientSession, sem: asyncio.Semaphore):
        async with sem:
            if self._stop_requested:
                return None

            url_raw = item.get("url", "") or ""
            url = url_raw.strip()
            if not url:
                return None
            if not url.lower().startswith(("http://", "https://")):
                url = "https://" + url

            status =None
            final_url = ""
            html = ""

            try:
                self.log_update.emit(f"[FETCH] {url}")
                async with session.get(url, ssl=False, timeout=TIMEOUT_HEAVY, allow_redirects=True) as resp:
                    status = resp.status
                    final_url = str(resp.url)
                    html = await resp.text(errors="ignore")
            except aiohttp.ClientError as e:
                self.log_update.emit(f"[ERROR] Network error fetching {url}: {e}")
            except asyncio.TimeoutError:
                self.log_update.emit(f"[ERROR] Timeout fetching {url}")
            except Exception as e:
                self.log_update.emit(f"[ERROR] Could not fetch {url}: {e}")

            actual_id = self._extract_product_id(html)
            actual_gtin = self._extract_gtin(html)

            exp_id = norm_num(item.get("expected_id"))
            exp_gtin = norm_num(item.get("expected_gtin"))
            act_id_norm = norm_num(actual_id)
            act_gtin_norm = norm_num(actual_gtin)

            match_id = None
            if exp_id and act_id_norm:
                match_id = (exp_id == act_id_norm)

            match_gtin = None
            if exp_gtin and act_gtin_norm:
                match_gtin = (exp_gtin == act_gtin_norm)

            # Redirect detection: if final URL different from original
            redirect_from = ""
            redirect_to = ""
            if final_url and final_url.rstrip("/") != url.rstrip("/"):
                redirect_from = url_raw or url
                redirect_to = final_url

            return {
                "row": item.get("row"),
                "url": url_raw or url,
                "status": status,
                "from": redirect_from,
                "to": redirect_to,
                "actual_id": act_id_norm,
                "actual_gtin": act_gtin_norm,
                "expected_id": exp_id,
                "expected_gtin": exp_gtin,
                "match_id": match_id,
                "match_gtin": match_gtin,
            }

    def run(self):
        try:
            asyncio.run(self.main())
        except asyncio.CancelledError:
            self.log_update.emit("[WARN] Task was cancelled")
        except Exception as e:
            self.log_update.emit(f"[ERROR] ProductSheetWorker crashed: {e}")
        finally:
            self.finished.emit(self.results)

import asyncio
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from playwright.async_api import async_playwright
import sys
from pathlib import Path

# Provide resolving for standalone runs
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config.logger import get_logger

logger = get_logger(__name__)

class AsyncCrawler:
    def __init__(self, base_url: str, max_depth: int = 3, max_concurrency: int = 5):
        self.base_url = base_url
        self.max_depth = max_depth
        self.max_concurrency = max_concurrency

        # Clean base URL domains to strip 'www.' variations safely
        parsed_base = urlparse(base_url)
        self.allowed_domain = parsed_base.netloc.replace("www.", "")
        self.allowed_path_prefix = parsed_base.path if parsed_base.path else "/"

        # State tracking structures (Thread-safe inside single event loop)
        self.visited_urls = set()
        self.results = {}
        self.lock = asyncio.Lock()  # Protects shared state variables

    def _canonicalize_url(self, url: str) -> str:
        """Normalizes URLs to reduce duplicates caused by minor URL variations."""
        parsed = urlparse(url)

        scheme = (parsed.scheme or "https").lower()
        netloc = parsed.netloc.lower().replace("www.", "")

        path = parsed.path or "/"
        if path != "/":
            path = path.rstrip("/")

        # Remove common marketing/tracking query parameters
        tracking_keys = {"fbclid", "gclid", "msclkid", "mc_cid", "mc_eid"}
        query_items = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=False):
            lowered_key = key.lower()
            if lowered_key.startswith("utm_") or lowered_key in tracking_keys:
                continue
            query_items.append((key, value))

        # Sort query params so ?b=1&a=2 becomes ?a=2&b=1
        query_items.sort()
        normalized_query = urlencode(query_items, doseq=True)

        # Rebuild URL without fragments (handled by urlunparse natively with empty string)
        return urlunparse((scheme, netloc, path, "", normalized_query, ""))

    def _is_valid_url(self, url: str) -> bool:
        """Ensures the target URL matches the core domain boundary and path."""
        try:
            parsed = urlparse(url)
            clean_netloc = parsed.netloc.replace("www.", "")
            
            correct_domain = clean_netloc == self.allowed_domain
            # Safeguard path checks against empty root configurations
            current_path = parsed.path if parsed.path else "/"
            correct_path = current_path.startswith(self.allowed_path_prefix)
            
            return correct_domain and correct_path
        except Exception:
            return False

    async def _worker(self, queue: asyncio.Queue, context, out_queue: asyncio.Queue = None):
        """Worker instance designed to process queue segments concurrently."""
        while True:
            url, depth = await queue.get()
            
            async with self.lock:
                if url in self.visited_urls or depth > self.max_depth:
                    queue.task_done()
                    continue
                self.visited_urls.add(url)

            logger.info("processing_url", depth=depth, url=url)
            
            page = await context.new_page()
            try:
                # Optimized configurations for faster rendering
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                
                # Extract page details
                text_content = await page.evaluate("document.body.innerText")
                
                if out_queue:
                    await out_queue.put((url, text_content))
                else:
                    async with self.lock:
                        self.results[url] = text_content

                # Discover downstream page anchors
                hrefs = await page.eval_on_selector_all("a", "elements => elements.map(el => el.href)")
                
                for href in hrefs:
                    # Clean and canonicalize every discovered link before checking it
                    absolute_url = self._canonicalize_url(urljoin(url, href))
                    
                    async with self.lock:
                        if self._is_valid_url(absolute_url) and absolute_url not in self.visited_urls:
                            await queue.put((absolute_url, depth + 1))
                            
            except Exception as e:
                logger.error("crawl_error", url=url, error=str(e))
            finally:
                await page.close()
                queue.task_done()

    async def crawl(self, out_queue: asyncio.Queue = None):
        """Main orchestrator utilizing a concurrent worker execution loop."""
        async with async_playwright() as p:
            # Optimize memory utilization by disabling features unnecessary for text retrieval
            browser = await p.chromium.launch(
                headless=True, 
                args=["--disable-gpu", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) EnterpriseRAGCrawler/1.0"
            )
            
            queue = asyncio.Queue()
            await queue.put((self.base_url, 0))
            
            # Fire up parallel workers up to max_concurrency ceiling
            workers = [
                asyncio.create_task(self._worker(queue, context, out_queue)) 
                for _ in range(self.max_concurrency)
            ]
            
            # Wait cleanly until the structural queue pipeline drains completely
            await queue.join()
            
            # Wind down parallel worker tasks gracefully
            for worker in workers:
                worker.cancel()
                
            await asyncio.gather(*workers, return_exceptions=True)
            await browser.close()
            
        return self.results

if __name__ == "__main__":
    test_url = "https://cellpointdigital.com"
    crawler = AsyncCrawler(test_url, max_depth=2, max_concurrency=4)
    content = asyncio.run(crawler.crawl())
    print(f"\nSuccessfully crawled {len(content)} total platform urls.")
    print(f"First 10 items of the crawled content:\n{list(content.items())[:10]}")
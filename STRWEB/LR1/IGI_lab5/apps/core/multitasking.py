import asyncio
import threading
import time
from statistics import mean

from django.shortcuts import render


# ───── А. THREADING: 5 потоков берут книги через Semaphore(2) ─────

def borrow_book(name, semaphore, results, lock):
    with semaphore:
        start = time.perf_counter()
        time.sleep(0.3)   # имитация обращения к БД/каталогу
        elapsed = time.perf_counter() - start
        with lock:
            results.append({"name": name, "time": round(elapsed, 3)})


def run_threading():
    semaphore = threading.Semaphore(2)   # 2 «библиотекаря»
    lock = threading.Lock()
    results = []
    readers = [f"Читатель-{i+1}" for i in range(5)]

    t0 = time.perf_counter()
    threads = [
        threading.Thread(target=borrow_book, args=(r, semaphore, results, lock))
        for r in readers
    ]
    for t in threads: t.start()
    for t in threads: t.join()
    total = round(time.perf_counter() - t0, 3)
    return results, total


# ───── Б. MULTIPROCESSING: индексация слов в 4 «томах» ─────

def index_words_chunk(text_chunk):
    """Считает уникальные слова в куске текста. Запускается в отдельном процессе."""
    import collections
    words = text_chunk.lower().split()
    return dict(collections.Counter(words))


def run_multiprocessing():
    from multiprocessing import Pool
    import collections

    # Генерируем 4 «тома» по ~10 000 слов каждый
    base = ("косметология дерматология уход лицо кожа процедура клиент врач "
            "крем маска пилинг лазер инъекция витамин увлажнение тон очищение ") * 625
    chunks = [base] * 4

    t0 = time.perf_counter()
    with Pool(processes=4) as pool:
        results = pool.map(index_words_chunk, chunks)
    total = round(time.perf_counter() - t0, 3)

    # Объединяем счётчики
    merged = collections.Counter()
    for r in results:
        merged.update(r)
    top10 = merged.most_common(10)
    return top10, total


# ───── В. ASYNCIO: поиск книги по 10 онлайн-каталогам ─────

async def search_catalog(catalog_id, delay):
    await asyncio.sleep(delay)
    return {"catalog": f"Каталог-{catalog_id}", "found": catalog_id % 3 != 0}


async def run_async_search():
    import random
    random.seed(42)
    delays = [round(random.uniform(0.05, 0.3), 2) for _ in range(10)]
    t0 = time.perf_counter()
    tasks = [search_catalog(i+1, d) for i, d in enumerate(delays)]
    results = await asyncio.gather(*tasks)
    total = round(time.perf_counter() - t0, 3)
    return results, total


def multitasking_view(request):
    # A — threading
    thread_results, thread_time = run_threading()

    # Б — multiprocessing
    mp_top10, mp_time = run_multiprocessing()

    # В — asyncio
    loop = asyncio.new_event_loop()
    async_results, async_time = loop.run_until_complete(run_async_search())
    loop.close()

    context = {
        "thread_results": thread_results,
        "thread_time": thread_time,
        "mp_top10": mp_top10,
        "mp_time": mp_time,
        "async_results": async_results,
        "async_time": async_time,
    }
    return render(request, "multitasking.html", context)

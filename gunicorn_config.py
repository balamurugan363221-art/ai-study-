import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_class = 'gthread'
bind = '0.0.0.0:10000'
timeout = 120
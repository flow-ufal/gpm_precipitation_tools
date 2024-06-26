from datetime import datetime
import multiprocessing as mp
import psutil

start = datetime.now()

def loop(core, r):
    proc = psutil.Process()
    proc.cpu_affinity([core])
    for n in range(r):
        result = (n*(n+1))/2
    return result

cores = [0, 1, 2]
ranges = [100000000, 200000000, 300000000]
results = []

if __name__ == '__main__':
    with mp.Pool() as pool:
        for core in cores:
            p = pool.apply_async(func=loop, args=(core, ranges[core],))
            results.append(p)
        pool.close()
        pool.join()
result = 0

for p in results:
    result = result + p.get()
    print(f'Resultado: {result}')
    print(f'Tempo: {datetime.now() - start}')

#!/usr/bin/env python3

from queue import Queue
from KlippyRPCShim import KlippyRPCShim

def main():
    krpc = KlippyRPCShim()
    info = {
        "method": "info",
        "params": {
            "client_info": {
                "program": "KRPC", "version": "0.0.1"
            }
        }
    }
    # Register itself and test connection
    resp = krpc.query(info)
    print(f"sync response: {resp}")
    promise = krpc.query_async(info)
    print(f"async response: {promise()}")

    # Test subscription
    import statistics
    request = {"method": "adxl345/dump_adxl345", "params": {"sensor": "adxl345"}}
    pkgs = 5
    generator, cancel = krpc.subscribe(request)
    for resp in generator():
        params = resp.get("params")
        if params is None:
            continue
        d = params["data"]
        val = [row[1] for row in d]

        # Compute mean and standard deviation
        mean_val = statistics.mean(val)
        stddev_val = statistics.stdev(val) if len(val) > 1 else 0.0

        print(f"Mean value: {mean_val:.3f}, StdDev: {stddev_val:.3f}")
        pkgs -= 1
        if pkgs <= 0:
            cancel()

    params_q = Queue(1)
    krpc.register_remote_method(callback=params_q.put, remote_method="noop")
    while True:
        print(f"{params_q.get()}")

if __name__ == "__main__":
    main()

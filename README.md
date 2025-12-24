# KlippyRPCShim
Simple klipper raw API wrapper

## Installation
```bash
pip install git+https://github.com/nefelim4ag/KlippyRPCShim.git
```

## Usage

Just take a peek at example.py

```python
from KlippyRPCShim import KlippyRPCShim

krpc = KlippyRPCShim()
info = krpc.query({
    "method": "info",
    "params": {"client_info": {"program": "MyApp", "version": "1.0"}}
})
print(info)
```

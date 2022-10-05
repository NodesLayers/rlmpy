# rlmpy
A Wrapper library for Python to get or set information on Reprise License Manager servers using rlmutil executable

## Usage

```python
import rlmpy

rlm_server_data = rlmpy.rlmInfo(
    server="rlm.mylicenseserver.com", 
    port="4101", 
    rlmutil_exe="C:/path/to/my/rlmutil/file(.exe)"
)
```

rlm_server_data.licenses returns:
--------
```python
[
    {'available': 0,
      'count': 1,
      'exp': 'permanent',
      'inuse': 1,
      'license': 'hiero_i',
      'min_remove': 120,
      'obsolete': 0,
      'pool': 'pool:',
      'reserved': 0,
      'soft_limit': 1,
      'total_checkouts': 17,
      'version': 'v2022.1120'},
     {'available': 1,
      'count': 1,
      'exp': 'permanent',
      'inuse': 0,
      'license': 'hiero_i',
      'min_remove': 120,
      'obsolete': 0,
      'pool': 'pool:',
      'reserved': 0,
      'soft_limit': 1,
      'total_checkouts': 0,
      'version': 'v2017.1107'},
     {'available': 1,
      'count': 20,
      'exp': 'permanent',
      'inuse': 19,
      'license': 'nuke_r',
      'min_remove': 120,
      'obsolete': 0,
      'pool': 'pool:',
      'reserved': 0,
      'soft_limit': 20,
      'total_checkouts': 1452,
      'version': 'v2022.1107'},
]
```
  

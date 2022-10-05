# rlmpy
A Wrapper library for Python to get or set information on Reprise License Manager servers using rlmutil executable

## Usage

```python
rlm_server_data = rlmpy.rlmInfo(
    server="rlm.mylicenseserver.com", 
    port="4101", 
    rlmutil_exe="C:/path/to/my/rlmutil/file(.exe)")
```
  

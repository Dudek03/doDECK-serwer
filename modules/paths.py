import os
import sys


def get_app_data_dir() -> str:
    """
    Returns path to application data directory (%APPDATA%\\doDECK or ~/.dodeck).
    Creates directory if it does not exist.
    """
    appdata = os.getenv("APPDATA")
    if not appdata:
        appdata = os.path.expanduser("~")
    data_dir = os.path.join(appdata, "doDECK")
    try:
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    except Exception:
        fallback = os.path.join(os.getenv("TEMP", os.path.expanduser("~")), "doDECK")
        try:
            os.makedirs(fallback, exist_ok=True)
        except Exception:
            pass
        return fallback


def get_config_path(filename: str) -> str:
    """
    Returns a safe path to a configuration file (e.g. buttons_config.json, trusted_devices.json).

    Resolution order:
    1. If file already exists in current directory (unless System32):
       use it (useful for local dev and tests).
    2. If file exists next to .exe executable (unless System32 or temp):
       use it (portable mode).
    3. If file exists in APPDATA:
       use it.
    4. Default: return path in APPDATA (always writable).
    """
    sys_root = os.environ.get("SystemRoot", r"C:\Windows")
    sys_root_norm = os.path.normpath(sys_root).lower()

    # 1. Current working directory (unless in System32)
    cwd = os.path.normpath(os.getcwd())
    if not cwd.lower().startswith(sys_root_norm):
        local_candidate = os.path.join(cwd, filename)
        if os.path.exists(local_candidate):
            return local_candidate

    # 2. Directory next to executable or script (unless in System32 or Temp)
    exe_dir = (
        os.path.dirname(os.path.abspath(sys.executable))
        if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    exe_dir_norm = os.path.normpath(exe_dir).lower()
    temp_dir = os.path.normpath(os.getenv("TEMP", "")).lower()

    if not exe_dir_norm.startswith(sys_root_norm):
        if not (temp_dir and exe_dir_norm.startswith(temp_dir)):
            exe_candidate = os.path.join(exe_dir, filename)
            if os.path.exists(exe_candidate):
                return exe_candidate

    # 3. File in application data directory (APPDATA)
    data_dir = get_app_data_dir()
    appdata_candidate = os.path.join(data_dir, filename)
    if os.path.exists(appdata_candidate):
        return appdata_candidate

    # 4. Default path for creating new file
    return appdata_candidate


def set_safe_working_directory() -> None:
    """Changes working directory to app data directory if process started in System32."""
    try:
        sys_root = os.environ.get("SystemRoot", r"C:\Windows")
        sys_root_norm = os.path.normpath(sys_root).lower()
        cwd = os.path.normpath(os.getcwd()).lower()
        if cwd.startswith(sys_root_norm):
            target_dir = get_app_data_dir()
            os.chdir(target_dir)
    except Exception:
        pass

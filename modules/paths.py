import os
import sys


def get_app_data_dir():
    """
    Zwraca ścieżkę do katalogu danych aplikacji (%APPDATA%\\doDECK lub ~/.dodeck).
    Tworzy katalog, jeśli nie istnieje.
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


def get_config_path(filename):
    """
    Zwraca bezpieczną ścieżkę do pliku konfiguracyjnego (np. buttons_config.json, trusted_devices.json).

    Hierarchia wyboru:
    1. Jeśli plik już istnieje w bieżącym katalogu (o ile to nie System32):
       użyj go (przydatne przy testach i uruchamianiu w repozytorium).
    2. Jeśli plik istnieje obok pliku wykonywalnego .exe (o ile to nie System32 i nie temp):
       użyj go (tryb przenośny).
    3. Jeśli plik istnieje w katalogu APPDATA:
       użyj go.
    4. Domyślnie: zwróć ścieżkę w APPDATA (gdzie zawsze jest prawo do zapisu).
    """
    sys_root = os.environ.get("SystemRoot", r"C:\Windows")
    sys_root_norm = os.path.normpath(sys_root).lower()

    # 1. Bieżący katalog roboczy (jeśli nie jest w System32)
    cwd = os.path.normpath(os.getcwd())
    if not cwd.lower().startswith(sys_root_norm):
        local_candidate = os.path.join(cwd, filename)
        if os.path.exists(local_candidate):
            return local_candidate

    # 2. Katalog obok pliku wykonywalnego / skryptu (jeśli nie jest w System32 ani w Temp)
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

    # 3. Plik w katalogu danych aplikacji (APPDATA)
    data_dir = get_app_data_dir()
    appdata_candidate = os.path.join(data_dir, filename)
    if os.path.exists(appdata_candidate):
        return appdata_candidate

    # 4. Domyślna lokalizacja do utworzenia nowego pliku
    return appdata_candidate


def set_safe_working_directory():
    """Zmienia katalog roboczy na katalog danych aplikacji, jeśli proces wystartował w System32."""
    try:
        sys_root = os.environ.get("SystemRoot", r"C:\Windows")
        sys_root_norm = os.path.normpath(sys_root).lower()
        cwd = os.path.normpath(os.getcwd()).lower()
        if cwd.startswith(sys_root_norm):
            target_dir = get_app_data_dir()
            os.chdir(target_dir)
    except Exception:
        pass

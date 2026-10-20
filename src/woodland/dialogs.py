"""Windows 原生导入/导出文件选择器。"""
import os
from pathlib import Path
from .scoring import SaveError

def choose_save_file(save=False):
    """Windows 原生文件对话框；无需额外 GUI 依赖，也不会更改工作目录。"""
    if os.name != 'nt':
        raise SaveError('File dialogs require Windows. F5/F9 still use the local save folder.')
    import ctypes
    from ctypes import wintypes
    class OpenFileName(ctypes.Structure):
        _fields_ = [('lStructSize', wintypes.DWORD), ('hwndOwner', wintypes.HWND),
            ('hInstance', wintypes.HINSTANCE), ('lpstrFilter', wintypes.LPCWSTR),
            ('lpstrCustomFilter', wintypes.LPWSTR), ('nMaxCustFilter', wintypes.DWORD),
            ('nFilterIndex', wintypes.DWORD), ('lpstrFile', wintypes.LPWSTR),
            ('nMaxFile', wintypes.DWORD), ('lpstrFileTitle', wintypes.LPWSTR),
            ('nMaxFileTitle', wintypes.DWORD), ('lpstrInitialDir', wintypes.LPCWSTR),
            ('lpstrTitle', wintypes.LPCWSTR), ('Flags', wintypes.DWORD),
            ('nFileOffset', wintypes.WORD), ('nFileExtension', wintypes.WORD),
            ('lpstrDefExt', wintypes.LPCWSTR), ('lCustData', ctypes.c_ssize_t),
            ('lpfnHook', ctypes.c_void_p), ('lpTemplateName', wintypes.LPCWSTR),
            ('pvReserved', ctypes.c_void_p), ('dwReserved', wintypes.DWORD),
            ('FlagsEx', wintypes.DWORD)]
    buffer = ctypes.create_unicode_buffer(32768)
    if save:
        buffer.value = 'MiniFPS-save.json'
    info = OpenFileName()
    info.lStructSize = ctypes.sizeof(info)
    ctypes.windll.user32.GetForegroundWindow.restype = wintypes.HWND
    info.hwndOwner = ctypes.windll.user32.GetForegroundWindow()
    info.lpstrFilter = 'MiniFPS JSON saves\0*.json\0\0'
    info.lpstrFile = ctypes.cast(buffer, wintypes.LPWSTR)
    info.nMaxFile = len(buffer)
    info.lpstrTitle = 'Export MiniFPS save' if save else 'Import MiniFPS save'
    info.lpstrDefExt = 'json'
    info.Flags = 0x00080000 | 0x00000800 | 0x00000008 | (0x00000002 if save else 0x00001000)
    function = ctypes.windll.comdlg32.GetSaveFileNameW if save else ctypes.windll.comdlg32.GetOpenFileNameW
    function.argtypes = [ctypes.POINTER(OpenFileName)]
    function.restype = wintypes.BOOL
    if function(ctypes.byref(info)):
        return Path(buffer.value)
    if ctypes.windll.comdlg32.CommDlgExtendedError():
        raise SaveError('Windows could not open the file dialog.')
    return None

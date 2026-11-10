"""Acceso nativo a memoria y procesos descendientes en Windows."""

from __future__ import annotations

import ctypes
from typing import Any


def _process_depth(pid: int, parents: dict[int, int], process_ids: set[int]) -> int:
    """Calcula la profundidad de un proceso dentro del árbol observado."""
    level = 0
    parent_pid = parents.get(pid)
    ancestors = {pid}
    while parent_pid in process_ids and parent_pid not in ancestors:
        level += 1
        ancestors.add(parent_pid)
        parent_pid = parents.get(parent_pid)
    return level


class WindowsProcessTreeMemory:
    """Mide y termina un proceso Windows junto con sus descendientes."""

    metric = "PeakProcessTreeWorkingSetSize"

    def __init__(self, pid: int) -> None:
        self._pid = pid
        self._peak_bytes = 0
        self._handles: dict[int, Any] = {}
        self._initialize_windows()

    def _initialize_windows(self) -> None:
        from ctypes import wintypes

        class MemoryCountersEx(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]

        self._counters_type = MemoryCountersEx
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._psapi = ctypes.WinDLL("psapi", use_last_error=True)
        self._process_entry = self._process_entry_type()
        self._kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self._kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        self._kernel32.Process32FirstW.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(self._process_entry),
        ]
        self._kernel32.Process32FirstW.restype = wintypes.BOOL
        self._kernel32.Process32NextW.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(self._process_entry),
        ]
        self._kernel32.Process32NextW.restype = wintypes.BOOL
        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self._kernel32.TerminateProcess.restype = wintypes.BOOL
        self._kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._kernel32.WaitForSingleObject.restype = wintypes.DWORD
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL
        self._psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(MemoryCountersEx),
            wintypes.DWORD,
        ]
        self._psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    @staticmethod
    def _process_entry_type() -> type[ctypes.Structure]:
        from ctypes import wintypes

        class ProcessEntry32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        return ProcessEntry32W

    def _windows_process_parents(self) -> dict[int, int]:
        snapshot = self._kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
        invalid_handle = ctypes.c_void_p(-1).value
        if not snapshot or ctypes.cast(snapshot, ctypes.c_void_p).value == invalid_handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            parents: dict[int, int] = {}
            entry = self._process_entry()
            entry.dwSize = ctypes.sizeof(entry)
            has_entry = self._kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
            while has_entry:
                parents[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
                has_entry = self._kernel32.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            self._kernel32.CloseHandle(snapshot)
        return parents

    def _windows_process_tree(self) -> set[int]:
        parents = self._windows_process_parents()
        process_ids = {self._pid}
        while True:
            descendants = {
                pid for pid, parent_pid in parents.items() if parent_pid in process_ids
            }
            expanded = process_ids | descendants
            if expanded == process_ids:
                return process_ids
            process_ids = expanded

    def _open_windows_process(self, pid: int) -> None:
        if pid in self._handles:
            return
        access = 0x0001 | 0x0400 | 0x0010  # TERMINATE | QUERY_INFORMATION | VM_READ
        handle = self._kernel32.OpenProcess(access, False, pid)
        if handle:
            self._handles[pid] = handle

    def _remaining_process_ids(self, process_ids: set[int]) -> set[int]:
        return {
            pid
            for pid in process_ids
            if pid not in self._handles
            or self._kernel32.WaitForSingleObject(self._handles[pid], 0) != 0
        }

    def terminate_windows_tree(self) -> set[int]:
        """Termina descendientes y lanzador usando sus handles de proceso."""
        known_processes = {self._pid}
        for _ in range(5):
            try:
                parents = self._windows_process_parents()
            except OSError:
                return self._remaining_process_ids(known_processes)
            while True:
                descendants = {
                    pid
                    for pid, parent_pid in parents.items()
                    if parent_pid in known_processes and pid not in known_processes
                }
                if not descendants:
                    break
                known_processes.update(descendants)

            for pid in known_processes:
                self._open_windows_process(pid)
            for pid in sorted(
                known_processes,
                key=lambda process_id: _process_depth(process_id, parents, known_processes),
                reverse=True,
            ):
                handle = self._handles.get(pid)
                if handle is not None:
                    self._kernel32.TerminateProcess(handle, 1)
            for handle in self._handles.values():
                self._kernel32.WaitForSingleObject(handle, 1000)

            alive = self._remaining_process_ids(known_processes) & parents.keys()
            if not alive:
                return set()

        try:
            parents = self._windows_process_parents()
        except OSError:
            return self._remaining_process_ids(known_processes)
        while True:
            descendants = {
                pid
                for pid, parent_pid in parents.items()
                if parent_pid in known_processes and pid not in known_processes
            }
            if not descendants:
                break
            known_processes.update(descendants)
        return self._remaining_process_ids(known_processes) & parents.keys()

    def read(self) -> int:
        process_ids = self._windows_process_tree()
        total_bytes = 0
        for pid in process_ids:
            self._open_windows_process(pid)
            handle = self._handles.get(pid)
            if handle is None:
                continue
            counters = self._counters_type()
            counters.cb = ctypes.sizeof(counters)
            if self._psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb
            ):
                total_bytes += int(counters.WorkingSetSize)
        self._peak_bytes = max(self._peak_bytes, total_bytes)
        return self._peak_bytes

    def close(self) -> None:
        for handle in self._handles.values():
            self._kernel32.CloseHandle(handle)
        self._handles.clear()

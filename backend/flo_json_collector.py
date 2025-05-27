import json
import regex
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
import logging


class CollectionStatus(Enum):
    success = "success"
    partial = "partial"
    error = "error"


class FloException(Exception):
    """Custom exception for FloJsonOutputCollector"""
    def __init__(self, message: str, error_code: int = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class FloOutputCollector:
    """Base class for output collectors"""
    def __init__(self):
        self.data = []
        self.status = CollectionStatus.success


class FloJsonOutputCollector(FloOutputCollector):
    """
    FloJsonOutputCollector — collects JSON payloads from LLM/agent outputs,
    gracefully handles comments, and offers "Flo" Q-promise looping.
    Key Features:
      - strip out // and /*…*/ comments before parsing
      - recursive regex to find balanced { … } blocks
      - strict mode: raise if no JSON found
      - peek, pop, fetch to manage collected data
      - rewind(): recursive promise-then replay, newest-first
      - iter_q(): while–for hybrid iterator over memory steps
    """

    def __init__(self, strict: bool = False):
        super().__init__()
        self.strict = strict                         # Enforce JSON presence?
        self.status = CollectionStatus.success       # success, partial, or error
        self.data: List[Dict[str, Any]] = []         # stored JSON dictionaries
        self.memory_trail: List[Dict[str, Any]] = [] # breadcrumb trail for emergent work
        self.session_id: str = ""                    # for persistent context
        self.ip_trail: List[str] = []                # IP trail maintenance

    def append(self, agent_output: str):
        """Extracts JSON from `agent_output` and appends the resulting dict."""
        extracted = self.__extract_jsons(agent_output)
        self.data.append(extracted)
        
        # Add to memory trail for breadcrumb tracking
        self.memory_trail.append({
            "timestamp": self.__get_timestamp(),
            "raw_output": agent_output[:200] + "..." if len(agent_output) > 200 else agent_output,
            "extracted_json": extracted,
            "status": self.status.value
        })

    def __strip_comments(self, json_str: str) -> str:
        """Remove JS-style comments so json.loads() will succeed."""
        cleaned, length, i = [], len(json_str), 0

        while i < length:
            char = json_str[i]

            if char not in '"/*':
                cleaned.append(char); i += 1; continue

            if char == '"':
                cleaned.append(char); i += 1
                while i < length:
                    cleaned.append(json_str[i])
                    if json_str[i] == '"' and json_str[i-1] != '\\':
                        i += 1
                        break
                    i += 1
                continue

            if char == '/' and i + 1 < length:
                nxt = json_str[i+1]
                if nxt == '/':
                    i += 2
                    while i < length and json_str[i] != '\n':
                        i += 1
                    continue
                if nxt == '*':
                    i += 2
                    while i+1 < length:
                        if json_str[i] == '*' and json_str[i+1] == '/':
                            i += 2
                            break
                        i += 1
                    continue

            cleaned.append(char); i += 1

        return ''.join(cleaned)

    def __extract_jsons(self, llm_response: str) -> Dict[str, Any]:
        """
        1) Find all balanced `{ … }` blocks via recursive regex
        2) Strip comments and json.loads() each
        3) Merge into one dict (later keys override earlier)
        4) On strict mode, error if no JSON found
        """
        pattern = r'\{(?:[^{}]|(?R))*\}'
        matches = regex.findall(pattern, llm_response)
        merged: Dict[str, Any] = {}

        for json_str in matches:
            try:
                cleaned = self.__strip_comments(json_str)
                obj = json.loads(cleaned)
                merged.update(obj)
            except json.JSONDecodeError as e:
                self.status = CollectionStatus.partial
                logging.error(f'Invalid JSON in response: {json_str} — {e}')

        if self.strict and not matches:
            self.status = CollectionStatus.error
            logging.error(f'No JSON found in strict mode: {llm_response}')
            raise FloException(
                'JSON response expected in collector model: strict', error_code=1099
            )
        return merged

    # ———————————————————————————————
    # Standard Data Management
    # ———————————————————————————————

    def pop(self) -> Dict[str, Any]:
        """Remove and return the last collected JSON dict."""
        return self.data.pop() if self.data else {}

    def peek(self) -> Optional[Dict[str, Any]]:
        """View the last collected JSON dict without removing it."""
        return self.data[-1] if self.data else None

    def fetch(self) -> Dict[str, Any]:
        """Merge all collected dicts into one and return it."""
        return self.__merge_data()

    def __merge_data(self) -> Dict[str, Any]:
        merged = {}
        for d in self.data:
            merged.update(d)
        return merged

    # ———————————————————————————————
    # Flo Q-Promise Looping Methods
    # ———————————————————————————————

    def rewind(
        self,
        then_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        depth: Optional[int] = None
    ):
        """
        Recursively replay memory entries newest→oldest, invoking `then_callback` per step.
        Mirrors JS Promise.then chaining in reverse order.
        :param then_callback: function to handle each entry
        :param depth: max number of entries to process
        """
        if not self.data:
            logging.warning("No memory to rewind.")
            return

        entries = self.data[::-1]            # reverse: newest first
        if depth:
            entries = entries[:depth]

        def _recursive(idx: int):
            if idx >= len(entries):
                return
            entry = entries[idx]
            if then_callback:
                then_callback(entry)
            _recursive(idx + 1)

        _recursive(0)

    def iter_q(self, depth: Optional[int] = None) -> "FloIterator":
        """
        Return a FloIterator that yields one-item lists of entries,
        enabling a while–for hybrid loop over memory steps.
        """
        return FloIterator(self, depth)

    # ———————————————————————————————
    # Advanced Memory Management
    # ———————————————————————————————

    def get_memory_trail(self) -> List[Dict[str, Any]]:
        """Get the complete memory breadcrumb trail."""
        return self.memory_trail

    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context state."""
        return {
            "total_entries": len(self.data),
            "status": self.status.value,
            "strict_mode": self.strict,
            "session_id": self.session_id,
            "memory_trail_length": len(self.memory_trail),
            "last_entry": self.peek(),
            "merged_context": self.fetch()
        }

    def set_session_context(self, session_id: str, ip_address: str = ""):
        """Set persistent session context."""
        self.session_id = session_id
        if ip_address and ip_address not in self.ip_trail:
            self.ip_trail.append(ip_address)

    def clear_memory(self):
        """Clear all collected data and memory trail."""
        self.data.clear()
        self.memory_trail.clear()
        self.status = CollectionStatus.success

    def __get_timestamp(self) -> str:
        """Get current timestamp for memory trail."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


class FloIterator:
    """
    Hybrid while–for iterator over FloJsonOutputCollector data.
    Newest entries first, depth-limited.
    """

    def __init__(self, collector: FloJsonOutputCollector, depth: Optional[int] = None):
        self.entries = collector.data[::-1]
        self.limit = depth if depth is not None else len(self.entries)
        self.index = 0
        self.collector = collector

    def has_next(self) -> bool:
        """True if more entries remain."""
        return self.index < self.limit and self.index < len(self.entries)

    def next(self) -> List[Dict[str, Any]]:
        """
        Return the next "batch" of entries (here, a single-item list).
        Returns [] when exhausted.
        """
        if not self.has_next():
            return []
        entry = self.entries[self.index]
        self.index += 1
        return [entry]

    def current_position(self) -> Dict[str, Any]:
        """Get current iterator position information."""
        return {
            "index": self.index,
            "total": len(self.entries),
            "limit": self.limit,
            "has_next": self.has_next(),
            "remaining": max(0, min(self.limit, len(self.entries)) - self.index)
        }

    def peek_next(self) -> Optional[Dict[str, Any]]:
        """Peek at the next entry without advancing iterator."""
        if not self.has_next():
            return None
        return self.entries[self.index]

    def reset(self):
        """Reset iterator to beginning."""
        self.index = 0

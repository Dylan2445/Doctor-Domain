from typing import Optional, Callable

class AuthState:
    _instance = None
    _listeners = []

    def __init__(self):
        self._access_token = None
        self._is_logged_in = False

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = AuthState()
        return cls._instance
    
    def add_listener(self, listener: Callable[[], None]):
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self):
        for listener in self._listeners:
            listener()

    @property
    def is_logged_in(self) -> bool:
        return self._is_logged_in

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token

    def login(self, access_token: str):
        self._access_token = access_token
        self._is_logged_in = True
        self._notify_listeners()

    def logout(self):
        self._access_token = None
        self._is_logged_in = False
        self._notify_listeners()
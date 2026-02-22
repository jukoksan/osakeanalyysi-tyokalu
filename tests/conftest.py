"""
Pytest-konfiguraatio: mockaa streamlit ennen app-moduulin importia.
"""
import sys
from unittest.mock import MagicMock

# --- Streamlit mock ---
# st.cache_data on dekoraattori → palautetaan aina itse funktio muuttumattomana
def _cache_data_passthrough(*args, **kwargs):
    """Toimii sekä @st.cache_data että @st.cache_data(ttl=...) -muodoissa."""
    if len(args) == 1 and callable(args[0]):
        # Käytetty ilman argumentteja: @st.cache_data
        return args[0]
    # Käytetty argumenteilla: @st.cache_data(ttl=300)
    return lambda f: f

_st = MagicMock()
_st.session_state = {"lang": "fi"}
_st.cache_data = _cache_data_passthrough
_st.cache_data.clear = MagicMock()

sys.modules.setdefault("streamlit", _st)

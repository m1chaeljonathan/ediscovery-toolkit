"""First-run setup wizard.

Detects LLM providers, guides model selection/download, and persists
config.yaml so the wizard never appears again unless the user reconfigures.
"""

import platform
import time

import requests
import streamlit as st

from config import load_config, save_config

# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------

_PROBE_TIMEOUT = 2  # seconds


def _probe_ollama(base_url: str) -> dict | None:
    """Probe an Ollama instance. Returns {'models': [...]} or None."""
    # base_url is OpenAI-compat (/v1), Ollama native API is one level up
    api_root = base_url.rsplit('/v1', 1)[0]
    try:
        resp = requests.get(f"{api_root}/api/tags", timeout=_PROBE_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            models = [m['name'] for m in data.get('models', [])]
            return {'models': models, 'api_root': api_root, 'base_url': base_url}
    except Exception:
        pass
    return None


def _probe_openai_compat(base_url: str) -> dict | None:
    """Probe an OpenAI-compatible endpoint (LM Studio, vLLM, etc.)."""
    try:
        resp = requests.get(f"{base_url}/models", timeout=_PROBE_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            models = [m['id'] for m in data.get('data', [])]
            return {'models': models, 'base_url': base_url}
    except Exception:
        pass
    return None


def detect_providers() -> dict:
    """Scan known ports and return detected providers."""
    results = {}

    # Check configured URL first
    cfg = load_config()
    configured_url = cfg['llm']['base_url']

    # Ollama on standard port
    ollama_urls = ['http://localhost:11434/v1']
    # Docker inter-container
    if 'ollama:11434' in configured_url:
        ollama_urls.insert(0, configured_url)
    # Deduplicate while preserving order
    seen = set()
    for url in ollama_urls:
        if url not in seen:
            seen.add(url)
            result = _probe_ollama(url)
            if result:
                results['ollama'] = result
                break

    # LM Studio on standard port
    lm_url = 'http://localhost:1234/v1'
    result = _probe_openai_compat(lm_url)
    if result:
        results['lm_studio'] = result

    return results


# ---------------------------------------------------------------------------
# Ollama model management
# ---------------------------------------------------------------------------

# Recommended models in order of preference
RECOMMENDED_MODELS = [
    ('llama3.1:8b', '4.7 GB — fast, good for most tasks'),
    ('qwen2.5:32b', '20 GB — best quality, needs 32GB+ RAM'),
    ('phi4:14b', '9 GB — good balance of speed and quality'),
]


def pull_ollama_model(api_root: str, model_name: str) -> bool:
    """Pull a model from Ollama with streaming progress. Returns True on success."""
    progress_bar = st.progress(0, text=f"Downloading {model_name}...")
    status_text = st.empty()

    try:
        resp = requests.post(
            f"{api_root}/api/pull",
            json={"name": model_name, "stream": True},
            stream=True,
            timeout=600,
        )
        for line in resp.iter_lines():
            if not line:
                continue
            import json
            data = json.loads(line)
            status = data.get('status', '')

            if 'total' in data and 'completed' in data:
                pct = data['completed'] / data['total']
                progress_bar.progress(
                    min(pct, 1.0),
                    text=f"Downloading {model_name}: {pct:.0%}")
            else:
                status_text.caption(status)

        progress_bar.progress(1.0, text=f"{model_name} ready")
        status_text.empty()
        return True
    except Exception as e:
        progress_bar.empty()
        status_text.error(f"Download failed: {e}")
        return False


def test_llm_connection(base_url: str, model: str,
                        api_key: str = 'local') -> dict:
    """Send a simple test prompt. Returns {'ok': bool, 'ms': int, 'error': str}."""
    try:
        from openai import OpenAI
        client = OpenAI(base_url=base_url, api_key=api_key)
        start = time.time()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello in one sentence."}],
            max_tokens=30,
        )
        elapsed = int((time.time() - start) * 1000)
        text = resp.choices[0].message.content.strip()
        return {'ok': True, 'ms': elapsed, 'response': text}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# ---------------------------------------------------------------------------
# Wizard UI
# ---------------------------------------------------------------------------

def _init_wizard_state():
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 'detect'
    if 'wizard_providers' not in st.session_state:
        st.session_state.wizard_providers = {}
    if 'wizard_choice' not in st.session_state:
        st.session_state.wizard_choice = None


def render_wizard() -> bool:
    """Render the setup wizard. Returns True if setup is complete."""
    _init_wizard_state()

    st.header("Welcome to the eDiscovery Toolkit")
    st.caption("Let's configure your LLM provider. All data stays on your machine.")

    step = st.session_state.wizard_step

    # ------------------------------------------------------------------
    # Step 1: Detection
    # ------------------------------------------------------------------
    if step == 'detect':
        with st.spinner("Scanning for LLM providers..."):
            providers = detect_providers()
            st.session_state.wizard_providers = providers

        if providers:
            st.success(f"Found {len(providers)} provider(s)")
            for name, info in providers.items():
                label = {'ollama': 'Ollama', 'lm_studio': 'LM Studio'}.get(
                    name, name)
                model_list = ', '.join(info['models'][:5]) if info['models'] \
                    else 'no models installed'
                st.write(f"- **{label}** — {model_list}")

            if 'ollama' in providers and providers['ollama']['models']:
                # Ollama with models — offer quick start
                models = providers['ollama']['models']
                st.divider()
                selected = st.selectbox(
                    "Select model", models,
                    help="Choose which model the toolkit will use for "
                         "document analysis and term generation.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Use this model", type="primary"):
                        st.session_state.wizard_choice = {
                            'provider': 'ollama',
                            'base_url': providers['ollama']['base_url'],
                            'model': selected,
                            'api_key': 'local',
                        }
                        st.session_state.wizard_step = 'test'
                        st.rerun()
                with c2:
                    if st.button("Choose different setup"):
                        st.session_state.wizard_step = 'choose'
                        st.rerun()

            elif 'ollama' in providers and not providers['ollama']['models']:
                # Ollama running but no models
                st.warning("Ollama is running but has no models installed.")
                if st.button("Download a model", type="primary"):
                    st.session_state.wizard_step = 'ollama_pull'
                    st.rerun()
                if st.button("Choose different setup"):
                    st.session_state.wizard_step = 'choose'
                    st.rerun()

            else:
                # LM Studio or other detected
                st.session_state.wizard_step = 'choose'
                st.rerun()
        else:
            # Nothing detected
            st.info("No LLM provider detected on standard ports.")
            st.session_state.wizard_step = 'choose'
            st.rerun()

    # ------------------------------------------------------------------
    # Step 2: Choose provider
    # ------------------------------------------------------------------
    elif step == 'choose':
        st.subheader("Choose LLM provider")

        provider = st.radio(
            "How would you like to connect?",
            [
                "Install Ollama (recommended — free, local, private)",
                "Enter cloud API key (OpenAI / Anthropic)",
                "Custom endpoint URL (LM Studio, vLLM, etc.)",
            ],
            help="Ollama runs models locally on your machine. "
                 "Cloud APIs require an internet connection and API key.")

        if st.button("Continue", type="primary"):
            if 'Install Ollama' in provider:
                st.session_state.wizard_step = 'ollama_install'
            elif 'cloud API' in provider:
                st.session_state.wizard_step = 'cloud'
            else:
                st.session_state.wizard_step = 'custom'
            st.rerun()

        if st.button("Re-scan for providers"):
            st.session_state.wizard_step = 'detect'
            st.rerun()

    # ------------------------------------------------------------------
    # Step 2a: Ollama install instructions
    # ------------------------------------------------------------------
    elif step == 'ollama_install':
        st.subheader("Install Ollama")

        system = platform.system()
        if system == 'Darwin':
            st.markdown("""
**macOS** — Install with Homebrew:
```bash
brew install ollama
ollama serve
```
Or download from [ollama.com](https://ollama.com/download)
""")
        elif system == 'Linux':
            st.markdown("""
**Linux** — One-line install:
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```
""")
        else:
            st.markdown("""
**Windows** — Download the installer from [ollama.com](https://ollama.com/download)
""")

        st.info("After installing, start Ollama and click the button below.")

        if st.button("I've installed Ollama — scan again", type="primary"):
            st.session_state.wizard_step = 'detect'
            st.rerun()

        if st.button("Back"):
            st.session_state.wizard_step = 'choose'
            st.rerun()

    # ------------------------------------------------------------------
    # Step 2b: Ollama model pull
    # ------------------------------------------------------------------
    elif step == 'ollama_pull':
        st.subheader("Download a model")
        providers = st.session_state.wizard_providers

        api_root = providers.get('ollama', {}).get('api_root',
                                                    'http://localhost:11434')
        base_url = providers.get('ollama', {}).get('base_url',
                                                    'http://localhost:11434/v1')

        st.caption("Choose a model to download. Larger models produce "
                   "better results but need more RAM.")

        options = [f"{name}  ({desc})" for name, desc in RECOMMENDED_MODELS]
        options.append("Other (enter model name)")
        choice = st.radio("Model", options)

        custom_model = ""
        if 'Other' in choice:
            custom_model = st.text_input(
                "Model name",
                placeholder="e.g. mistral:7b, gemma2:9b",
                help="Any model name from the Ollama library "
                     "(ollama.com/library).")

        if st.button("Download", type="primary"):
            if 'Other' in choice:
                model_name = custom_model.strip()
            else:
                model_name = choice.split('(')[0].strip()

            if not model_name:
                st.error("Enter a model name.")
            else:
                success = pull_ollama_model(api_root, model_name)
                if success:
                    st.session_state.wizard_choice = {
                        'provider': 'ollama',
                        'base_url': base_url,
                        'model': model_name,
                        'api_key': 'local',
                    }
                    st.session_state.wizard_step = 'test'
                    st.rerun()

        if st.button("Back"):
            st.session_state.wizard_step = 'choose'
            st.rerun()

    # ------------------------------------------------------------------
    # Step 2c: Cloud API
    # ------------------------------------------------------------------
    elif step == 'cloud':
        st.subheader("Cloud API Configuration")

        cloud_provider = st.radio(
            "Provider",
            ["OpenAI", "Anthropic", "Other"],
            help="Select your cloud LLM provider.")

        defaults = {
            'OpenAI': ('https://api.openai.com/v1', 'gpt-4o'),
            'Anthropic': ('https://api.anthropic.com/v1', 'claude-sonnet-4-6'),
            'Other': ('', ''),
        }
        default_url, default_model = defaults[cloud_provider]

        base_url = st.text_input(
            "API base URL", value=default_url,
            help="The base URL for the OpenAI-compatible API endpoint.")
        model = st.text_input(
            "Model", value=default_model,
            help="Model identifier (e.g. gpt-4o, claude-sonnet-4-6).")
        api_key = st.text_input(
            "API key", type="password",
            help="Your API key. Stored locally in config.yaml only.")

        if st.button("Test connection", type="primary"):
            if not api_key:
                st.error("Enter an API key.")
            else:
                st.session_state.wizard_choice = {
                    'provider': 'cloud',
                    'base_url': base_url,
                    'model': model,
                    'api_key': api_key,
                }
                st.session_state.wizard_step = 'test'
                st.rerun()

        if st.button("Back"):
            st.session_state.wizard_step = 'choose'
            st.rerun()

    # ------------------------------------------------------------------
    # Step 2d: Custom endpoint
    # ------------------------------------------------------------------
    elif step == 'custom':
        st.subheader("Custom Endpoint")

        base_url = st.text_input(
            "Endpoint URL",
            placeholder="http://localhost:1234/v1",
            help="Any OpenAI-compatible API endpoint.")

        # Try to auto-detect models
        models = []
        if base_url:
            result = _probe_openai_compat(base_url)
            if result and result['models']:
                models = result['models']
                st.success(f"Detected {len(models)} model(s)")

        if models:
            model = st.selectbox("Model", models)
        else:
            model = st.text_input(
                "Model name",
                help="The model identifier to use.")

        api_key = st.text_input(
            "API key (optional)", type="password",
            help="Leave blank if the endpoint doesn't require authentication.")

        if st.button("Test connection", type="primary"):
            if not base_url or not model:
                st.error("Enter an endpoint URL and model name.")
            else:
                st.session_state.wizard_choice = {
                    'provider': 'custom',
                    'base_url': base_url,
                    'model': model,
                    'api_key': api_key or 'local',
                }
                st.session_state.wizard_step = 'test'
                st.rerun()

        if st.button("Back"):
            st.session_state.wizard_step = 'choose'
            st.rerun()

    # ------------------------------------------------------------------
    # Step 3: Test connection
    # ------------------------------------------------------------------
    elif step == 'test':
        st.subheader("Testing connection")
        choice = st.session_state.wizard_choice

        with st.spinner("Sending test prompt..."):
            result = test_llm_connection(
                choice['base_url'], choice['model'], choice['api_key'])

        if result['ok']:
            st.success(f"Connection successful ({result['ms']}ms)")
            st.write(f"**Provider**: {choice['provider']}")
            st.write(f"**Model**: {choice['model']}")
            st.write(f"**Response**: \"{result['response']}\"")

            if st.button("Save and start using the toolkit", type="primary"):
                _save_wizard_config(choice)
                # Clear wizard state
                for key in list(st.session_state.keys()):
                    if key.startswith('wizard_'):
                        del st.session_state[key]
                st.rerun()
        else:
            st.error(f"Connection failed: {result['error']}")
            st.write(f"**Endpoint**: {choice['base_url']}")
            st.write(f"**Model**: {choice['model']}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Retry", type="primary"):
                    st.rerun()
            with c2:
                if st.button("Back to setup"):
                    st.session_state.wizard_step = 'choose'
                    st.rerun()

    return False


def _save_wizard_config(choice: dict):
    """Save wizard selections to config.yaml."""
    cfg = load_config()
    cfg['llm']['base_url'] = choice['base_url']
    cfg['llm']['model'] = choice['model']
    cfg['llm']['api_key'] = choice['api_key']
    cfg['setup_complete'] = True
    save_config(cfg)

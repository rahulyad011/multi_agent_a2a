# Simple OCI GenAI Setup

## Quick Setup

### 1. Set Environment Variables

Create a `.env` file or export these variables:

```bash
# OCI GenAI Configuration (required)
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..your_compartment_id
OCI_GENAI_ENDPOINT=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com

# Optional: Model ID (defaults to cohere.command-r-plus)
OCI_MODEL_ID=cohere.command-r-plus

# Optional: Max tokens (defaults to 2000)
OCI_MAX_TOKENS=2000
```

### 2. Ensure OCI Config File Exists

```bash
# If not already done
oci setup config
```

This creates `~/.oci/config` with your OCI credentials.

### 3. Run the Orchestrator

```bash
uv run src/agents/orchestrator/main_host.py
```

The orchestrator will automatically detect OCI environment variables and use OCI GenAI!

## Available Models

- `cohere.command-r-plus` (recommended, default)
- `cohere.command-r`
- `meta.llama-3.1-405b-instruct`
- `meta.llama-3.1-70b-instruct`
- `mistral.mistral-large`

## Example .env File

```bash
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..aaaaaaaaxxxxx
OCI_GENAI_ENDPOINT=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com
OCI_MODEL_ID=cohere.command-r-plus
OCI_MAX_TOKENS=2000
```

## Getting Your Compartment ID

```bash
oci iam compartment list --all
```

## How It Works

The code uses your existing `configure_llm_chat` function pattern from `src/utils/oci_llm.py`. When OCI environment variables are detected, it automatically:

1. Loads OCI config from `~/.oci/config`
2. Creates `ChatOCIGenAI` instance using your pattern
3. Uses it instead of LiteLLM

No code changes needed - just set the environment variables!


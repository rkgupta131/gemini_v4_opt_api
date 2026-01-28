# router/uncertainty_gate.py

def UG_check(output: str) -> bool:
    """
    Very simple uncertainty gate:
    - fails if output is empty or extremely short
    - you can extend to logprobs, semantic checks, etc.
    """
    if not output:
        return False

    if len(output.strip()) < 10:
        return False

    return True
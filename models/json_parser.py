"""
Improved JSON parser with error recovery and common JSON fixes.

Handles common JSON errors that LLMs sometimes produce.
"""

import json
import re
from typing import Optional


def fix_common_json_errors(json_str: str) -> str:
    """
    Attempts to fix common JSON errors that LLMs sometimes produce.
    
    Fixes:
    - Trailing commas in objects and arrays
    - Unescaped quotes in strings (limited)
    - Comments (removes them)
    - Items appearing after array/list closures (moves them inside)
    - Structural issues with nested arrays/objects
    """
    fixed = json_str
    
    # Remove single-line comments (// ...)
    fixed = re.sub(r'//.*?$', '', fixed, flags=re.MULTILINE)
    
    # Remove multi-line comments (/* ... */)
    fixed = re.sub(r'/\*.*?\*/', '', fixed, flags=re.DOTALL)
    
    # Fix trailing commas before closing brackets/braces
    # This is tricky - we need to be careful not to break valid JSON
    # Pattern: ,\s*([}\]])
    fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
    
    # Fix items appearing after array closure: ]\s*,\s*"string" -> move inside array
    # Pattern: ]\s*,\s*(".*?")\s*,
    # This handles cases like: [ "item1" ], "item2" -> [ "item1", "item2" ]
    def fix_array_items_after_closure(match):
        array_end = match.group(1)  # The ]
        items = match.group(2)  # The items after
        return array_end[:-1] + ', ' + items + array_end[-1]
    
    # More aggressive: find patterns like ]\s*,\s*"string" and move them inside
    # We'll do this by finding closing brackets followed by comma and string items
    pattern = r'(\]\s*),\s*(".*?")\s*,'
    while re.search(pattern, fixed):
        fixed = re.sub(pattern, r'\1, \2,', fixed, count=1)
    
    # Fix items after array closure before object closure: ]\s*,\s*"key"\s*:\s*"value"
    # Pattern: ]\s*,\s*(".*?")\s*:\s*(".*?")\s*,
    pattern2 = r'(\]\s*),\s*(".*?")\s*:\s*(".*?")\s*,'
    while re.search(pattern2, fixed):
        fixed = re.sub(pattern2, r'\1, \2: \3,', fixed, count=1)
    
    # Fix orphaned items after array closure (items that should be in the array)
    # Pattern: ]\s*,\s*(".*?")\s*$
    # This is more complex - we need to track bracket depth
    lines = fixed.split('\n')
    result_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this line has a closing bracket followed by comma and string
        if re.search(r'\]\s*,\s*"', line):
            # Try to move the item before the closing bracket
            # Find the matching opening bracket
            bracket_match = re.search(r'(\]\s*),\s*(".*?")', line)
            if bracket_match:
                # Replace ] , "item" with , "item" ]
                line = re.sub(r'(\]\s*),\s*(".*?")', r', \2\1', line)
        result_lines.append(line)
        i += 1
    fixed = '\n'.join(result_lines)
    
    return fixed


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extracts JSON from text that might contain markdown or other content.
    
    Tries multiple strategies:
    1. Find JSON between ```json ... ``` or ``` ... ```
    2. Find JSON between first { and last }
    3. Find JSON between first [ and last ] (for array responses)
    """
    # Strategy 1: Look for code blocks
    code_block_patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
    ]
    
    for pattern in code_block_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            # Try the longest match (most likely to be complete)
            candidate = max(matches, key=len).strip()
            if candidate.startswith('{') or candidate.startswith('['):
                return candidate
    
    # Strategy 2: Find first { and last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace+1]
    
    # Strategy 3: Find first [ and last ]
    first_bracket = text.find('[')
    last_bracket = text.rfind(']')
    
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        return text[first_bracket:last_bracket+1]
    
    return None


def fix_array_structure_issues(json_str: str) -> str:
    """
    Fixes specific array structure issues where items appear after array closure.
    
    Handles cases like:
    - [ "item1" ], "item2" -> [ "item1", "item2" ]
    - [ "item1" ], "item2", "item3" -> [ "item1", "item2", "item3" ]
    
    Uses regex to find and fix patterns where items appear after closing brackets.
    """
    fixed = json_str
    
    # Pattern: closing bracket, optional whitespace, comma, whitespace, quoted string(s)
    # We want to move the items inside the array before the closing bracket
    
    # More targeted: find ] followed by comma and quoted strings that should be in the array
    # Pattern: ]\s*,\s*(".*?")(\s*,\s*".*?")*\s*,
    # This matches: ], "item1", "item2", 
    
    def fix_items_after_bracket(match):
        # Extract the items after the bracket
        items_text = match.group(1)  # Everything after ], including items
        # The items should be moved before the closing bracket
        # We need to find where the bracket is and move items there
        return ']'  # We'll handle the replacement differently
    
    # Strategy: Use a more careful regex that captures the bracket and items
    # Pattern: (\]\s*),\s*((?:"[^"]*"\s*,\s*)+)"[^"]*"
    # This matches: ], "item1", "item2"
    
    # Simpler approach: find ] followed by comma and string, replace with string before ]
    # But we need to be careful about context - only fix within object structures
    
    # Pattern to find: ]\s*,\s*"string"
    pattern = r'(\]\s*),\s*("(?:[^"\\]|\\.)*")'
    
    def move_item_inside(m):
        bracket = m.group(1)  # The ] with whitespace
        item = m.group(2)  # The quoted string
        # Move item before closing bracket
        return bracket[:-1] + ', ' + item + bracket[-1]
    
    # Apply the fix iteratively (limit iterations to avoid infinite loops)
    max_iterations = 20
    for _ in range(max_iterations):
        new_fixed = re.sub(pattern, move_item_inside, fixed)
        if new_fixed == fixed:
            break
        fixed = new_fixed
    
    # Also handle multiple items: ]\s*,\s*"item1",\s*"item2"
    # Pattern: (\]\s*),\s*("(?:[^"\\]|\\.)*")(\s*,\s*"(?:[^"\\]|\\.)*")+
    pattern2 = r'(\]\s*),\s*("(?:[^"\\]|\\.)*")((?:\s*,\s*"(?:[^"\\]|\\.)*")+)'
    
    def move_items_inside(m):
        bracket = m.group(1)
        first_item = m.group(2)
        more_items = m.group(3)
        # Move all items before closing bracket
        return bracket[:-1] + ', ' + first_item + more_items + bracket[-1]
    
    for _ in range(max_iterations):
        new_fixed = re.sub(pattern2, move_items_inside, fixed)
        if new_fixed == fixed:
            break
        fixed = new_fixed
    
    return fixed


def parse_json_with_fallback(text: str) -> Optional[dict]:
    """
    Parses JSON with multiple fallback strategies.
    
    Returns the parsed object or None if all strategies fail.
    """
    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract JSON from text
    extracted = extract_json_from_text(text)
    if extracted and extracted != text:
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Fix common errors and try again
    fixed = fix_common_json_errors(text)
    if fixed != text:
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
    
    # Strategy 4: Fix array structure issues
    fixed_array = fix_array_structure_issues(text)
    if fixed_array != text:
        try:
            return json.loads(fixed_array)
        except json.JSONDecodeError:
            pass
    
    # Strategy 5: Extract and fix common errors
    if extracted:
        fixed_extracted = fix_common_json_errors(extracted)
        if fixed_extracted != extracted:
            try:
                return json.loads(fixed_extracted)
            except json.JSONDecodeError:
                pass
    
    # Strategy 6: Extract and fix array structure
    if extracted:
        fixed_array_extracted = fix_array_structure_issues(extracted)
        if fixed_array_extracted != extracted:
            try:
                return json.loads(fixed_array_extracted)
            except json.JSONDecodeError:
                pass
    
    # Strategy 7: Try fixing extracted with both methods
    if extracted:
        fixed_both = fix_array_structure_issues(fix_common_json_errors(extracted))
        if fixed_both != extracted:
            try:
                return json.loads(fixed_both)
            except json.JSONDecodeError:
                pass
    
    return None


def get_json_error_context(json_str: str, error_pos: int, context_size: int = 100) -> str:
    """
    Gets context around a JSON error position for debugging.
    """
    start = max(0, error_pos - context_size)
    end = min(len(json_str), error_pos + context_size)
    
    context = json_str[start:end]
    
    # Calculate line and column
    line_num = json_str[:error_pos].count('\n') + 1
    col_num = error_pos - json_str.rfind('\n', 0, error_pos) - 1
    
    # Find the line with the error
    lines = json_str[:error_pos].split('\n')
    error_line = lines[-1] if lines else ''
    
    return f"Line {line_num}, Column {col_num}\nError line: {error_line}\nContext:\n{context}"



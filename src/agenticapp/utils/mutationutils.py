import difflib
import ast
import inspect

def apply_specific_mutation(source_code: str, line_number: int, mutator_type: str) -> tuple:
    """
    Applies a specific mutation to the source code at given line number.
    Returns tuple: (mutated_code, mutation_details)
    """
    lines = source_code.split('\n')
    original_line = lines[line_number - 1]
    mutated_line = original_line
    
    # Implement mutation rules based on mutator type
    if mutator_type == 'ArithmeticOperatorReplacement':
        replacements = {'+': '-', '*': '/', '-': '+', '/': '*'}
        for op, replacement in replacements.items():
            if op in original_line:
                mutated_line = original_line.replace(op, replacement)
                break
                
    elif mutator_type == 'ComparisonOperatorReplacement':
        replacements = {'>': '<', '<': '>=', '==': '!='}
        for op, replacement in replacements.items():
            if op in original_line:
                mutated_line = original_line.replace(op, replacement)
                break
                
    elif mutator_type == 'ConstantReplacement':
        if 'True' in original_line:
            mutated_line = original_line.replace('True', 'False')
        elif 'False' in original_line:
            mutated_line = original_line.replace('False', 'True')
        elif any(char.isdigit() for char in original_line):
            mutated_line = original_line.replace('0', '1').replace('1', '0')

    # Apply mutation
    lines[line_number - 1] = mutated_line
    mutated_code = '\n'.join(lines)
    
    # Generate diff
    diff = difflib.unified_diff(
        source_code.splitlines(),
        mutated_code.splitlines(),
        lineterm='',
        fromfile='original',
        tofile='mutated'
    )
    
    return mutated_code, {
        'original_line': original_line,
        'mutated_line': mutated_line,
        'diff': '\n'.join(diff),
        'line_number': line_number,
        'mutator_type': mutator_type
    }


def apply_mutation(source_code: str) -> tuple[str, str]:
    """
    Apply a simple mutation to the source code.
    Example: Replace '==' with '!=' to simulate a mutation.

    Returns:
        mutated_code (str): The mutated version of the source code.
        mutation_diff (str): Unified diff showing changes made.
    """
    mutated_code = source_code.replace("<", "<=")

    original_lines = source_code.splitlines(keepends=True)
    mutated_lines = mutated_code.splitlines(keepends=True)

    mutation_diff = ''.join(
        difflib.unified_diff(original_lines, mutated_lines, fromfile='original.py', tofile='mutated.py')
    )

    return mutated_code, mutation_diff

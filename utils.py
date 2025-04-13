def colored_text(text, color):
    colors = {
        'yellow': '\033[93m',
        'green': '\033[92m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def hugenote_prompt(message):
    prefix = colored_text("[HUGENOTE]:", "yellow")
    return input(f"{prefix} {message}\n>>> ").strip()
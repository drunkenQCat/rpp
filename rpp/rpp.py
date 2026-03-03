"""
Complete Lark-based RPP parser implementation
This replicates the functionality of the original PLY-based parser
"""

from .element import Element


class Token:
    """Simple token class"""
    def __init__(self, type_, value):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        return f'Token({self.type!r}, {self.value!r})'


def tokenize(string):
    """
    Tokenize RPP content similar to the original PLY scanner.
    This is a line-based tokenizer.
    """
    lines = string.splitlines()
    for lineno, line in enumerate(lines, start=1):
        is_first_token_in_line = True
        while line:
            line = line.strip()
            if not line:
                break
            
            # Check for quoted strings
            if line[0] in ('"', "'", '`'):
                quote = line[0]
                try:
                    quote_end = line.index(quote, 1)
                    yield Token('STRING', line[1:quote_end])
                    line = line[quote_end+1:]
                except ValueError:
                    # No closing quote, treat rest as string
                    yield Token('STRING', line[1:])
                    line = ''
            else:
                if is_first_token_in_line:
                    if line.startswith('<'):
                        yield Token('OPEN', '<')
                        line = line[1:]
                    elif line.startswith('>'):
                        yield Token('CLOSE', '>')
                        line = line[1:]
                    elif line.startswith('|'):
                        # Pipe-prefixed line, treat as string
                        yield Token('STRING', line)
                        line = ''
                
                if line:
                    # Split by whitespace
                    parts = line.split(maxsplit=1)
                    if len(parts) > 1:
                        thing, rest = parts
                    else:
                        thing, rest = parts[0], ''
                    
                    yield Token('STRING', thing)
                    line = rest
            
            is_first_token_in_line = False
        
        yield Token('NEWLINE', '\n')


def loads(string):
    """Load RPP content from string"""
    # Tokenize the input
    tokens = list(tokenize(string))
    return _parse_tokens(tokens)


def _parse_tokens(tokens):
    """Parse tokens into Element structure using recursive descent"""
    pos = [0]  # Use list for mutable reference
    
    def peek():
        if pos[0] < len(tokens):
            return tokens[pos[0]]
        return None
    
    def consume():
        token = peek()
        if token:
            pos[0] += 1
        return token
    
    def parse_tree():
        token = consume()
        if not token or token.type != 'OPEN':
            raise ValueError(f"Expected OPEN token, got {token}")
        
        # Parse tag and attributes
        tag = None
        attrib = []
        children = []
        
        while True:
            token = peek()
            if not token:
                raise ValueError("Unexpected end of input")
            
            if token.type == 'STRING':
                consume()
                if tag is None:
                    tag = token.value
                else:
                    attrib.append(token.value)
            elif token.type == 'NEWLINE':
                consume()
                # After newline, we might have children or close
                while True:
                    token = peek()
                    if not token:
                        raise ValueError("Unexpected end of input")
                    
                    if token.type == 'CLOSE':
                        break
                    elif token.type == 'OPEN':
                        # Nested tree
                        children.append(parse_tree())
                        # Consume the newline after the nested tree
                        if peek() and peek().type == 'NEWLINE':
                            consume()
                    elif token.type == 'STRING':
                        # Simple list
                        children.append(parse_simple_list())
                    else:
                        consume()
            elif token.type == 'CLOSE':
                consume()
                break
            else:
                consume()
        
        return Element(tag=tag, attrib=tuple(attrib), children=children)
    
    def parse_simple_list():
        items = []
        while True:
            token = peek()
            if not token or token.type != 'STRING':
                break
            consume()
            items.append(token.value)
        
        # Consume the trailing newline
        if peek() and peek().type == 'NEWLINE':
            consume()
        
        # If only one item, return it directly (not wrapped in a list)
        if len(items) == 1:
            return items[0]
        return items
    
    # Skip leading newlines
    while peek() and peek().type == 'NEWLINE':
        consume()
    
    return parse_tree()


def load(fp):
    """Load RPP content from file pointer"""
    return loads(fp.read())


def dumps(lists, indent=2):
    """Dump RPP content to string"""
    from .encoder import encode
    return encode(lists, indent=indent)


def dump(lists, fp, indent=2):
    """Dump RPP content to file pointer"""
    fp.write(dumps(lists, indent))
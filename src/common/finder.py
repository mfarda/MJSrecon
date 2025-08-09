from urllib.parse import urlparse



def find_urls_with_extension(urls, extension):
    """
    Returns a list of URLs that end with the given extension (case-insensitive).
    Args:
        urls (Iterable[str]): List or set of URLs.
        extension (str): Extension to match (e.g., '.js').
    Returns:
        List[str]: URLs ending with the given extension.
    """
    ext = extension.lower()
    return [url for url in urls if urlparse(url).path.lower().endswith(ext)]


def exclude_urls_with_extensions(urls, excluded_extensions=None, config=None):
    """
    Returns a list of URLs that do NOT end with any of the excluded extensions.
    Args:
        urls (Iterable[str]): List or set of URLs.
        excluded_extensions (set, optional): Set of extensions to exclude. 
                                          If None, uses config['excluded_extensions'].
        config (dict, optional): Configuration dictionary.
    Returns:
        List[str]: URLs that don't end with any excluded extension.
    """
    if excluded_extensions is None and config:
        excluded_extensions = config['excluded_extensions']
    elif excluded_extensions is None:
        excluded_extensions = set()  # Default empty set if no config provided
    
    excluded_lower = {ext.lower() for ext in excluded_extensions}
    return [url for url in urls if not any(urlparse(url).path.lower().endswith(ext) for ext in excluded_lower)]


def write_lines_to_file(path, lines):
    """
    Writes a list or set of strings to a file, one per line.
    Args:
        path (str or Path): The file path to write to.
        lines (Iterable[str]): The lines to write.
    """
    with open(path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(f"{line}\n") 
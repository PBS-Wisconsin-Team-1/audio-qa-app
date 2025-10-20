def seconds_to_mmss(seconds):
    """Convert seconds to mm:ss format"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"
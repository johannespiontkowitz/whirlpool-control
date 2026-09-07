def control_bubble_level(bubble_level, cover_closed):
    if cover_closed:
        return 0
    return bubble_level

def get_bubble_level_text(bubble_level):
    if bubble_level == 0:
        return "Off"
    elif bubble_level < 1024:
        return "Low"
    elif bubble_level < 2048:
        return "Medium"
    else:
        return "High"
def pump_should_run(current_temp, target_temp, offset = 0.5):
    return current_temp < (target_temp - offset)

def control_bubble_level(bubble_level, cover_closed):
    if cover_closed:
        return 0
    return bubble_level
def pump_should_run(current_temp, target_temp, offset = 0.5):
    return current_temp < (target_temp - offset)
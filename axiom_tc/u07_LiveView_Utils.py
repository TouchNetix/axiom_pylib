def convert_u83_measurement_noise_to_string(noise_as_float100):
    return "%.2f" % (float(noise_as_float100) / 100)

def convert_u83_channel_state_to_string(state):
    if state == 0:
        return "Scan"
    elif state == 1:
        return "Capture"
    elif state == 2:
        return "Settle"
    elif state == 3:
        return "Qualification"
    elif state == 4:
        return "Ready"
    elif state == 5:
        return "Noisy"
    elif state == 6:
        return "Inactive"
    elif state == 7:
        return "Reset"
    else:
        return "<UNKNOWN_U83_CHANNEL_STATE>"

def convert_self_test_result_to_string(result):
    if result == 0x00:
        return "Not Yet Run"
    elif result == 0x01:
        return "In Progress"
    elif result == 0x02:
        return "Pass"
    elif result == 0x03:
        return "Must Retry"
    elif result == 0x7E:
        return "Not Implemented"
    elif result == 0x7F:
        return "Never Run"
    elif (result & 0x80) != 0:
        return "Fail (Extended Error Bits: 0x%02X)" % (result & 0x7F)
    else:
        return "<UNKNOWN_SELF_TEST_RESULT>"

def convert_self_test_overall_result_to_string(overall_result):
    if overall_result == 0x01:
        return "In Progress"
    elif overall_result == 0x02:
        return "Pass"
    elif overall_result == 0x7D:
        return "No Tests Done"
    elif overall_result == 0x7F:
        return "Never Run"
    elif overall_result == 0x80:
        return "Fail"
    else:
        return "<UNKNOWN_OVERALL_RESULT>"

def convert_self_test_cause_to_string(cause):
    if cause == 0:
        return "Boot"
    elif cause == 1:
        return "Heartbeat"
    elif cause == 2:
        return "Host Triggered"
    else:
        return "<UNKNOWN_CAUSE>"

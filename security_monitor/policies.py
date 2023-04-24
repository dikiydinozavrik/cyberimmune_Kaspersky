
def check_operation(id, details):
    authorized = False
    src = details['source']
    dst = details['deliver_to']
    operation = details['operation']
    if  src == 'sensor' and dst == 'decision_server' \
        and operation == 'signal_sent':
        authorized = True   
    if src == 'decision_server' and dst == 'scada' \
        and operation == 'info_sent':
        authorized = True   
    if src == 'decision_server' and dst == 'protection_system' \
        and operation == 'alarm':
        authorized = True   
    if src == 'update_server' and dst == 'decision_server' \
        and operation == 'software_update':
        authorized = True   
    if src == 'update_checker' and dst == 'update_server' \
        and operation == 'verified_update':
        authorized = True   
    if src == 'file_server' and dst == 'update_checker' \
        and operation == 'update_file'
        authorized = True   
    if src == 'update_checker' and dst == 'storage' \
        and operation == 'verified_setiings':
        authorized = True   
    if src == 'decision_server' and dst == 'storage' \
        and operation == 'logs_writing':
        authorized = True
    if src == 'storage' and dst == 'decision_server' \
        and operation == 'settings_downloading':
        authorized = True     
     
    return authorized

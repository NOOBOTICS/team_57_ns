import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/nobel/team57/team_57_ns/three_ws/install/tortoisebot_control'

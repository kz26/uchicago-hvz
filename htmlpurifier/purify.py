import subprocess
import os
from django.conf import settings

MY_DIRPATH = os.path.dirname(os.path.realpath(__file__))
HTMLPURIFIER_SCRIPT_PATH = getattr(settings, 'HTMLPURIFIER_SCRIPT_PATH', os.path.join(MY_DIRPATH, 'htmlpurifier-cli.php'))

def purify(data):
    cl = ['php', '-f', HTMLPURIFIER_SCRIPT_PATH]
    cwd = os.path.dirname(__file__) 
    p = subprocess.Popen(cl, cwd=cwd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    out = p.communicate(data.encode('utf8'))
    return out[0]


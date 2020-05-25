import redis
from  main import process_files, setup_output
from globals import Paths
from utils import setup_dirs
from template import *

r = redis.Redis(host='redis')
file_path = r.lpop( 'queue' )
if file_path:
    file_path = file_path.decode("utf-8")
    print(file_path)
    template = Template('./inputs/Burkina/template.json')
    print(template.marker_path)

    args = {
        'noCropping': False,
        'setLayout': True,
        'autoAlign': True,
    }
    args = {
            'noCropping': True,
            'autoAlign': False,
            'setLayout': False,
            'input_dir': ['inputs'],
            'output_dir': 'outputs',
            'template': None
    }

    paths = Paths('/outputs/docker')
    setup_dirs(paths)

    process_files([file_path], template, args, setup_output(paths, template)) 


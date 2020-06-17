import redis, json
from  main import process_files, setup_output
from globals import Paths
from utils import setup_dirs
from template import *
from tempfile import TemporaryDirectory
from sys import exit
from pdf2image import convert_from_path
import os.path

dpi = 72

args = {
        'noCropping': True,
        'autoAlign': False,
        'setLayout': False,
        'input_dir': ['inputs'],
        'output_dir': 'outputs',
        'template': None
}

def processImages( files, template ):
    if template == 'default':
        template = Template('./inputs/default/template.json')
        result = process_files(files, template, args, setup_output(paths, template), unmarked_symbol='0') 
        print( result )

    file_path = file_path.decode("utf-8")
    print(file_path)
    template = Template('./inputs/Burkina/template.json')
    print(template.marker_path)

    #args = {
    #    'noCropping': False,
    #    'setLayout': True,
    #    'autoAlign': True,
    #}


    result = process_files([file_path], template, args, setup_output(paths, template), unmarked_symbol='0' if data['default'] else '') 
    print( result )

r = redis.Redis(host='redis')

data = r.lpop('queue')
if not data: exit()

data = json.loads(data)

if data['file'] and os.path.isfile(data['file']):
    paths = Paths('/outputs/docker')
    setup_dirs(paths)
    if data['file'].lower().endswith('.pdf'):
        with TemporaryDirectory() as temp_path:
            processImages( convert_from_path(
                    data['file'],
                    dpi=dpi,
                    output_folder=temp_path,
                    paths_only=True,
                    fmt='jpeg'
                ), data['template'] )
    else: data['file'] = processImages( [data['file']], data['template'])

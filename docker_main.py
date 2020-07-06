import redis, json, requests, time, sys
from  main import process_files, setup_output
from globals import Paths
from utils import setup_dirs
from template import Template
from tempfile import TemporaryDirectory, NamedTemporaryFile
from pdf2image import convert_from_path
import os.path
from io import StringIO
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.storage.queue import QueueServiceClient, QueueClient, QueueMessage, TextBase64DecodePolicy

dpi = 72

args = {
        'noCropping': True,
        'autoAlign': False,
        'setLayout': False,
        'input_dir': ['inputs'],
        'output_dir': 'outputs',
        'template': None
}


def setup_output_paths( paths ):
    paths = Paths( paths )
    setup_dirs(paths)
    return paths

def get_template_codes( files, template ):
    print('get_tempalte_code')
    if template == 'default':
        template = Template('./inputs/default/template.json')
        paths = setup_output_paths( '/output/default/' )
        results = process_files(files, template, args, setup_output(paths, template), unmarked_symbol='0') 

        codes = []
        for result in results:
            code = result['code'].lstrip('0')
            page = result['page'].lstrip('0')
            if code.isdigit() and page.isdigit():
                codes.append( (int(code, 2), int(page, 2) ) )
        return codes
    else: return [template]

def get_template( exam_code, page ):
    url = os.environ['SERVER_URL_PREFIX'] + '/exams'
    data = {
        'exam_id': exam_code,
    }
    resp = requests.post( url, json=data )
    if resp.status_code != 201:
        print('Error could not get template for exam %s, error %s' % (exam_code, resp.status_code))
        return
    return Template( json_obj=json.loads(resp.json()['data']['jsonconf'])[page-1] )

def get_candidat_id( exam_code, cnib ):
    url = os.environ['SERVER_URL_PREFIX'] + '/admin/admit/acndidate/exam/getall?'
    data = {
        'exam_id': exam_code,
    }
    resp = requests.post( url, json=data )
    if resp.status_code != 201:
        print('Error could not retrieve candidates for exam %s, error %s' % (exam_code, resp.status_code))
        return
    data = resp.json()
    for candidat in data['candidates']:
        if candidat['cnibnumber'] == 'B'+cnib:
            return candidat['id']
    print('Error could not find candidate that matches CNIB B%s for exam %s' % (cnib, exam_code))

def processImages( files, template ):
    codes = get_template_codes( files, template)
    results = []
    for exam_code, img_file in  zip(codes, files):
        #print(exam_code, img_file)
        # TODO call api with code to get json
        template = get_template( exam_code[0], exam_code[1] )
        if template:
            paths = setup_output_paths( '/outputs/%s/%s' % exam_code )
            template = template
            result = process_files([img_file], template, args, setup_output(paths, template)) 
            sendResults( exam_code[0], result[0] )
            results.append( result )
    return results

def sendResults( exam_code, results ):
    candidat_id = get_candidat_id( exam_code, results['roll'])
    if not candidat_id:
        return

    url = os.environ['SERVER_URL_PREFIX'] + '/composition/question/answered'
    data = {
        'exam_id': exam_code,
        'candidat_id': candidat_id
    }
    for q_id, answer in results.items():
        if q_id.startswith('Q'):
            data['question_id'] = q_id[1:]
            data.update( {'answer1':0, 'answer2':0, 'answer3':0, 'answer4':0} )
            if 'A' in answer or '1' in answer:
                data['answer1'] = 1
            if 'B' in answer or '2' in answer:
                data['answer2'] = 1
            if 'C' in answer or '3' in answer:
                data['answer3'] = 1
            if 'D' in answer or '4' in answer:
                data['answer4'] = 1

            # print( data )
            resp = requests.post( url, json=data )
            if resp.status_code != 201:
                print('Error writting exam resault exam_id: %s candidat_id: %s question_id %s' % (data['exam_id'], data['candidat_id'], data['question_id']))
                break
             
def process( file_path, template_name):
    print( 'Processing %s'% file_path)
    file_type = os.path.splitext( file_path )[1]
    if file_type.lower() == '.pdf':
        with TemporaryDirectory() as temp_path:
            return processImages( convert_from_path(
                file_path,
                dpi=dpi,
                output_folder=temp_path,
                paths_only=True,
                fmt='jpeg'
                ), template_name )
    elif file_type.lower() in ['.jpeg', '.jpg', '.png']:
        return processImages( [file_path], template_name)
    else:
        print( 'Error: file type \'%s\' not supported' % file_type)
def next_omr_data():
    if os.environ['OMR_QUEUE_SERVICE'].lower() == 'redis':
        r = redis.Redis(host='redis')
        data = r.lpop(os.environ['OMR_QUEUE'])
        if not data:
            return
        data = json.loads(data)
        if data and  data['file'] and os.path.isfile(data['file']):
            return process( data['file'], data['template'])

    elif os.environ['OMR_QUEUE_SERVICE'].lower() == 'azure':
        connection_string = os.environ['AZURE_STORAGE_CONNECTION_STRING']
        queue_client = QueueClient.from_connection_string(connection_string, os.environ['OMR_QUEUE'], message_decode_policy=TextBase64DecodePolicy())
        blob_service_client = BlobServiceClient.from_connection_string( connection_string )
        container_client = blob_service_client.get_container_client(os.environ['AZURE_STORAGE_CONTAINER'])
        messages = queue_client.receive_messages(visibility_timeout=30)
        results = []
        for msg in messages:
            content = json.loads(msg.content)
            data = content['data']
            print('Received %s from azure' % data['url'])
            blob_client = container_client.get_blob_client(os.path.basename(data['url']))
            with NamedTemporaryFile(suffix=os.path.splitext(data['url'])[1]) as blob_file:
                download_stream = blob_client.download_blob()
                blob_file.write( download_stream.readall() )
                results.append( process(blob_file.name, 'default') )
                queue_client.delete_message(msg)
        return results

def run( ):
    while True:
        results = next_omr_data()
        sys.stdout.flush()
        time.sleep( int(float( os.getenv('CYCLE_TIME', 15) )) )

if __name__ == '__main__':
    run()



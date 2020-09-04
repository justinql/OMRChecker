import redis, json, requests, time, sys, glob, traceback, os.path, re
from  main import process_files, setup_output
from globals import Paths
from utils import setup_dirs
from template import Template
from tempfile import TemporaryDirectory, NamedTemporaryFile
from pdf2image import convert_from_path
from io import StringIO
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.storage.queue import QueueServiceClient, QueueClient, QueueMessage, TextBase64DecodePolicy


class OMRDocker:
    OMR_QUEUE_SERVICE_OPTIONS = ('redis', 'azure')

    dpi = 72

    args = {
            'noCropping': True,
            'autoAlign': False,
            'setLayout': False,
            'input_dir': ['inputs'],
            'output_dir': 'outputs',
            'template': None
    }

    def __init__( self ):
        self.cycle_time = os.getenv('CYCLE_TIME', 15)
        self.server_url_prefix = os.environ['SERVER_URL_PREFIX']
        self.omr_queue_service = os.environ['OMR_QUEUE_SERVICE'].lower()
        self.omr_queue_name = os.environ['OMR_QUEUE']

        if self.omr_queue_service not in self.OMR_QUEUE_SERVICE_OPTIONS:
            raise Exception( 'Error OMR_QUEUE_SERVICE must be one of %s' % (self.OMR_QUEUE_SERVICE_OPTIONS,) )

        if self.omr_queue_service == 'azure':
            self.azure_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING', None)
            self.azure_input_container_name = os.getenv('AZURE_STORAGE_CONTAINER', None)
            self.azure_output_container_name = os.getenv('AZURE_OUTPUT_CONTAINER', None)

            if not self.azure_connection_string:
                raise Exception( 'Error enviroment variable AZURE_STORAGE_CONNECTION_STRING must be specified when using azure' )
            if not self.azure_input_container_name:
                raise Exception( 'Error enviroment variable AZURE_STORAGE_CONTAINER must be specified when using azure' )
            if not self.azure_output_container_name:
                raise Exception( 'Error enviroment variable AZURE_OUTPUT_CONTAINER must be specified when using azure' )
                

            self.azure_blob_service_client = BlobServiceClient.from_connection_string( self.azure_connection_string )
            self.azure_queue_client = QueueClient.from_connection_string(self.azure_connection_string, self.omr_queue_name, message_decode_policy=TextBase64DecodePolicy())

    def setup_output_paths( self, paths ):
        paths = Paths( paths )
        setup_dirs(paths)
        return paths

    def move_output_files( self, src_path, dest_path, prefix='', include_orginal=False ):
        extensions = ('*.jpg', '*.jpeg', '*.JPG', '*.JPEG')
        for ext in extensions:
            for output_file in glob.glob(os.path.join(src_path, ext)):
                print( 'Moving %s to %s' % (output_file, dest_path) )
                with open( output_file, 'rb' ) as data:
                    if self.omr_queue_service == 'azure':
                        blob_name = os.path.join( dest_path, prefix+self.basename)
                        blob_client = self.azure_blob_service_client.get_blob_client(container=self.azure_output_container_name, blob=blob_name)
                        blob_client.upload_blob( data, overwrite=True )
                        break

        if include_orginal:
            with open( self.original_file, 'rb' ) as data:
                if self.omr_queue_service == 'azure':
                    blob_name = os.path.join( dest_path, 'original_'+self.basename)
                    blob_client = self.azure_blob_service_client.get_blob_client(container=self.azure_output_container_name, blob=blob_name)
                    blob_client.upload_blob( data, overwrite=True )

    def get_template_codes( self, files, template ):
        if template == 'default':
            codes = []
            with TemporaryDirectory() as tmp_dir:
                paths = self.setup_output_paths( tmp_dir )
                with open('./template.json', 'r') as default_json_file:
                    template_json = json.load( default_json_file )
                    results = self.process_file_with_retries(files, template_json, paths, tmp_dir, unmarked_symbol='0', retries=4)

                    for result in results:
                        code = result['code'].lstrip('0')
                        page = result['page'].lstrip('0')
                        if code.isdigit() and page.isdigit():
                            codes.append( (int(code, 2), int(page, 2) ) )
                        else:
                            pass # TODO send to azure error container here
                            self.move_output_files( os.path.join(tmp_dir,'CheckedOMRs'), 'scan-errors', prefix='corrected_', include_orginal=True)
                            break
            return codes
        else: return [(template, 1)]

    def get_template( self, exam_code, page ):
        if self.use_local_template:
            with open('./blank_template.json', 'r') as f: 
                return json.load(f)[page-1]
        url = self.server_url_prefix + '/exams'
        data = {
            'exam_id': exam_code,
        }
        resp = requests.post( url, json=data )
        if resp.status_code != 201:
            print('Error could not get template for exam %s, error %s' % (exam_code, resp.status_code))
            return
        return json.loads(resp.json()['data']['jsonconf'])[page-1]

    def get_candidat_id( self, exam_code, cnib ):
        url = self.server_url_prefix + '/admin/admit/acndidate/exam/getall?'
        data = {
            'exam_id': exam_code,
        }
        resp = requests.post( url, json=data )
        if resp.status_code != 201:
            print('Error could not retrieve candidates for exam %s, error %s' % (exam_code, resp.status_code))
            return
        data = resp.json()
        for candidat in data['candidates']:
            if candidat and candidat['cnibnumber'] == 'B'+cnib:
                return candidat['id']
        print('Error could not find candidate that matches CNIB B%s for exam %s' % (cnib, exam_code))

    def send_results( self, exam_code, results, result_dir ):
        # This section of code is slow
        # Flushing output to make logs easier to follow
        sys.stdout.flush()

        candidat_id = self.get_candidat_id( exam_code, results['roll'])
        if not candidat_id:
            # TODO send to azure error container, no-user folder
            self.move_output_files( os.path.join(result_dir,'CheckedOMRs'), os.path.join('candidate-not-found', results['roll'], str(exam_code)), prefix='corrected_', include_orginal=True )
            return

        url = self.server_url_prefix + '/composition/question/answered'
        data = {
            'exam_id': exam_code,
            'candidat_id': candidat_id
        }
        if self.use_local_template:
            resp = requests.post(self.server_url_prefix + '/examquestion/exam', json={'exam_id':exam_code})
            q_data = resp.json()
            questions = q_data['data']
            question_ids = {}
            for q in questions:
                question_ids[q['order']] = str(q['question']['id'])
            new_results = {}
            print(question_ids)
            for q_id, answer in results.items():
                if q_id.startswith('Q'):
                    new_results['Q'+question_ids[ int(q_id[1:]) ]] = answer
            results = new_results
        print(results)
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
 
    def process_file_with_retries(self, files, template_json, paths, tmp_dir, unmarked_symbol='', retries=4):
        retries *= 2
        start_marker_width_ration= int(template_json['Options']['Marker']['SheetToMarkerWidthRatio'])
        marker_width_ration = start_marker_width_ration
        error = None
        for i in range(retries):
            try:
                print('marker ration', marker_width_ration)
                template_json['Options']['Marker']['SheetToMarkerWidthRatio'] = marker_width_ration
                template = Template(json_obj=template_json)
                return process_files(files, template, self.args, setup_output(paths, template), unmarked_symbol=unmarked_symbol) 
            except Exception as error:
                scale = int( (i+2)/2 )
                if i%2 == 0:
                    marker_width_ration = start_marker_width_ration + scale
                else:
                    marker_width_ration = start_marker_width_ration - scale
                pass
        if error:
            self.move_output_files( os.path.join(tmp_dir,'CheckedOMRs'), 'scan-errors', prefix='corrected_', include_orginal=True)
            raise error



    def process_images( self, files, template ):
        codes = self.get_template_codes( files, template)
        results = []
        for exam_code, img_file in  zip(codes, files):
            #print(exam_code, img_file)
            template = self.get_template( exam_code[0], exam_code[1] )
            if template:
                with TemporaryDirectory() as tmp_dir:
                    full_tmp_dir = os.path.join( tmp_dir, str(exam_code[0]), str(exam_code[1]))
                    paths = self.setup_output_paths( full_tmp_dir )
                    result = self.process_file_with_retries([img_file], template, paths, full_tmp_dir, retries=4)

                    self.send_results( exam_code[0], result[0], full_tmp_dir)
                    results.append( result )
                    self.move_output_files( os.path.join(full_tmp_dir, 'CheckedOMRs'), os.path.join( 'results', 'B'+result[0]['roll'], str(exam_code[0]),str(exam_code[1]) ), prefix='corrected_', include_orginal=True )
           # else:
           #     pass # TODO add to azure error folder
           #     self.move_output_files( os.path.join(tmp_dir,'CheckedOMRs'), 'scan-errors', prefix='corrected_', include_orginal=True)
        return results

            
    def process( self, file_path, template_name ):
        print( 'Processing %s'% file_path)
        file_type = os.path.splitext( file_path )[1]
        if file_type.lower() == '.pdf':
            with TemporaryDirectory() as temp_path:
                return self.process_images( convert_from_path(
                    file_path,
                    dpi=self.dpi,
                    output_folder=temp_path,
                    paths_only=True,
                    fmt='jpeg'
                    ), template_name )
        elif file_type.lower() in ['.jpeg', '.jpg', '.png']:
            return self.process_images( [file_path], template_name)
        else:
            print( 'Error: file type \'%s\' not supported' % file_type)

    def next_redis_data( self ):
        r = redis.Redis(host='redis')
        data = r.lpop(self.omr_queue_name)
        if not data:
            return
        data = json.loads(data)
        if data and  data['file'] and os.path.isfile(data['file']):
            self.basename = os.path.basename( data['file'] )
            self.original_file = data['file']
            return self.process( data['file'], data['template'])

    def next_azure_data( self ):
            container_client = self.azure_blob_service_client.get_container_client(self.azure_input_container_name)
            messages = self.azure_queue_client.receive_messages(visibility_timeout=120)
            results = []
            for msg in messages:
                self.use_local_template = False

                content = json.loads(msg.content)
                data = content['data']
                print('Received %s from azure' % data['url'])
                self.basename = os.path.basename(data['url'])
                
                exam = 'default'
                m = re.search("{container}/(.+)/{basename}".format(container= self.azure_input_container_name, basename=self.basename), os.path.normpath(data['url']))
                if m:
                    self.use_local_template = True
                    exam = m.group(1)

                print("Using: %s", exam)
                blob_client = container_client.get_blob_client( self.basename if exam == 'default' else os.path.join(exam, self.basename) )
                with NamedTemporaryFile(suffix=os.path.splitext(data['url'])[1]) as blob_file:
                    download_stream = blob_client.download_blob()
                    blob_file.write( download_stream.readall() )
                    self.original_file = blob_file.name
                    results.append( self.process(blob_file.name, exam) )
                    self.azure_queue_client.delete_message(msg)
            return results

    def next_omr_data( self ):
        if self.omr_queue_service == 'redis':
            return self.next_redis_data()

        elif self.omr_queue_service == 'azure':
            return self.next_azure_data()

    def run( self ):
        while True:
            try:
                results = self.next_omr_data()
            except Exception as  e:
                print(e)
                traceback.print_tb(e.__traceback__)
            finally:
                sys.stdout.flush()
                time.sleep( int(float( self.cycle_time )) )

if __name__ == '__main__':
    OMRDocker().run()

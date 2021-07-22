import redis, json, requests, time, sys, glob, traceback, os.path, re, csv, mysql.connector
from  main import process_files, setup_output
from globals import Paths
from utils import setup_dirs
from template import Template
from tempfile import TemporaryDirectory, NamedTemporaryFile
from pdf2image import convert_from_path
from io import StringIO
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.storage.queue import QueueServiceClient, QueueClient, QueueMessage, TextBase64DecodePolicy
import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import datetime


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

    csv_file = 'csv_file.csv'

    send_to_api = True

    def __init__( self ):
        self.cycle_time = os.getenv('CYCLE_TIME', 15)
        self.server_url_prefix = os.environ['SERVER_URL_PREFIX'].rstrip('/')
        self.omr_queue_service = os.environ['OMR_QUEUE_SERVICE'].lower()
        self.omr_queue_name = os.environ['OMR_QUEUE']
        self.send_to_api = os.getenv('SEND_TO_API', False)
        self.db_type = os.getenv('DB_TYPE', 'cosmodb')

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
        extensions = ('*.jpg', '*.jpeg', '*.JPG', '*.JPEG', '*.csv')
        for ext in extensions:
            for output_file in glob.glob(os.path.join(src_path, ext)):
                print( 'Moving %s to %s' % (output_file, dest_path) )
                with open( output_file, 'rb' ) as data:
                    if self.omr_queue_service == 'azure':
                        blob_name = os.path.join( dest_path, prefix+ext.replace('*', ".".join(self.basename.split('.'))))
                        blob_client = self.azure_blob_service_client.get_blob_client(container=self.azure_output_container_name, blob=blob_name)
                        blob_client.upload_blob( data, overwrite=True )
                        break

        if include_orginal:
            with open( self.original_file, 'rb' ) as data:
                if self.omr_queue_service == 'azure':
                    blob_name = os.path.join( dest_path, 'original_'+self.basename)
                    blob_client = self.azure_blob_service_client.get_blob_client(container=self.azure_output_container_name, blob=blob_name)
                    blob_client.upload_blob( data, overwrite=True )
        
    #def log_error( self, error_type, error ):
    #    if self.omr_queue_service == 'azure':
    #        blob_name = os.path.join( error_type, error_type+'.csv')
    #        error += ',' + self.basename
    #        blob_client = self.azure_blob_service_client.get_blob_client(container=self.azure_output_container_name, blob=blob_name)
    #        blob_client.append_block( error )
    #        with NamedTemporaryFile(suffix=os.path.splitext(data['url'])[1]) as blob_file:
    #            download_stream = blob_client.download_blob()
    #            blob_file.write( download_stream.readall() )

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
            if resp.status_code != 404:
                raise Exception("Error communicating with API server at %s, %s" % self.server_url_prefix, resp.status_code)
            return
        return json.loads(resp.json()['data']['jsonconf'])[page-1]

    def format_roll(self, roll):
        formated = ''
        for i in range(0, len(roll), 4):
            if i > 0:
                formated += '_'
            formated += roll[i:i+4]
        return formated

    def get_candidat_id( self, exam_code, roll ):
        url = self.server_url_prefix + '/candidat/findbycode'
        roll = str(roll)
        if len(roll) != 16:
            print('Error candidates id %s is not formated correctly' % (roll))
            return
        roll = self.format_roll( roll ) 
        data = {
                'candidatecode': roll 
        }
        resp = requests.post( url, json=data )
        if resp.status_code != 201:
            print('Error could not find candidates %s, error %s' % (roll, resp.status_code))
            if resp.status_code != 404:
                raise Exception("Error communicating with API server at %s, %s" % self.server_url_prefix, resp.status_code)
            return
        data = resp.json()
        return data['data']['id']
        #url = self.server_url_prefix + '/admin/admit/acndidate/exam/getall?'
        #data = {
        #    'exam_id': exam_code,
        #}
        #resp = requests.post( url, json=data )
        #if resp.status_code != 201:
        #    print('Error could not retrieve candidates for exam %s, error %s' % (exam_code, resp.status_code))
        #    return
        #data = resp.json()
        #for candidat in data['candidates']:
        #    if candidat and ''.join(re.findall(r'\d', candidat['candidatecode'])) == str(roll):
        #        return candidat['id']
        #print('Error could not find candidate that matches CNIB %s for exam %s' % (roll, exam_code))

    def calculate_percentage( self, results ):
        total = len( results )
        score = 0
        for r in results.values():
            score += r['points'] 
        return score/total        
            
    def calculate_specialty_percentage( self, results ):
        total = 0
        score = 0
        for r in results.values():
            if r['specialty']:
                score += r['points'] 
                total+=1
        if total >0:
            return score/total
        return 0
    
    def calculate_general_percentage( self, results ):
        total = 0
        score = 0
        for r in results.values():
            if not r['specialty']:
                score += r['points'] 
                total+=1
        if total >0:
            return score/total
        return 0
        
    def correct_all( self, results, questions ):
        total_question = len(questions)
        for q in questions:
            if q['order'] > 50 : continue
            q_id = str(q['question']['id'])
            #print(q_id)
            result = results[ q_id ]
            results[q_id]['points'] = self.correction_question(result,q['answer'])
            results[q_id]['specialty'] = 0
            if total_question == 50 and q['order'] <=30 or total_question == 60 and q['order'] <=40:
                results[q_id]['specialty'] = 1
                
        return results
    
    def correction_question( self, result, answer,value=1 ):
       #print(result['answer1'] , answer['isanser1correct'] , result['answer2'] , answer['isanser2correct'] , result['answer3'] , answer['isanser3correct'] , result['answer4'] , answer['isanser4correct'])
        if result['answer1'] == answer['isanser1correct'] and result['answer2'] == answer['isanser2correct'] and result['answer3'] == answer['isanser3correct'] and result['answer4'] == answer['isanser4correct']:
            return value
        return 0
        
    def send_results( self, exam_code, results, result_dir ):
        # This section of code is slow
        # Flushing output to make logs easier to follow
        sys.stdout.flush()

        roll = results['roll']

        #candidat_id = self.get_candidat_id( exam_code, results['roll'])
        candidat_id = 1
        if not candidat_id:
            # TODO send to azure error container, no-user folder
            self.move_output_files( os.path.join(result_dir,'CheckedOMRs'), os.path.join('candidate-not-found', results['roll'], str(exam_code)), prefix='corrected_', include_orginal=True )
            #self.log_error( 'candidate-not-found', ','.join([results['roll'], str(exam_code)]) )
            return

        url = self.server_url_prefix + '/composition/question/answered'
        data = {
            'exam_id': exam_code,
            'candidat_id': candidat_id
        }
        if self.use_local_template:
            resp = requests.post(self.server_url_prefix + '/examquestion/exam', json={'exam_id':'724'})
            #resp = requests.post(self.server_url_prefix + '/examquestion/exam', json={'exam_id':exam_code})
            q_data = resp.json()
            questions = q_data['data']
            question_ids = {}
            for q in questions:
                question_ids[q['order']] = str(q['question']['id'])
            new_results = {}
            for q_id, answer in results.items():
                if q_id.startswith('Q'):
                    new_results['Q'+question_ids[ int(q_id[1:]) ]] = answer
            results = new_results
        db_values = []
        
        #creating table to save all the answers the candidate selected      
        results_to_correct = {}
        for q_id, answer in results.items():
            data = {
              #  'exam_id': exam_code,
              #  'candidat_id': candidat_id
            }
            if q_id.startswith('Q'):
                data['question_id'] = q_id[1:]
            else: 
                data['question_id'] = q_id
            data.update( {'answer1':0, 'answer2':0, 'answer3':0, 'answer4':0} )
            if 'A' in answer or '1' in answer:
                data['answer1'] = 1
            if 'B' in answer or '2' in answer:
                data['answer2'] = 1
            if 'C' in answer or '3' in answer:
                data['answer3'] = 1
            if 'D' in answer or '4' in answer:
                data['answer4'] = 1
                    
            #sending all the answers the candidate selected        
            results_to_correct[ str(data['question_id']) ] = data
                   
            print( data )
           # if self.send_to_api:
             #   resp = requests.post( url, json=data )
            #    if resp.status_code != 201:
            #        print('Error writting exam resault exam_id: %s candidat_id: %s question_id %s' % (data['exam_id'], data['candidat_id'], data['question_id']))
            #        if resp.status_code != 404:
            #            raise Exception("Error communicating with API server at %s, %s" % self.server_url_prefix, resp.status_code)
             #       break

           # else:
           #     db_values.append((data['question_id'], data['answer1'], data['answer2'], data['answer3'], data['answer4']))
                    
        #sending the questions and results from the candidate to correct 
        candidate_result_to_save = self.correct_all(results_to_correct, questions )
        percentage = self.calculate_percentage(candidate_result_to_save) 
        specialty_percentage = self.calculate_specialty_percentage(candidate_result_to_save) 
        general_percentage = self.calculate_general_percentage(candidate_result_to_save) 
        
        
        
        if True or not self.send_to_api:
            blob_name = os.path.join( 'results', roll, exam_code, '1', 'corrected_'+self.basename+'.jpg')
            blob_client = self.azure_blob_service_client.get_blob_client(container=self.azure_output_container_name, blob=blob_name)
            dest_url = blob_client.url
            blob_name = os.path.join( exam_code, self.basename)
            blob_client = self.azure_blob_service_client.get_blob_client(container=self.azure_input_container_name, blob=blob_name)
            org_url = blob_client.url

            if self.db_type == 'mysql':
                db = mysql.connector.connect(
                    host=os.environ['DB_HOST'],
                    user=os.environ['DB_USER'],
                    password=os.environ['DB_PASSWORD'],
                    database=os.environ['DB_NAME']
                )

                cursor = db.cursor()
                query = 'insert into exam_attempts(exam_id,candidate_id,candidate_roll,org_url,dest_url) values(%s,%s,%s,%s,%s)'
                values = ( data['exam_id'], data['candidat_id'], self.format_roll(roll), org_url, dest_url )
                cursor.execute(query, values)
                db.commit()
                exam_attempt_id = cursor.lastrowid
                query = 'insert into exam_answers(exam_attempt_id,question_id,answer1,answer2,answer3,answer4) values(%s,%s,%s,%s,%s,%s)'
                values = [(exam_attempt_id,)+value for value in db_values]
                cursor.executemany(query, values)
                db.commit()
            if self.db_type == 'cosmodb':
                self.connect_azure_cosmodb()
                #Azure cosmosDB insert
                candidate_results = self.format_candidate_results(exam_code,candidat_id,self.format_roll(roll),percentage,specialty_percentage,general_percentage,candidate_result_to_save,org_url,dest_url)
                try:
                    self.container.create_item(body=candidate_results)
                except: 
                    print("Candidate ID %s already exist for exam %s" % (candidat_id, exam_code))

 
 
 
    def format_candidate_results(self,exam_id,candidate_id,candidate_roll,percentage,specialty_percentage,general_percentage,candidate_result_to_save,org_url,dest_url):
        # notice new fields have been added to the sales order
        return  {
                'id' : str(candidate_id),
                'exam_id' : exam_id,
                'candidate_id' : candidate_id,
                'candidate_roll' : candidate_roll,
                'result_percentage' : percentage,
                'specialty_percentage' : specialty_percentage,
                'general_percentage' : general_percentage,
                'result_to_save' : candidate_result_to_save,
                'org_url' : org_url,
                'dest_url' : dest_url
                }

    
        
    def connect_azure_cosmodb(self):
        host = os.environ.get('ACCOUNT_HOST', 'https://autocorrect.documents.azure.com:443/')
        master_key = os.environ.get('ACCOUNT_KEY', 'Q5dLvu05GXXjQrYbTYYwvwj76TPoxp4trbPD7TYKwGSkPHqQ2mkeECzQU5F4U8WPazYEdUdV979U7NFzmBlYJw==')
        database_id = os.environ.get('COSMOS_DATABASE', 'Autocorrect_2021')
        container_id = os.environ.get('COSMOS_CONTAINER', 'Items')

        client = cosmos_client.CosmosClient(host, {'masterKey': master_key}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
            # setup database for this sample
        try:
            db = client.create_database(id=database_id)
            print('Database with id \'{0}\' created'.format(database_id))

        except exceptions.CosmosResourceExistsError:
            db = client.get_database_client(database_id)
            print('Database with id \'{0}\' was found'.format(database_id))

        # setup container for this sample
        try:
            self.container = db.create_container(id=container_id, partition_key=PartitionKey(path='/exam_id'))
            print('Container with id \'{0}\' created'.format(container_id))

        except exceptions.CosmosResourceExistsError:
            self.container = db.get_container_client(container_id)
            print('Container with id \'{0}\' was found'.format(container_id))

 

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
                    self.move_output_files( os.path.join(full_tmp_dir, 'CheckedOMRs'), os.path.join( 'results', result[0]['roll'], str(exam_code[0]),str(exam_code[1]) ), prefix='corrected_', include_orginal=True )
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
            messages_per_cycle= int(float( os.getenv('MESSAGES_PER_CYCLE', 1) ))
            messages = self.azure_queue_client.receive_messages(visibility_timeout=messages_per_cycle*130, messages_per_page=messages_per_cycle)
            results = []
            for msg in messages:
                self.use_local_template = False

                content = json.loads(msg.content)
                data = content['data']
                print('Received %s from azure' % data['url'])
                self.basename = os.path.basename(data['url'])
                
                exam = 'default'
                m = re.search("{container}/(.+)/{basename}".format(
                    container=re.escape( self.azure_input_container_name ),
                    basename=re.escape(self.basename)
                ), os.path.normpath(data['url']))
                if m:
                    self.use_local_template = True
                    exam = m.group(1)

                print( os.path.join(exam, self.basename) )
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

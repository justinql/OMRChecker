#!python
import uuid

class TemplateGenerator:

    MULTIPLE_CHOICE = 'MC'
    INTEGER = 'INT'
    
    height = 3000
    width = 1000

    bubble_height = 50
    bubble_width = 50

    gap_width = 50;
    gap_height = 50;
    big_gap_width = 0;
    big_gap_height = 100;

    q_per_group = 5
    group_per_row = 5
    row_per_block = 3

    block_width = 500
    block_height = 500

    template = {
            'Dimensions': [width, height],
            'BubbleDimensions': [bubble_width, bubble_height],
            'Options' : {
                'Marker': {
                    'RelativePath': 'omr_marker.jpg'
                    },
                'OverrideFlags': {'noCropping':True},
                },
            'Concatenations': {},
            'Singles': [],
            'QBlocks':{},
    }
    qblock = {
            'qType' : None,
            'orig' : [],
            'gaps' : [gap_width, gap_height],
            'bigGaps' : [big_gap_width, big_gap_width],
            'qNos': [ [ [] ] ],
    }

    '''
    {
        Q1: ['A', 'B', 'C', 'D', 'E']
        Q2: {
                type: 'MC',
                length: 5
            },
        Q3: {
                type: 'INT',
                length: 100
            },
        Q4: 100

    }
    '''
    @classmethod
    def generate(cls, questions ):
        if not isinstance( questions, dict):
            raise Exception('Question not of type dict')

        template = cls.template
        qblock = cls.qblock
        qblock['orig'] = [100, 100]
        for q, value in questions.items():
            if isinstance( value, str ):
                value = { 'type' : value }
            elif isinstance( value, int ):
                value = { 
                        'type' : cls.INTEGER,
                        'length' : value,
                        }

            if isinstance( value, dict ) and 'type' in value:
                if value['type'] == cls.MULTIPLE_CHOICE:
                    template['Singles'].append( q )
                    qblock['qType'] = 'QTYPE_MC%d%s' % (value.get('length', 4), value.get('orientation', 'H') )
                    qblock['qNos'][-1][-1].append( q )
                elif value['type'] == cls.INTEGER:
                    max_value = value.get( 'length', value.get( 'max', 9 ) )
                    digits = len( str( max_value ) )
                    if digits == 1:
                        template['Singles'].append( q )
                    else:
                        concat = []
                        for i in range( digits ):
                            concat.append( '%s_%d' % (q, i) )
                        template['Concatenations'][q] = concat
                    qblock['qType'] = 'QTYPE_MC%d%s' % (value.get('length', 4), value.get('orientation', 'H') )
                    qblock['qNos'][-1][-1].append( q )


            if len( qblock['qNos'][-1][-1] ) == cls.q_per_group:
                if len( qblock['qNos'][-1] ) == cls.group_per_row:
                    if len( qblock ) == cls.row_per_block:
                        template['QBlocks'][uuid.uuid4()] = qblock
                        new_qblock = cls.qblock
                        new_qblock['qType'] = qblock['qType']
                        new_qblock['orig'] = [
                                qblock['orig'][0] + cls.block_width,
                                qblock['orig'][1] + cls.block_height
                        ]
                        qblock = new_qblock
                    qblock['qNos'].append([])
                qblock['qNos'][-1].append([])

        if not( len( qblock['qNos'][-1][-1] ) ):
            del qblock['qNos'][-1][-1]
        template['QBlocks'][uuid.uuid4()] = qblock
        return template


if __name__ == "__main__":
    from pprint import pprint
    questions = {
        'Q1': {
                'type': 'MC',
                'length': 5,
            },
        'Q2': {
                'type': 'MC',
                'length': 5,
            },
        'Q3': {
                'type': 'MC',
                'length': 5,
            },
        'Q4': {
                'type': 'MC',
                'length': 5,
            },
        'Q5': {
                'type': 'MC',
                'length': 5,
            },
        'Q6': {
                'type': 'MC',
                'length': 5,
            },
        'Q7': {
                'type': 'MC',
                'length': 5,
            },
        'Q8': {
                'type': 'MC',
                'length': 5,
            },
        'Q9': {
                'type': 'MC',
                'length': 5,
            },
        'Q10': {
                'type': 'MC',
                'length': 5,
            },
        'Q11': {
                'type': 'INT',
                'length': 50,
            },
        }
    pprint( TemplateGenerator.generate( questions) )

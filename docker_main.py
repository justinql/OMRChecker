import redis, json
from  main import process_files, setup_output
from globals import Paths
from utils import setup_dirs
from template import *
from tempfile import TemporaryDirectory, SpooledTemporaryFile
from sys import exit
from pdf2image import convert_from_path
import os.path
from io import StringIO
import requests

dpi = 72

args = {
        'noCropping': True,
        'autoAlign': False,
        'setLayout': False,
        'input_dir': ['inputs'],
        'output_dir': 'outputs',
        'template': None
}

template_3 =    {
        "Dimensions": [
            550,
            730
            ],
        "BubbleDimensions": [
            10,
            10
            ],
        "Options": {
            "OverrideFlags": {
                "noCropping": True
                },
            "Marker": {
                "RelativePath": "omr_marker.jpg",
                "SheetToMarkerWidthRatio": 40.8
                }
            },
        "Concatenations": {
            "roll": [
                "roll_0",
                "roll_1",
                "roll_2",
                "roll_3",
                "roll_4",
                "roll_5",
                "roll_6",
                "roll_7",
                "roll_8"
                ]
            },
        "Singles": [
            "Q127",
            "Q128",
            "Q129",
            "Q130",
            "Q131",
            "Q132",
            "Q133",
            "Q134",
            "Q135",
            "Q136",
            "Q137",
            "Q138",
            "Q139",
            "Q140",
            "Q141",
            "Q142",
            "Q143",
            "Q144",
            "Q145",
            "Q146",
            "Q147",
            "Q148",
            "Q149",
            "Q150",
            "Q151",
            "Q152",
            "Q153",
            "Q154",
            "Q155",
            "Q156",
            "Q157",
            "Q158",
            "Q159",
            "Q160",
            "Q161",
            "Q162",
            "Q163",
            "Q164",
            "Q165",
            "Q166",
            "Q253",
            "Q254",
            "Q255",
            "Q256",
            "Q257",
            "Q258",
            "Q259",
            "Q260",
            "Q261",
            "Q262",
        "Q263",
            "Q264",
            "Q265",
            "Q266",
            "Q267",
            "Q268",
            "Q269",
            "Q270",
            "Q271",
            "Q272"
        ],
        "QBlocks": {
                "roll_0": {
                    "qType": "QTYPE_ROLL",
                    "orig": [
                        74,
                        101
                        ],
                    "gaps": [
                        15,
                        15
                        ],
                    "bigGaps": [
                        0,
                        0
                        ],
                    "qNos": [
                        [
                            [
                                "roll_0"
                                ]
                            ]
                        ]
                    },
                "roll_1": {
                    "qType": "QTYPE_ROLL",
                    "orig": [
                        89,
                        101
                        ],
                    "gaps": [
                        15,
                        15
                        ],
                    "bigGaps": [
                        0,
                        0
                        ],
                    "qNos": [
                        [
                            [
                                "roll_1"
                                ]
                            ]
                        ]
                    },
                "roll_2": {
                    "qType": "QTYPE_ROLL",
                    "orig": [
                        104,
                        101
                        ],
                    "gaps": [
                        15,
                        15
                        ],
                    "bigGaps": [
                        0,
                        0
                        ],
                    "qNos": [
                        [
                            [
                                "roll_2"
                                ]
                            ]
                        ]
                    },
                "roll_3": {
                        "qType": "QTYPE_ROLL",
                        "orig": [
                            119,
                            101
                            ],
                        "gaps": [
                            15,
                            15
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "roll_3"
                                    ]
                                ]
                            ]
                        },
                "roll_4": {
                        "qType": "QTYPE_ROLL",
                        "orig": [
                            134,
                            101
                            ],
                        "gaps": [
                            15,
                            15
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "roll_4"
                                    ]
                                ]
                            ]
                        },
                "roll_5": {
                        "qType": "QTYPE_ROLL",
                        "orig": [
                            149,
                            101
                            ],
                        "gaps": [
                            15,
                            15
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "roll_5"
                                    ]
                                ]
                            ]
                        },
                "roll_6": {
                        "qType": "QTYPE_ROLL",
                        "orig": [
                            164,
                            101
                            ],
                        "gaps": [
                            15,
                            15
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "roll_6"
                                    ]
                                ]
                            ]
                        },
                "roll_7": {
                        "qType": "QTYPE_ROLL",
                        "orig": [
                            179,
                            101
                            ],
                        "gaps": [
                            15,
                            15
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "roll_7"
                                    ]
                                ]
                            ]
                        },
                "roll_8": {
                        "qType": "QTYPE_ROLL",
                        "orig": [
                            194,
                            101
                            ],
                        "gaps": [
                            15,
                            15
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "roll_8"
                                    ]
                                ]
                            ]
                        },
                "Q127": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            288
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q127"
                                    ]
                                ]
                            ]
                        },
                "Q128": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            305
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q128"
                                    ]
                                ]
                            ]
                        },
                "Q129": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            322
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q129"
                                    ]
                                ]
                            ]
                        },
                "Q130": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            339
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q130"
                                    ]
                                ]
                            ]
                        },
                "Q131": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            356
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q131"
                                    ]
                                ]
                            ]
                        },
                "Q132": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            373
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q132"
                                    ]
                                ]
                            ]
                        },
                "Q133": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            390
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q133"
                                    ]
                                ]
                            ]
                        },
                "Q134": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            407
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q134"
                                    ]
                                ]
                            ]
                        },
                "Q135": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            424
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q135"
                                    ]
                                ]
                            ]
                        },
                "Q136": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            441
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q136"
                                    ]
                                ]
                            ]
                        },
                "Q137": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            458
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q137"
                                    ]
                                ]
                            ]
                        },
                "Q138": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            475
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q138"
                                    ]
                                ]
                            ]
                        },
                "Q139": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            492
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q139"
                                    ]
                                ]
                            ]
                        },
                "Q140": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            509
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q140"
                                    ]
                                ]
                            ]
                        },
                "Q141": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            526
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q141"
                                    ]
                                ]
                            ]
                        },
                "Q142": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            543
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q142"
                                    ]
                                ]
                            ]
                        },
                "Q143": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            560
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q143"
                                    ]
                                ]
                            ]
                        },
                "Q144": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            577
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q144"
                                    ]
                                ]
                            ]
                        },
                "Q145": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            594
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q145"
                                    ]
                                ]
                            ]
                        },
                "Q146": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            611
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q146"
                                    ]
                                ]
                            ]
                        },
                "Q147": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            628
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q147"
                                    ]
                                ]
                            ]
                        },
                "Q148": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            645
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q148"
                                    ]
                                ]
                            ]
                        },
                "Q149": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            87,
                            662
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q149"
                                    ]
                                ]
                            ]
                        },
                "Q150": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            288
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q150"
                                    ]
                                ]
                            ]
                        },
                "Q151": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            305
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q151"
                                    ]
                                ]
                            ]
                        },
                "Q152": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            322
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q152"
                                    ]
                                ]
                            ]
                        },
                "Q153": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            339
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q153"
                                    ]
                                ]
                            ]
                        },
                "Q154": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            356
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q154"
                                    ]
                                ]
                            ]
                        },
                "Q155": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            373
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q155"
                                    ]
                                ]
                            ]
                        },
                "Q156": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            390
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q156"
                                    ]
                                ]
                            ]
                        },
                "Q157": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            407
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q157"
                                    ]
                                ]
                            ]
                        },
                "Q158": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            424
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q158"
                                    ]
                                ]
                            ]
                        },
                "Q159": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            441
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q159"
                                    ]
                                ]
                            ]
                        },
                "Q160": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            458
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q160"
                                    ]
                                ]
                            ]
                        },
                "Q161": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            475
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q161"
                                    ]
                                ]
                            ]
                        },
                "Q162": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            492
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q162"
                                    ]
                                ]
                            ]
                        },
                "Q163": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            509
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q163"
                                    ]
                                ]
                            ]
                        },
                "Q164": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            526
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q164"
                                    ]
                                ]
                            ]
                        },
                "Q165": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            543
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q165"
                                    ]
                                ]
                            ]
                        },
                "Q166": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            560
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q166"
                                    ]
                                ]
                            ]
                        },
                "Q253": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            577
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q253"
                                    ]
                                ]
                            ]
                        },
                "Q254": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            594
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q254"
                                    ]
                                ]
                            ]
                        },
                "Q255": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            611
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q255"
                                    ]
                                ]
                            ]
                        },
                "Q256": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            628
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q256"
                                    ]
                                ]
                            ]
                        },
                "Q257": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            645
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q257"
                                    ]
                                ]
                            ]
                        },
                "Q258": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            243,
                            662
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q258"
                                    ]
                                ]
                            ]
                        },
                "Q259": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            288
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q259"
                                    ]
                                ]
                            ]
                        },
                "Q260": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            305
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q260"
                                    ]
                                ]
                            ]
                        },
                "Q261": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            322
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q261"
                                    ]
                                ]
                            ]
                        },
                "Q262": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            339
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q262"
                                    ]
                                ]
                            ]
                        },
                "Q263": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            356
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q263"
                                    ]
                                ]
                            ]
                        },
                "Q264": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            373
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q264"
                                    ]
                                ]
                            ]
                        },
                "Q265": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            390
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q265"
                                    ]
                                ]
                            ]
                        },
                "Q266": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            407
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q266"
                                    ]
                                ]
                            ]
                        },
                "Q267": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            424
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q267"
                                    ]
                                ]
                            ]
                        },
                "Q268": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            441
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q268"
                                    ]
                                ]
                            ]
                        },
                "Q269": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            458
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q269"
                                    ]
                                ]
                            ]
                        },
                "Q270": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            475
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q270"
                                    ]
                                ]
                            ]
                        },
                "Q271": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            492
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q271"
                                    ]
                                ]
                            ]
                        },
                "Q272": {
                        "qType": "QTYPE_MCQ4",
                        "orig": [
                            399,
                            509
                            ],
                        "gaps": [
                            17,
                            17
                            ],
                        "bigGaps": [
                            0,
                            0
                            ],
                        "qNos": [
                            [
                                [
                                    "Q272"
                                    ]
                                ]
                            ]
                        }
                }
    }


def setup_output_paths( paths ):
    paths = Paths( paths )
    setup_dirs(paths)
    return paths

def get_template_codes( files, template ):
    if template == 'default':
        template = Template('./inputs/default/template.json')
        paths = setup_output_paths( '/output/default/' )
        results = process_files(files, template, args, setup_output(paths, template), unmarked_symbol='0') 

        codes = []
        for result in results:
            codes.append( (int(result['code'].lstrip('0'), 2), int(result['page'].lstrip('0'), 2) ) )
        return codes
    else: return [template]


def processImages( files, template ):
    codes = get_template_codes( files, template)
    for exam_code, img_file in  zip(codes, files):
        print(exam_code, img_file)
        # TODO call api with code to get json
        paths = setup_output_paths( '/outputs/%s/%s' % exam_code )
        template = Template( json_obj=template_3 )
        results = process_files([img_file], template, args, setup_output(paths, template)) 
        sendResults( exam_code[0], results[0] )

def sendResults( exam_code, results ):
    url = os.environ['SERVER_URL_PREFIX'] + '/composition/question/answered'
    data = {
        'exam_id': exam_code,
        'candidat_id': 396#results['roll']
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

            #print( data )
            resp = requests.post( url, json=data )
            print( resp)

def next_omr_data():
    r = redis.Redis(host='redis')
    data = r.lpop('queue')
    if not data:
        return
    return json.loads(data)

def process( ):
    data = next_omr_data()
    if data and  data['file'] and os.path.isfile(data['file']):
        if data['file'].lower().endswith('.pdf'):
            with TemporaryDirectory() as temp_path:
                return processImages( convert_from_path(
                    data['file'],
                    dpi=dpi,
                    output_folder=temp_path,
                    paths_only=True,
                    fmt='jpeg'
                    ), data['template'] )
        else: return processImages( [data['file']], data['template'])

if __name__ == '__main__':
    process()



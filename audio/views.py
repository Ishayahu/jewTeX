from django.shortcuts import render
from urllib.request import urlopen
import boto3
from boto3.s3.transfer import TransferConfig
import keyring
from django.http import JsonResponse, HttpResponse
import json

MB = 1024*1024
BUCKET = 'jaudio'
KEY = ';o3faje;oajfo3fj;oifjw3ajsf;oj;aews'
LOGIN = 'YCAJEU_5qQfMclLxzquja0v9J'
PASSWORD = 'YCN0rvD8b6kjPpPVSPCX7mqnnhABs9o1pi53iNOn'


def get_s3():
    # password = keyring.get_password('yandexs3', LOGIN)
    # password = 'YCN0rvD8b6kjPpPVSPCX7mqnnhABs9o1pi53iNOn'

    s3 = boto3.resource(service_name='s3', endpoint_url='https://storage.yandexcloud.net',
                        region_name='ru-central1',
                        aws_access_key_id=LOGIN,
                        aws_secret_access_key=PASSWORD
                        )

    config = TransferConfig(multipart_threshold=200 * MB, max_concurrency=1,
                            multipart_chunksize=200 * MB, use_threads=True)

    # s3.meta.client.upload_file(Bucket=BUCKET, Key=remote_backup_name, Filename=backup_full_filename,
    #                            Config=config)
    return s3, config


def chek_key(key, func):
    if key != KEY:
        def _decorator(*args, **kwargs):
            return JsonResponse({'result': 'error', 'value': 'Key not correct'})
    else:
        def _decorator(*args, **kwargs):
            func(*args, **kwargs)
    return _decorator


def list(request):
    def parse_objects(objects, obj_dict={}, level=0):
        if level > 2:
            # finalyse recursion
            for obj in objects:
                obj_elements = obj.split('.')
                obj_dict[obj_elements[0]][obj_elements[1]][obj_elements[2]].append(obj)
            return obj_dict

        else:
            for obj in objects:
                obj_elements = obj.split('.')
                match level:
                    case 0:
                        obj_dict[obj_elements[0]] = {}
                    case 1:
                        obj_dict[obj_elements[0]][obj_elements[1]] = {}
                    case 2:
                        obj_dict[obj_elements[0]][obj_elements[1]][obj_elements[2]] = []
            return parse_objects(objects, obj_dict, level+1)

    s3, config = get_s3()
    response = s3.meta.client.list_objects_v2(Bucket=BUCKET)
    obj_response = response['Contents']
    objects = []
    for obj in obj_response:
        objects.append(obj['Key'])
    # json_response = json.loads(response['Contents'])
    # objects = response['Contents']
    objects_dict = parse_objects(objects)
    import pprint
    pprint.pprint(objects_dict)
    return render(request, 'audio/list.html', {
        'jsonObjects': json.dumps(objects_dict)
    })

    # return JsonResponse({'result': 'ok', 'objects': json_response})


def get_toc(response, name):
    import os
    from jewTeX.settings import BASE_DIR
    # print(os.path.join(BASE_DIR, fr'toc\{name}'))
    with open(os.path.join(BASE_DIR, fr'toc/{name}'), 'r', encoding='utf8') as f:
        lines = f.readlines()
    result = {}
    for line in lines:
        datas = line.split('\t')
        print(datas)
        result[datas[0]] = datas[1]
    return JsonResponse(result)

def get(response, name):
    from boto3 import session
    session = session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        region_name='ru-central1',
        aws_access_key_id=LOGIN,
        aws_secret_access_key=PASSWORD
    )

    get_object_response = s3.get_object(Bucket=BUCKET, Key=name)

    body = get_object_response['Body']
    raw_stream = body._raw_stream
    d = raw_stream.data

    response = HttpResponse(d, content_type='audio/opus')
    response['Content-Disposition'] = 'attachment; filename="foo.opus"'
    response['accept-ranges'] = 'bytes'
    # response['content-type'] = 'bytes'
    response['Content-Length'] = len(d)
    response['Content-Range'] = f'bytes 0-{len(d)}/{len(d)}'
    return response
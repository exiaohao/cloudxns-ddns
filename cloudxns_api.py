import functools
import hashlib
import json
import logging
import requests
import time

logger = logging.Logger(__name__)

GET = 'get'
POST = 'post'
PUT = 'put'
DELETE = 'delete'
__API_PATH__ = 'https://www.cloudxns.net/api2'


class DomainService:
    LIST = 'domain_list'
    RECORD = 'domain_record'


class MethodNotAllowed(Exception):
    pass


class CloudXNS:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key

    def _request_header(self, request_url, request_body):
        """
        产生请求头
        :param request_url:
        :param request_body:
        :return: http request header
        """
        if isinstance(request_body, dict):
            request_params = '?' + '&'.join(['{k}={v}'.format(k=k, v=v) for k, v in request_body.items()])
        elif request_body is None:
            request_params = ''
        else:
            request_params = request_body

        api_request_date = time.strftime('%a %b %d %H:%M:%S %Y', time.localtime())
        api_hmac_origin = self.api_key + request_url + request_params + api_request_date + self.secret_key
        api_hmac = hashlib.md5(api_hmac_origin.encode()).hexdigest()
        return {
            'Content-Type': 'application/json',
            'user-agent': 'CloudXNS-Python/v3',
            'API-KEY': self.api_key,
            'API-REQUEST-DATE': api_request_date,
            'API-HMAC': api_hmac,
            'API-FORMAT': 'json',
        }

    def request_ctx(func):
        """
        请求前加headers,后转json
        :return:
        """
        @functools.wraps(func)
        def wrapper(self, request_url, request_body, disable_fmt=False, *args, **kwargs):
            headers = self._request_header(request_url, request_body)
            http_status, result = func(self, headers, request_url, request_body, *args, **kwargs)
            if disable_fmt:
                return result

            try:
                result = json.loads(result)
            except Exception as ex:
                logger.exception(ex)
                return {
                    'code': -1,
                    'http_status': http_status,
                    'message': result,
                }
            if result['code'] != 1:
                return {
                    'code': -1,
                    'http_status': http_status,
                    'message': result['message'],
                }
            return result['data']

        return wrapper

    @request_ctx
    def _request_api(self, headers, request_url, request_body, method=GET):
        print(headers, request_url, request_body, method)
        """
        请求CloudXNS API
        :param headers:
        :param request_url:
        :param request_body:
        :param method:
        :return:
        """
        try:
            if method == POST:
                result = requests.post(
                    url=request_url,
                    data=request_body,
                    headers=headers,
                )
            elif method == GET:
                result = requests.get(
                    url=request_url,
                    params=request_body,
                    headers=headers,
                )
            elif method == PUT:
                result = requests.put(
                    url=request_url,
                    data=request_body,
                    headers=headers,
                )
            elif method == DELETE:
                result = requests.delete(
                    url=request_url,
                    headers=headers,
                )
            else:
                return {}
        except Exception as ex:
            logger.exception(ex)
            return {}

        return result.status_code, result.content.decode('utf-8')

    def domain_list(self):
        """
        获取域名列表
        :return:
        """
        return self._request_api(
            request_url= __API_PATH__ + '/domain',
            request_body='',
        )
    
    def record_list(self, domain_id):
        """
        获取解析记录
        """
        return self._request_api(
            request_url= '{}/{}/{}'.format(__API_PATH__, 'record', domain_id),
            request_body={
                'host_id': 0,
                'offset': 0,
                'row_num': 1000,
            }
        )


    def update_record(self, domain_id, record_id, host, value, ttl=60):
        """
        更新记录
        """
        return self._request_api(
            request_url= '{}/{}/{}'.format(__API_PATH__, 'record', record_id),
            request_body={
                'domain_id': domain_id,
                'host': host,
                'value': value,
            },
            method=PUT,
        )

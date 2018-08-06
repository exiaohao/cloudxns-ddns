import etcd
import hug
import yaml

from cloudxns_api import (
    CloudXNS,
    DomainService,
)
from etcd import (
    EtcdKeyNotFound,
)
from response import (
    json_success,
    json_error,
)

def get_config(name):
    with open(name) as f:
        return yaml.safe_load(f)

ddns_config = get_config('config.yaml')
etcd_client = etcd.Client(host=ddns_config['etcd']['host'], port=ddns_config['etcd']['port'])
cloudxns_client = CloudXNS(**ddns_config['cloudxns'])

def update_domain_list(save_to_etcd=True, ttl=14400):
    """
    获取域名列表
    """
    domain_list = []
    for domain in cloudxns_client.domain_list():
        if domain['status'] != 'ok':
            continue
        domain_list.append({
            'id': domain['id'], 
            'domain': domain['domain']
        })

    if save_to_etcd:
        etcd_client.write(
            key=DomainService.LIST, 
            value=domain_list, 
            ttl=ttl
        )
    return domain_list

def update_record_list(domain_id, save_to_etcd=True, ttl=7200):
    """
    更新域名解析
    """
    record_list = []
    for record in cloudxns_client.record_list(domain_id):
        print(record)
        if record['status'] != 'ok':
            continue
        if record['type'] not in ('A', 'AAAA',):
            continue
        record_list.append({
            'record_id': record['record_id'],
            'host_id': record['host_id'],
            'host': record['host'],
            'value': record['value'],
            'update_time': record['update_time'],
        }) 
    if save_to_etcd:
        etcd_client.write(
            key='{}/{}'.format(DomainService.RECORD, domain_id),
            value=record_list,
            ttl=ttl,
        )
    return record_list 


@hug.get('/')
def welcome():
    return json_error("Method not allowed", 405)

@hug.get('/update_addr')
def update_addr(domain: str, sub_domain: str, ip_addr: str):
    try:
        domain_list = eval(etcd_client.get(DomainService.LIST).value)
    except EtcdKeyNotFound:
        domain_list = update_domain_list()
    except TypeError:
        domain_list = update_domain_list()

    domain_id = -1
    for domain_object in domain_list:
        if domain_object['domain'][:-1] == domain:
            domain_id = int(domain_object['id'])
            break

    if domain_id == -1:
        return json_error('Domain not registered', 4001)

    try:
        record_list = eval(etcd_client.get('{}/{}'.format(DomainService.RECORD, domain_id)).value)
    except EtcdKeyNotFound:
        record_list = update_record_list(domain_id)
    except TypeError:
        record_list = update_record_list(domain_id)
    
    for _record in record_list:
        if _record['host'] == sub_domain:
            if _record['value'] == ip_addr:
                return json_success("Record not updated")
            result = cloudxns_client.update_record(
                domain_id=domain_id,
                record_id=_record['record_id'],
                host=sub_domain,
                value=ip_addr,
            )
            return json_success(result)

    return json_success({"result": "Nothing to do", "record_list": record_list})
    

def force_update():
    pass

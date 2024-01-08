import re
import ipaddress
from juniper_curly_braces_to_set import convert_config


def parse_juniper_inactive_ip(data: str) -> list[dict]:
    """

    :param data:
    :return:
    """
    result = []  # list of dict
    reg_exp = re.compile(r'deactivate interfaces (\S+) unit (\S+) family inet address (\S+)', flags=re.MULTILINE)
    reg_exp_ri = re.compile(r'(?:deactivate|set) routing-instances (\S+) interface (\S+)', flags=re.MULTILINE)

    data, comment = convert_config(data, deactivate_inheritance_flag=True)  # конвертируем конфигурацию juniper в display set
    if match := reg_exp_ri.findall(data):
        print(match)
        ri_dct = {t[1]: t[0] for t in match}
    else:
        ri_dct = {}

    if match := reg_exp.findall(data):
        ip_lst = [{'interface': f'{param[0]}.{param[1]}', 'address': param[2], 'ri': ri_dct.get(f'{param[0]}.{param[1]}', 'GRT')} for param in match]
        return ip_lst
    else:
        return []

    # Добавляем routing-instance в словарь адресов
    # for ip_param in ip_lst:
    #     ip = ip_param.get('address')
    #     interface = ip_param.get('interface')
    #     ri = ri_dct.get(interface)
    #     result.append({})


if __name__ == '__main__':

    with open('example.conf', 'r', encoding='utf-8') as file:
        data = file.read()

    result = parse_juniper_inactive_ip(data)
    print(result)



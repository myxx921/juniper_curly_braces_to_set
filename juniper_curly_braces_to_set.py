import re

from collections import defaultdict


def is_branch_start(line_: str) -> bool:
    """
    Checks that the string is a start of a branch.
    :param line_:
    :return:
    """
    if line_.endswith(' {'):
        return True
    else:
        return False


def is_branch_end(line_: str) -> bool:
    """
    Checks that the string is a end of a branch.
    :param line_:
    :return:
    """
    if line_.endswith('}'):
        return True
    else:
        return False


def is_leaf(line_: str) -> bool:
    """
    Checks that the string is a leaf.
    :param line_:
    :return:
    """
    if line_.endswith(';'):
        return True
    else:
        return False


def is_inactive(line_: str) -> bool:
    """
    Checks that the string is inactive.
    :param line_:
    :return:
    """
    if line_.lstrip().startswith('inactive: '):
        return True
    else:
        return False


def is_protected(line_: str) -> bool:
    """
    Checks that the string is protected.
    :param line_:
    :return:
    """
    if line_.lstrip().startswith('protect: '):
        return True
    else:
        return False


def is_multi_line_comment_start(line_: str) -> bool:
    """
    Checks that the string is starts of a multi-line annotation
    :param line_:
    :return:
    """
    if re.search(r'^/\*.*$', line_):
        return True
    else:
        return False


def is_multi_line_comment_end(line_: str) -> bool:
    """
    Checks that the string is end of a multi-line annotation
    :param line_:
    :return:
    """
    if re.search(r'^.*\*/$', line_):
        return True
    else:
        return False


def if_substrin_in_quotation_marks(line_: str) -> bool:
    """
    Checks if there is a quoted substring in the string
    :param line_:
    :return:
    """
    if re.search(r'^.*?".*?".*?$', line_):
        return True
    else:
        return False


def inheritance_deactivate(data_lst: list) -> list:
    """
    Inherits deactivation for all nested records in set format. Useful for parsing deactivated strings.
    :param data_lst:
    :return:
    """

    result_lst = []  # list for collect result strings
    deactivate_lst = []  # list for collecting deactivating strings
    # Collect deactivating string
    for line in data_lst:
        if line.startswith('deactivate '):
            deactivate_lst.append(re.sub(r'^deactivate ', '', line))
    # Analize record
    for line in data_lst:
        if line.startswith('set '):  # skip not "set" record
            normalized_line = re.sub(r'^set ', '', line)  # normalize record
            for deactivate_line in deactivate_lst:  # check whether it is necessary to deactivate the record
                if normalized_line.startswith(deactivate_line):
                    result_lst.append(f'deactivate {normalized_line}')
                    break
            else:
                result_lst.append(line)  # if record not deactivate add to list as is
        else:
            result_lst.append(line)
    return result_lst


def convert_config(data: str, deactivate_inheritance_flag: bool = False) -> tuple[str, str]:
    """
    Convert juniper "curly braces" config to "set" format.
    :param data: juniper "curly braces" config str
    :param deactivate_inheritance_flag:  if True execute deactivation inheritance
    :return: juniper set format config
    """
    multi_line_comment_flag = False  # Flag if multi-line comment starts
    prefix_lst = []  # list of branch name
    result_lst = []  # list of set command
    comments_lst = []  # list of annotation
    comment_line = ''
    # level = 0
    # current_hierarchy_level = 0
    # need_inheritance_deactivate = False

    for line in data.split('\n'):

        line = line.lstrip()  # removing the leading spaces

        # Analize single-line comment
        if line.lstrip().startswith('#'):
            if prefix_lst:
                comments_lst.append('annotate ' + ''.join(prefix_lst) + '"' + line.lstrip('#') + '"')
            continue
        if is_multi_line_comment_start(line) and is_multi_line_comment_end(line):
            comments_lst.append('annotate ' + ''.join(prefix_lst) + line)
            continue
        # Analize multi-line comment
        if is_multi_line_comment_start(line):  # set multi-line comment flag
            multi_line_comment_flag = True
        if multi_line_comment_flag:
            comment_line += line
            continue
        if is_multi_line_comment_end(line) and multi_line_comment_flag:
            comments_lst.append('annotate ' + ''.join(prefix_lst) + line)
            multi_line_comment_flag = False
            comment_line = ''  # clear temp comment
            continue
        line = re.sub(r'; ##.*$', ';', line)  # removing the trailing comment

        # Analize action
        if is_inactive(line):
            line = re.sub(r'^inactive: ', '', line)
            action = 'deactivate '
        elif is_protected(line):
            line = re.sub(r'^protect: ', '', line)
            action = 'protect '
        else:
            action = 'set '

        # with deactivate inheritance online
        # Analize start of branch or leaf
        # if is_branch_start(line):
        #     line = line.rstrip('{')  # normalize prefix
        #     prefix_lst.append(line)  # append prefix to prefix list
        #     current_hierarchy_level = len(prefix_lst)  # current hierarchy level
        #     if action == 'deactivate ' and inactive_inheritance:
        #         need_inheritance_deactivate = True
        #         level = len(prefix_lst)
        #
        #     if need_inheritance_deactivate:
        #         action = 'deactivate '
        #     if action == 'deactivate ':
        #         result_lst.append(action + ''.join(prefix_lst))
        #
        # elif is_leaf(line):
        #     if need_inheritance_deactivate:
        #         action = 'deactivate '
        #     result_lst.append(action + ''.join(prefix_lst) + line.rstrip(';'))
        # elif is_branch_end(line):
        #     prefix_lst.pop()
        #     if need_inheritance_deactivate and level >= current_hierarchy_level:
        #         need_inheritance_deactivate = False

        # Analize start of branch or leaf
        if is_branch_start(line):
            line = line.rstrip('{')  # normalize prefix
            prefix_lst.append(line)  # append prefix to prefix list
            if action == 'deactivate ':  # we need add deactivate branch record
                result_lst.append(action + ''.join(prefix_lst))
        elif is_leaf(line):
            result_lst.append(action + ''.join(prefix_lst) + line.rstrip(';'))
        elif is_branch_end(line):
            prefix_lst.pop()

    if deactivate_inheritance_flag:
        result_lst = inheritance_deactivate(result_lst)

    config_in_set = '\n'.join(result_lst)
    comments_str = '\n'.join(comments_lst)

    return config_in_set, comments_str


def inheritance_configuration_group(data: str):
    """
    Add inheritance set from configuration group
    :return:
    """

    # Make configuration group dict
    configuration_group_dct = defaultdict(list)
    match = re.findall(r'^set groups (\S+) (.*)$', data, flags=re.MULTILINE)
    for item in match:
        configuration_group_dct[item[0]].append(item[1])
    print(configuration_group_dct)
    raise NotImplemented


def cli():
    pass


if __name__ == '__main__':

    with open('example.conf', 'r', encoding='utf-8') as file:
        data = file.read()

    # Print set config
    config, comments = convert_config(data, deactivate_inheritance_flag=True)
    with open('result.txt', 'w', encoding='utf-8') as file:
        file.write(config)

    inheritance_configuration_group(config)

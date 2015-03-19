from api_core.exceptions import InternalServerErrorException
import settings
import re


def parse_haproxy_configtest_output(output):
    """
    This function parses an output of a HAProxy configuration test.
    :param output: output of a 'haproxy' command
    :return: parsed output in a form of a list
    """
    output_sections = re.compile('^\[[A-Z]+\]')
    blacklisted_lines = ' '.join(settings.HAPROXY_BLACKLISTED_OUTPUT)
    configtest_output = output.splitlines()
    parsed_output = []
    previous_line = ''

    if not output:
        return []

    for line in configtest_output:
        if line not in blacklisted_lines:
            if output_sections.match(line):
                if previous_line:
                    parsed_output.append(previous_line)
                previous_line = line
            elif line.startswith('   |'):
                previous_line += line.replace('   |', '')

    return parsed_output


def raise_500_error(return_code, error_message):
    """
    Function simplifies generation of a Internal Server Error with a custom body message. Its primary purpose is to make
    code more clean in API views working with a 'haproxy' command.
    :param return_code: exit code generated after command execution
    :param error_message: output to be send with a return code
    :raises: api_core.exceptions.InternalServerErrorException
    """
    data = {'return code': return_code, 'error': error_message}
    raise InternalServerErrorException(detail=data)
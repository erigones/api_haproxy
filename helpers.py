import settings
import re


def parse_haproxy_configtest_output(output):
    """
    This function helps with parsing of error/warning output lines of a HAProxy configuration test.
    :param output: output of a haproxy command run
    :return: list of warnings and alerts
    """
    output_sections = re.compile('^\[[A-Z]+\]')
    blacklisted_lines = ' '.join(settings.HAPROXY_BLACKLISTED_OUTPUT)
    configtest_output = output.splitlines()
    parsed_output = []
    previous_line = ''

    for line in configtest_output:
        if line not in blacklisted_lines:
            if output_sections.match(line):
                if previous_line:
                    parsed_output.append(previous_line)
                previous_line = line
            elif line.startswith('   |'):
                previous_line += line.replace('   |', '')

    return parsed_output

import re
from functools import reduce
import typer
from typing import List
import yaml
import os
import jmespath
from pathlib import Path

DEPENDENCY_REGEXP = re.compile(r'((implementation|api|compile)|(test([\w])+))\s+(\"|\')([^:\s]+)\:([^:\s]+)(\:([^:\s]+))?(\"|\')')
DEPENDENCY_MANAGEMENT_REGEXP = re.compile(r'(dependency)\s+(\"|\')([^:\s]+)\:([^:\s]+)(\:([^:\s]+))?(\"|\')')
PROPERTY_REGEXP = re.compile(r'^([^=]+)=(.*)$')
VERSION_REGEXP = re.compile(r'\$([\w\_]+)')
app = typer.Typer()


@app.command("dep")
def create(
        gradle_file: List[str] = typer.Option(default=[]),
        properties_file: str = typer.Option(default=None)
):
    properties = dict()
    if properties_file is not None:
        for prop_str in open(properties_file).readlines():
            match = PROPERTY_REGEXP.match(prop_str)
            if match is None:
                continue
            property_name = match.group(1)
            value = match.group(2)
            properties[property_name] = value
    for file in gradle_file:
        file_data = open(file).read()

        result = ""

        result += "<dependencies>\n"
        for dep in DEPENDENCY_REGEXP.findall(file_data):
            scope = 'compile' if dep[0] == 'implementation' else 'test'
            version = dep[8]
            version_match = VERSION_REGEXP.match(version)
            if version_match is not None:
                version = properties.get(version_match.group(1))
            artifact_id = dep[6]
            group_id = dep[5]
            if version is not None and version != '':
                result += """
                    <dependency>
                      <groupId>%s</groupId>
                      <artifactId>%s</artifactId>
                      <version>%s</version>
                      <scope>%s</scope>
                    </dependency>
                """ % (group_id, artifact_id, version, scope)
            else:
                result += """
                    <dependency>
                      <groupId>%s</groupId>
                      <artifactId>%s</artifactId>
                      <scope>%s</scope>
                    </dependency>
                """ % (group_id, artifact_id, scope)
        result += "</dependencies>\n\n"

        result += "<dependencyManagement>\n<dependencies>\n"
        for dep in DEPENDENCY_MANAGEMENT_REGEXP.findall(file_data):
            version = dep[5]
            version_match = VERSION_REGEXP.match(version)
            if version_match is not None:
                version = properties.get(version_match.group(1))
            artifact_id = dep[3]
            group_id = dep[2]
            result += """
                  <dependency>
                    <groupId>%s</groupId>
                    <artifactId>%s</artifactId>
                    <version>%s</version>
                  </dependency>
            """ % (group_id, artifact_id, version)
        result += "</dependencyManagement>\n</dependencies>\n"

        output = os.path.basename(os.path.dirname(os.path.realpath(file))) + ".pom.xml"
        f = open(output, "w")
        f.write(result)
        f.close()


if __name__ == '__main__':
    app()

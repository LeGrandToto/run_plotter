from datetime import datetime
from textwrap import indent
from typing import Optional
import xml.etree.ElementTree as ET

def as_text(element: ET.Element, indent: int= 0) -> list[str]:
    def render_tag(element: ET.Element) -> str:
        attributes = [f'{attr}="{value}"' for attr, value in element.attrib.items()]
        if attributes:
            attributes = " " + " ".join(attributes)
        else:
            attributes = ""
        return ("  " * indent) + f"<{element.tag}{attributes}>"

    def render_closing_tag(element: ET.Element, indent= 0) -> str:
        return ("  " * indent) + f"</{element.tag}>\n"
    lines = [render_tag(element)]
    if element.text:
        lines.append(element.text)
    if len(element):
        lines[-1] += "\n"
    for child in element:
        lines.extend(as_text(child, indent + 1))
    lines.append(render_closing_tag(element, indent= indent if len(element) else 0))
    return lines
    

def main(gpx_path: str, output: str, initial_time: Optional[datetime]= None):
    with open(gpx_path, "r") as fd:
        with open(output, "w") as dest:
            for line in fd.readlines():
                line = [line]
                if "trkpt" in line[0]:
                    root = ET.fromstringlist(line[0])
                    new_root = ET.Element(root.tag)
                    for attribute, value in root.attrib.items():
                        if attribute == "lat" or attribute == "lon":
                            value = value.replace(" ", "")
                            new_root.attrib[attribute] = value
                        elif attribute == "tim":
                            initial_time = datetime.fromtimestamp(int(value.replace(" ", "")))
                            time_element = ET.Element("time")
                            time_element.text = f"{initial_time.year}-{initial_time.month:02d}-{initial_time.day}T{initial_time.time()}Z"
                            new_root.append(time_element)
                    
                    line = as_text(new_root, indent= 3)
                    print(line)
                    # line_parts = line[0].split('"')
                    # line[0] = '"'.join((line_part.replace(" ", "") if index in [1, 3, 5] else line_part for index, line_part in enumerate(line_parts)))
                    
                dest.writelines(line)


def parse_args():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("gpx_path", help= "GPX file to fix")
    parser.add_argument("output", help= "destination path to save the fixed file")
    parser.add_argument("-initial_time", type= datetime, help= "Time of the first waypoint of the track")

    args = parser.parse_args()

    return args.__dict__

if __name__ == "__main__":
    main(**parse_args())

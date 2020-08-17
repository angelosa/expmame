from abc import ABC, abstractmethod

def xml_read_subfield(xml_item, subkey):
    return [child for child in xml_item if child.tag == subkey][0].text

class SWListReader(ABC):
    def __init__(self, src_path, tqdm_wrapper):
        self.src_path = src_path
        self.tqdm = tqdm_wrapper

    @abstractmethod
    def xml_parse_item(self, xml_item):
        pass

    def xml_to_records(self):
        import xml.etree.ElementTree as EL
        xml_root = EL.parse(self.src_path).getroot()
        xml_software_list = [child for child in xml_root if child.tag == "software"]
        converted_list = []
        for xml_item in self.tqdm(xml_software_list):
            converted_list.append(self.xml_parse_item(xml_item))

        return converted_list

    @abstractmethod
    def file_parse_item(self, sw_item, sw_status, buffered_file):
        return {}

    def augmentate_items(self, converted_list):
        with open(self.src_path, "r", encoding="utf-8", newline="\n") as raw_xml:
            buf = raw_xml.readlines()
        aug_list = []
        for item in self.tqdm(converted_list):
            aug_item = self.file_parse_item(item["name"], item["supported"], buf)
            aug_list.append({
                **item,
                **aug_item
            })

        return aug_list


class SWListArchimedesReader(SWListReader):
    def xml_parse_item(self, xml_item):
        return {
            "name": xml_item.get("name"),
            "cloneof": xml_item.get("cloneof"),
            "supported": xml_item.get("supported"),
            "description": xml_read_subfield(xml_item, "description"),
            "year":  xml_read_subfield(xml_item, "year"),
            "publisher": xml_read_subfield(xml_item, "publisher")
        }

    def file_parse_item(self, sw_item, sw_status, buffered_file):
        import re
        # TODO: use beautiful soup instead
        def extract_endidx(sw_name, file_str):
            for item in file_str:
                line_read = item.strip()
                if re.match(r"\<software name\=\"" + sw_name + "\"", line_read):
                    return file_str.index(item)
            raise ValueError("header not found for sw_name: " + sw_name)

        def extract_startidx(file_str, end_idx):
            reverse_list = file_str[end_idx::-1]
            comments = []
            for item in reverse_list:
                line_read = item.strip()
                if re.match(r"\<!--(.*)-->", line_read):
                    comments.append(line_read)
                if re.match(r"<\/software>", line_read) or re.match(r"<softwarelist ", line_read):
                    return "\n".join(comments[::-1]).replace("<!--","").replace("-->","")
            raise ValueError("startidx not found " + str(end_idx))
        
        def calculate_result(sw_item, sw_status, ext_status):
            if sw_status is not None:
                return sw_status
            
            if ext_status is None:
                return "untested"

            if ext_status.lower().find("boot ok") != -1:
                return "yes"

            return "untested"
            # crude validation
            #raise NotImplementedError(sw_item, sw_status, ext_status)

        ext_status = extract_startidx(
            buffered_file, 
            extract_endidx(sw_item, buffered_file)
        )

        # TODO: types should be an internal flag, 
        # change the anchor in the file itself or even split the XML into separate entities
        ext_status = ext_status.replace("Notes of interest \n Games \n ", "").strip()
        if ext_status in [
                "Public Domain", "Application", "Magazines", "Hardware", 
                "Languages", "Educational", "Business", "Compilations", "System"
            ]:
            ext_status = ""
        ext_status = ext_status.replace("\n", "")
        return {
            "status": ext_status,
            # override the XML value for now ...
            "supported": calculate_result(sw_item, sw_status, ext_status)
        }

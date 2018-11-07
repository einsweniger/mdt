from pathlib import Path
from . import strained
import sys
import json
from pprint import pprint
from code import interact
from inspect import Parameter, Signature
from typing import List, Tuple


def find_folders(folder: Path):
    for path in folder.iterdir():
        if path.is_dir():
            yield path


def find_html(folder: Path):
    for path in folder.iterdir():
        if path.is_file() and path.suffix == '.json':
            yield path


def find_function_files(root: Path):
    for folder in find_folders(root):
        for subfolder in find_folders(folder):
            yield from find_html(subfolder)


def check_simple_argument(arg: dict):
    if 'type' not in arg:
        pprint(arg)
        interact(banner='simple arg has no type', local=locals())
    if 'description' not in arg:
        pprint(arg)
        interact(banner='simple arg has no description', local=locals())


text_to_class = {
    'int': int,
    'str': str,
    'float': float
}


def build_simple_required(arg) -> Parameter:
    structure = arg.pop('structure')
    tp = text_to_class[structure.pop('type')]
    _ = structure.pop('description')
    if len(structure) != 0:
        interact(banner='structure has more contents', local=locals())

    p = Parameter(arg['name'], Parameter.POSITIONAL_OR_KEYWORD, annotation=tp)
    return p


def build_simple_default(arg) -> Parameter:
    structure = arg.pop('structure')
    tp = text_to_class[structure.pop('type')]
    default = structure.pop('default')
    _ = structure.pop('description')
    if len(structure) != 0:
        interact(banner='structure has more contents', local=locals())

    if tp in (int, float):
        try:
            default = tp(default)
        except ValueError:
            default = tp(0)

    p = Parameter(arg['name'], Parameter.POSITIONAL_OR_KEYWORD, annotation=tp, default=default)
    return p


def build_simple_parameters(args) -> Tuple[List[Parameter],List[Parameter]]:
    required = [Parameter('self', Parameter.POSITIONAL_OR_KEYWORD)]
    default = []
    for arg in args:
        annotation = arg.pop('annotation')
        if 'required' in annotation:
            annotation.pop('required')
            if not 0 == len(annotation):
                interact(banner='annotation has more contents', local=locals())
            required.append(build_simple_required(arg))
            continue

        if 'default' in annotation:
            annotation.pop('default')
            if not 0 == len(annotation):
                interact(banner='annotation has more contents', local=locals())
            default.append(build_simple_default(arg))
            continue
        interact(banner='simple param is not required, has no default?', local=locals())
    return required, default



def gen_function_body(sig: Signature):
    data = []
    "return self.post_web_service('mod_assign_save_grade', args=data)"
    for param in sig.parameters:
        if 'self'== param:
            continue
        data.append((3,f"'{param}': {param},"))
    if len(data) == 0:
        return [(2,'data = {}')]
    return [(2,'data = {')] + data + [(2,'}')]


def gen_doc_string(arguments, description, response_info):
    docs = []
    docs.append((2, '"""'))
    docs.append((2, description))
    docs.append((2, ''))
    for argument in arguments:
        p_name = argument.pop('name')
        p_descr = argument.pop('description')
        docs.append((2, f':param {p_name}: {p_descr}'))
        # param_docs.append(f'        :param {p_name}: {p_descr}')
    if response_info is not None:
        docs.append((2, f':return: {response_info["description"]}'))
        # param_docs.append(f'        :return: {response_info["description"]}')
        docs.append((2, '"""'))
    return docs


def read_annotation(annotations):
    if annotations is None:
        return None, False

    if 'description' not in annotations:
        pprint(annotations)
        interact(banner='had no description!', local=locals())

    description = annotations.pop('description')
    optional = False
    if 'optional' in annotations:
        optional = annotations.pop('optional')

    if len(annotations) != 0:
        pprint(annotations)
        interact(banner='annotations had more info!', local=locals())

    return description, optional


def build_complex_response(response_info, depth=0):
    if type(response_info) is not list:
        # there are two cases where moodle returns an empty object
        # {'default': {}, 'type': 'object'}
        # TODO
        return

    if len(response_info) != 2:
        # pprint(response_info)
        # interact(banner='response_info is not len 2', local=locals())
        annotations = None
        structure = response_info
    else:
        annotations, structure = response_info

    description, optional = read_annotation(annotations)
    if type(structure) is dict:
        if '' in structure:
            # anonymous object
            # todo
            thing = structure.pop('')
            return
        else:
            #pprint(structure)
            for name, definition in structure.items():
                if 'type' in definition and definition['type'] in text_to_class:
                    print(f'found simple argument {name} -> {definition}')
                    if definition is None:
                        interact(banner='definition is None', local=locals())
                else:
                    return build_complex_response(definition, depth+1)


    if type(structure) is list:
        if len(structure) == 1:
            # list of objects
            pass
        else:
            pprint(structure)
            interact(banner='structure', local=locals())


def main(root: Path):
    function_descriptions = []
    for path in find_function_files(root):
        function_description = []
        funcname = path.stem
        #print(funcname)

        structure = json.loads(path.read_text())

        simple = []
        complex = []
        arguments = structure.pop('Arguments')
        for argument in arguments:
            kind = argument.pop('kind')
            if 'simple' == kind:
                simple.append(argument)
            else:
                complex.append(argument)
        if len(complex) != 0:
            continue
        simple_required, simple_default = build_simple_parameters(simple)

        response_kind = None
        response_info = None
        description = structure.pop("description")
        response = structure.pop('Response')
        if  response is not None:
            response_kind, response_info = response
            if 'complex' == response_kind:

                build_complex_response(response_info)
                continue
            response_type = text_to_class[response_info['type']]
        else:
            response_type = Signature.empty

        sig = Signature(simple_required+simple_default,return_annotation=response_type)
        function_description.append((1, f'def {funcname}{sig}:'))

        function_description += gen_doc_string(arguments, description, response_info)
        function_description += gen_function_body(sig)
        function_description.append((2,f"return self.post_web_service('{funcname}', args=data)"))
        asd = ''
        for indent, line in function_description:
            asd += '    '*indent + line + '\n'
        #print(asd)


if __name__ == '__main__':
    try:
        api_folder = str(sys.argv[1])
    except KeyError:
        print('please provide the folder of the retreived documentation as parameter')
        raise SystemExit(1)
    folder = Path(api_folder)
    if not folder.is_dir():
        raise SystemExit(f'no such directory {folder}')

    file = folder / strained
    if not file.is_file():
        raise SystemExit(f'no such file {file}')
    main(folder)

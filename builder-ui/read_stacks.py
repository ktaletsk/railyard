import os
import yaml
import tempfile
import copy
import hashlib

def sort_dep_list(dep_list):
    return sorted(dep_list, key=lambda k: next(iter(k)) if type(k)==dict else k)

def get_hash(package):
    p = copy.deepcopy(package)
    
    # Name of the base stack does not matter for hash
    p.pop('name')
    
    # Sort everything by package name or put into set to make hash stable under permutations
    p['dependencies']['env'] = sort_dep_list(p['dependencies']['env'])
    p['dependencies']['apt'] = sort_dep_list(p['dependencies']['apt'])
    p['dependencies']['conda'] = sort_dep_list(p['dependencies']['conda'])
    p['dependencies']['pip'] = sort_dep_list(p['dependencies']['pip'])
    p['dependencies']['labextensions'] = sort_dep_list(p['dependencies']['labextensions'])
    p['dependencies']['scripts'] = sort_dep_list(p['dependencies']['scripts'])
    p['dependencies']['addfiles'] = sort_dep_list(p['dependencies']['addfiles'])
    
    return hashlib.sha256(repr(sorted(p.items())).encode()).hexdigest()

def dockerfile_block(name, lines):
    offset = ' ' * (len(name) + 1)
    return name + ' ' + ('\n'+offset).join(lines) + '\n'

def dockerfile_comment(comment):
    return '# ' + comment + '\n'

def readStacks(base_stack, additional_stacks):
    # Open base stack
    with open(base_stack) as file:
        base_stack_obj = yaml.safe_load(file)

    # Open additional stacks
    for stack in additional_stacks:
        with open(stack) as file:
            stack_obj = yaml.safe_load(file)
            
#             if stack_obj==None:
#                 return base_stack_obj

            if 'dependencies' in stack_obj:
                # Merge environment variables
                if 'env' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['env'].extend(stack_obj['dependencies']['env'])

                # Merge apt-get dependencies
                if 'apt' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['apt'].extend(stack_obj['dependencies']['apt'])

                # Merge conda dependencies
                if 'conda' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['conda'].extend(stack_obj['dependencies']['conda'])

                # Merge pip dependencies
                if 'pip' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['pip'].extend(stack_obj['dependencies']['pip'])

                # Merge jupyter labextensions
                if 'labextensions' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['labextensions'].extend(stack_obj['dependencies']['labextensions'])

                # Merge install scripts
                if 'scripts' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['scripts'].extend(stack_obj['dependencies']['scripts'])

                # Merge addfiles
                if 'addfiles' in stack_obj['dependencies']:
                    print(stack_obj['dependencies']['addfiles'])
                    base_stack_obj['dependencies']['addfiles'].extend(stack_obj['dependencies']['addfiles'])

    return base_stack_obj
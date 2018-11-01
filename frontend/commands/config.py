from . import pm

@pm.command(
    'dump config'
)
def config():
    print(WorkTree.get_global_config_values())
    for cfg in WorkTree.get_config_file_list():
        print(cfg)

import cProfile, pstats, os


### http://stackoverflow.com/questions/5375624/a-decorator-that-profiles-a-method-call-and-logs-the-profiling-result ###
from cloudshell.cp.azure.domain.services.parsers.azure_model_parser import AzureModelsParser


def profileit(scriptName):
    def inner(func):
        profiling = r'C:\TFS\QualiSystems\Trunk\Drop\TestShell\ExecutionServer\python\2.7.10\Scripts'

        def wrapper(*args, **kwargs):
            if not profiling:
                return func(*args, **kwargs)
            reservation = args[1].reservation
            reservation_id = reservation.reservation_id
            environment_name = reservation.environment_name
            prof = cProfile.Profile()
            retval = prof.runcall(func, *args, **kwargs)
            # prof.snapshot_stats()
            file_name = os.path.join(profiling, scriptName + "_" + environment_name + "_" + reservation_id + ".text")
            dump_name = os.path.join(profiling, scriptName + "_" + environment_name + "_" + reservation_id + ".prof")
            prof.dump_stats(dump_name)
            s = open(file_name, 'w')
            stats = pstats.Stats(prof, stream=s)
            stats.dump_stats(dump_name)
            stats.strip_dirs().sort_stats('cumtime').print_stats()
            return retval

        return wrapper

    return inner

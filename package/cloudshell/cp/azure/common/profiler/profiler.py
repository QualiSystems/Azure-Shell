import cProfile, pstats, os

import random


def profileit(scriptName):
    def inner(func):
        profiling = r'TBD'

        def wrapper(*args, **kwargs):
            if not profiling:
                return func(*args, **kwargs)
            type_args = type(args)
            type_kwargs = type(kwargs)

            len_args = len(args)
            len_kwargs = len(kwargs)

            if len_args >= 2:
                try:
                    reservation = args[1].reservation
                except:
                    reservation = args[1].remote_reservation
            else:
                try:
                    reservation = kwargs["command_context"].reservation
                except:
                    kwargs["command_context"].remote_reservation

            if reservation:
                reservation_id = reservation.reservation_id
                environment_name = reservation.environment_name
                prof = cProfile.Profile()
                retval = prof.runcall(func, *args, **kwargs)
                # prof.snapshot_stats()
                random_var = str(random.randrange(1, 100))
                file_name = os.path.join(profiling,
                                         scriptName + "_" + environment_name + "_" + reservation_id + "_" + random_var + ".text")
                dump_name = os.path.join(profiling,
                                         scriptName + "_" + environment_name + "_" + reservation_id + ".prof")
                # prof.dump_stats(dump_name)
                s = open(file_name, 'w')
                stats = pstats.Stats(prof, stream=s)
                # stats.dump_stats(dump_name)
                stats.strip_dirs().sort_stats('cumtime').print_stats()
                return retval
            else:
                return func(*args, **kwargs)

        return wrapper

    return inner
